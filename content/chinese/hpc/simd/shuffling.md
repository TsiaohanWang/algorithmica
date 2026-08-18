---
title: 寄存器内的混洗
weight: 6
---

[掩码](../masking)让你可以把操作只作用于向量的部分元素。这是一种非常有效且常用的数据操作技巧，但在许多情况下，你需要执行更高级的操作——在向量寄存器内部重排数值，而不仅仅是与其他向量混合。

问题是，在硬件中为每一种可能的用途都单独加入一条元素混洗指令是不现实的。但我们能做到的是：只加入一条通用的置换指令，它接受一个置换的下标，并通过预先计算的查找表来产生这些下标。

这个总体想法也许太抽象了，所以我们直接看例子。

### 混洗与 popcount

*总体计数*（population count），又称*汉明重量*（Hamming weight），是二进制串中 `1` 位的个数。

这是一项常用操作，因此 x86 上有一条单独的指令来计算一个字的总体计数：

```c++
const int N = (1<<12);
int a[N];

int popcnt() {
    int res = 0;
    for (int i = 0; i < N; i++)
        res += __builtin_popcount(a[i]);
    return res;
}
```

它还支持 64 位整数，使总吞吐量提升一倍：

```c++
int popcnt_ll() {
    long long *b = (long long*) a;
    int res = 0;
    for (int i = 0; i < N / 2; i++)
        res += __builtin_popcountl(b[i]);
    return res;
}
```

所需的只有两条指令：融合了加载的 popcount 和加法。它们都有很高的吞吐量，因此代码每周期处理约 $8+8=16$ 字节——它受限于这块 CPU 上 4 的译码宽度。

这些指令大约在 2008 年随 SSE4 加入 x86 CPU。让我们暂时回到向量化甚至还没成为一件事的年代，尝试用别的手段实现 popcount。

朴素的办法是逐位地遍历二进制串：

```c++
__attribute__ (( optimize("no-tree-vectorize") ))
int popcnt() {
    int res = 0;
    for (int i = 0; i < N; i++)
        for (int l = 0; l < 32; l++)
            res += (a[i] >> l & 1);
    return res;
}
```

不出所料，它只比每周期 ⅛ 字节稍快一点——大约在 0.2 左右。

我们可以不按单个比特、而按字节来处理：先[预计算](/hpc/compilation/precalc)一个 256 元素的小*查找表*，存各个字节的总体计数，然后在遍历数组原始字节时查询它：

```c++
struct Precalc {
    alignas(64) char counts[256];

    constexpr Precalc() : counts{} {
        for (int m = 0; m < 256; m++)
            for (int i = 0; i < 8; i++)
                counts[m] += (m >> i & 1);
    }
};

constexpr Precalc P;

int popcnt() {
    auto b = (unsigned char*) a; // careful: plain "char" is signed
    int res = 0;
    for (int i = 0; i < 4 * N; i++)
        res += P.counts[b[i]];
    return res;
}
```

现在它每周期处理约 2 字节，如果改用 16 位字（`unsigned short`）会升到约 2.7。

