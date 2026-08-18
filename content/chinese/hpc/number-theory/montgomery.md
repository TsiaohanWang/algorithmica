---
title: Montgomery 乘法
weight: 4
published: true
---

毫不意外，[模运算](../modular)中很大一部分计算常常花在取模操作上，它和[通用整数除法](/hpc/arithmetic/division/)一样慢，通常需要 15~20 个周期，具体取决于操作数大小。

处理这个麻烦的最佳方式是干脆避免取模操作，把它推迟或替换为[分支预测（predication）](/hpc/pipelining/branchless)，例如在计算模和时就可以这样做：

```cpp
const int M = 1e9 + 7;

// input: array of n integers in the [0, M) range
// output: sum modulo M
int slow_sum(int *a, int n) {
    int s = 0;
    for (int i = 0; i < n; i++)
        s = (s + a[i]) % M;
    return s;
}

int fast_sum(int *a, int n) {
    int s = 0;
    for (int i = 0; i < n; i++) {
        s += a[i]; // s < 2 * M
        s = (s >= M ? s - M : s); // will be replaced with cmov
    }
    return s;
}

int faster_sum(int *a, int n) {
    long long s = 0; // 64-bit integer to handle overflow
    for (int i = 0; i < n; i++)
        s += a[i]; // will be vectorized
    return s % M;
}
```

然而，有时你只有一连串的模乘法，除了依赖需要常量模数与一些预计算的[整数除法技巧](../../arithmetic/division/)之外，没有很好的办法摆脱对除法余数的计算。

但还有另一种专门为模运算设计的技术，称为 *Montgomery 乘法*。

### Montgomery 空间

Montgomery 乘法的做法是：先把乘数变换到 *Montgomery 空间*，在那里模乘法可以廉价地完成，然后在需要它们的真实值时再变换回来。与通用的整数除法方法不同，Montgomery 乘法对于只做一次模约减并不高效，只有在存在一连串模运算时才值得使用。

该空间由模数 $n$ 和一个与 $n$ 互质的正整数 $r \ge n$ 定义。算法涉及对 $r$ 取模和除以 $r$ 的运算，因此实践中常取 $2^{32}$ 或 $2^{64}$，这样这些操作可以分别用右移和按位与完成。

<!-- 因此 $n$ 需要是奇数，这样 $2$ 的每个幂次都会与 $n$ 互质。如果不是，我们可以把它变成奇数（？）。 -->

**定义。** 数 $x$ 在 Montgomery 空间中的*代表元* $\bar x$ 定义为

$$
\bar{x} = x \cdot r \bmod n
$$

计算这个变换涉及一次乘法和一次取模——这正是我们一开始就想优化掉的昂贵操作——所以我们只在往返变换到 Montgomery 空间的开销值得的情况下使用这种方法，而不是用于一般的模乘法。

<!-- 注意，这个变换恰恰是我们想优化的那种乘法，所以它仍然是一项昂贵的操作。然而，我们只需把数变换进空间一次、在该空间内高效地执行任意多次运算、最后把最终结果变换回来，如果我们做了大量模 $n$ 的运算，这应该是有利的。 -->

在 Montgomery 空间内部，加法、减法和相等性检查照常进行：

$$
x \cdot r + y \cdot r \equiv (x + y) \cdot r \bmod n
$$

但乘法并非如此。用 $*$ 表示 Montgomery 空间中的乘法、$\cdot$ 表示「普通」乘法，我们期望结果为：

$$
\bar{x} * \bar{y} = \overline{x \cdot y} = (x \cdot y) \cdot r \bmod n
$$

但 Montgomery 空间中的普通乘法得到：

$$
\bar{x} \cdot \bar{y} = (x \cdot y) \cdot r \cdot r \bmod n
$$

因此，Montgomery 空间中的乘法定义为

$$
\bar{x} * \bar{y} = \bar{x} \cdot \bar{y} \cdot r^{-1} \bmod n
$$

这意味着，在 Montgomery 空间中普通相乘两个数之后，我们需要乘上 $r^{-1}$ 并取模来*约减*结果——而这个特定操作有一种高效的做法。

### Montgomery 约减

假设 $r=2^{32}$，模数 $n$ 为 32 位，需要约减的数 $x$ 为 64 位（两个 32 位数的乘积）。我们的目标是计算 $y = x \cdot r^{-1} \bmod n$。

由于 $r$ 与 $n$ 互质，我们知道在 $[0, n)$ 范围内存在两个数 $r^{-1}$ 和 $n^\prime$ 使得

$$
r \cdot r^{-1} + n \cdot n^\prime = 1
$$

