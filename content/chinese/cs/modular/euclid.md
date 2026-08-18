---
title: 欧几里得算法
weight: 1
---

非负整数 $a$ 与 $b$ 的*最大公约数*（英文 *greatest common divisor*）是同时整除 $a$ 和 $b$ 的最大的数 $x$。

$$
\gcd(a, b) = \max_{k: \; k|a \, \land \, k | b} k
$$

当两个数都为零时，结果未定义——任意多大的数都合适。除这种情况外，有下面的观察：如果其中一个数为零，那么它们的 $\gcd$ 等于另一个数。

## 求法

**欧几里得算法**在 $O(\log \min(a, b))$ 内求两个数 $a$ 和 $b$ 的 $\gcd$，基于下面这个简单的公式：

$$
\gcd(a, b) = \begin{cases}
a, & b = 0 \\
\gcd(b,\, a - b), & b > 0
\end{cases}
$$

这里假设 $a > b$。

证明这个公式的正确性：

* 如果 $g = \gcd(a, b)$ 整除 $a$ 和 $b$，那么它们的差 $(a-b)$ 也被 $g$ 整除。

* $b$ 的任何更大因数 $d$ 都不能整除 $(a-b)$：如果 $d > g$，那么 $d$ 不能整除 $a$，因此也不整除 $(a - b)$。

直接的递归实现：

```c++
int gcd(int a, int b) {
    if (a < b)
        swap(a, b);
    if (b == 0)
        return a;
    else
        return gcd(b, a - b);
}
```

这个算法可能很慢——例如对 pair $(10^9, 1)$ 它要做十亿次迭代。

进一步优化的思路是：不从 $a$ 里一次减一个 $b$，而是减到下次 $a$ 和 $b$ 互换位置为止——让新的 $b$ 小于新的 $a$。达到这个目的简单办法是：一次性从 $a$ 中尽可能多地减 $b$，即把新的 $b$ 取为 $a$ 除以 $b$ 的余数：

$$
\gcd(a, b) = \begin{cases}
a, & b = 0 \\
\gcd(b,\, a \bmod b), & b > 0
\end{cases}
$$

实现：

```c++
int gcd(int a, int b) {
    if (b == 0)
        return a;
    else
        return gcd(b, a % b);
}
```

稍快一些的迭代形式：

```c++
int gcd(int a, int b) {
    while (b > 0) {
        a %= b;
        swap(a, b);
    }
    return a;
}
```

在现代 C++ 中内置了库函数 `gcd`，推荐使用它，但别忘处理负数与 $(0, 0)$ 的情况。

此外，除了欧几里得算法，还有一个快 2–3 倍的[二进制 GCD](https://en.algorithmica.org/hpc/analyzing-performance/gcd/)。

### 运行时间

可以证明，每两次迭代较小的数至少减半，因此算法运行在 $O(\log \min (a, b))$。这个估计不仅对最坏情况成立，对平均情况也成立。

![算法在不同输入上的运行时间](../img/euclidean.png)

值得注意的是，算法最坏的输入是相邻的斐波那契数。在图上它们表现为黄金比例比例下的蓝点。

有时还值得知道：求从 1 到 $A$ 的 $n$ 个数的 $\gcd$，运行时间不是 $O(n \log A)$，而是 $O(n + \log A)$——这用归纳法容易证明。
