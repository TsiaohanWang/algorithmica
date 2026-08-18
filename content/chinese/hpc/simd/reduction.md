---
title: 归约
weight: 3
---

*归约*（reduction，在函数式编程中也称为 *折叠*（folding））是对一段任意元素计算某个结合且可交换的运算（即 $(a \circ b) \circ c = a \circ (b \circ c)$ 且 $a \circ b = b \circ a$）的值。

归约最简单的例子是计算数组的和：

```c++
int sum(int *a, int n) {
    int s = 0;
    for (int i = 0; i < n; i++)
        s += a[i];
    return s;
}
```

朴素的方法不太容易向量化，因为循环的状态（当前前缀的和 $s$）依赖于上一次迭代。克服这一点的办法是把单个标量累加器 $s$ 拆成 8 个独立的累加器，让 $s_i$ 存放原数组中每隔 8 个取一个、偏移为 $i$ 的那些元素之和：

$$
s_i = \sum_{j=0}^{n / 8} a_{8 \cdot j + i }
$$

如果我们把这 8 个累加器存放在单个 256 位向量中，就可以通过把数组中连续的 8 元素段依次相加来一次性更新它们。用[向量扩展](../intrinsics)来实现，这是直截了当的：

```c++
int sum_simd(v8si *a, int n) {
    //       ^ you can just cast a pointer normally, like with any other pointer type
    v8si s = {0};

    for (int i = 0; i < n / 8; i++)
        s += a[i];
    
    int res = 0;
    
    // sum 8 accumulators into one
    for (int i = 0; i < 8; i++)
        res += s[i];

    // add the remainder of a
    for (int i = n / 8 * 8; i < n; i++)
        res += a[i];
        
    return res;
}
```

你可以把这种方法用于其他归约，例如求数组的最小值或异或和。

### 指令级并行

我们的实现与编译器自动生成的代码一致，但它实际上并不是最优的：当我们只用一个累加器时，[我们必须等待](/hpc/pipelining/throughput)一个周期才能让向量加法在循环迭代之间完成，而对应指令在这颗微架构上的[吞吐量](/hpc/pipelining/tables/)是 2。

如果我们再把数组分成 $B \geq 2$ 部分，每部分使用一个*独立*的累加器，就可以让向量加法的吞吐量饱和，把性能提高一倍：

```c++
const int B = 2; // how many vector accumulators to use

int sum_simd(v8si *a, int n) {
    v8si b[B] = {0};

    for (int i = 0; i + (B - 1) < n / 8; i += B)
        for (int j = 0; j < B; j++)
            b[j] += a[i + j];

    // sum all vector accumulators into one
    for (int i = 1; i < B; i++)
        b[0] += b[i];
    
    int s = 0;

    // sum 8 scalar accumulators into one
    for (int i = 0; i < 8; i++)
        s += b[0][i];

     // add the remainder of a
    for (int i = n / (8 * B) * (8 * B); i < n; i++)
        s += a[i];

    return s;
}
```

如果你有超过 2 个相关的执行端口，可以相应增大 `B` 常量，但 $n$ 倍的性能提升只适用于能装进 L1 缓存的数组——对更大的数组，[内存带宽](/hpc/cpu-cache/bandwidth)会成为瓶颈。

### 水平求和

把存储在向量寄存器中的 8 个累加器求和成一个标量、得到总和的部分，称为「水平求和」（horizontal summation）。

虽然逐一提取并相加每个标量只需常数个周期，但用一条[特殊指令](https://software.intel.com/sites/landingpage/IntrinsicsGuide/#techs=AVX,AVX2&text=_mm256_hadd_epi32&expand=2941)可以算得稍微快一些——它把寄存器中相邻的元素对相加。

![SSE/AVX 中的水平求和。注意输出的存储方式：(a b a b) 这种交错排列在归约操作中很常见](../img/hsum.png)

由于这是一个非常特殊的操作，它只能用 SIMD 内建函数完成——尽管编译器对标量代码大概也会生成差不多的流程：

```c++
int hsum(__m256i x) {
    __m128i l = _mm256_extracti128_si256(x, 0);
    __m128i h = _mm256_extracti128_si256(x, 1);
    l = _mm_add_epi32(l, h);
    l = _mm_hadd_epi32(l, l);
    return _mm_extract_epi32(l, 0) + _mm_extract_epi32(l, 1);
}
```

还有[其他类似的指令](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html#techs=AVX,AVX2&ig_expand=3037,3009,5135,4870,4870,4872,4875,833,879,874,849,848,6715,4845&text=horizontal)，例如用于整数乘法，或计算相邻元素之间的绝对差（用于图像处理）。

还有一条特定的指令 `_mm_minpos_epu16`，它计算 8 个 16 位整数中的水平最小值及其索引。这是唯一一条一步到位的水平归约指令：其他全部需要多步计算。