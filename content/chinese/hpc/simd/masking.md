---
title: 掩蔽与混合
weight: 4
---

SIMD 编程的一大挑战是控制流的选项非常有限——因为你施加到向量上的操作对其所有元素都是一样的。

这使得那些通常用 `if` 或任何其他分支就能轻松解决的问题变得困难得多。在 SIMD 中，它们必须借助各种[无分支编程](/hpc/pipelining/branchless)技术来处理，而这些技术并不总是那么容易套用。

### 掩蔽

让计算无分支的主要方法是通过*谓词执行*（predication）——同时计算两个分支的结果，然后要么用某种算术技巧，要么用一条特殊的「条件移动」指令：

```c++
for (int i = 0; i < N; i++)
    a[i] = rand() % 100;

int s = 0;

// branch:
for (int i = 0; i < N; i++)
    if (a[i] < 50)
        s += a[i];

// no branch:
for (int i = 0; i < N; i++)
    s += (a[i] < 50) * a[i];

// also no branch:
for (int i = 0; i < N; i++)
    s += (a[i] < 50 ? a[i] : 0);
```

要向量化这个循环，我们需要两条新指令：

- `_mm256_cmpgt_epi32`：比较两个向量中的整数，如果第一个元素大于第二个元素，就产生一个全 1 的掩码，否则产生全 0 的掩码。
- `_mm256_blendv_epi8`：根据提供的掩码混合（合并）两个向量的值。

通过对向量的元素进行掩蔽和混合，使只有选中的子集受到计算影响，我们就可以用类似于条件移动的方式执行谓词操作：

```c++
const reg c = _mm256_set1_epi32(49);
const reg z = _mm256_setzero_si256();
reg s = _mm256_setzero_si256();

for (int i = 0; i < N; i += 8) {
    reg x = _mm256_load_si256( (reg*) &a[i] );
    reg mask = _mm256_cmpgt_epi32(x, c);
    x = _mm256_blendv_epi8(x, z, mask);
    s = _mm256_add_epi32(s, x);
}
```

（为简洁起见，省略了一些细节，例如[水平求和以及数组剩余部分的处理](../reduction)。）

这就是 SIMD 中通常执行谓词的方式，但它并不总是最优的。我们可以利用混合的两个值之一是 0 这个事实，改用掩码的按位 `and` 而不是混合：

```c++
const reg c = _mm256_set1_epi32(50);
reg s = _mm256_setzero_si256();

for (int i = 0; i < N; i += 8) {
    reg x = _mm256_load_si256( (reg*) &a[i] );
    reg mask = _mm256_cmpgt_epi32(c, x);
    x = _mm256_and_si256(x, mask);
    s = _mm256_add_epi32(s, x);
}
```

这个循环会稍快一些，因为在这颗特定的 CPU 上，向量 `and` 比 `blend` 少花一个周期。

还有其他几条指令支持把掩码作为输入，最值得注意的是：

- `_mm256_blend_epi32` 内建函数是一个 `blend`，它接受 8 位整数掩码而不是向量（这就是它末尾没有 `v` 的原因）。
- `_mm256_maskload_epi32` 和 `_mm256_maskstore_epi32` 内建函数：从内存加载/存储一个 SIMD 块，并一次性与掩码做 `and` 运算。

我们也可以对内置向量类型使用谓词：

```c++
vec *v = (vec*) a;
vec s = {};

for (int i = 0; i < N / 8; i++)
    s += (v[i] < 50 ? v[i] : 0);
```

所有这些版本都能达到约 13 GFLOPS 的性能，因为这个例子太简单，编译器可以完全靠自己完成向量化。让我们继续看一些无法自动向量化的更复杂的例子。

### 查找

在下一个例子中，我们需要在数组中查找某个特定的值并返回它的位置（也就是 `std::find`）：

```c++
const int N = (1<<12);
int a[N];

int find(int x) {
    for (int i = 0; i < N; i++)
        if (a[i] == x)
            return i;
    return -1;
}
```

为了给 `find` 函数做基准测试，我们用从 $0$ 到 $(N - 1)$ 的数填充数组，然后反复查找一个随机元素：

```c++
for (int i = 0; i < N; i++)
    a[i] = i;

for (int t = 0; t < K; t++)
    checksum ^= find(rand() % N);
```

标量版本大约有 4 GFLOPS 的性能。这个数字包含了我们不必处理的元素，所以请在脑海中把这个数字除以 2（即平均需要检查的元素比例）。

要向量化它，我们需要把一个元素向量与要查找的值比较是否相等，产生一个掩码，然后以某种方式检查这个掩码是否为零。如果不是零，那么要找的元素就在这个 8 元素块的某个位置。

