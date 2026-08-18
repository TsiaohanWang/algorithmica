---
title: 模意义下的「除法」
weight: 3
prerequisites:
- /cs/algebra/binpow
- extended-euclid
---

竞赛题里经常需要按质数模（最常见是 $10^9 + 7$）计算大的组合量。这样做的目的是让选手不必使用高精度，从而专注于题目本身。

普通的模算术操作并不难——只需取模并注意溢出。例如：

```cpp
c = (a + b) % mod;
c = (a - b + mod) % mod;
c = a * b % mod;
```

但除法会出问题——我们不能直接除。

例如 $\frac{8}{2} = 4$，但

$$
\frac{8 \bmod 5}{2 \bmod 5} = \frac{3}{2} \neq 4
$$

需要找某个表现得像 $\frac{1}{a} = a^{-1}$ 的元素，用它代替「除法」去乘。这样的元素叫模 $m$ 下的*逆元*。对 $a = 0$，模逆元未定义，正如普通除法一样。

## 用快速幂

费马小定理说：对任何质数 $p$ 和任何整数 $a$，

$$
a^p \equiv a \pmod p
$$

现在把这个已知结果「除」两次：

$$
a^p \equiv a \implies a^{p-1} \equiv 1 \implies a^{p-2} \equiv a^{-1}
$$

于是 $a^{p-2}$ 表现得像模乘法意义下的 $a^{-1}$，正是我们需要的。

可以用快速幂在 $O(\log p)$ 内算 $a^{p-2}$。

```c++
const int mod = 1e9 + 7;

// 模快速幂
int binpow(int a, int n) {
    int res = 1;
    while (n != 0) {
        if (n & 1)
            res = res * a % mod;
        a = a * a % mod;
        n >>= 1;
    }
    return res;
}

// 求逆元作为 a^(p-2)
int inv(int x) {
    return binpow(x, mod - 2);
}
```

这个方法简单快速，但要记住只对质数模有效。

对合数模，按欧拉定理，数 $a$ 要取 $(\phi(m)-1)$ 次幂，为此需要分解。

## 用扩展欧几里得算法

[扩展欧几里得算法](../extended-euclid)可以求如下形式方程的整数解

$$ Ax + By = 1 $$

把 $A$ 和 $B$ 分别代成 $a$ 和 $m$：

$$ ax + my = 1 $$

方程的一个解就是 $a^{-1}$，因为对模 $m$ 取这个方程，得到

$$ ax + my = 1 \iff ax \equiv 1 \iff x \equiv a^{-1} \pmod m $$

这个方法相对快速幂的优势：

- 只要逆存在，即使模不是质数也能求出。
- 算法手算更简单。
- 优化后算法稍快。

但作者本人几乎总用快速幂。

### 简化实现

先给实现，再理解为什么它正确：

```cpp
int inv(int a, int m) {
    if (a == 1)
        return 1;
    return (1 - 1ll * inv(m % a, a) * m) / a + m;
}
```

用归纳法证明函数确实返回逆元。

基础情形显然：$1 \cdot 1 \equiv 1$。

第二种情形检查公式正确性：

- $(1 - f(m \bmod a, a) \cdot m)$ 被 $a$ 整除，因为 $f(m \bmod a, a) \equiv m^{-1} \pmod a$。
- $\frac{f(m \bmod a, a) \cdot m}{a}$ 被 $m$ 整除，所以最终表达式模 $m$ 同余于 $\frac{1}{a} = a^{-1}$。

为什么答案会在 0 到 $(m - 1)$ 范围内，留作读者练习。

## 预计算逆元

多数时候我们是在组合数学语境下求逆元。

例如，尤其常用的是算二项式系数，为此需要能反转阶乘：

$$
C_n^k = \frac{n!}{(n-k)! k!}
$$

简单做法是预计算普通阶乘，每次调用 `inv` 一两次：

```c++
int t[maxn]; // 阶乘，可用简单循环预计算

int c(int n, int k) {
    return t[n] * inv(t[k]) % mod * inv(t[n - k]) % mod;
}

// 或，几乎快一倍：
int c(int n, int k) {
    return t[n] * inv(t[k] * t[n - k] % mod) % mod;
}
```

但这会在不罕见的情形（某个组合公式位于热循环内）给复杂度加上多余的对数。因此值得预计算常用逆元。

### 逆阶乘

如果已有 `inv`，就不心疼多花 $O(\log m)$ 次操作算 $(a!)^{-1}$。

之后 $(a-1)!$ 的逆元可以用 $O(1)$ 按公式算：

$$
(a-1)!^{-1}
=
(a!)^{-1} \cdot a
\equiv
\frac{1}{1 \cdot 2 \cdot \ldots \cdot (a-1)}
\pmod p
$$

其余所有逆阶乘都可以同样从前一个迭代算出。

```c++
// 普通阶乘：
int f[maxn];

f[0] = 1;
for (int i = 1; i < maxn; i++)
    f[i] = i * f[i - 1] % mod;

// 逆阶乘：
int r[maxn];

r[maxn - 1] = inv(f[maxn - 1])
for (int i = maxn - 1; i >= 1; i--)
    r[i-1] = r[i] * i % mod;
```

还有求 1 到 $(p - 1)$ 所有数逆元的[方法](http://e-maxx.ru/algo/reverse_element)，但通常模很大，不常适用。

## 为什么是 $10^9+7$？

几个原因：

1. 这个表达式很好敲（`1e9+7`）。
2. 是质数。
3. 足够大。
4. `int` 相加不溢出。
5. `long long` 相乘不溢出。

顺便，$10^9 + 9$ 有全部同样的性质。有时也用它们。

有时会看到 $998244353$。它具备除第一个外的所有性质，但能在[快速傅里叶变换](/cs/algebra/fft)的一种变体中使用。有时甚至把它加进无关的题目里，以免向选手透露主题。