而且 $r^{-1}$ 和 $n^\prime$ 都可以计算出来，例如使用[扩展欧几里得算法](../euclid-extended)。

利用这个恒等式，我们可以把 $r \cdot r^{-1}$ 表示为 $(1 - n \cdot n^\prime)$，并把 $x \cdot r^{-1}$ 写成

$$
\begin{aligned}
x \cdot r^{-1} &= x \cdot r \cdot r^{-1} / r
\\             &= x \cdot (1 - n \cdot n^{\prime}) / r
\\             &= (x - x \cdot n \cdot n^{\prime}    ) / r
\\             &\equiv (x - x \cdot n \cdot n^{\prime} + k \cdot r \cdot n) / r &\pmod n &\;\;\text{(for any integer $k$)}
\\             &\equiv (x - (x \cdot n^{\prime} - k \cdot r) \cdot n) / r &\pmod n
\end{aligned}
$$

现在，如果我们选择 $k$ 为 $\lfloor x \cdot n^\prime / r \rfloor$（即 $x \cdot n^\prime$ 乘积的高 64 位），那么它将抵消掉，$(k \cdot r - x \cdot n^{\prime})$ 将恰好等于 $x \cdot n^{\prime} \bmod r$（$x \cdot n^\prime$ 的低 32 位），这意味着：

$$
x \cdot r^{-1} \equiv (x - x \cdot n^{\prime} \bmod r \cdot n) / r
$$

算法本身只是计算这个公式：执行两次乘法计算 $q = x \cdot n^{\prime} \bmod r$ 和 $m = q \cdot n$，然后从 $x$ 中减去它并把结果右移来除以 $r$。

剩下唯一要处理的是结果可能不在 $[0, n)$ 范围内；但由于

$$
x < n \cdot n < r \cdot n \implies x / r < n
$$

且

$$
m = q \cdot n < r \cdot n \implies m / r < n
$$

可以保证

$$
-n < (x - m) / r < n
$$

因此，我们只需检查结果是否为负，若为负则加上 $n$，得到如下算法：

```c++
typedef __uint32_t u32;
typedef __uint64_t u64;

const u32 n = 1e9 + 7, nr = inverse(n, 1ull << 32);

u32 reduce(u64 x) {
    u32 q = u32(x) * nr;      // q = x * n' mod r
    u64 m = (u64) q * n;      // m = q * n
    u32 y = (x - m) >> 32;    // y = (x - m) / r
    return x < m ? y + n : y; // if y < 0, add n to make it be in the [0, n) range
}
```

这最后一次检查相对便宜，但它仍然在关键路径上。如果我们接受结果落在 $[0, 2 \cdot n - 2]$ 范围内而不是 $[0, n)$，我们可以去掉它并无条件给结果加 $n$：

```c++
u32 reduce(u64 x) {
    u32 q = u32(x) * nr;
    u64 m = (u64) q * n;
    u32 y = (x - m) >> 32;
    return y + n
}
```

我们还可以把 `>> 32` 操作在计算图中提前一步，改为计算 $\lfloor x / r \rfloor - \lfloor m / r \rfloor$ 而不是 $(x - m) / r$。这是正确的，因为 $x$ 和 $m$ 的低 32 位反正相等，由于

$$
m = x \cdot n^\prime \cdot n \equiv x \pmod r
$$

