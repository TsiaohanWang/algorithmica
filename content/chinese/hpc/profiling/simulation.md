---
title: 程序模拟
weight: 3
---

最后一类性能剖析方法（准确地说是一组方法）不是通过真正运行程序来收集数据，而是用专门的工具*模拟*程序，分析「应该」发生什么。

<!--

这类剖析器有很多子类，区别在于它们模拟计算的哪个方面，但本节我们要重点讨论的是*机器码分析器*。

最后一类方法（准确地说是一组方法）不是通过真正运行程序来收集数据，而是用专门的工具*模拟*它来分析「应该」发生什么，这些工具大致分为两类。

-->

这类剖析器有很多子类，区别在于它们模拟计算的哪个方面。本文我们关注[缓存](/hpc/cpu-cache)与[分支预测](/hpc/pipelining/branching)，并为此使用 [Cachegrind](https://valgrind.org/docs/manual/cg-manual.html)——它是 [Valgrind](https://valgrind.org/) 中面向剖析的部分，而 Valgrind 本身是一款成熟的、用于内存泄漏检测和内存调试的工具。

### 用 Cachegrind 做剖析

Cachegrind 本质上是检查二进制中「有趣」的指令——那些执行内存读/写以及条件/间接跳转的指令——并把它们替换为用软件数据结构模拟相应硬件操作的代码。因此它不需要访问源代码，可以直接处理已经编译好的程序，并且可以像这样在任意程序上运行：

```bash
valgrind --tool=cachegrind --branch-sim=yes ./run
#      同时模拟分支预测 ^   ^ 任意命令，不一定是单个进程
```

它会插桩所有涉及的二进制，运行它们，并输出一份类似于 [perf stat](../events) 的汇总：

```
I   refs:      483,664,426
I1  misses:          1,858
LLi misses:          1,788
I1  miss rate:        0.00%
LLi miss rate:        0.00%

D   refs:      115,204,359  (88,016,970 rd   + 27,187,389 wr)
D1  misses:      9,722,664  ( 9,656,463 rd   +     66,201 wr)
LLd misses:         72,587  (     8,496 rd   +     64,091 wr)
D1  miss rate:         8.4% (      11.0%     +        0.2%  )
LLd miss rate:         0.1% (       0.0%     +        0.2%  )

LL refs:         9,724,522  ( 9,658,321 rd   +     66,201 wr)
LL misses:          74,375  (    10,284 rd   +     64,091 wr)
LL miss rate:          0.0% (       0.0%     +        0.2%  )

Branches:       90,575,071  (88,569,738 cond +  2,005,333 ind)
Mispredicts:    19,922,564  (19,921,919 cond +        645 ind)
Mispred rate:         22.0% (      22.5%     +        0.0%   )
```

我们喂给 Cachegrind 的示例代码与[上一节](../events)完全相同：创建一个一百万个随机整数的数组，排序它，然后对它执行一百万次二分查找。Cachegrind 显示的数值与 perf 大致相同，只是 perf 测到的内存读数和分支数因[推测执行](/hpc/pipelining)而略微偏高：它们确实在硬件中发生并递增硬件计数器，但随后被丢弃，不影响实际性能，因此模拟中忽略不计。

Cachegrind 只建模第一级缓存（数据 `D1`、指令 `I1`）和最后一级缓存（`LL`，统一缓存），其特性是从系统中推断出来的。它对你没有任何限制，因为你也可以在命令行设置它们，例如建模 L2 缓存：`--LL=<size>,<associativity>,<line size>`。

目前看来它只是拖慢了我们的程序，并没有提供任何 `perf stat` 给不出的信息。要从中获得比汇总信息更多的东西，我们可以检查一个专门的剖析信息文件——它默认转储在当前目录，名为 `cachegrind.out.<pid>`。该文件人类可读，但通常用 `cg_annotate` 命令来读取：

```bash
cg_annotate cachegrind.out.4159404 --show=Dr,D1mr,DLmr,Bc,Bcm
#                                    ^ 我们只关心数据读取和分支
```

它首先显示运行期间所用的参数，包括缓存系统的特性：

```
I1 cache:         32768 B, 64 B, 8-way associative
D1 cache:         32768 B, 64 B, 8-way associative
LL cache:         8388608 B, 64 B, direct-mapped
```

它对 L3 缓存的建模不太准确：它不是统一的（总共 8M，但单个核心只能看到 4M），而且是 16 路组相联，不过我们暂时忽略这点。

接着，它输出类似 `perf report` 的按函数汇总：

```
Dr         D1mr      DLmr Bc         Bcm         file:function
--------------------------------------------------------------------------------
19,951,476 8,985,458    3 41,902,938 11,005,530  ???:query()
24,832,125   585,982   65 24,712,356  7,689,480  ???:void std::__introsort_loop<...>
16,000,000        60    3  9,935,484    129,044  ???:random_r
18,000,000         2    1  6,000,000          1  ???:random
 4,690,248    61,999   17  5,690,241  1,081,230  ???:setup()
 2,000,000         0    0          0          0  ???:rand
```

可以看到排序阶段有大量分支预测失败，二分查找阶段则有大量 L1 缓存未命中和分支预测失败。这些信息 perf 给不了我们——它只能告诉我们整个程序的总计数。

Cachegrind 另一个很棒的特性是源代码的逐行标注。为此，你需要用调试信息（`-g`）编译程序，然后要么显式告诉 `cg_annotate` 要标注哪些源文件，要么直接传 `--auto=yes` 让它标注一切它能触及的代码（包括标准库源码）。

于是从源码到分析的整个过程是这样的：

```bash
g++ -O3 -g sort-and-search.cc -o run
valgrind --tool=cachegrind --branch-sim=yes --cachegrind-out-file=cachegrind.out ./run
cg_annotate cachegrind.out --auto=yes --show=Dr,D1mr,DLmr,Bc,Bcm
```

由于 glibc 的实现可读性不佳，为了便于讲解，我们用自己写的二分查找替换 `lower_bound`，它会像下面这样被标注：

```c++
Dr         D1mr      DLmr Bc         Bcm       
         .         .    .          .         .  int binary_search(int x) {
         0         0    0          0         0      int l = 0, r = n - 1;
         0         0    0 20,951,468 1,031,609      while (l < r) {
         0         0    0          0         0          int m = (l + r) / 2;
19,951,468 8,991,917   63 19,951,468 9,973,904          if (a[m] >= x)
         .         .    .          .         .              r = m;
         .         .    .          .         .          else
         0         0    0          0         0              l = m + 1;
         .         .    .          .         .      }
         .         .    .          .         .      return l;
         .         .    .          .         .  }
```

遗憾的是，Cachegrind 只追踪内存访问和分支。当瓶颈由别的东西造成时，我们需要[其他模拟工具](../mca)。
