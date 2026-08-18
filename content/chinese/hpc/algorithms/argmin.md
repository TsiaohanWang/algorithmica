---
title: 用 SIMD 求 argmin
weight: 7
---

计算数组的*最小值*是[很容易向量化](/hpc/simd/reduction)的，因为它与其他任何归约没有区别：在 AVX2 下，你只需要在内部操作中使用方便的 `_mm256_min_epi32` 内建函数即可。它能在单周期内计算两个 8 元素向量的最小值——甚至比标量版本还快，后者至少需要一次比较和一次条件移动。

而寻找该最小元素的*下标*（*argmin*）则要难得多，但依然可以非常高效地进行向量化。在本节中，我们将设计一个算法，它以（几乎）计算最小值时的速度来求 argmin，比朴素的标量方法快约 15 倍。

### 标量基线

对于我们的基准测试，我们创建一个随机 32 位整数数组，然后反复尝试找出其中最小值的下标（若不唯一，则取第一个）：

```c++
const int N = (1 << 16);
alignas(32) int a[N];

for (int i = 0; i < N; i++)
    a[i] = rand();
```

为便于说明，我们假设 $N$ 是 2 的幂，并令所有实验在 $N=2^{13}$ 下进行，这样[内存带宽](/hpc/cpu-cache/bandwidth)就不再是瓶颈。

要实现标量版本的 argmin，我们只需要维护下标而不是最小值：

```c++
int argmin(int *a, int n) {
    int k = 0;

    for (int i = 0; i < n; i++)
        if (a[i] < a[k])
            k = i;
    
    return k;
}
```

它的运行速度大约为 1.5 GFLOPS——即平均每秒处理 $1.5 \cdot 10^9$ 个值，或者说每周期约 0.75 个值（CPU 主频为 2GHz）。

让我们把它与 `std::min_element` 比较一下：

```c++
int argmin(int *a, int n) {
    int k = std::min_element(a, a + n) - a;
    return k;
}
```

<!--

https://github.com/llvm-mirror/libcxx/blob/78d6a7767ed57b50122a161b91f59f19c9bd0d19/include/algorithm#L2489

https://github.com/gcc-mirror/gcc/blob/16e2427f50c208dfe07d07f18009969502c25dc8/libstdc%2B%2B-v3/include/bits/stl_algo.h#L5606

```nasm
lea	r8, 24[rdx]	# __first,
mov	r11d, DWORD PTR [rax]
cmp	DWORD PTR 12[rdx], r11d
cmovl	rax, r10	# __result,, __result, __first
```

```nasm
cmp	eax, r12d	# prephitmp_103, _108	
jle	.L36	#,	
mov	eax, r12d	# prephitmp_103, _108	
mov	ecx, ebp	# k, ivtmp.29	
.L36:	
lea	rdx, 4[r8]	# ivtmp.29,	
```

```nasm
cmp	eax, r12d	# prephitmp_103, _108	
jle	.L36	#,	
mov	eax, r12d	# prephitmp_103, _108	
mov	ecx, ebp	# k, ivtmp.29	
.L36:	
lea	rdx, 4[r8]	# ivtmp.29,	
```

-->

GCC 的版本约为 0.28 GFLOPS——显然，编译器无法穿透所有这些抽象层。这是又一个提醒我们永远不要使用 STL 的例子。

### 下标向量

向量化标量实现的问题在于，连续迭代之间存在依赖关系。在优化[数组求和](/hpc/simd/reduction)时，我们遇到过同样的问题，解决办法是把数组分成 8 个切片，每个切片代表下标对 8 取模余数相同的那部分元素。此处我们可以使用同样的技巧，只不过还需要把数组下标也考虑进去。

当连续的元素及其下标都在向量中时，我们就可以用[谓词执行](/hpc/pipelining/branchless)来并行处理它们：

