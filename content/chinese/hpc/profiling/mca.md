---
title: 机器码分析器
weight: 4
---

*机器码分析器（machine code analyzer*）是一种程序：它接收一小段汇编代码，利用编译器可获得的信息[模拟](../simulation)其在特定微架构上的执行，并输出整个代码块的延迟、吞吐量，以及 CPU 内各种资源的周期级利用率。

### 使用 `llvm-mca`

机器码分析器有很多种，但我个人偏爱 `llvm-mca`，你大概可以通过包管理器把它和 `clang` 一起装上。你也可以通过一个名为 [UICA](https://uica.uops.info) 的网页工具使用它，或者在 [Compiler Explorer](https://godbolt.org/) 中把语言选成“Analysis”来调用它。

`llvm-mca` 所做的是：把给定的汇编片段运行一定数量的迭代，并计算每条指令资源使用的统计信息，这对定位瓶颈很有用。

我们以数组求和作为简单例子：

```asm
loop:
    addl (%rax), %edx
    addq $4, %rax
    cmpq %rcx, %rax
    jne	 loop
````

下面是用 `llvm-mca` 对 Skylake 微架构的分析结果：

```yaml
Iterations:        100
Instructions:      400
Total Cycles:      108
Total uOps:        500

Dispatch Width:    6
uOps Per Cycle:    4.63
IPC:               3.70
Block RThroughput: 0.8
```

首先，它输出关于该循环和硬件的一般信息：

- 它“运行”了该循环 100 次，在 108 个周期内总共执行了 400 条指令，相当于平均每周期执行 $\frac{400}{108} \approx 3.7$ 条[指令（IPC）](/hpc/complexity/hardware)。
- CPU 理论上每周期最多能执行 6 条指令（[分派宽度（dispatch width）](/hpc/architecture/layout)）。
- 理论上每轮循环平均可以在 0.8 个周期内执行完（[代码块反向吞吐量（block reciprocal throughput）](/hpc/pipelining/tables)）。
- 这里的“uOps”是 CPU 把每条指令拆分成的微操作（例如，融合加载-加法由两个 uOps 组成）。

接着它会给出关于每条指令的信息：

```yaml
Instruction Info:
[1]: uOps
[2]: Latency
[3]: RThroughput
[4]: MayLoad
[5]: MayStore
[6]: HasSideEffects (U)

[1]    [2]    [3]    [4]    [5]    [6]    Instructions:
 2      6     0.50    *                   addl	(%rax), %edx
 1      1     0.25                        addq	$4, %rax
 1      1     0.25                        cmpq	%rcx, %rax
 1      1     0.50                        jne	-11
```

其中没有任何[指令表](/hpc/pipelining/tables)中没有的信息：

- 每条指令被拆分成多少个 uOps；
- 每条指令需要多少个周期完成（延迟）；
- 考虑到同一指令的多个副本可以同时执行，每条指令在均摊意义下需要多少个周期完成（反向吞吐量）。

然后它输出可能是最重要的部分——哪些指令在什么时间、什么位置执行：

```yaml
Resource pressure by instruction:
[0]    [1]    [2]    [3]    [4]    [5]    [6]    [7]    [8]    [9]    Instructions:
 -      -     0.01   0.98   0.50   0.50    -      -     0.01    -     addl (%rax), %edx
 -      -      -      -      -      -      -     0.01   0.99    -     addq $4, %rax
 -      -      -     0.01    -      -      -     0.99    -      -     cmpq %rcx, %rax
 -      -     0.99    -      -      -      -      -     0.01    -     jne  -11
```

由于执行端口上的争用会引发[结构冒险](/hpc/pipelining/hazards)，端口常常成为吞吐量导向循环的瓶颈，而这张图有助于诊断其原因。它不会给你一张周期级精确的甘特图之类的东西，但会给出每条指令所用执行端口的聚合统计，让你找出哪个端口过载了。

<!--

CPU 是非常复杂的东西，但本质上，有若干个专门处理特定类型指令的“端口”。这些端口常常成为瓶颈，上面的图有助于诊断原因。

我们还没有准备好讨论其工作原理，但会在最后一章详细讲述。

-->