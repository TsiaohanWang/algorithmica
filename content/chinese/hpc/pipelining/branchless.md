---
title: 无分支编程
weight: 3
published: true
---

正如我们在[上一节](../branching)中确认的那样，CPU 无法有效预测的分支代价高昂：分支预测失败后，可能需要停顿很长的流水线来重新取指。本节我们讨论从一开始就消除分支的手段。

### 谓词化

我们继续之前的同一个案例研究——创建一个随机数数组，把所有小于 50 的元素累加起来：

```c++
for (int i = 0; i < N; i++)
    a[i] = rand() % 100;

volatile int s;

for (int i = 0; i < N; i++)
    if (a[i] < 50)
        s += a[i];
```

我们的目标是消除由 `if` 语句引起的分支。我们可以这样尝试去除它：

```c++
for (int i = 0; i < N; i++)
    s += (a[i] < 50) * a[i];
```

现在这个循环每元素约花费 7 个周期，而原来是约 14 个周期。而且，如果把 `50` 改成其他阈值，性能保持不变，因此它不再依赖于分支概率。

但等等……难道不应该还有一个分支吗？`(a[i] < 50)` 是如何映射到汇编的？

汇编中没有布尔类型，也没有任何能根据比较结果产生 1 或 0 的指令，但我们可以这样间接计算它：`(a[i] - 50) >> 31`。这个技巧依赖于[整数的二进制表示](/hpc/arithmetic/integer)，具体来说，如果表达式 `a[i] - 50` 是负数（意味着 `a[i] < 50`），那么结果的最高位会被置为 1，我们可以用右移把它提取出来。

```nasm
mov  ebx, eax   ; t = x
sub  ebx, 50    ; t -= 50
sar  ebx, 31    ; t >>= 31
imul  eax, ebx   ; x *= t
```

实现这整个序列的另一种更复杂的方式，是把符号位转换为掩码，然后用按位 `and` 代替乘法：`((a[i] - 50) >> 31 - 1) & a[i]`。由于 `imul` 与其他指令不同，需要 3 个周期，这会让整个序列快 1 个周期：

```nasm
mov  ebx, eax   ; t = x
sub  ebx, 50    ; t -= 50
sar  ebx, 31    ; t >>= 31
; imul  eax, ebx ; x *= t
sub  ebx, 1     ; t -= 1 (causing underflow if t = 0)
and  eax, ebx   ; x &= t
```

注意，从编译器的视角看，这个优化在技术上并不正确：对于最小的 50 个可表示整数——即 $[-2^{31}, - 2^{31} + 49]$ 范围内的数——结果会因下溢而出错。我们知道所有数都在 0 到 100 之间，不会发生这种情况，但编译器并不知道。

但编译器实际上选择了不同的做法。它没有采用这个算术技巧，而是使用了一条特殊的 `cmov`（“条件移动（conditional move）”）指令，根据条件来赋值（条件的计算和检查与跳转一样，借助标志寄存器完成）：

```nasm
mov     ebx, 0      ; cmov doesn't support immediate values, so we need a zero register
cmp     eax, 50
cmovge  eax, ebx    ; eax = (eax >= 50 ? eax : ebx=0)
```

所以上面的代码实际上更接近这样的三元运算符写法：

```c++
for (int i = 0; i < N; i++)
    s += (a[i] < 50 ? a[i] : 0);
```

两种写法都会被编译器优化成下面的汇编：

```nasm
    mov     eax, 0
    mov     ecx, -4000000
loop:
    mov     esi, dword ptr [rdx + a + 4000000]  ; load a[i]
    cmp     esi, 50
    cmovge  esi, eax                            ; esi = (esi >= 50 ? esi : eax=0)
    add     dword ptr [rsp + 12], esi           ; s += esi
    add     rdx, 4
    jnz     loop                                ; "iterate while rdx is not zero"
```

这一通用技术称为*谓词化（predication*），它大致等价于下面这个代数技巧：

$$
x = c \cdot a + (1 - c) \cdot b
$$

