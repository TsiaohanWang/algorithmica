---
title: 整数除法
weight: 6
---

与其他算术运算相比，除法在 x86 乃至所有计算机上的表现都很糟糕。浮点除法与整数除法都素以难以在硬件中实现而著称：电路在 ALU 中占用大量空间，计算过程要经过很多级流水，结果 `div` 及其同族的指令通常需要 10–20 个周期才能完成，数据类型越小时延会略短一些。

### x86 中的除法与取模

由于没人愿意为了单独的取模操作把这套复杂的电路再复制一份，`div` 指令同时承担了这两种功能。要执行 32 位整数除法，你需要把被除数*专门*放到 `eax` 寄存器中，然后以除数作为唯一操作数调用 `div`。此后，商将存放在 `eax` 中，余数存放在 `edx` 中。

唯一的注意事项是，被除数实际上需要存放在*两个*寄存器 `eax` 和 `edx` 中：这一机制支持 64 位除以 32 位、甚至 128 位除以 64 位的除法，与[128 位乘法](../integer)的工作原理类似。执行常规的 32 位除以 32 位有符号除法时，我们需要把 `eax` 符号扩展为 64 位，并将其高位部分存入 `edx`：

```nasm
div(int, int):
    mov  eax, edi
    cdq
    idiv esi
    ret
```

对于无符号除法，只需把 `edx` 置零，以免它干扰结果：

```nasm
div(unsigned, unsigned):
    mov  eax, edi
    xor  edx, edx
    div  esi
    ret
```

而在这两种情况下，除了 `eax` 中的商之外，你还可以在 `edx` 中取到余数：

```nasm
mod(unsigned, unsigned):
    mov  eax, edi
    xor  edx, edx 
    div  esi
    mov  eax, edx
    ret
```

你还可以让 128 位整数（存放在 `rdx:rax` 中）除以一个 64 位整数：

```nasm
div(u128, u64):
    ; a = rdi + rsi, b = rdx
    mov  rcx, rdx
    mov  rax, rdi
    mov  rdx, rsi
    div  edx 
    ret
```

被除数的高位部分必须小于除数，否则会发生溢出。正是由于这一约束，很难让编译器自己生成这样的代码：如果用[128 位整数类型](../integer)除以一个 64 位整数，编译器会为它包上一层额外的检查，而这些检查实际上可能是多余的。

### 除以常数

即使完全用硬件实现，整数除法也慢得令人痛苦，但在某些情况下，如果除数是常数，就可以避开除法。一个众所周知的例子是除以 2 的幂，可以用单周期的二进制移位代替：[二进制 GCD 算法](/hpc/algorithms/gcd)就是这一技巧的绝佳展示。

一般情况下，有几种巧妙的技巧可以用乘法代替除法，代价是少量预计算。所有这些技巧都基于以下想法：考虑一个浮点数 $x$ 除以另一个浮点数 $y$ 的任务，其中 $y$ 事先已知。我们可以计算一个常数

$$
d \approx y^{-1}
$$

然后在运行时计算

$$
x / y = x \cdot y^{-1} \approx x \cdot d
$$

$\frac{1}{y}$ 的结果最多偏差 $\epsilon$，而乘法 $x \cdot d$ 只会再引入一个 $\epsilon$ 的误差，因此总误差最多为 $2 \epsilon + \epsilon^2 = O(\epsilon)$，这在浮点场景下是可以接受的。

<!--
例如，`double` 有 53 个尾数位，因此机器精度为 $\frac{1}{53}$，如果我们还确保它以正确的方式舍入。
-->

### Barrett 约减

如何把这一技巧推广到整数？计算 `int d = 1 / y` 似乎行不通，因为结果只会是 0。我们能做到的最好办法，是把它表示成

$$
d = \frac{m}{2^s}
$$

然后找到一个“魔法”数 $m$ 和一个二进制移位量 $s$，使得对范围内所有 `x` 都有 `x / y == (x * m) >> s`。

$$
  \lfloor x / y \rfloor
= \lfloor x \cdot y^{-1} \rfloor
= \lfloor x \cdot d \rfloor
= \lfloor x \cdot \frac{m}{2^s} \rfloor
$$

可以证明这样的数对总是存在的，而且编译器实际上会自行执行这种优化。每当遇到除以常数时，它都会用一次乘法和一次二进制移位来替代。以下是 `unsigned long long` 除以 $(10^9 + 7)$ 时生成的汇编代码：

```nasm
;  input (rdi): x
; output (rax): x mod (m=1e9+7)
mov    rax, rdi
movabs rdx, -8543223828751151131  ; load magic constant into a register
mul    rdx                        ; perform multiplication
mov    rax, rdx
shr    rax, 29                    ; binary shift of the result
```

这种技术被称为 *Barrett 约减*，它之所以叫“约减”，是因为它主要用于取模运算，而取模可以借助下面的公式用一次除法、一次乘法与一次减法来代替：

$$
r = x - \lfloor x / y \rfloor \cdot y
$$

这种方法需要一些预计算，包括执行一次真正的除法。因此，只有当你要执行不止一次、而是多次除以同一个常数除数的除法时，它才划算。

### 为什么有效

为什么这样的 $m$ 和 $s$ 总是存在并不十分清楚，更不用说如何找到它们了。但给定固定的 $s$，直觉告诉我们，$m$ 应尽可能接近 $2^s/y$，以便让 $2^s$ 相互抵消。于是有两个自然的选择：$\lfloor 2^s/y \rfloor$ 和 $\lceil 2^s/y \rceil$。第一个不成立，因为如果你代入

