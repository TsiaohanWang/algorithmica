---
title: 二进制 GCD
weight: 1
aliases: [/hpc/analyzing-performance/gcd]
---

在本节中，我们将推导出一个 `gcd` 的变体，它比 C++ 标准库中的版本快约 2 倍。

## 欧几里得算法

欧几里得算法解决的是求两个整数 $a$ 和 $b$ 的*最大公约数*（GCD）问题，定义为能同时整除 $a$ 和 $b$ 的最大的数 $g$：

$$
\gcd(a, b) = \max_{g: \; g|a \, \land \, g | b} g
$$

你可能已经从计算机科学的教材中知道了这个算法，但我还是在这里总结一下。它基于下面的公式（假设 $a > b$）：

$$
\gcd(a, b) = \begin{cases}
    a, & b = 0
\\ \gcd(b, a \bmod b), & b > 0
\end{cases}
$$

这是成立的，因为如果 $g = \gcd(a, b)$ 同时整除 $a$ 和 $b$，那么它也应该整除 $(a \bmod b = a - k \cdot b)$；但任何更大的 $b$ 的因子 $d$ 则不会：$d > g$ 意味着 $d$ 不能整除 $a$，因此也整除不了 $(a - k \cdot b)$。

上面的公式本质上就是算法本身：你可以直接递归地应用它，由于每次其中一个参数严格减小，它最终会收敛到 $b = 0$ 的情形。