要检查掩码是否为零，可以使用 `_mm256_movemask_ps` 内建函数：它取出向量中每个 32 位元素的最高位，生成一个 8 位整数掩码。然后我们可以检查这个掩码是否非零——如果非零，还可以用 `ctz` 指令立刻得到索引：

```c++
int find(int needle) {
    reg x = _mm256_set1_epi32(needle);

    for (int i = 0; i < N; i += 8) {
        reg y = _mm256_load_si256( (reg*) &a[i] );
        reg m = _mm256_cmpeq_epi32(x, y);
        int mask = _mm256_movemask_ps((__m256) m);
        if (mask != 0)
            return i + __builtin_ctz(mask);
    }

    return -1;
}
```

这个版本大约有 20 GFLOPS，比标量版本快约 5 倍。热循环里只用 3 条指令：

```nasm
vpcmpeqd  ymm0, ymm1, YMMWORD PTR a[0+rdx*4]
vmovmskps eax, ymm0
test      eax, eax
je        loop
```

检查一个向量是否为零是常见操作，SIMD 中有一个类似于 `test` 的操作可以用于此目的：

```c++
int find(int needle) {
    reg x = _mm256_set1_epi32(needle);

    for (int i = 0; i < N; i += 8) {
        reg y = _mm256_load_si256( (reg*) &a[i] );
        reg m = _mm256_cmpeq_epi32(x, y);
        if (!_mm256_testz_si256(m, m)) {
            int mask = _mm256_movemask_ps((__m256) m);
            return i + __builtin_ctz(mask);
        }
    }

    return -1;
}
```

我们后面仍然使用 `movemask` 来做 `ctz`，但热循环现在少了一条指令：

```nasm
vpcmpeqd ymm0, ymm1, YMMWORD PTR a[0+rdx*4]
vptest   ymm0, ymm0
je       loop
```

这对性能提升不大，因为 `vptest` 和 `vmovmskps` 的吞吐量都为 1，无论我们在循环中做其他什么事，它们都会成为计算的瓶颈。

为了绕过这个限制，我们可以按 16 个元素一块迭代，用按位 `or` 合并两个 256 位 AVX2 寄存器独立比较的结果：

```c++
int find(int needle) {
    reg x = _mm256_set1_epi32(needle);

    for (int i = 0; i < N; i += 16) {
        reg y1 = _mm256_load_si256( (reg*) &a[i] );
        reg y2 = _mm256_load_si256( (reg*) &a[i + 8] );
        reg m1 = _mm256_cmpeq_epi32(x, y1);
        reg m2 = _mm256_cmpeq_epi32(x, y2);
        reg m = _mm256_or_si256(m1, m2);
        if (!_mm256_testz_si256(m, m)) {
            int mask = (_mm256_movemask_ps((__m256) m2) << 8)
                     +  _mm256_movemask_ps((__m256) m1);
            return i + __builtin_ctz(mask);
        }
    }

    return -1;
}
```

移除了这个障碍之后，性能现在达到峰值约 34 GFLOPS。但为什么不是 40？它难道不该快一倍吗？

下面是这个循环一次迭代的汇编代码：

```nasm
vpcmpeqd ymm2, ymm1, YMMWORD PTR a[0+rdx*4]
vpcmpeqd ymm3, ymm1, YMMWORD PTR a[32+rdx*4]
vpor     ymm0, ymm3, ymm2
vptest   ymm0, ymm0
je       loop
```

每次迭代，我们需要执行 5 条指令。虽然所有相关执行端口的吞吐量平均允许在一个周期内完成，但我们做不到，因为这颗特定 CPU（Zen 2）的译码宽度是 4。因此，性能只能达到应有水平的 ⅘。

<!--

这台 CPU（Zen 2）每周期只能处理 4 条指令。以下是 [llvm-mca 报告](/hpc/profiling/mca)的相关部分：

vpcmpeqd 013
vpcmpeqd 013
vpor 0123
vptest 2

[7]    [8]    [9]    [10]   Instructions:
0.46   0.09    -     0.45   vpcmpeqd	ymm2, ymm1, ymmword ptr [4*rdx + a]
0.40   0.09   0.22   0.29   vpcmpeqd	ymm3, ymm1, ymmword ptr [4*rdx + a+32]
0.34   0.11   0.08   0.47   vpor	ymm0, ymm3, ymm2
 -     1.00   1.00    -     vptest	ymm0, ymm0

-->

为了缓解这个问题，我们可以再次把每轮迭代处理的 SIMD 块数量加倍：