这样你就可以消除分支，但代价是必须*同时*求值两个分支以及 `cmov` 本身。由于求值“>=”分支不需要任何成本，其性能恰好等同于带分支版本中[“总是是”的情况](../branching/#branch-prediction)。

### 谓词化什么时候有益

使用谓词化消除了[控制冒险](../hazards)，但引入了数据冒险。流水线仍然会停顿，不过代价更低：你只需要等待 `cmov` 得出结果，而无需在预测失败时冲刷整条流水线。

然而，在很多情况下，保留带分支的代码反而更高效。当计算*两个*分支（而不是只算*一个*）的成本超过了潜在分支预测失败的惩罚时，就是这种情况。

在我们的例子中，当分支能以超过约 75% 的概率被预测时，带分支的代码胜出。

![](../img/branchy-vs-branchless.svg)

编译器通常以这 75% 的阈值作为启发式依据，来决定是否使用 `cmov`。遗憾的是，这个概率在编译时通常是未知的，所以需要通过以下几种方式之一来提供：

- 我们可以使用[基于轮廓的优化（profile-guided optimization）](/hpc/compilation/situational/#profile-guided-optimization)，让它自行决定是否使用谓词化。
- 我们可以使用[可能性属性](../branching#hinting-likeliness-of-branches)和[编译器特有的内建函数](/hpc/compilation/situational)来提示分支的可能性：GCC 中的 `__builtin_expect_with_probability` 和 Clang 中的 `__builtin_unpredictable`。
- 我们可以用三元运算符或各种算术技巧重写带分支的代码，这相当于程序员与编译器之间的一种隐性约定：如果程序员这样写代码，那大概就是希望它成为无分支的。

“正确的做法”是使用分支提示，但遗憾的是，对它们的支持还很欠缺。目前，等编译器后端在决定 `cmov` 是否更有利时，[这些提示似乎已经丢失](https://bugs.llvm.org/show_bug.cgi?id=40027)。目前已有[一些进展](https://discourse.llvm.org/t/rfc-cmov-vs-branch-optimization/6040)朝这个方向努力，但眼下还没有什么好办法能强制编译器生成无分支代码，所以有时候最好的指望就是在汇编里写一小段代码。

<!--

因为这是非常依赖具体架构的。

在没有分支可能性提示的情况下

尽管任何使用三元运算符的程序都与使用 `if` 语句的程序等价

这两段代码看起来等价。我猜测编译器并不知道 `s + a[i]` 不会导致整数溢出。

（编译器无法优化它，因为技术上[不允许](/hpc/compilation/contracts)这样做：尽管 `y - x` 是合法的，`x - y` 却可能上溢或下溢，从而引发未定义行为。虽然这完全正确，但我想编译器就是不敢执行它。）

这类无分支计算技巧在各种并行算法中尤其重要。

`cmov` 版本并不在乎分支的概率。它只在分支概率低于 75% 时胜出，而这通常就是编译器设定的启发式阈值。

这是一项合法的优化，但我猜在应用程序员与编译器工程师之间已经形成了一种隐性约定：如果你写了三元运算符，那大概就是在暗示这个分支很可能难以预测。

这种通用技术称为*无分支（branchless / branch-free*）编程。谓词化是它的主要工具，但还有更复杂的方式。

-->

<!--

我们再举几个例子作为练习。

```c++
int max(int a, int b) {
    return (a > b) * a + (a <= b) * b;
}
```

```c++
int max(int a, int b) {
    return (a > b ? a : b);
}
```


```c++
int abs(int a, int b) {
    return max(diff, -diff);
}
```

```c++
int abs(int a, int b) {
    int diff = a - b;
    return (diff < 0 ? -diff : diff);
}
```

```c++
int abs(int a) {
    return (a > 0 ? a : -a);
}
```

```c++
int abs(int a) {
    int mask = a >> 31;
    a ^= mask;
    a -= mask;
    return a;
}
```

-->

### 更大的例子

**字符串**。 简单来说，一个 `std::string` 由一个指向堆上某处分配的空终止 `char` 数组（也称为“C 字符串”）的指针和一个存放字符串长度的整数组成。

字符串的一个常见取值是空字符串——这也是它的默认值。你总得设法处理它，惯用的做法是把指针设为 `nullptr`、长度设为 `0`，然后在每个涉及字符串的过程开头检查指针是否为空或长度是否为零。

然而，这需要一个独立的分支，代价不菲（除非大多数字符串要么全为空、要么全非空）。为了去掉这个检查、从而也去掉分支，我们可以分配一个“零 C 字符串”，也就是在某个地方分配一个零字节，然后把所有空字符串都指向那里。现在所有针对空字符串的操作都得读取这个无用的零字节，但这仍然比一次分支预测失败便宜得多。

**二分查找**。 标准的二分查找[可以无分支地实现](/hpc/data-structures/binary-search)，在小数组（能装进缓存的那种）上，它比带分支的 `std::lower_bound` 快约 4 倍：

```c++
int lower_bound(int x) {
    int *base = t, len = n;
    while (len > 1) {
        int half = len / 2;
        base += (base[half - 1] < x) * half; // will be replaced with a "cmov"
        len -= half;
    }
    return *base;
}
```

除了更复杂之外，它还有一个轻微的缺点：它可能做更多的比较（恒为 $\lceil \log_2 n \rceil$ 次，而不是 $\lfloor \log_2 n \rfloor$ 或 $\lceil \log_2 n \rceil$ 次），并且无法对未来的内存读取进行推测（这相当于预取，所以在非常大的数组上不占优势）。

一般来说，数据结构是通过隐式或显式地*填充*它们、使操作只需恒定次数的迭代来实现无分支的。更复杂的例子请参阅[这篇文章](/hpc/data-structures/binary-search)。

<!--

无分支实现唯一的缺点是它可能做更多的内存读取：

通常有两种方式可以实现这一点：

而且一般来说，数据结构可以“填充（padding）”成固定大小或固定高度。

编译器没有充分的理由不能自行做到这一点，但遗憾的是，现状就是如此。

-->

**数据并行编程**。 无分支编程对 [SIMD](/hpc/simd) 应用非常重要，因为它们从根上就没有分支。

在我们数组求和的例子中，去掉累加器上的 `volatile` 类型限定符，编译器就能[向量化](/hpc/simd/auto-vectorization)这个循环：

```c++
/* volatile */ int s = 0;

for (int i = 0; i < N; i++)
    if (a[i] < 50)
        s += a[i];
```

现在它每元素只需约 0.3 个周期，主要[受限于内存](/hpc/cpu-cache/bandwidth)带宽。

编译器通常能向量化任何没有分支或迭代间依赖的循环——以及一些偏离这个条件的特定小场景，比如[归约（reduction）](/hpc/simd/reduction)或只含单个 if-无-else 的简单循环。对更复杂代码的向量化是一个非常不平凡的问题，可能涉及[掩码（masking）](/hpc/simd/masking)、[寄存器内置换（in-register permutations）](/hpc/simd/shuffling)等各种技术。

<!--

**快速幂**。 然而，当它是常数时

当我们能以小批量迭代时，[自动向量化](/hpc/simd/autovectorization)能把它加速 13 倍。

-->