教材大概还提到过：欧几里得算法的最坏输入——使总步数最大的输入——是相邻的斐波那契数，由于它们呈指数增长，算法在最坏情况下的运行时间是对数级别的。如果把平均运行时间定义为均匀分布整数对上的期望步数，那么*平均*运行时间同样是对数级别的。[维基百科条目](https://en.wikipedia.org/wiki/Euclidean_algorithm)还有一个更精确的 $0.84 \cdot \ln n$ 渐近估计的晦涩推导。

![在黄金比例的比例处可以看到亮蓝色的线条](../img/euclid.svg)

实现欧几里得算法的方式有很多。最简单的就是把定义直接翻译成代码：

```c++
int gcd(int a, int b) {
    if (b == 0)
        return a;
    else
        return gcd(b, a % b);
}
```

可以更紧凑地改写成这样：

```c++
int gcd(int a, int b) {
    return (b ? gcd(b, a % b) : a);
}
```

也可以改写为一个循环，这样更接近硬件实际执行的方式。不过它并不会更快，因为编译器很容易优化尾递归。

```c++
int gcd(int a, int b) {
    while (b > 0) {
        a %= b;
        std::swap(a, b);
    }
    return a;
}
```

你甚至可以把循环体写成这样一个令人困惑的一行代码——自 C++17 起它甚至能编译通过，不会触发未定义行为的警告：

```c++
int gcd(int a, int b) {
    while (b) b ^= a ^= b ^= a %= b;
    return a;
}
```

所有这些版本，以及 C++17 引入的 `std::gcd`，几乎都是等价的，并被[编译](https://godbolt.org/z/r8z5KcGqK)成功能上如下的汇编循环：

```nasm
; a = eax, b = edx
loop:
    ; modulo in assembly:
    mov  r8d, edx
    cdq
    idiv r8d
    mov  eax, r8d
    ; (a and b are already swapped now)
    ; continue until b is zero:
    test edx, edx
    jne  loop
```

如果你在上面运行 [perf](/hpc/profiling/events)，会看到它约 90% 的时间都花在 `idiv` 这一行上。这并不令人意外：通用的[整数除法](/hpc/arithmetic/division)在所有计算机（包括 x86）上都臭名昭著地慢。

但有一种除法在硬件上表现很好：除以 2 的幂。

## 二进制 GCD

*二进制 GCD 算法*大约与欧几里得同时代被发现，但出现在文明世界的另一端——古代中国。1967 年，Josef Stein 重新发现了它，用于那些没有除法指令或除法指令很慢的计算机——那个年代的 CPU 为罕见或复杂的操作耗费数百或数千个周期并不罕见。

与欧几里得算法类似，它也基于几条相似的观察：

1. $\gcd(0, b) = b$，对称地 $\gcd(a, 0) = a$；
2. $\gcd(2a, 2b) = 2 \cdot \gcd(a, b)$；
3. 若 $b$ 为奇数，则 $\gcd(2a, b) = \gcd(a, b)$，对称地，若 $a$ 为奇数，则 $\gcd(a, b) = \gcd(a, 2b)$；
4. 若 $a$ 和 $b$ 均为奇数，则 $\gcd(a, b) = \gcd(|a − b|, \min(a, b))$。

同样，算法本身只是反复应用这些恒等式。

它的运行时间仍然是对数级别的，而且更容易证明，因为每个恒等式都会让其中一个参数除以 2——除了最后一种情况，其中新的第一个参数（两个奇数的绝对差）保证是偶数，因而会在下一轮迭代中被除以 2。

这个算法之所以特别值得我们关注，是因为它用到的算术运算只有移位、比较和减法，而它们通常都只需要一个周期。

### 实现

这个算法之所以没有出现在教科书里，是因为它不能再被写成简单的一行代码了：

```c++
int gcd(int a, int b) {
    // base cases (1)
    if (a == 0) return b;
    if (b == 0) return a;
    if (a == b) return a;

    if (a % 2 == 0) {
        if (b % 2 == 0) // a is even, b is even (2)
            return 2 * gcd(a / 2, b / 2);
        else            // a is even, b is odd (3)
            return gcd(a / 2, b);
    } else {
        if (b % 2 == 0) // a is odd, b is even (3)
            return gcd(a, b / 2);
        else            // a is odd, b is odd (4)
            return gcd(std::abs(a - b), std::min(a, b));
    }
}
```

运行一下，然后……它很糟糕。与 `std::gcd` 的速度差确实是 2 倍，只不过方向反了。这主要是因为区分这些情况需要大量分支。让我们开始优化。

首先，把所有除以 2 换成除以我们所能除的 2 的最高次幂。我们可以用 `__builtin_ctz`——现代 CPU 上的「统计末尾零」指令——高效地做到这一点。每当我们本应在原算法中除以 2 时，就调用这个函数，它会给出应该把数右移的确切位数。假设我们处理的是大的随机数，这预计会把迭代次数减少近一半，因为 $1 + \frac{1}{2} + \frac{1}{4} + \frac{1}{8} + \ldots \to 2$。

其次，可以注意到条件 2 现在只可能在一开始成立一次——因为其他每个恒等式都会让至少一个数保持为奇数。因此我们可以在一开始就只处理这一次，而在主循环中不再考虑它。

第三，可以注意到，在我们进入条件 4 并应用它的恒等式之后，$a$ 将永远是偶数、$b$ 将永远是奇数，所以我们已经知道下一轮迭代会进入条件 3。这意味着我们其实可以立即「去除 $a$ 的因子 2」；而如果这样做，下一轮又会在条件 4 中。这意味着我们只可能处于条件 4，或被条件 1 终止，这就不需要分支了。

综合这些想法，我们得到如下实现：

```c++
int gcd(int a, int b) {
    if (a == 0) return b;
    if (b == 0) return a;

    int az = __builtin_ctz(a);
    int bz = __builtin_ctz(b);
    int shift = std::min(az, bz);
    a >>= az, b >>= bz;
    
    while (a != 0) {
        int diff = a - b;
        b = std::min(a, b);
        a = std::abs(diff);
        a >>= __builtin_ctz(a);
    }
    
    return b << shift;
}
```

它运行耗时 116ns，而 `std::gcd` 需要 198ns。几乎快了一倍——也许我们还能优化到 100ns 以下？

为此我们需要再仔细看看[它的汇编代码](https://godbolt.org/z/nKKMe48cW)，尤其是这一段：

```nasm
; a = edx, b = eax
loop:
    mov   ecx, edx
    sub   ecx, eax       ; diff = a - b
    cmp   eax, edx
    cmovg eax, edx       ; b = min(a, b)
    mov   edx, ecx
    neg   edx
    cmovs edx, ecx       ; a = max(diff, -diff) = abs(diff)
    tzcnt ecx, edx       ; az = __builtin_ctz(a)
    sarx  edx, edx, ecx  ; a >>= az
    test  edx, edx       ; a != 0?
    jne   loop
```

让我们画出这个循环的依赖图：

<!--
\node [draw, circle] (diff)  at (3, 10) {diff};
\node [draw, circle] (min)   at (1.5, 8.9) {min};
\node [draw, circle] (abs)   at (3, 8.9) {abs};
\node [draw, circle] (ctz)   at (3, 7.8) {ctz};
\node [draw, circle] (shift) at (3, 6.6) {shift};
\node [draw, circle] (test)  at (3, 5.3) {test};

\path [->] (diff) edge (abs);
\path [->] (abs) edge (ctz);
\path [->] (ctz) edge (shift);
\path [->, dashed] (min) edge [bend left] (diff);
\path [->, dotted] (shift) edge (test);
\path [->, dashed] (shift) edge [bend right=75] (diff);
\path [->, dashed] (shift) edge [bend left=25] (min);
-->

![](../img/gcd-dependency1.png)

现代处理器可以并行执行许多指令，这实质上意味着这个计算的真正「代价」大约等于其关键路径上的延迟之和。在这个例子中，就是 `diff`、`abs`、`ctz` 和 `shift` 的总延迟。

我们可以利用一个事实来降低这个延迟：其实只用 `diff = a - b` 就能计算 `ctz`，因为一个能被 $2^k$ 整除的[负数](../hpc/arithmetic/integer/#signed-integers)在其二进制表示末尾仍然有 $k$ 个零。这让我们不必先算出 `max(diff, -diff)`，从而得到这样一条更短的依赖图：

<!--
\node [draw, circle] (diff)  at (3, 10) {diff};
\node [draw, circle] (min)   at (1.5, 8.9) {min};
\node [draw, circle] (abs)   at (4.5, 8.9) {abs};
\node [draw, circle] (ctz)   at (3, 8.9) {ctz};
\node [draw, circle] (shift) at (3, 7.8) {shift};
\node [draw, circle] (test)  at (5.6, 9.4) {test};

\path [->] (diff) edge (abs);
\path [->] (diff) edge (ctz);
\path [->] (ctz) edge (shift);
\path [->, dashed] (min) edge [bend left] (diff);
\path [->, dotted] (diff) edge (test);
\path [->, dashed] (shift) edge [bend left=25] (min);
\path [->, dashed] (abs) edge [bend left=25] (diff);
-->

![](../img/gcd-dependency2.png)

想想最终代码将如何执行，你大概就不会那么困惑了：

```c++
int gcd(int a, int b) {
    if (a == 0) return b;
    if (b == 0) return a;

    int az = __builtin_ctz(a);
    int bz = __builtin_ctz(b);
    int shift = std::min(az, bz);
    b >>= bz;
    
    while (a != 0) {
        a >>= az;
        int diff = b - a;
        az = __builtin_ctz(diff);
        b = std::min(a, b);
        a = std::abs(diff);
    }
    
    return b << shift;
}
```

它运行耗时 91ns，已经足够好，就此打住。

如果有人想通过手工改写汇编或使用查找表再省下最后几次迭代、多挤出几个纳秒，请[告诉我](http://sereja.me/)。

### 致谢

主要的优化思路属于 Daniel Lemire 和 Ralph Corderoy，他们在 2013 年的圣诞假期里[闲得没事干](https://lemire.me/blog/2013/12/26/fastest-way-to-compute-the-greatest-common-divisor/)想到了这些。