```c++
unsigned get_mask(reg m) {
    return _mm256_movemask_ps((__m256) m);
}

reg cmp(reg x, int *p) {
    reg y = _mm256_load_si256( (reg*) p );
    return _mm256_cmpeq_epi32(x, y);
}

int find(int needle) {
    reg x = _mm256_set1_epi32(needle);

    for (int i = 0; i < N; i += 32) {
        reg m1 = cmp(x, &a[i]);
        reg m2 = cmp(x, &a[i + 8]);
        reg m3 = cmp(x, &a[i + 16]);
        reg m4 = cmp(x, &a[i + 24]);
        reg m12 = _mm256_or_si256(m1, m2);
        reg m34 = _mm256_or_si256(m3, m4);
        reg m = _mm256_or_si256(m12, m34);
        if (!_mm256_testz_si256(m, m)) {
            unsigned mask = (get_mask(m4) << 24)
                          + (get_mask(m3) << 16)
                          + (get_mask(m2) << 8)
                          +  get_mask(m1);
            return i + __builtin_ctz(mask);
        }
    }

    return -1;
}
```

现在它展现出 43 GFLOPS 的吞吐量——比最初的标量实现快约 10 倍。

把它扩展到每轮 64 个值也没有帮助：小数组在命中条件时会承受所有这些额外 `movemask` 的开销，而更大的数组反正也会受[内存带宽](/hpc/cpu-cache/bandwidth)限制。

### 统计数量

作为最后一个练习，让我们求一个值在数组中的出现次数，而不只是它的首次出现：

```c++
int count(int x) {
    int cnt = 0;
    for (int i = 0; i < N; i++)
        cnt += (a[i] == x);
    return cnt;
}
```

要向量化它，我们只需要把比较掩码转换成每个元素为 1 或 0，然后求和：

```c++
const reg ones = _mm256_set1_epi32(1);

int count(int needle) {
    reg x = _mm256_set1_epi32(needle);
    reg s = _mm256_setzero_si256();

    for (int i = 0; i < N; i += 8) {
        reg y = _mm256_load_si256( (reg*) &a[i] );
        reg m = _mm256_cmpeq_epi32(x, y);
        m = _mm256_and_si256(m, ones);
        s = _mm256_add_epi32(s, m);
    }

    return hsum(s);
}
```

两种实现都得到约 15 GFLOPS：编译器可以完全靠自己把第一种向量化。

但有一个编译器发现不了的技巧：全 1 的掩码在重新解释为整数时是[负一](/hpc/arithmetic/integer)。因此我们可以跳过「与最低位相与」的部分，直接使用掩码本身，最后再把结果取负：

```c++
int count(int needle) {
    reg x = _mm256_set1_epi32(needle);
    reg s = _mm256_setzero_si256();

    for (int i = 0; i < N; i += 8) {
        reg y = _mm256_load_si256( (reg*) &a[i] );
        reg m = _mm256_cmpeq_epi32(x, y);
        s = _mm256_add_epi32(s, m);
    }

    return -hsum(s);
}
```

在这种特定的架构上，这并没有提升性能，因为吞吐量实际上受更新 `s` 的限制：它依赖于上一次迭代，所以循环不可能比每个 CPU 周期一次迭代更快。如果我们把累加器一分为二，就可以利用[指令级并行](../reduction#instruction-level-parallelism)：

```c++
int count(int needle) {
    reg x = _mm256_set1_epi32(needle);
    reg s1 = _mm256_setzero_si256();
    reg s2 = _mm256_setzero_si256();

    for (int i = 0; i < N; i += 16) {
        reg y1 = _mm256_load_si256( (reg*) &a[i] );
        reg y2 = _mm256_load_si256( (reg*) &a[i + 8] );
        reg m1 = _mm256_cmpeq_epi32(x, y1);
        reg m2 = _mm256_cmpeq_epi32(x, y2);
        s1 = _mm256_add_epi32(s1, m1);
        s2 = _mm256_add_epi32(s2, m2);
    }

    s1 = _mm256_add_epi32(s1, s2);

    return -hsum(s1);
}
```

现在它提供了约 22 GFLOPS 的性能，这已经是它能达到的上限了。

在把这套代码适配到更短的数据类型时，请记住累加器可能会溢出。为了解决这个问题，可以再加一个更大尺寸的累加器，并定期停下循环，把局部累加器中的值累加进去，然后重置局部累加器。例如，对于 8 位整数，这意味着创建另一个内层循环，执行 $\lfloor \frac{256-1}{8} \rfloor = 15$ 次迭代。

<!-- TODO：8-bit 示例 -->
<!-- TODO：先 ILP，再 -1 -->