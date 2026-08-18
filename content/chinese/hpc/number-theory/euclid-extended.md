---
title: 扩展欧几里得算法
weight: 3
---

[费马定理](../modular/#fermats-theorem) 允许我们通过[快速幂](..exponentiation/)在 $O(\log n)$ 次操作内计算模乘法逆元，但它只对质数模数有效。它有一个推广形式，即[欧拉定理](https://en.wikipedia.org/wiki/Euler%27s_theorem)，该定理指出，如果 $m$ 与 $a$ 互质，那么

$$
a^{\phi(m)} \equiv 1 \pmod m
$$

其中 $\phi(m)$ 是[欧拉函数](https://en.wikipedia.org/wiki/Euler%27s_totient_function)，定义为与 $m$ 互质的正整数 $x < m$ 的个数。当 $m$ 是质数这一特殊情形下，所有 $m - 1$ 个剩余都与它互质，$\phi(m) = m - 1$，从而得到费马定理。

只要知道 $\phi(m)$，我们就能把 $a$ 的逆元计算为 $a^{\phi(m) - 1}$；但反过来，计算它并不快：你通常需要先得到 $m$ 的[分解](/hpc/algorithms/factorization/)才能做到。还有一种更通用的方法，通过修改[欧几里得算法](/hpc/algorithms/gcd/)实现。

### 算法

*扩展欧几里得算法*除了求出 $g = \gcd(a, b)$ 之外，还求出满足下式的整数 $x$ 和 $y$：

$$
a \cdot x + b \cdot y = g
$$

如果我们把 $b$ 换成 $m$、把 $g$ 换成 $1$，就解决了求模逆元的问题：

$$
a^{-1} \cdot a + k \cdot m = 1
$$

注意，如果 $a$ 与 $m$ 不互质，则无解，因为 $a$ 和 $m$ 的任何整数组合都不可能得到不是它们最大公约数倍数的值。

该算法同样是递归的：它为 $\gcd(b, a \bmod b)$ 计算系数 $x'$ 和 $y'$，再恢复出原始数对的解。如果我们有数对 $(b, a \bmod b)$ 的解 $(x', y')$

$$
b \cdot x' + (a \bmod b) \cdot y' = g
$$

那么，为了得到初始输入的解，我们可以把 $(a \bmod b)$ 改写成 $(a - \lfloor \frac{a}{b} \rfloor \cdot b)$ 并代入上述方程：

$$
b \cdot x' + (a - \Big \lfloor \frac{a}{b} \Big \rfloor \cdot b) \cdot y' = g
$$

现在我们按 $a$ 和 $b$ 重新整理各项，得到

$$
a \cdot \underbrace{y'}_x + b \cdot \underbrace{(x' - \Big \lfloor \frac{a}{b} \Big \rfloor \cdot y')}_y = g
$$

与最初的表达式比较，我们可以推断：只需把 $a$ 和 $b$ 的系数分别作为初始的 $x$ 和 $y$ 即可。

### 实现

我们把算法实现为递归函数。由于它的输出不是一个而是三个整数，我们通过引用把系数传给函数：

```c++
int gcd(int a, int b, int &x, int &y) {
    if (a == 0) {
        x = 0;
        y = 1;
        return b;
    }
    int x1, y1;
    int d = gcd(b % a, a, x1, y1);
    x = y1 - (b / a) * x1;
    y = x1;
    return d;
}
```

要计算逆元，我们只需传入 $a$ 和 $m$，然后返回算法求出的 $x$ 系数。由于我们传入的是两个正数，其中一个系数为正、另一个为负（正负取决于迭代次数是奇数还是偶数），所以我们只需检查 $x$ 是否为负，若是则加上 $m$ 得到正确的剩余：

```c++
int inverse(int a) {
    int x, y;
    gcd(a, M, x, y);
    if (x < 0)
        x += M;
    return x;
}
```

它大约需要 160ns——比用[快速幂](../exponentiation)求逆元快 10ns。为了进一步优化，我们可以类似地把它改为迭代版本——耗时 135ns：

```c++
int inverse(int a) {
    int b = M, x = 1, y = 0;
    while (a != 1) {
        y -= b / a * x;
        b %= a;
        swap(a, b);
        swap(x, y);
    }
    return x < 0 ? x + M : x;
}
```

注意，与快速幂不同，这里的运行时间取决于 $a$ 的值。例如，对于这个特定的 $m$（$10^9 + 7$），最坏输入恰好是 564400443，算法对它执行 37 次迭代，耗时 250ns。

**练习题**。尝试把同样的技巧应用于[二进制 GCD](/hpc/algorithms/gcd/#binary-gcd)（除非你比我更擅长优化，否则它不会带来性能提升）。