---
title: 整数分解
weight: 3
published: true
---

把整数分解为质数的问题，是计算[数论](/hpc/number-theory/)的核心问题。它至少从公元前 3 世纪起就被人[研究](https://www.cs.purdue.edu/homes/ssw/chapter3.pdf)，并且已经发展出[许多方法](https://en.wikipedia.org/wiki/Category:Integer_factorization_algorithms)，分别对不同规模的输入高效。

在本案例研究中，我们专门考虑*机器字大小*整数的分解：即 $10^9$ 和 $10^{18}$ 量级的数。这本书很少见地，会带你真正学到一种渐近上更优的算法：我们从几种基本方法出发，逐步构建出 $O(\sqrt[4]{n})$ 时间的 *Pollard rho 算法*，并将其优化到能在 0.3–0.4ms 内分解 60 位半素数，比此前的最高水平快约 3 倍。

<!--
整数分解之所以有趣，是因为 RSA 问题。
与本书的其他案例研究不同，在这里你确实会学到一种此前从未见过的渐近更优的算法——Pollard rho 算法——据我所知，我们将其优化到比现有实现快近 4 倍。
-->

### 基准测试

对于所有方法，我们都将实现 `find_factor` 函数：它接收一个正整数 $n$，返回它的任意一个非平凡因子（如果 $n$ 是质数则返回 `1`）：

```c++
// I don't feel like typing "unsigned long long" each time
typedef __uint16_t u16;
typedef __uint32_t u32;
typedef __uint64_t u64;
typedef __uint128_t u128;

u64 find_factor(u64 n);
```

要求出完整的分解，可以对 $n$ 调用它、约去该因子，然后继续，直到再也找不到新的因子为止：

```c++
vector<u64> factorize(u64 n) {
    vector<u64> factorization;
    do {
        u64 d = find_factor(n);
        factorization.push_back(d);
        n /= d;
    } while (d != 1);
    return factorization;
}
```

每去掉一个因子后，问题规模都会显著变小，因此完整分解的最坏运行时间等于一次 `find_factor` 调用的最坏运行时间。

对于许多分解算法（包括本节介绍的那些），运行时间随较小的质因子而伸缩。因此，为了构造最坏情况的输入，我们使用*半素数*：两个在同一数量级上的质数 $p \le q$ 的乘积。我们生成一个 $k$ 位半素数，作为两个随机 $\lfloor k / 2 \rfloor$ 位质数的乘积。

由于部分算法本质上是随机化的，我们也容忍一个较小（<1%）的假阴性错误率（即 $n$ 其实是合数，但 `find_factor` 返回了 `1`），尽管这个比率可以在不显著损失性能的情况下降到几乎为零。

### 试除法

<!--

试除法最早由 Fibonacci 在 1202 年描述。尽管动物们可能早就知道它。也许有些动物会分解因数？科学优先权大概属于试图分东西的恐龙或远古鱼类。

0.056024

-->

最基础的方法是尝试把每个小于 $n$ 的整数当作因子：

```c++
u64 find_factor(u64 n) {
    for (u64 d = 2; d < n; d++)
        if (n % d == 0)
            return d;
    return 1;
}
```

我们可以注意到：如果 $n$ 被 $d < \sqrt n$ 整除，那么它也被 $\frac{n}{d} > \sqrt n$ 整除，因此没有必要单独检查后者。这让我们可以提前停止试除，只检查不超过 $\sqrt n$ 的潜在因子：

```c++
u64 find_factor(u64 n) {
    for (u64 d = 2; d * d <= n; d++)
        if (n % d == 0)
            return d;
    return 1;
}
```

在我们的基准测试中，$n$ 是半素数，我们总能找到较小的那个因子，所以 $O(n)$ 和 $O(\sqrt n)$ 两种实现表现相同，每秒都能分解约 2k 个 30 位数——但分解单个 60 位数却要整整 20 秒。

### 查找表

如今，你可以在 Linux 终端或 Google 搜索框里输入 `factor 57` 来得到任意数的分解。但在计算机发明之前，更实际的做法是使用*因数分解表*：收录前 $N$ 个数的因数分解的专门书籍。

我们也可以在[编译期](/hpc/compilation/precalc/)计算这样的查找表。为了节省空间，我们可以只存储一个数的最小因子。由于最小因子不超过 $\sqrt n$，每个 16 位整数只需要一个字节：

```c++
template <int N = (1<<16)>
struct Precalc {
    unsigned char divisor[N];

    constexpr Precalc() : divisor{} {
        for (int i = 0; i < N; i++)
            divisor[i] = 1;
        for (int i = 2; i * i < N; i++)
            if (divisor[i] == 1)
                for (int k = i * i; k < N; k += i)
                    divisor[k] = i;
    }
};

constexpr Precalc P{};

u64 find_factor(u64 n) {
    return P.divisor[n];
}
```

用这种方法，我们每秒可以处理 3M 个 16 位整数，不过对于更大的数，速度可能会[变慢](../../cpu-cache/bandwidth/)。虽然计算并存储前 $2^{16}$ 个数的因子只需要几毫秒和 64KB 内存，但这种方法对更大的输入扩展性不佳。

### 轮筛法

为了节省纸张，前计算机时代的因数分解表通常排除能被 $2$ 和 $5$ 整除的数，使表的大小缩小为原来的 ½ × ⅘ = 0.4。在十进制数制下，你可以快速判断一个数能否被 $2$ 或 $5$ 整除（看它的末位数字），并尽可能持续地用 $2$ 或 $5$ 去除 $n$，最终到达因数分解表中的某个条目。

我们可以把类似的技巧用到试除法中：先检查数能否被 $2$ 整除，然后只考虑奇数因子：

```c++
u64 find_factor(u64 n) {
    if (n % 2 == 0)
        return 2;
    for (u64 d = 3; d * d <= n; d += 2)
        if (n % d == 0)
            return d;
    return 1;
}
```

需要执行的除法少了 50%，因此这个算法快了一倍。

这种方法还可以推广：如果数不能被 $3$ 整除，我们也可以忽略所有 $3$ 的倍数，其他因子同理。问题是，随着要排除的质数增多，只遍历那些不被它们整除的数就变得不那么直接了，因为这些数遵循一种不规则的模式——除非质数的个数很少。

例如，如果考虑 $2$、$3$ 和 $5$，那么在前 $90$ 个数中，我们只需要检查：

```center
(1,) 7, 11, 13, 17, 19, 23, 29,
31, 37, 41, 43, 47, 49, 53, 59,
61, 67, 71, 73, 77, 79, 83, 89…
```

你可以注意到一个规律：这个序列每 $30$ 个数重复一次。这并不奇怪，因为要判断一个数能否被 $2$、$3$ 或 $5$ 整除，我们只需要它模 $2 \times 3 \times 5 = 30$ 的余数。这意味着我们只需要在每 $30$ 个数中检查 8 个具有特定余数的数，性能按比例提升：

```c++
u64 find_factor(u64 n) {
    for (u64 d : {2, 3, 5})
        if (n % d == 0)
            return d;
    u64 offsets[] = {0, 4, 6, 10, 12, 16, 22, 24};
    for (u64 d = 7; d * d <= n; d += 30) {
        for (u64 offset : offsets) {
            u64 x = d + offset;
            if (n % x == 0)
                return x;
        }
    }
    return 1;
}
```

正如预期，它比朴素试除法快 $\frac{30}{8} = 3.75$ 倍，每秒约处理 7.6k 个 30 位数。考虑更多质数还能进一步提升性能，但收益递减：每加入一个新质数 $p$，迭代次数减少 $\frac{1}{p}$，但跳表（skip-list）的大小增大到 $p$ 倍，需要按比例占用更多内存。

### 预计算质数表

如果我们不断增加轮筛法中质数的个数，最终会排除所有合数，只检查质因子。此时我们不需要那组偏移量，只需要质数数组：

```c++
const int N = (1 << 16);

struct Precalc {
    u16 primes[6542]; // # of primes under N=2^16

    constexpr Precalc() : primes{} {
        bool marked[N] = {};
        int n_primes = 0;

        for (int i = 2; i < N; i++) {
            if (!marked[i]) {
                primes[n_primes++] = i;
                for (int j = 2 * i; j < N; j += i)
                    marked[j] = true;
            }
        }
    }
};

constexpr Precalc P{};

u64 find_factor(u64 n) {
    for (u16 p : P.primes)
        if (n % p == 0)
            return p;
    return 1;
}
```

这种方法让我们每秒能处理近 20k 个 30 位整数，但对更大的（64 位）数不适用，除非它们含有小的（$< 2^{16}$）因子。

注意，这实际上是一种渐近优化：前 $n$ 个数中有 $O(\frac{n}{\ln n})$ 个质数，因此这个算法执行 $O(\frac{\sqrt n}{\ln \sqrt n})$ 次操作，而轮筛法只是消除了一大但恒定的因子占比。如果我们把它扩展到 64 位数并预计算 $2^{32}$ 以下的所有质数（存储它们需要几百 MB 内存），相对加速比将提高 $\frac{\ln \sqrt{n^2}}{\ln \sqrt n} = 2 \cdot \frac{1/2}{1/2} \cdot \frac{\ln n}{\ln n} = 2$ 倍。

试除法的所有变体（包括本方法）都受整数除法的速度制约；如果我们事先知道因子并允许一些额外的预计算，整数除法是可以[优化](/hpc/arithmetic/division/)的。在我们的情形下，适合使用[Lemire 除法检查](/hpc/arithmetic/division/#lemire-reduction)：

```c++
// ...precomputation is the same as before,
// but we store the reciprocal instead of the prime number itself
u64 magic[6542];
// for each prime i:
magic[n_primes++] = u64(-1) / i + 1;

u64 find_factor(u64 n) {
    for (u64 m : P.magic)
        if (m * n < m)
            return u64(-1) / m + 1;
    return 1;
}
```

这使算法快了约 18 倍：我们现在每秒可以分解约 **35 万**个 30 位数，这实际上是我们拥有的针对该数值范围最高效的算法。虽然或许还可以用 [SIMD](/hpc/simd) 并行执行这些检查来进一步优化，但我们将到此为止，转而尝试一种不同的、渐近上更好的方法。

### Pollard rho 算法

<!--

先看这个奇怪的代码片段：

```c++
u64 find_factor(u64 n) {
    while (true) {
        if (u64 g = gcd(randint(2, n - 1), n); g != 1)
            return g;
    }
}
```

它同样在寻找因子，但做法是反复尝试计算 $n$ 与其随机余数的 [GCD](../gcd)，如果该余数与 $n$ 不互质，就能得到 $n$ 的一个有效因子。令人惊讶的是，这个算法并没有*那么*糟糕：最坏情况下它需要期望 $O(\sqrt n)$ 次迭代（再乘以 GCD 带来的 $\log n$），因为每次试验命中的可能不只是 $p$ 或 $q = \frac{n}{p}$，还有它们的 $\frac{n}{p} + \frac{n}{q} = O(\sqrt n)$ 个倍数。

就其本身而言，这个算法只是计算分解的一种另类方式，但可以变得有用。如果我们不采用随机数，而是把这个 $\gcd$ 技巧应用到某个特定的数列上，就得到 $O(n^\frac{1}{4})$ 的方法，即著名的 Pollard rho 算法。

除了这个技巧之外，Pollard rho 算法还依赖生日悖论的一个推论：我们需要向一个集合中加入 $O(\sqrt{n})$ 个从 $1$ 到 $n$ 的随机数，直到出现碰撞。

-->

Pollard rho 是一种随机化的 $O(\sqrt[4]{n})$ 整数分解算法，它利用了[生日悖论](https://en.wikipedia.org/wiki/Birthday_problem)：

> 只需要抽取 $d = \Theta(\sqrt{n})$ 个介于 $1$ 和 $n$ 之间的随机数，就能以高概率得到一个碰撞。

其背后的推理是：$d$ 个被加入的元素中，每个都有 $\frac{d}{n}$ 的概率与某个其他元素碰撞，这意味着碰撞的期望次数是 $\frac{d^2}{n}$。如果 $d$ 渐近小于 $\sqrt n$，那么当 $n \to \infty$ 时这个比值趋于零；反之则趋于无穷。

考虑某个函数 $f(x)$，它接收一个余数 $x \in [0, n)$，并以某种从数论角度看似随机的方式把它映射到 $n$ 的另一个余数。具体来说，我们将使用 $f(x) = x^2 + 1 \bmod n$，对我们的目的而言它足够随机。

现在考虑这样一张图：每个数字顶点 $x$ 都有一条指向 $f(x)$ 的边。这样的图称为*函数图*。在函数图中，任意元素的「轨迹」——即从该元素出发并不断沿边前进所走的路径——是一条最终绕成环的路径（因为顶点集合有限，到某个时刻我们必然走到一个已经访问过的顶点）。

![元素的轨迹形似希腊字母 ρ（rho），算法因此得名](../img/rho.jpg)

考虑某个特定元素 $x_0$ 的轨迹：

$$
x_0, \; f(x_0), \; f(f(x_0)), \; \ldots
$$

让我们把这个序列的每个元素对 $p$（$n$ 的最小质因子）取模，得到另一个序列。

**引理.** 约化序列在进入循环之前的期望长度是 $O(\sqrt[4]{n})$。

**证明:** 由于 $p$ 是最小因子，故 $p \leq \sqrt n$。每沿一条新边走，我们本质上就是在生成一个介于 $0$ 和 $p$ 之间的随机数（我们把 $f$ 视作一个「确定性的随机」函数）。生日悖论表明，我们只需要生成 $O(\sqrt p) = O(\sqrt[4]{n})$ 个数就能得到一个碰撞，从而进入循环。

因为我们不知道 $p$，这个模 $p$ 序列只是想象中的，但如果我们能在其中找到一个循环——即存在 $i$ 和 $j$ 使得

$$
f^i(x_0) \equiv f^j(x_0) \pmod p
$$

那么我们也能求出 $p$ 本身：

$$
p = \gcd(|f^i(x_0) - f^j(x_0)|, n)
$$

算法本身只是用这个 GCD 技巧和 Floyd 的「[龟兔赛跑](https://en.wikipedia.org/wiki/Cycle_detection#Floyd's_tortoise_and_hare)」算法来找到这个循环和 $p$：我们维护两个指针 $i$ 和 $j = 2i$，并检查

$$
\gcd(|f^i(x_0) - f^j(x_0)|, n) \neq 1
$$

这等价于比较 $f^i(x_0)$ 和 $f^j(x_0)$ 对 $p$ 的模。由于 $j$（兔子）以 $i$（乌龟）两倍的速度递增，它们的差每轮迭代增加 1，最终会等于（或成为倍数）循环长度，此时 $i$ 和 $j$ 指向相同的元素。而正如我们半页前证明的，进入循环只需 $O(\sqrt[4]{n})$ 次迭代：

```c++
u64 f(u64 x, u64 mod) {
    return ((u128) x * x + 1) % mod;
}

u64 diff(u64 a, u64 b) {
    // a and b are unsigned and so is their difference, so we can't just call abs(a - b)
    return a > b ? a - b : b - a;
}

const u64 SEED = 42;

u64 find_factor(u64 n) {
    u64 x = SEED, y = SEED, g = 1;
    while (g == 1) {
        x = f(f(x, n), n); // advance x twice
        y = f(y, n);       // advance y once
        g = gcd(diff(x, y));
    }
    return g;
}
```

虽然它每秒只能处理约 25k 个 30 位整数——比用快速除法技巧逐个检查质数慢近 15 倍——但在 60 位数上它远远胜过所有 $\tilde{O}(\sqrt n)$ 算法，每秒约能分解 90 个。

### Pollard–Brent 算法

Floyd 的找环算法有一个问题：它移动迭代器的次数超过了必要——慢的那个迭代器会额外访问至少一半的顶点。

一种解决办法是记住快迭代器访问过的值 $x_i$，每两次迭代用 $x_i$ 与 $x_{\lfloor i / 2 \rfloor}$ 之差计算一次 GCD。但也可以不借助额外内存，用另一种原理实现：乌龟不是每轮都移动，而是在迭代次数成为 2 的幂时被重置为快迭代器的值。这样我们既节省了额外的迭代，又仍能使用同样的 GCD 技巧，在每轮迭代比较 $x_i$ 与 $x_{2^{\lfloor \log_2 i \rfloor}}$：

```c++
u64 find_factor(u64 n) {
    u64 x = SEED;
    
    for (int l = 256; l < (1 << 20); l *= 2) {
        u64 y = x;
        for (int i = 0; i < l; i++) {
            x = f(x, n);
            if (u64 g = gcd(diff(x, y), n); g != 1)
                return g;
        }
    }

    return 1;
}
```

注意我们还设置了迭代次数的上限，这样算法能在合理时间内结束；若 $n$ 是质数则返回 `1`。

它实际上*没有*提升性能，反而使算法慢了约 1.5 倍，这可能与 $x$ 过于陈旧有关。它把大部分时间花在计算 GCD 而不是推进迭代器上——事实上，正因为如此，这个算法当前的时间需求是 $O(\sqrt[4]{n} \log n)$。

我们不去[优化 GCD 本身](../gcd)，而是优化它的调用次数。可以利用这样一个事实：如果 $a$、$b$ 中有一个含有因子 $p$，那么 $a \cdot b \bmod n$ 也会含有它，所以与其计算 $\gcd(a, n)$ 和 $\gcd(b, n)$，不如直接计算 $\gcd(a \cdot b \bmod n, n)$。这样，把 GCD 的计算分成每组 $M = O(\log n)$ 个，就能把 $\log n$ 从渐近式中去掉：

```c++
const int M = 1024;

u64 find_factor(u64 n) {
    u64 x = SEED;
    
    for (int l = M; l < (1 << 20); l *= 2) {
        u64 y = x, p = 1;
        for (int i = 0; i < l; i += M) {
            for (int j = 0; j < M; j++) {
                y = f(y, n);
                p = (u128) p * diff(x, y) % n;
            }
            if (u64 g = gcd(p, n); g != 1)
                return g;
        }
    }

    return 1;
}
```

现在它每秒完成 425 次分解，瓶颈是取模的速度。

### 优化取模

最后一步是应用 [Montgomery 乘法](/hpc/number-theory/montgomery/)。由于模数恒定，我们可以在 Montgomery 空间中完成所有计算——推进迭代器、乘法，甚至计算 GCD——在那里约减是廉价的：

```c++
struct Montgomery {
    u64 n, nr;
    
    Montgomery(u64 n) : n(n) {
        nr = 1;
        for (int i = 0; i < 6; i++)
            nr *= 2 - n * nr;
    }

    u64 reduce(u128 x) const {
        u64 q = u64(x) * nr;
        u64 m = ((u128) q * n) >> 64;
        return (x >> 64) + n - m;
    }

    u64 multiply(u64 x, u64 y) {
        return reduce((u128) x * y);
    }
};

u64 f(u64 x, u64 a, Montgomery m) {
    return m.multiply(x, x) + a;
}

const int M = 1024;

u64 find_factor(u64 n, u64 x0 = 2, u64 a = 1) {
    Montgomery m(n);
    u64 x = SEED;
    
    for (int l = M; l < (1 << 20); l *= 2) {
        u64 y = x, p = 1;
        for (int i = 0; i < l; i += M) {
            for (int j = 0; j < M; j++) {
                x = f(x, m);
                p = m.multiply(p, diff(x, y));
            }
            if (u64 g = gcd(p, n); g != 1)
                return g;
        }
    }

    return 1;
}
```

这个实现每秒能处理约 3k 个 60 位整数，比 [PARI](https://pari.math.u-bordeaux.fr/) / [SageMath 的 `factor`](https://doc.sagemath.org/html/en/reference/structure/sage/structure/factorization.html) / `cat semiprimes.txt | time factor` 快约 3 倍。

### 进一步的改进

**优化**。 我们的 Pollard 算法实现仍有很大的优化空间：

- 我们或许可以使用更好的找环算法，利用图是随机图这一事实。例如，前几次迭代就进入循环的可能性很小（环的长度和进入环之前走过的路径长度在期望上相等，因为在绕回来之前，我们走过的路径上的顶点是独立选取的），所以我们可以先把迭代器推进一段时间，再开始用 GCD 技巧做试验。
- 我们当前的方法受限于推进迭代器的速度（Montgomery 乘法的延迟远高于它的倒数吞吐量），而在等待它完成期间，我们可以利用之前的值执行不止一次试验。
- 如果我们并行运行 $p$ 个使用不同种子的独立算法实例，只要其中任何一个找到答案就停止，那么完成时间会快 $\sqrt p$ 倍（推理与生日悖论类似，试着自行证明）。我们不一定需要多个核：这里有大量未被利用的[指令级并行](/hpc/pipelining/)，所以我们可以在同一线程上并发运行两三个相同的操作，或者使用 [SIMD](/hpc/simd) 指令并行执行 4 或 8 次乘法。

如果再看到 3 倍的提升、吞吐量达到约每秒 1 万个，我也不会感到惊讶。如果你[实现了](https://github.com/sslotin/amh-code/tree/main/factor)其中的一些想法，请[告诉我](http://sereja.me/)。

<!-- 另一个观察：期望上「尾」和环的长度相等，因为当我们绕回来时，会独立地选择所走过路径上的任意一个顶点。如何针对*平均*情况优化尚不清楚。 -->

**错误**。 实际实现还需要处理的另一个方面是可能的错误。我们当前的实现对 60 位整数有 0.7% 的错误率，而且数值越小错误率越高。这些错误来自三个主要来源：

- 循环根本没有被找到（算法本质上是随机的，不保证一定能找到循环）。此时需要进行素性测试，并可选地重新开始。
- `p` 变量变成零（因为 $p$ 和 $q$ 都可能进入乘积）。输入规模越小或常数 `M` 越大，这种情况就越可能发生。此时我们需要要么重新启动整个过程，要么（更好的做法）回滚最后 $M$ 次迭代，逐一执行试验。
- Montgomery 乘法中的溢出。我们当前的实现对此相当宽松，如果 $n$ 很大，我们需要添加更多形如 `x > mod ? x - mod : x` 的语句来处理溢出。

**更大的数**。 如果我们先用之前实现的方法排除小数和带小质因子的数，这些问题就不那么重要了。一般来说，最优方法应当取决于数的规模：

- 小于 $2^{16}$：使用查找表；
- 小于 $2^{32}$：使用带快速整除检查的预计算质数表；
- 小于 $2^{64}$ 左右：使用带 Montgomery 乘法的 Pollard rho 算法；
- 小于 $10^{50}$：改用 [Lenstra 椭圆曲线分解法](https://en.wikipedia.org/wiki/Lenstra_elliptic-curve_factorization)；
- 小于 $10^{100}$：改用[二次筛法](https://en.wikipedia.org/wiki/Quadratic_sieve)；
- 大于 $10^{100}$：改用[普通数域筛法](https://en.wikipedia.org/wiki/General_number_field_sieve)。

<!-- 需要约 100KB 内存。6542 * 8 -->

最后三种方法与我们所做的工作非常不同，需要更深入的数论知识，它们值得单独用一篇文章（甚至一门完整的大学课程）来讲述。