$$
\Bigl \lfloor \frac{x \cdot \lfloor 2^s/y \rfloor}{2^s} \Bigr \rfloor
$$

那么对于任意整数 $\frac{x}{y}$（其中 $y$ 不是偶数），结果都会严格小于真实值。这就只剩下另一种情况 $m = \lceil 2^s/y \rceil$。现在，让我们尝试推导计算结果的上下界：

$$
  \lfloor x / y \rfloor
= \Bigl \lfloor \frac{x \cdot m}{2^s} \Bigr \rfloor
= \Bigl \lfloor \frac{x \cdot \lceil  2^s /y \rceil}{2^s} \Bigr \rfloor
$$

先从 $m$ 的界开始：

$$
2^s / y
\le
\lceil 2^s / y \rceil
<
2^s / y + 1
$$

现在来看整个表达式：

$$
x / y - 1
<
\Bigl \lfloor \frac{x \cdot \lceil  2^s /y \rceil}{2^s} \Bigr \rfloor
<
x / y + x / 2^s
$$

可以看到，结果落在大小为 $(1 + \frac{x}{2^s})$ 的区间内某处；如果对所有可能的 $x / y$，这个区间内总是恰好包含一个整数，那么算法就保证能给出正确答案。事实证明，我们总可以把 $s$ 设得足够大来实现这一点。

这里的最坏情况是什么？如何选取 $x$ 和 $y$，使得 $(x/y - 1, x/y + x / 2^s)$ 区间内包含两个整数？可以看到，整数比值不行，因为左边界不包含在内，而且假设 $x/2^s < 1$，区间内只会包含 $x/y$ 本身。最坏的情况其实是 $x/y$ 尽可能接近 $1$ 但不超过 $1$。对于 $n$ 位整数，这就是第二大的整数除以最大的整数：

$$
\begin{aligned}
    x = 2^n - 2
\\  y = 2^n - 1
\end{aligned}
$$

在这种情况下，下界为 $(\frac{2^n-2}{2^n-1} - 1)$，上界为 $(\frac{2^n-2}{2^n-1} + \frac{2^n-2}{2^s})$。左边界尽可能地接近整数，而整个区间的大小也是第二大的可能值。关键结论来了：如果 $s \ge n$，那么这个区间内唯一包含的整数就是 $1$，因此算法总会返回它。

### Lemire 约减

Barrett 约减有点复杂，而且由于取模是间接计算的，它生成的指令序列也比较长。有一种新的（[2019 年](https://arxiv.org/pdf/1902.01961.pdf)）方法更简单，在某些情况下取模甚至更快。它还没有一个公认的名字，我打算称之为 [Lemire](https://lemire.me/blog/) 约减。

主要思想如下。考虑某个整数分数的浮点表示：

$$
\frac{179}{6} = 11101.1101010101\ldots = 29\tfrac{5}{6} \approx 29.83
$$

我们如何“解剖”它来得到需要的各个部分呢？

- 要得到整数部分（29），只需在小数点之前向下取整或截断。
- 要得到小数部分（⅚），只需取小数点后面的部分。
- 要得到余数（5），把小数部分乘以除数即可。

现在，对于 32 位整数，我们可以令 $s = 64$，并考察在“乘后移位”方案中做的计算：

$$
  \lfloor x / y \rfloor
= \Bigl \lfloor \frac{x \cdot m}{2^s} \Bigr \rfloor
= \Bigl \lfloor \frac{x \cdot \lceil  2^s /y \rceil}{2^s} \Bigr \rfloor
$$

这里我们真正做的是把 $x$ 乘以一个浮点常数（$x \cdot m$），然后截断结果 $(\lfloor \frac{\cdot}{2^s} \rfloor)$。

如果我们不取最高位而取最低位会怎样？这对应的正是小数部分——如果我们再把它乘以 $y$ 并截断结果，得到的恰好就是余数：

$$
r = \Bigl \lfloor \frac{ (x \cdot \lceil  2^s /y \rceil \bmod 2^s) \cdot y }{2^s} \Bigr \rfloor
$$

这之所以完美可行，是因为我们在这里做的事情可以解释为三次串联的浮点乘法，总相对误差为 $O(\epsilon)$。由于 $\epsilon = O(\frac{1}{2^s})$ 且 $s = 2n$，误差总小于 1，因此结果是精确的。

```c++
uint32_t y;

uint64_t m = uint64_t(-1) / y + 1; // ceil(2^64 / y)

uint32_t mod(uint32_t x) {
    uint64_t lowbits = m * x;
    return ((__uint128_t) lowbits * y) >> 64; 
}

uint32_t div(uint32_t x) {
    return ((__uint128_t) m * x) >> 64;
}
```

我们还可以只用一次乘法判断 $x$ 能否被 $y$ 整除，依据是：除法的余数为零，当且仅当小数部分（$m \cdot x$ 的低 64 位）不超过 $m$（否则，它乘以 $y$ 再右移 64 位后会变成一个非零数）。

```c++
bool is_divisible(uint32_t x) {
    return m * x < m;
}
```

这种方法的唯一缺点是需要原始大小四倍的整数类型来执行乘法，而其他约减方法用 double 就够了。

还有一种方法可以通过仔细处理中间结果的两半来计算 64×64 的取模；具体实现留给读者作为练习。

### 延伸阅读

关于优化整数除法的更通用实现，可以看看 [libdivide](https://github.com/ridiculousfish/libdivide) 和 [GMP](https://gmplib.org/)。

《[Hacker's Delight](https://www.amazon.com/Hackers-Delight-2nd-Henry-Warren/dp/0321842685)》也值得一读，其中有一整章专门讲述整数除法。