```c++
typedef __m256i reg;

int argmin(int *a, int n) {
    // indices on the current iteration
    reg cur = _mm256_setr_epi32(0, 1, 2, 3, 4, 5, 6, 7);
    // the current minimum for each slice
    reg min = _mm256_set1_epi32(INT_MAX);
    // its index (argmin) for each slice
    reg idx = _mm256_setzero_si256();

    for (int i = 0; i < n; i += 8) {
        // load a new SIMD block
        reg x = _mm256_load_si256((reg*) &a[i]);
        // find the slices where the minimum is updated
        reg mask = _mm256_cmpgt_epi32(min, x);
        // update the indices
        idx = _mm256_blendv_epi8(idx, cur, mask);
        // update the minimum (can also similarly use a "blend" here, but min is faster)
        min = _mm256_min_epi32(x, min);
        // update the current indices
        const reg eight = _mm256_set1_epi32(8);
        cur = _mm256_add_epi32(cur, eight);       // 
        // can also use a "blend" here, but min is faster
    }

    // find the argmin in the "min" register and return its real index

    int min_arr[8], idx_arr[8];
    
    _mm256_storeu_si256((reg*) min_arr, min);
    _mm256_storeu_si256((reg*) idx_arr, idx);

    int k = 0, m = min_arr[0];

    for (int i = 1; i < 8; i++)
        if (min_arr[i] < m)
            m = min_arr[k = i];

    return idx_arr[k];
}
```

