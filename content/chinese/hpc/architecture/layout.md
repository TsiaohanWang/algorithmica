---
title: 机器码布局
weight: 10
published: true
---

计算机工程师喜欢把 [CPU 的流水线](/hpc/pipelining)在思想上分成两部分：*前端*（front-end），负责从内存取指并译码*；后端*（back-end），负责调度指令并最终执行。通常性能瓶颈在执行阶段，因此本书中的大部分精力都会花在围绕后端进行优化上。

但有时情况会反过来：前端来不及向后端输送指令，无法使其饱和。这可能有多种原因，归根结底都与机器码在内存中的布局方式有关，并且会以匪夷所思的方式影响性能，比如删除未使用的代码、交换 `if` 分支，甚至改变函数声明的顺序，都可能导致性能提升或恶化。

### CPU 前端

机器码在被转换成指令、CPU 理解程序员意图之前，首先要经过我们关心的两个重要阶段：*取指*（fetch）和*译码*（decode）。

在**取指**阶段，CPU 只是从主内存加载一块固定大小的字节，其中包含若干条指令的二进制编码。在 x86 上这个块的大小通常是 32 字节，不过不同机器上可能有所不同。一个重要的细节是，这个块必须是[对齐](/hpc/cpu-cache/cache-lines)的：块的地址必须是其大小（本例中为 32B）的倍数。

<!-- todo：指令跨越块边界时会发生什么？ -->