相比 `popcnt` 指令，这个方案仍然非常慢，但它现在可以向量化了。我们不打算用 [gather](../moving#non-contiguous-load) 指令来加速它，而是走另一条路：让查找表小到能装进一个寄存器，然后用特殊的 [pshufb](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#text=pshuf&techs=AVX,AVX2&expand=6331) 指令并行地查表。

最初随 128 位 SSE3 引入的 `pshufb` 接受两个寄存器：一个是包含 16 个字节值的查找表，另一个是 16 个 4 位下标（0 到 15）的向量，指定每个位置选哪个字节。在 256 位 AVX2 中，不再使用带别扭的 5 位下标的 32 字节查找表，而是有一条指令独立地在两个 128 位通道上执行同样的混洗操作。

因此，对我们的用途，我们创建一张 16 字节的查找表，存每个半字节（半个字节）的总体计数，重复两遍：

```c++
const reg lookup = _mm256_setr_epi8(
    /* 0 */ 0, /* 1 */ 1, /* 2 */ 1, /* 3 */ 2,
    /* 4 */ 1, /* 5 */ 2, /* 6 */ 2, /* 7 */ 3,
    /* 8 */ 1, /* 9 */ 2, /* a */ 2, /* b */ 3,
    /* c */ 2, /* d */ 3, /* e */ 3, /* f */ 4,

    /* 0 */ 0, /* 1 */ 1, /* 2 */ 1, /* 3 */ 2,
    /* 4 */ 1, /* 5 */ 2, /* 6 */ 2, /* 7 */ 3,
    /* 8 */ 1, /* 9 */ 2, /* a */ 2, /* b */ 3,
    /* c */ 2, /* d */ 3, /* e */ 3, /* f */ 4
);
```

现在，要计算一个向量的总体计数，我们把它的每个字节拆成低、高两个半字节，然后用这张查找表取回它们的计数。剩下的工作就是仔细地把它们加起来：

```c++
const reg low_mask = _mm256_set1_epi8(0x0f);

int popcnt() {
    int k = 0;

    reg t = _mm256_setzero_si256();

    for (; k + 15 < N; k += 15) {
        reg s = _mm256_setzero_si256();
        
        for (int i = 0; i < 15; i += 8) {
            reg x = _mm256_load_si256( (reg*) &a[k + i] );
            
            reg l = _mm256_and_si256(x, low_mask);
            reg h = _mm256_and_si256(_mm256_srli_epi16(x, 4), low_mask);

            reg pl = _mm256_shuffle_epi8(lookup, l);
            reg ph = _mm256_shuffle_epi8(lookup, h);

            s = _mm256_add_epi8(s, pl);
            s = _mm256_add_epi8(s, ph);
        }

        t = _mm256_add_epi64(t, _mm256_sad_epu8(s, _mm256_setzero_si256()));
    }

    int res = hsum(t);

    while (k < N)
        res += __builtin_popcount(a[k++]);

    return res;
}
```

这段代码每周期处理约 30 字节。理论上内层循环能做到 32，但因为 8 位计数器可能溢出，我们每 15 次迭代就必须停下它。

`pshufb` 指令在有些 SIMD 算法里如此关键，以至于想出这个算法的 [Wojciech Muła](http://0x80.pl/)——把它当作了自己的 [Twitter 账号](https://twitter.com/pshufb)。你还可以算得更快：看看他的 [GitHub 仓库](https://github.com/WojciechMula/sse-popcount)，里面有各种向量化的 popcount 实现；他的[最新论文](https://arxiv.org/pdf/1611.07612.pdf)则对最先进的方案做了详细讲解。

### 置换与查找表

本章最后一个主要例子是 `filter`（过滤）。它是一种非常重要的数据处理原语：接受一个数组作为输入，只把满足给定谓词的元素（按原有顺序）写出来。

在单线程标量情形下，实现它轻而易举——维护一个计数器，每次写入时递增：

```c++
int a[N], b[N];

int filter() {
    int k = 0;

    for (int i = 0; i < N; i++)
        if (a[i] < P)
            b[k++] = a[i];

    return k;
}
```

要对它做向量化，我们使用 `_mm256_permutevar8x32_epi32` 内建函数。它接受一个值向量，并用一个下标向量逐一选取它们。尽管名字里有 "permute"，它并不是*置换*这些值，而只是*复制*它们来构成一个新向量：结果中允许出现重复。

我们算法的总体思路如下：

- 在一个数据向量上计算谓词——在本例中，即执行比较得到掩码；
- 用 `movemask` 指令得到一个标量的 8 位掩码；
- 用这个掩码去索引一张查找表，它返回一个置换，把满足谓词的元素（按原顺序）移到向量开头；
- 用 `_mm256_permutevar8x32_epi32` 内建函数置换这些值；
- 把整个置换后的向量写进缓冲区——它可能带一些尾部垃圾，但前缀是正确的；
- 计算标量掩码的总体计数，并把缓冲区指针移动这个数量。

首先，我们需要预计算这些置换：

```c++
struct Precalc {
    alignas(64) int permutation[256][8];

    constexpr Precalc() : permutation{} {
        for (int m = 0; m < 256; m++) {
            int k = 0;
            for (int i = 0; i < 8; i++)
                if (m >> i & 1)
                    permutation[m][k++] = i;
        }
    }
};

constexpr Precalc T;
```

然后就可以实现算法本身：

```c++
const reg p = _mm256_set1_epi32(P);

int filter() {
    int k = 0;

    for (int i = 0; i < N; i += 8) {
        reg x = _mm256_load_si256( (reg*) &a[i] );
        
        reg m = _mm256_cmpgt_epi32(p, x);
        int mask = _mm256_movemask_ps((__m256) m);
        reg permutation = _mm256_load_si256( (reg*) &T.permutation[mask] );
        
        x = _mm256_permutevar8x32_epi32(x, permutation);
        _mm256_storeu_si256((reg*) &b[k], x);
        
        k += __builtin_popcount(mask);
    }

    return k;
}
```

向量化版本实现起来要费些功夫，但它比标量版本快 6–7 倍（当 `P` 极低或极高时加速比略小，因为[分支变得可预测](/hpc/pipelining/branching)）。

![](../img/filter.svg)

循环性能仍然相对较低——每次迭代耗时 4 个 CPU 周期——因为在这块 CPU（Zen 2）上，`movemask`、`permute` 和 `store` 的吞吐量都很低，而且都要经过同一个执行端口（P2）。在大多数其他 x86 CPU 上，你可以预期它快约 2 倍。

在 AVX-512 上过滤还能实现得更快得多：它有一条特殊的 "[compress](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html#ig_expand=7395,7392,7269,4868,7269,7269,1820,1835,6385,5051,4909,4918,5051,7269,6423,7410,150,2138,1829,1944,3009,1029,7077,519,5183,4462,4490,1944,1395&text=_mm512_mask_compress_epi32)" 指令，接受一个数据向量和一个掩码，把未屏蔽的元素连续写出来。这在那些依赖各种过滤子程序的算法（如快速排序）中会产生巨大的差别。

<!--

你可以使用寄存器，也可以从内存中取。还有一些使用立即数（编译期常数？）

_mm256_permute2x128_si256 — 交换通道
_mm256_slli_si256 srli
_mm256_permute_ps 使用掩码

https://stackoverflow.com/questions/9795529/how-to-find-the-horizontal-maximum-in-a-256-bit-avx-vector Norbert P. 和 Peter Cordes

_MM_SHUFFLE

https://stackoverflow.com/questions/37088449/macro-for-generating-immediates-for-avx-shuffle-intrinsics

-->
