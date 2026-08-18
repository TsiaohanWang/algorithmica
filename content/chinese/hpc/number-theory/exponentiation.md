---
title: 快速幂
weight: 2
---

在模运算（以及一般的计算代数）中，你经常需要把一个数提升到 $n$ 次幂——比如做[模除法](../modular/#modular-division)、执行[素数测试](../modular/#fermats-theorem)，或者计算某些组合数值——而你通常希望用少于 $\Theta(n)$ 次操作完成计算。

*快速幂*（binary exponentiation），又称*平方求幂*（exponentiation by squaring），是一种用 $O(\log n)$ 次乘法计算 $n$ 次幂的方法，它基于如下观察：

$$
\begin{aligned}
    a^{2k}       &= (a^k)^2
\\  a^{2k + 1}   &= (a^k)^2 \cdot a
\end{aligned}
$$

要计算 $a^n$，我们可以递归地计算 $a^{\lfloor n / 2 \rfloor}$，将其平方，然后如果 $n$ 是奇数再乘上 $a$，对应如下递推式：

$$
a^n = f(a, n) = \begin{cases}
   1,               && n = 0
\\ f(a, \frac{n}{2})^2,     && 2 \mid n
\\ f(a, n - 1) \cdot a, && 2 \nmid n
\end{cases}
$$

由于每两次递归转移 $n$ 至少减半，这个递推的深度以及乘法总次数至多为 $O(\log n)$。

### 递归实现

既然已经有了递推式，很自然地把它实现为分支匹配的递归函数：

```c++
const int M = 1e9 + 7; // modulo
typedef unsigned long long u64;

u64 binpow(u64 a, u64 n) {
    if (n == 0)
        return 1;
    if (n % 2 == 1)
        return binpow(a, n - 1) * a % M;
    else {
        u64 b = binpow(a, n / 2);
        return b * b % M;
    }
}
```

在我们的基准测试中，我们取 $n = m - 2$，这样计算的就是 $a$ 模 $m$ 的[乘法逆元](../modular/#modular-division)：

```c++
u64 inverse(u64 a) {
    return binpow(a, M - 2);
}
```

我们使用 $m = 10^9+7$，这是竞赛编程中计算组合问题校验和时常用的模数——因为它是一个质数（允许用快速幂求逆元）、足够大、加法不会溢出 `int`、乘法不会溢出 `long long`，而且可以方便地写成 `1e9 + 7`。

由于我们在代码中把它用作编译期常量，编译器可以通过[用乘法替代](/hpc/arithmetic/division/)来优化取模运算（即使它不是编译期常量，手动计算一次魔数常量、再用其做快速约减也更划算）。

执行路径——以及随之而来的运行时间——取决于 $n$ 的值。对于这个特定的 $n$，基准实现每次调用大约需要 330ns。由于递归会引入一些[开销](/hpc/architecture/functions/)，把它展开成迭代过程是合理的。

### 迭代实现

$a^n$ 的结果可以表示为 $a$ 的一些 2 的幂次之积——这些幂次对应 $n$ 的二进制表示中的 1。例如，如果 $n = 42 = 32 + 8 + 2$，那么

$$
a^{42} = a^{32+8+2} = a^{32} \cdot a^8 \cdot a^2 
$$

为了计算这个乘积，我们可以遍历 $n$ 的二进制位，维护两个变量：$a^{2^k}$ 的值，以及考虑了 $n$ 的低 $k$ 位之后的当前乘积。每一步，如果 $n$ 的第 $k$ 位为 1，就把当前乘积乘上 $a^{2^k}$；无论哪种情况，都把 $a^k$ 平方得到 $a^{2^k \cdot 2} = a^{2^{k+1}}$，供下一轮迭代使用。

```c++
u64 binpow(u64 a, u64 n) {
    u64 r = 1;
    
    while (n) {
        if (n & 1)
            r = res * a % M;
        a = a * a % M;
        n >>= 1;
    }
    
    return r;
}
```

迭代实现每次调用大约需要 180ns。主要的计算开销相同；改进主要来自依赖链的缩短：`a = a * a % M` 必须在循环继续之前完成，而它现在可以与 `r = res * a % M` 并发执行。

性能还受益于 $n$ 是常量，[使所有分支都可预测](/hpc/pipelining/branching/)，并让调度器提前知道需要执行什么。不过，编译器并不会利用这一点，也不会展开 `while(n) n >>= 1` 循环。我们可以把它改写成执行固定 30 次迭代的 `for` 循环：

```c++
u64 inverse(u64 a) {
    u64 r = 1;
    
    #pragma GCC unroll(30)
    for (int l = 0; l < 30; l++) {
        if ( (M - 2) >> l & 1 )
            r = r * a % M;
        a = a * a % M;
    }

    return r;
}
```

这迫使编译器展开循环并精确地输出我们需要的指令，再省下 10ns，使总运行时间约为 170ns。

注意，性能不仅取决于 $n$ 的二进制长度，还取决于二进制中 1 的个数。如果 $n$ 是 $2^{30}$，耗时大约少 20ns，因为我们不需要执行任何分支路径上的乘法。