接下来是**译码**阶段：CPU 查看这一块字节，丢弃指令指针之前的所有内容，把剩下的部分拆分成指令。机器指令用可变数量的字节编码：像 `inc rax` 这样简单又常见的指令只占一个字节，而某些带有编码常量和改变行为的前缀的冷僻指令可能长达 15 个字节。因此，从一个 32 字节的块中，可以译码出数量不定的指令，但不会超过某个取决于机器的上限，称为*译码宽度*（decode width）。在我的 CPU（[Zen 2](https://en.wikichip.org/wiki/amd/microarchitectures/zen_2)）上，译码宽度是 4，这意味着每个周期最多能译码 4 条指令并传递给下一阶段。

这些阶段以流水线方式工作：如果 CPU 能判断出（或[预测](/hpc/pipelining/branching/)出）下一步需要哪个指令块，那么取指阶段就不必等待当前块的最后一条指令译码完，而是立即加载下一个块。

<!--

译码流缓冲（Decoded Stream Buffer，DSB）

循环流检测器（Loop Stream Detector，LSD）

-->

### 代码对齐

在其他条件相同的情况下，编译器通常偏好机器码更短的指令，因为这样单个 32B 取指块里能塞进更多指令，也能减小二进制文件的体积。但有时反过来更可取，原因在于取回的指令块必须对齐。

想象你需要执行一段从某个 32B 对齐块的最后一个字节开始的指令序列。第一条指令也许无需额外延迟就能执行，但后续指令就得再等一个周期来做一次额外的取指。如果代码块对齐在 32B 边界上，那么最多可以同时译码并执行 4 条指令（除非它们特别长或相互依赖）。

考虑到这一点，编译器经常做一种看似有害的优化：它们有时偏好机器码更长的指令，甚至插入什么都不做的空指令[^nop]，以便让关键的跳转位置对齐到合适的 2 的幂边界上。

[^nop]: 这类指令被称为空操作（no-op，NOP）指令。在 x86 上，「官方」的什么都不做的方式是 `xchg rax, rax`（把寄存器与自身交换）：CPU 能识别它，除了译码阶段外不会花额外周期去执行。`nop` 简写会映射到相同的机器码。

在 GCC 中，你可以用 `-falign-labels=n` 标志指定特定的对齐策略，如果想更有选择性，可以[把](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html) `-labels` 替换成 `-function`、`-loops` 或 `-jumps`。在 `-O2` 和 `-O3` 优化级别下，它默认开启——不指定特定对齐时，会使用（通常合理的）取决于机器的默认值。

<!-- 被迫译码一堆多余的 NOP 通常不是问题。 -->

### 指令缓存

指令的存储和取回与数据一样，很大程度上使用同一套[内存系统](/hpc/cpu-cache)，只不过较低层的缓存被替换成了独立的*指令缓存*（因为你不会希望一次随机的数据读取把处理它的代码给挤出去）。

指令缓存在以下两种情况下至关重要：

- 你不知道接下来要执行什么指令，需要用[低延迟](/hpc/cpu-cache/latency)取回下一个块，
- 或者正在执行一长串冗长但处理快速的指令，需要[高带宽](/hpc/cpu-cache/bandwidth)。

因此，对于机器码很大的程序，内存系统可能成为瓶颈。这一考虑限制了前面讨论过的优化技术的适用范围：

- [内联函数](../functions)并非总是最优，因为它减少了代码共享、增大了二进制体积，需要更多指令缓存。
- [循环展开](../loops)即使编译期已知迭代次数，也只在某种程度上有利：到了一定程度，CPU 就不得不同时从主内存取指令和数据，这时它很可能会被内存带宽卡住。
- 过度的[代码对齐](#code-alignment)会增大二进制体积，同样需要更多指令缓存。多花一个周期取指，比起缓存未命中、等待从主内存取回指令来说，只是个小代价。

另一个方面是，把频繁使用的指令序列放在相同的[缓存行](/hpc/cpu-cache/cache-lines)和[内存页](/hpc/cpu-cache/paging)上可以改善[缓存局部性](/hpc/external-memory/locality)。为了提升指令缓存的利用率，你应该让热代码与热代码聚在一起、冷代码与冷代码聚在一起，并尽可能删除死（未使用）代码。如果你想进一步探索这个想法，可以看看 Facebook 的 [Binary Optimization and Layout Tool（BOLT）](https://engineering.fb.com/2018/06/19/data-infrastructure/accelerate-large-scale-applications-with-bolt/)，它最近已被[合并](https://github.com/llvm/llvm-project/commit/4c106cfdf7cf7eec861ad3983a3dd9a9e8f3a8ae)进 LLVM。

### 不对称分支

假设出于某种原因，你需要一个计算整数区间长度的辅助函数。它接受两个参数 $x$ 和 $y$，但为了方便，它既可以对应 $[x, y]$ 也可以对应 $[y, x]$，取决于哪一个非空。用普通 C 语言，你大概会写成这样：

```c++
int length(int x, int y) {
    if (x > y)
        return x - y;
    else
        return y - x;
}
```

在 x86 汇编中，实现它的方式就多样得多了，并会对性能产生明显影响。我们先试着把这段代码直接映射成汇编：

```nasm
length:
    cmp  edi, esi
    jle  less
    ; x > y
    sub  edi, esi
    mov  eax, edi
done:
    ret
less:
    ; x <= y
    sub  esi, edi
    mov  eax, esi
    jmp  done
```

虽然最初的 C 代码看起来非常对称，但汇编版本就不对称了。这导致一个有趣的怪现象：其中一个分支可以比另一个分支执行得稍快一些：如果 `x > y`，CPU 只需顺序执行 `cmp` 到 `ret` 之间的 5 条指令；如果函数是对齐的，它们会一次性全部被取回；而在 `x <= y` 的情况下，还需要多两次跳转。

可以合理地假设 `x > y` 的情况是*不太可能*的（谁会去计算一个反着的区间的长度呢？），更像是一种几乎从不发生的异常。我们可以检测这种情况，简单地交换 `x` 和 `y`：

```c++
int length(int x, int y) {
    if (x > y)
        swap(x, y);
    return y - x;
}
```

汇编大致会是这样，和 if-without-else 模式的通常写法一样：

```nasm
length:
    cmp  edi, esi
    jle  normal     ; if x <= y, no swap is needed, and we can skip the xchg
    xchg edi, esi
normal:
    sub  esi, edi
    mov  eax, esi
    ret
```

指令总数现在是 6，从 8 降下来了。但对我们假设的情况来说，它还是没有优化到位：如果我们认为 `x > y` 永远不会发生，那么加载永远不会执行的 `xchg edi, esi` 指令就是一种浪费。我们可以把它移出正常执行路径来解决：

```nasm
length:
    cmp  edi, esi
    jg   swap
normal:
    sub  esi, edi
    mov  eax, esi
    ret
swap:
    xchg edi, esi
    jmp normal
```

这个技巧在处理异常情况时相当好用；在高级语言中，你可以给编译器一个[提示](/hpc/compilation/situational)，说明某个分支比另一个分支更可能发生：

```c++
int length(int x, int y) {
    if (x > y) [[unlikely]]
        swap(x, y);
    return y - x;
}
```

这种优化只在你知道某个分支极少被走到时才有利。如果不是这种情况，还有比代码布局更重要的[其他方面](/hpc/pipelining/hazards)，会促使编译器完全避免分支——在这种情况下，用一条特殊的「条件传送」指令来代替，它大致对应三元表达式 `(x > y ? y - x : x - y)` 或调用 `abs(x - y)`：

```nasm
length:
    mov   edx, edi
    mov   eax, esi
    sub   edx, esi
    sub   eax, edi
    cmp   edi, esi
    cmovg eax, edx  ; "mov if edi > esi"
    ret
```

消除分支是一个重要的话题，我们将在[下一章的很大篇幅](/hpc/pipelining/branching)里更详细地讨论它。

<!--

这一体系结构的特性

当你的代码中有分支时，如何把它们对应的指令序列放在内存中就有多种选择——而令人惊讶的是，。

```nasm
length:
    mov   edx, edi
    mov   eax, esi
    sub   edx, esi
    sub   eax, edi
    cmp   edi, esi
    cmovg eax, edx  ; "mov if edi > esi"
    ret
```

假设 `x > y` 从不或几乎从不发生，那么带分支的版本会短 2 条指令。

https://godbolt.org/z/bb3a3ahdE

（编译器无法优化它，因为从技术上讲它[不被允许](/hpc/compilation/contracts)：尽管 `y - x` 是合法的，但 `x - y` 可能上溢/下溢，导致未定义行为。虽然完全正确，但我猜编译器就是不敢执行它。）

我们将用[下一章的很大篇幅](/hpc/pipelining/branching)更详细地讨论它。

反正你不会去执行的东西，就没必要译码它。

一般来说，你应该把很少执行的代码挪到一边——即使在 if-without-else 模式的情况下也是如此。

-->