它的运行速度约为 8–8.5 GFLOPS。迭代之间仍然存在一些相互依赖，所以我们可以通过每轮迭代处理 8 个以上的元素来进一步优化，从而利用[指令级并行](/hpc/simd/reduction#instruction-level-parallelism)。

这会对性能有很大帮助，但还不足以达到计算最小值时的速度（约 24 GFLOPS），因为还有另一个瓶颈。每一轮迭代，我们需要一次融合比较（load-fused comparison）、一次融合最小值（load-fused minimum）、一次混合（blend）和一次加法——总共 4 条指令处理 8 个元素。由于该 CPU（Zen 2）的译码宽度只有 4，即使我们设法消除了所有其他瓶颈，性能仍会受限于 8 × 2 = 16 GFLOPS。

因此，我们将换一种方法，使每个元素所需的指令更少。

### 分支并不可怕

运行标量版本时，我们多久更新一次最小值？

直觉告诉我们：如果所有值都是独立随机抽取的，那么「下一个元素比前面所有元素都小」这一事件不应该频繁发生。更准确地说，它等于已处理元素个数的倒数。因此，`a[i] < a[k]` 条件被满足的期望次数等于调和级数之和：

$$
\frac{1}{2} + \frac{1}{3} + \frac{1}{4} + \ldots + \frac{1}{n} = O(\ln(n))
$$

所以对于一个一百元素的数组，最小值大约更新 5 次；一千元素是 7 次；一百万元素的数组也只需 14 次——与所有「是否为新最小值」检查的总数相比，这完全微不足道。

编译器大概无法自己推导出这一点，所以让我们[显式地提供](/hpc/compilation/situational)这一信息：

```c++
int argmin(int *a, int n) {
    int k = 0;

    for (int i = 0; i < n; i++)
        if (a[i] < a[k]) [[unlikely]]
            k = i;
    
    return k;
}
```

编译器[优化了机器码的布局](/hpc/architecture/layout)，CPU 现在能以约 2 GFLOPS 的速度执行该循环——相比没有提示的循环的 1.5 GFLOPS，这是一个微小但可观的提升。

思路如下：如果整个计算过程中最小值只更新十几次，我们就可以抛弃所有向量混合和下标更新的操作，只维护最小值，并定期检查它是否发生了变化。在这个检查内部，我们可以使用任何慢速的 argmin 更新方法，因为它只会被调用几次。

要用 SIMD 实现它，每轮迭代我们只需做一次向量加载、一次比较和一次判零测试：

```c++
int argmin(int *a, int n) {
    int min = INT_MAX, idx = 0;
    
    reg p = _mm256_set1_epi32(min);

    for (int i = 0; i < n; i += 8) {
        reg y = _mm256_load_si256((reg*) &a[i]); 
        reg mask = _mm256_cmpgt_epi32(p, y);
        if (!_mm256_testz_si256(mask, mask)) { [[unlikely]]
            for (int j = i; j < i + 8; j++)
                if (a[j] < min)
                    min = a[idx = j];
            p = _mm256_set1_epi32(min);
        }
    }
    
    return idx;
}
```

它的性能已经达到约 8.5 GFLOPS，但现在循环被 `testz` 指令所限制，该指令的吞吐量只有 1。解决办法是加载两个连续的 SIMD 块并取它们的最小值，这样 `testz` 实际上一次就能处理 16 个元素：

```c++
int argmin(int *a, int n) {
    int min = INT_MAX, idx = 0;
    
    reg p = _mm256_set1_epi32(min);

    for (int i = 0; i < n; i += 16) {
        reg y1 = _mm256_load_si256((reg*) &a[i]);
        reg y2 = _mm256_load_si256((reg*) &a[i + 8]);
        reg y = _mm256_min_epi32(y1, y2);
        reg mask = _mm256_cmpgt_epi32(p, y);
        if (!_mm256_testz_si256(mask, mask)) { [[unlikely]]
            for (int j = i; j < i + 16; j++)
                if (a[j] < min)
                    min = a[idx = j];
            p = _mm256_set1_epi32(min);
        }
    }
    
    return idx;
}
```

这个版本运行在约 10 GFLOPS。要消除其余障碍，我们可以做两件事：

- 将块大小增加到 32 个元素，以获得更多的指令级并行。
- 优化局部的 argmin：与其计算它的精确位置，不如只保存块的起始下标，然后在最后回过头来只找一次。这样每次检查通过时我们只需计算最小值并将其广播到向量中，更简单也快得多。

实现这两个优化后，性能跃升至约 22 GFLOPS：

```c++
int argmin(int *a, int n) {
    int min = INT_MAX, idx = 0;
    
    reg p = _mm256_set1_epi32(min);

    for (int i = 0; i < n; i += 32) {
        reg y1 = _mm256_load_si256((reg*) &a[i]);
        reg y2 = _mm256_load_si256((reg*) &a[i + 8]);
        reg y3 = _mm256_load_si256((reg*) &a[i + 16]);
        reg y4 = _mm256_load_si256((reg*) &a[i + 24]);
        y1 = _mm256_min_epi32(y1, y2);
        y3 = _mm256_min_epi32(y3, y4);
        y1 = _mm256_min_epi32(y1, y3);
        reg mask = _mm256_cmpgt_epi32(p, y1);
        if (!_mm256_testz_si256(mask, mask)) { [[unlikely]]
            idx = i;
            for (int j = i; j < i + 32; j++)
                min = (a[j] < min ? a[j] : min);
            p = _mm256_set1_epi32(min);
        }
    }

    for (int i = idx; i < idx + 31; i++)
        if (a[i] == min)
            return i;
    
    return idx + 31;
}
```

这已经接近上限了，因为仅仅计算最小值本身就能跑到约 24–25 GFLOPS。

所有这些「热爱分支」的 SIMD 实现的唯一问题是，它们依赖最小值极不频繁地更新。这对随机输入分布成立，但在最坏情况下则不成立。如果我们用一串递减的序列填充数组，最后一个实现的性能会下降到约 2.7 GFLOPS——慢了近 10 倍（不过仍然比标量代码快，因为我们只需在每个块上计算最小值）。

一种修复方法是采用类似快速排序这类随机化算法的手段：自己打乱输入，以随机顺序遍历数组。这样可以避免这个最坏情况的惩罚，但由于 RNG 和[内存](/hpc/cpu-cache/prefetching)相关的问题，实现起来比较棘手。还有一种更简单的解决方案。

### 先求最小值，再找下标

我们已经知道如何[快速计算数组的最小值](/hpc/simd/reduction)，也知道如何[在数组中查找元素](/hpc/simd/masking#searching)——那为什么我们不先单独算出最小值，然后再去查找它呢？

```c++
int argmin(int *a, int n) {
    int needle = min(a, n);
    int idx = find(a, n, needle);
    return idx;
}
```

如果我们将这两个子程序都实现到最优（参见链接的文章），随机数组的性能约为 18 GFLOPS，递减数组约为 12 GFLOPS——这很合理，因为我们预期要分别把数组读 1.5 遍和 2 遍。这本身并不算太差——至少我们避免了 10 倍的最坏情况性能惩罚——但问题是，这种受罚的性能也会延续到更大的数组上，此时我们受限于[内存带宽](/hpc/cpu-cache/bandwidth)而非计算能力。

幸运的是，我们已经知道如何修复它。我们可以把数组切分成固定大小 $B$ 的块，计算这些块上的最小值，同时维护全局最小值。当新块上的最小值低于全局最小值时，我们更新它，并记住当前全局最小值所在的块号。处理完整数组后，我们只需回到那个块，扫描它的 $B$ 个元素来找到 argmin。

这样我们只需要处理 $(N + B)$ 个元素，不必牺牲 ½ 或 ⅓ 的性能：

```c++
const int B = 256;

// returns the minimum and its first block
pair<int, int> approx_argmin(int *a, int n) {
    int res = INT_MAX, idx = 0;
    for (int i = 0; i < n; i += B) {
        int val = min(a + i, B);
        if (val < res) {
            res = val;
            idx = i;
        }
    }
    return {res, idx};
}

int argmin(int *a, int n) {
    auto [needle, base] = approx_argmin(a, n);
    int idx = find(a + base, B, needle);
    return base + idx;
}
```

最终实现的结果是：随机数组约 22 GFLOPS，递减数组约 19 GFLOPS。

完整的实现，包括 `min()` 和 `find()` 两个函数，大约有 100 行。[可以看一看](https://github.com/sslotin/amh-code/blob/main/argmin/combined.cc)，不过它距离生产级代码还差得远。

### 总结

以下是所有实现的结果汇总：

```
algorithm    rand   decr   reason for the performance difference
-----------  -----  -----  -------------------------------------------------------------
std          0.28   0.28   
scalar       1.54   1.89   efficient branch prediction
+ hinted     1.95   0.75   wrong hint
index        8.17   8.12
simd         8.51   1.65   scalar-based argmin on each iteration
+ ilp        10.22  1.74   ^ same
+ optimized  22.44  2.70   ^ same, but faster because there are less inter-dependencies
min+find     18.21  12.92  find() has to scan the entire array
+ blocked    22.23  19.29  we still have an optional horizontal minimum every B elements
```

请谨慎看待这些结果：测量[噪声很大](/hpc/profiling/noise)，它们只针对两种输入分布、一个特定的数组大小（$N=2^{13}$，即 L1 缓存的大小）、一个特定的架构（Zen 2）以及一个特定且略微过时的编译器（GCC 9.3）——而且编译器优化对基准测试代码的微小改动也非常敏感。

还有一些次要的地方可以优化，但潜在提升不到 10%，所以我就没有继续折腾。也许有一天我会鼓起勇气，把算法优化到理论极限，处理不能被块大小整除的数组大小和非对齐内存的情况，然后在许多架构上妥善地重新运行基准测试，附带 p 值之类的统计。如果有人赶在我之前做了这件事，请[发信告诉我](http://sereja.me/)。

### 致谢

第一个基于下标的 SIMD 算法是 Wojciech Muła 在 2018 年[最初设计的](http://0x80.pl/notesen/2018-10-03-simd-index-of-min.html)。

感谢 Zach Wegner [指出](https://twitter.com/zwegner/status/1491520929138151425)，当使用内建函数手动实现时，Muła 算法的性能会得到提升（我最初使用的是 [GCC 向量类型](/hpc/simd/intrinsics/#gcc-vector-extensions)）。

<!--

感谢 Alexander Monakov [一丝不苟](https://twitter.com/_monoid/status/1491827976438231049)并推动我去调查 STL 版本。

-->

文章发表后，我发现 [Marshall Lochbaum](https://www.aplwiki.com/wiki/Marshall_Lochbaum)（[BQN](https://mlochbaum.github.io/BQN/) 的创造者）在 2019 年从事 Dyalog APL 工作时设计了一个[非常相似的算法](https://forums.dyalog.com/viewtopic.php?f=13&t=1579&sid=e2cbd69817a17a6e7b1f76c677b1f69e#p6239)。请多关注数组编程语言的世界！
