---
title: 用 SIMD 求前缀和
weight: 8
---

*前缀和*，也叫*累积和*、*包含扫描*（inclusive scan）或简称为*扫描*（scan），是根据另一个序列 $a_i$ 按以下规则生成的一个数列 $b_i$：

$$
\begin{aligned}
b_0 &= a_0
\\ b_1 &= a_0 + a_1
\\ b_2 &= a_0 + a_1 + a_2
\\ &\ldots
\end{aligned}
$$

换句话说，输出序列的第 $k$ 个元素就是输入序列前 $k$ 个元素之和。

前缀和是许多算法中非常重要的原语，尤其在并行算法的语境下，它的计算规模几乎能随处理器数量完美扩展。遗憾的是，在单个 CPU 核上用 SIMD 并行来加速它要困难得多，但我们还是要试一试——并推导出一个比基线标量实现快约 2.5 倍的算法。

### 基线

作为基线，我们本可以直接调用 STL 的 `std::partial_sum`，但为了清晰起见，我们手动实现。我们创建一个整数数组，然后依次把前一个元素加到当前元素上：

```c++
void prefix(int *a, int n) {
    for (int i = 1; i < n; i++)
        a[i] += a[i - 1];
}
```

看上去每轮迭代需要两次读、一次加和一次写，但显然编译器会优化掉多余的读，用寄存器充当累加器：

```nasm
loop:
    add     edx, DWORD PTR [rax]
    mov     DWORD PTR [rax-4], edx
    add     rax, 4
    cmp     rax, rcx
    jne     loop
```