但为什么我们要自愿做两次右移而不是一次？这是有益的，因为对于 `((u64) q * n) >> 32`，我们需要做一次 32 乘 32 的乘法并取结果的高 32 位（x86 的 `mul` 指令[已经把它写入](/hpc/arithmetic/integer/#128-bit-integers)一个单独的寄存器，所以不花任何代价），而另一个右移 `x >> 32` 不在关键路径上。

```c++
u32 reduce(u64 x) {
    u32 q = u32(x) * nr;
    u32 m = ((u64) q * n) >> 32;
    return (x >> 32) + n - m;
}
```

Montgomery 乘法相对于其他模约减方法的主要优势之一，是它不需要非常大的数据类型：它只需要一次 $r \times r$ 乘法，并提取结果的低、高各 $r$ 位，这在大多数硬件上[有专门支持](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html#ig_expand=7395,7392,7269,4868,7269,7269,1820,1835,6385,5051,4909,4918,5051,7269,6423,7410,150,2138,1829,1944,3009,1029,7077,519,5183,4462,4490,1944,5055,5012,5055&techs=AVX,AVX2&text=mul)，也使其易于推广到 [SIMD](../../simd/) 和更大的数据类型：

```c++
typedef __uint128_t u128;

u64 reduce(u128 x) const {
    u64 q = u64(x) * nr;
    u64 m = ((u128) q * n) >> 64;
    return (x >> 64) + n - m;
}
```

注意，用通用整数除法技巧无法做 128 位除以 64 位的模运算：编译器会[退回到](https://godbolt.org/z/fbEE4v4qr)调用一个慢速的[长算术库函数](https://github.com/llvm-mirror/compiler-rt/blob/69445f095c22aac2388f939bedebf224a6efcdaf/lib/builtins/udivmodti4.c#L22)来支持它。

### 更快的逆元与变换

Montgomery 乘法本身很快，但它需要一些预计算：

- 求 $n$ 模 $r$ 的逆元以计算 $n^\prime$，
- 把数*变换到* Montgomery 空间，
- 把数*从* Montgomery 空间变换回来。

最后一个操作已经可以用我们刚实现的 `reduce` 过程高效完成，但前两个可以稍微优化。

**计算逆元** $n^\prime = n^{-1} \bmod r$ 可以利用 $r$ 是 2 的幂这一事实，通过如下恒等式，比扩展欧几里得算法更快地完成：

$$
a \cdot x \equiv 1 \bmod 2^k
\implies
a \cdot x \cdot (2 - a \cdot x)
\equiv
1 \bmod 2^{2k}
$$

证明：

$$
\begin{aligned}
a \cdot x \cdot (2 - a \cdot x)
   &= 2 \cdot a \cdot x - (a \cdot x)^2
\\ &= 2 \cdot (1 + m \cdot 2^k) - (1 + m \cdot 2^k)^2
\\ &= 2 + 2 \cdot m \cdot 2^k - 1 - 2 \cdot m \cdot 2^k - m^2 \cdot 2^{2k}
\\ &= 1 - m^2 \cdot 2^{2k}
\\ &\equiv 1 \bmod 2^{2k}.
\end{aligned}
$$

我们可以从 $x = 1$ 作为 $a$ 模 $2^1$ 的逆元出发，应用这个恒等式恰好 $\log_2 r$ 次，每次使逆元的位数翻倍——这有点让人想起[牛顿法](../../arithmetic/newton/)。

**变换** 把数变换到 Montgomery 空间可以乘 $r$ 后按[通常的方式](../../arithmetic/division/)取模，但我们也可以利用这个关系：

$$
\bar{x} = x \cdot r \bmod n = x * r^2
$$

把数变换进空间只是一次乘以 $r^2$ 的乘法。因此，我们可以预计算 $r^2 \bmod n$，然后做一次乘法和一次约减——这可能不一定真的更快，因为乘 $r=2^{k}$ 可以用左移实现，而乘 $r^2 \bmod n$ 不行。

### 完整实现

把所有内容封装进一个 `constexpr` 结构体很方便：

```c++
struct Montgomery {
    u32 n, nr;
    
    constexpr Montgomery(u32 n) : n(n), nr(1) {
        // log(2^32) = 5
        for (int i = 0; i < 5; i++)
            nr *= 2 - n * nr;
    }

    u32 reduce(u64 x) const {
        u32 q = u32(x) * nr;
        u32 m = ((u64) q * n) >> 32;
        return (x >> 32) + n - m;
        // returns a number in the [0, 2 * n - 2] range
        // (add a "x < n ? x : x - n" type of check if you need a proper modulo)
    }

    u32 multiply(u32 x, u32 y) const {
        return reduce((u64) x * y);
    }

    u32 transform(u32 x) const {
        return (u64(x) << 32) % n;
        // can also be implemented as multiply(x, r^2 mod n)
    }
};
```

为了测试它的性能，我们可以把 Montgomery 乘法接入[快速幂](../exponentiation/)：

```c++
constexpr Montgomery space(M);

int inverse(int _a) {
    u64 a = space.transform(_a);
    u64 r = space.transform(1);
    
    #pragma GCC unroll(30)
    for (int l = 0; l < 30; l++) {
        if ( (M - 2) >> l & 1 )
            r = space.multiply(r, a);
        a = space.multiply(a, a);
    }

    return space.reduce(r);
}
```

普通的快速幂配合编译器生成的快速取模技巧，每次 `inverse` 调用大约需要 170ns，而这个实现大约需要 166ns；如果省略 `transform` 和 `reduce`，则降到约 158ns（合理的用例是 `inverse` 作为更大的模运算中的子过程）。这是一个小小的改进，但 Montgomery 乘法在 SIMD 应用和更大的数据类型上会带来更大的优势。

**练习题。** 实现高效的*模*[矩阵乘法](/hpc/algorithms/matmul)。