[展开](/hpc/architecture/loops)循环后，实际上只剩两条指令：融合的读加和结果写回。理论上，它们应该能达到 2 GFLOPS（借助[超标量处理](/hpc/pipelining)，每 CPU 周期 1 个元素），但由于内存系统必须不断在读写之间[切换](/hpc/cpu-cache/bandwidth#directional-access)，实际性能在 1.2 到 1.6 GFLOPS 之间，取决于数组大小。

### 向量化

实现并行前缀和算法的一种方法是：把数组切分为小块，在它们上面独立计算*局部*前缀和，然后做第二遍扫描：把前面所有元素的和加到每个块中已计算好的值上。

![](../img/prefix-outline.png)

这样每个块都可以并行处理——无论是在计算局部前缀和阶段还是在累加阶段——所以通常你会把数组切成与处理器数量一样多的块。但因为我们只能使用一个 CPU 核，而且 SIMD 中的[非顺序内存访问](/hpc/simd/moving#non-contiguous-load)效果不佳，我们不打算这么做。相反，我们将使用等于一个 SIMD 通道大小的固定块大小，并在寄存器内计算前缀和。

现在，为了在局部计算这些前缀和，我们将使用另一种通常效率低下（总工作量是 $O(n \log n)$ 而不是线性的）的并行前缀和方法，但当数据已经在 SIMD 寄存器里时它就足够好了。思路是执行 $\log n$ 轮迭代，在第 $k$ 轮中，对所有适用的 $i$，把 $a_{i - 2^k}$ 加到 $a_i$ 上：

```c++
for (int l = 0; l < logn; l++)
    // (atomically and in parallel):
    for (int i = (1 << l); i < n; i++)
        a[i] += a[i - (1 << l)];
```

我们可以用归纳法证明这个算法是正确的：如果第 $k$ 轮时每个元素 $a_i$ 都等于原数组 $(i - 2^k, i]$ 段之和，那么把它加上 $a_{i - 2^k}$ 之后，它就等于 $(i - 2^{k+1}, i]$ 段之和。经过 $O(\log n)$ 轮之后，数组就变成了它的前缀和。

要在 SIMD 中实现它，我们可以用[置换](/hpc/simd/shuffling)把第 $i$ 个元素与第 $(i-2^k)$ 个元素对齐，但置换太慢了。相反，我们将使用 `sll`（「左移通道」）指令，它正好做这件事，并把没有匹配上的元素替换为零：

```c++
typedef __m128i v4i;

v4i prefix(v4i x) {
    // x = 1, 2, 3, 4
    x = _mm_add_epi32(x, _mm_slli_si128(x, 4));
    // x = 1, 2, 3, 4
    //   + 0, 1, 2, 3
    //   = 1, 3, 5, 7
    x = _mm_add_epi32(x, _mm_slli_si128(x, 8));
    // x = 1, 3, 5, 7
    //   + 0, 0, 1, 3
    //   = 1, 3, 6, 10
    return x;
}
```

遗憾的是，这个指令的 256 位版本会在两个 128 位通道内独立地执行这种字节移位，这是 AVX 的典型特征：

```c++
typedef __m256i v8i;

v8i prefix(v8i x) {
    // x = 1, 2, 3, 4, 5, 6, 7, 8
    x = _mm256_add_epi32(x, _mm256_slli_si256(x, 4));
    x = _mm256_add_epi32(x, _mm256_slli_si256(x, 8));
    x = _mm256_add_epi32(x, _mm256_slli_si256(x, 16)); // <- this does nothing
    // x = 1, 3, 6, 10, 5, 11, 18, 26
    return x;
}
```

我们仍然可以用它来以两倍速度计算 4 元素前缀和，但在累加时必须切换到 128 位 SSE。让我们写一个方便的函数，一鼓作气地计算局部前缀和：

```c++
void prefix(int *p) {
    v8i x = _mm256_load_si256((v8i*) p);
    x = _mm256_add_epi32(x, _mm256_slli_si256(x, 4));
    x = _mm256_add_epi32(x, _mm256_slli_si256(x, 8));
    _mm256_store_si256((v8i*) p, x);
}
```

现在，对于累加阶段，我们将创建另一个方便的函数：它同样接收指向 4 元素块的指针，外加一个 4 元素的前缀和向量。这个函数的职责是把前缀和向量加到块上，并更新它以便传给下一个块（通过在加法之前广播块的最后一个元素）：

<!--

想不出更有特色的名字，我们就叫它 `accumulate`：

-->

```c++
v4i accumulate(int *p, v4i s) {
    v4i d = (v4i) _mm_broadcast_ss((float*) &p[3]);
    v4i x = _mm_load_si128((v4i*) p);
    x = _mm_add_epi32(s, x);
    _mm_store_si128((v4i*) p, x);
    return _mm_add_epi32(s, d);
}
```

实现了 `prefix` 和 `accumulate` 之后，剩下的就是把我们的两遍算法粘合起来：

```c++
void prefix(int *a, int n) {
    for (int i = 0; i < n; i += 8)
        prefix(&a[i]);
    
    v4i s = _mm_setzero_si128();
    
    for (int i = 4; i < n; i += 4)
        s = accumulate(&a[i], s);
}
```

这个算法已经比标量实现快一倍多，但对超出 L3 缓存的大型数组会变慢——大约在[双向 RAM 带宽](/hpc/cpu-cache/bandwidth)的一半处开始，因为我们把整个数组读了两遍。

![](../img/prefix-simd.svg)

另一个有趣的数据点：如果只执行 `prefix` 阶段，性能约为 8.1 GFLOPS。`accumulate` 阶段稍慢，约 5.8 GFLOPS。做个合理性检查：总性能应为 $\frac{1}{ \frac{1}{5.8} + \frac{1}{8.1} } \approx 3.4$。

### 分块

所以，对于大型数组我们存在内存带宽问题。如果把它切分成能放进缓存的块并分别处理，就可以避免从 RAM 重新读取整个数组。我们需要传给下一个块的无非就是前面所有块的和，所以我们可以设计一个接口与 `accumulate` 类似的 `local_prefix` 函数：

```c++
const int B = 4096; // <- ideally should be slightly less or equal to the L1 cache

v4i local_prefix(int *a, v4i s) {
    for (int i = 0; i < B; i += 8)
        prefix(&a[i]);
    
    for (int i = 0; i < B; i += 4)
        s = accumulate(&a[i], s);

    return s;
}

void prefix(int *a, int n) {
    v4i s = _mm_setzero_si128();
    for (int i = 0; i < n; i += B)
        s = local_prefix(a + i, s);
}
```

（我们必须确保 $N$ 是 $B$ 的倍数，不过现在先忽略这种实现细节。）

分块版本的性能显著更好，而且不止在数组位于 RAM 中时如此：

![](../img/prefix-blocked.svg)

在 RAM 的情况下，相比未分块实现的加速只有约 1.5 倍而不是 2 倍。这是因为当我们第二次遍历缓存块而不是取下一个块时，内存控制器处于空闲状态——[硬件预取器](/hpc/cpu-cache/prefetching)还不够先进，无法识别这种模式。

### 连续加载

有几种方法可以解决这种利用率不足的问题。最明显的是使用[软件预取](/hpc/cpu-cache/prefetching)，在当前块仍在处理时就显式地请求下一个块。

最好把预取加在 `accumulate` 阶段，因为它比 `prefix` 更慢、内存密集度更低：

```c++
v4i accumulate(int *p, v4i s) {
    __builtin_prefetch(p + B); // <-- prefetch the next block
    // ...
    return s;
}
```

对于缓存内的数组性能略有下降，但对于 RAM 中的数组则更接近 2 GFLOPS：

![](../img/prefix-prefetch.svg)

另一种做法是对两个阶段做*交错*。我们不再把它们分成大块并交替执行，而是并发执行两个阶段，让 `accumulate` 阶段落后固定的若干次迭代——类似于 [CPU 流水线](/hpc/pipelining)：

```c++
const int B = 64;
//        ^ small sizes cause pipeline stalls
//          large sizes cause cache system inefficiencies

void prefix(int *a, int n) {
    v4i s = _mm_setzero_si128();

    for (int i = 0; i < B; i += 8)
        prefix(&a[i]);

    for (int i = B; i < n; i += 8) {
        prefix(&a[i]);
        s = accumulate(&a[i - B], s);
        s = accumulate(&a[i - B + 4], s);
    }

    for (int i = n - B; i < n; i += 4)
        s = accumulate(&a[i], s);
}
```

这有更多好处：循环以恒定速度推进，减轻了内存系统的压力；调度器能看到两个子程序的指令，从而能更高效地把指令分配给执行端口——有点像超线程，只不过发生在代码里。

正因为如此，即使在小的数组上性能也提升了：

![](../img/prefix-interleaved.svg)

最后，看起来我们并没有被[内存读端口](/hpc/pipelining/tables/)或[译码宽度](/hpc/architecture/layout/#cpu-front-end)所限制，所以我们可以免费加上预取，这会让性能进一步提升：

![](../img/prefix-interleaved-prefetch.svg)

我们能够获得的总加速比，小数组约为 $\frac{4.2}{1.5} \approx 2.8$ 倍，大数组约为 $\frac{2.1}{1.2} \approx 1.75$ 倍。

与标量代码相比，低精度数据的加速比可能更高，因为标量代码基本被限制为每周期执行一次迭代，与操作数大小无关；但和其他[一些基于 SIMD 的算法](../argmin)相比，这仍然有点「一般般」。这很大程度上是因为 AVX 没有全寄存器字节移位，否则 `accumulate` 阶段可以快一倍，更别提专门的前缀和指令了。

### 其他相关工作

你可以阅读[哥伦比亚大学的这篇论文](http://www.adms-conf.org/2020-camera-ready/ADMS20_05.pdf)，它聚焦于多核场景和 AVX-512（AVX-512 [勉强算有](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html#ig_expand=3037,4870,6715,4845,3853,90,7307,5993,2692,6946,6949,5456,6938,5456,1021,3007,514,518,7253,7183,3892,5135,5260,3915,4027,3873,7401,4376,4229,151,2324,2310,2324,591,4075,6130,4875,6385,5259,6385,6250,1395,7253,6452,7492,4669,4669,7253,1039,1029,4669,4707,7253,7242,848,879,848,7251,4275,879,874,849,833,6046,7250,4870,4872,4875,849,849,5144,4875,4787,4787,4787,3016,3018,5227,7359,7335,7392,4787,5259,5230,5230,5223,6438,488,483,6165,6570,6554,289,6792,6554,5230,6385,5260,5259,289,288,3037,3009,590,604,633,5230,5259,6554,6554,5259,6547,6554,3841,5214,5229,5260,5259,7335,5259,519,1029,515,3009,3009,3013,3011,515,6527,652,6527,6554,288&text=_mm512_alignr_epi32&techs=AVX_512)快速 512 位寄存器字节移位），以及[这个 StackOverflow 问题](https://stackoverflow.com/questions/10587598/simd-prefix-sum-on-intel-cpu)以获得更广泛的讨论。

这篇文章里描述的大部分内容此前已经为人所知。据我所知，我的贡献在于交错技术，它带来了约 20% 的适度性能提升。也许还有进一步改进的余地，但空间不大。

还有 CMU 的一位教授 [Guy Blelloch](https://www.cs.cmu.edu/~blelloch/)，早在 90 年代[向量处理器](https://en.wikipedia.org/wiki/Vector_processor)还很流行的时候，他就[倡导](https://www.cs.cmu.edu/~blelloch/papers/sc90.pdf)专为前缀和设计硬件。前缀和对并行应用非常重要，而硬件正变得越来越并行，所以也许未来 CPU 厂商会重拾这个想法，让前缀和的计算变得稍微容易一些。


<!--

用置换也可以做到，但那会毁掉 prefix 阶段的性能。

-->
