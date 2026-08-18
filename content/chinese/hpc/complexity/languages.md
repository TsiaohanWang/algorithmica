---
title: 编程语言
aliases:
  - /hpc/analyzing-performance
weight: 2
published: true
---

如果你在读这本书，那么在你的计算机科学之旅中，一定有过某个时刻第一次开始在意自己代码的效率。

对我来说那是高中时期，当时我意识到做网站和搞*实用*编程进不了大学，于是进入了算法编程奥林匹克竞赛这个令人兴奋的世界。我算是个还不错的程序员，尤其以高中生的标准来看，但此前我从未真正想过自己的代码执行要花多少时间。可突然间它开始变得重要了：每道题现在都有了严格的时间限制。我开始数自己的操作。一秒之内你能做多少次？

要回答这个问题，我对计算机架构知之甚少。但我也不需要正确答案——我需要一条经验法则。我的思路是：「2-3GHz 意味着每秒执行 20 到 30 亿条指令，而在一个对数组元素做点什么的简单循环里，我还得递增循环计数器、检查循环结束条件、做数组索引之类的事，所以每一条有用的指令再预留 3-5 条指令的空间」，最终我以 $5 \cdot 10^8$ 作为估计值。这些话没有一句是准确的，但数出我的算法需要多少次操作、再除以这个数，对我的用途来说是一条不错的经验法则。

真正的答案当然要复杂得多，而且高度取决于你所说的「操作」是哪一种。对于[指针追逐](/hpc/cpu-cache/latency)这类事情，它低至 $10^7$；对于 [SIMD 加速](/hpc/simd)的线性代数，它高达 $10^{11}$。为了展示这些惊人的差异，我们将以用不同语言实现的矩阵乘法作为案例研究——并更深入地探究计算机是如何执行它们的。

<!--

由于这套逻辑，再加上 CS 101 里确立的[计算模型](../)，许多程序员有一个误解：计算机每秒能执行固定数量的「操作」，而使用不同的编程语言会以某种方式对该数字产生[乘数效应](https://benchmarksgame-team.pages.debian.net/benchmarksgame/index.html)：

- 「这台机器上每秒大约能执行 $5 \cdot 10^8$ 次操作，」
- 「C 比 Java 快 2 倍，」
- 「Python 比 C++ 慢 100 倍。」

-->

## 语言的类型

<!--

处理器可以被看作*状态机*。它们把*状态*保存在几个固定长度的*寄存器*中，其中一个是指令指针，它指示下一条待读取和执行的指令在内存中的位置。这条指令以某种方式修改寄存器，并把指令指针移动到下一条要执行的指令上，如此往复。

这些指令——叫做*机器代码*——是二进制编码的，古怪且非常难以使用，所以如今没有人会神志清醒地直接编写它们。相反，我们使用更高级的编程语言，并借助替代手段把指令喂给处理器。

-->

在最低层面上，计算机执行由二进制编码的*指令*组成的*机器代码*，这些指令用来控制 CPU。它们具体、古怪，使用起来需要付出大量的智力劳动，所以人类在制造出计算机后最先做的事情之一就是创造*编程语言*，它抽象掉了计算机运作方式的一些细节，以简化编程过程。

一门编程语言从根本上说只是一个接口。用它所写的任何程序都只是一种更美观的、更高层的表示，最终仍需在某个时刻被转换成机器代码才能在 CPU 上执行——而做这件事有不同的手段：

- 从程序员的角度看，语言分两类：*编译型*，在执行前预先处理；*解释型*，在运行时借助一个叫做*解释器*的独立程序来执行。
- 从计算机的角度看，语言也分两类：*原生*（native），直接执行机器代码；*托管*（managed），依赖某种*运行时*来做这件事。

由于在解释器里运行机器代码没有意义，所以总共有三种类型的语言：

- 解释型语言，比如 Python、JavaScript 或 Ruby。
- 带运行时的编译型语言，比如 Java、C# 或 Erlang（以及运行在其 VM 上的语言，比如 Scala、F# 或 Elixir）。
- 编译型原生语言，比如 C、Go 或 Rust。

执行计算机程序没有「正确」的方式：每种方式都有各自的收益和缺点。解释器和虚拟机提供了灵活性，并带来一些不错的高层编程特性，比如动态类型、运行时修改代码和自动内存管理，但这些都伴随着一些不可避免的性能折衷，我们接下来就来讨论。

### 解释型语言

下面是一个用纯 Python 实现的、按定义写的 $1024 \times 1024$ 矩阵乘法：

```python
import time
import random

n = 1024

a = [[random.random()
      for row in range(n)]
      for col in range(n)]

b = [[random.random()
      for row in range(n)]
      for col in range(n)]

c = [[0
      for row in range(n)]
      for col in range(n)]

start = time.time()

for i in range(n):
    for j in range(n):
        for k in range(n):
            c[i][j] += a[i][k] * b[k][j]

duration = time.time() - start
print(duration)
```

这段代码运行了 630 秒。那可是 10 多分钟！

让我们试着把这个数字放到合适的参照系里。运行它的 CPU 时钟频率为 1.4GHz，意味着每秒执行 $1.4 \cdot 10^9$ 个周期，整个计算总计接近 $10^{15}$ 个周期，最内层循环里每次乘法大约耗费 880 个周期。

如果你想想 Python 为了搞清楚程序员的意思需要做哪些事情，这就不足为奇了：

- 它解析表达式 `c[i][j] += a[i][k] * b[k][j]`；
- 尝试搞清楚 `a`、`b` 和 `c` 是什么，并在一个带类型信息的特殊哈希表中查找它们的名字；
- 明白 `a` 是一个列表，取出它的 `[]` 运算符，检索 `a[i]` 的指针，发现它也是一个列表，再次取出它的 `[]` 运算符，得到 `a[i][k]` 的指针，然后是元素本身；
- 查找它的类型，发现它是一个 `float`，并取出实现 `*` 运算符的方法；
- 对 `b` 和 `c` 做同样的事情，最后把结果加赋值给 `c[i][j]`。

诚然，Python 这类被广泛使用的语言的解释器优化得很好，在重复执行同一段代码时可以跳过其中一些步骤。但即便如此，由于语言设计本身，一些相当可观的开销是不可避免的。如果我们去掉所有这些类型检查和指针追逐，或许能让每次乘法的周期数接近 1，或者接近原生乘法的「成本」？

### 托管型语言

同样的矩阵乘法过程，用 Java 实现：

```java
import java.util.Random;

public class Matmul {
    static int n = 1024;
    static double[][] a = new double[n][n];
    static double[][] b = new double[n][n];
    static double[][] c = new double[n][n];

    public static void main(String[] args) {
        Random rand = new Random();

        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                a[i][j] = rand.nextDouble();
                b[i][j] = rand.nextDouble();
                c[i][j] = 0;
            }
        }

        long start = System.nanoTime();

        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                for (int k = 0; k < n; k++)
                    c[i][j] += a[i][k] * b[k][j];
                
        double diff = (System.nanoTime() - start) * 1e-9;
        System.out.println(diff);
    }
}
```

现在它运行了 10 秒，大约相当于每次乘法 13 个 CPU 周期——比 Python 快 63 倍。考虑到我们需要从内存中非顺序地读取 `b` 的元素，这个运行时间大致符合预期。

Java 是一种*编译型*但不是*原生*的语言。程序首先编译成*字节码*，然后由虚拟机（JVM）来解释执行。为了获得更高的性能，代码中经常被执行的部分——比如最内层的 `for` 循环——会在运行时被编译成机器代码，然后几乎以零开销执行。这项技术叫做*即时编译*（just-in-time compilation）。

JIT 编译不是语言本身的特性，而是其实现的特性。Python 也有一个 JIT 编译的版本，叫做 [PyPy](https://www.pypy.org/)，它不需要对上述代码做任何修改，只需约 12 秒就能执行完。

### 编译型语言

现在轮到 C 了：

```cpp
#include <stdlib.h>
#include <stdio.h>
#include <time.h>

#define n 1024
double a[n][n], b[n][n], c[n][n];

int main() {
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            a[i][j] = (double) rand() / RAND_MAX;
            b[i][j] = (double) rand() / RAND_MAX;
        }
    }

    clock_t start = clock();

    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++)
                c[i][j] += a[i][k] * b[k][j];

    float seconds = (float) (clock() - start) / CLOCKS_PER_SEC;
    printf("%.4f\n", seconds);
    
    return 0;
}
```

用 `gcc -O3` 编译后，它需要 9 秒。

这看起来并不是多大的进步——比 Java 和 PyPy 快的那 1-3 秒可以归因于 JIT 编译的额外时间——但我们还没有利用上远比它们强大的 C 编译器生态。如果我们加上 `-march=native` 和 `-ffast-math` 标志，时间会骤降到 0.6 秒！

这里发生的事情是，我们[向编译器传达了](/hpc/compilation/flags/)我们所运行 CPU 的确切型号（`-march=native`），并给了它重排[浮点计算](/hpc/arithmetic/float)的自由（`-ffast-math`），于是它抓住了这个机会，用[向量化](/hpc/simd)实现了这次加速。

并不是说在不显著修改源代码的情况下，把 PyPy 和 Java 的 JIT 编译器调优到相同性能就不可能，但对于直接编译成原生代码的语言来说，这当然要容易得多。

### BLAS

最后，让我们看看专家级优化的实现能做到什么程度。我们将测试一个被广泛使用的优化线性代数库 [OpenBLAS](https://www.openblas.net/)。使用它的最简单方式是回到 Python，直接从 `numpy` 里调用它：

```python
import time
import numpy as np

n = 1024

a = np.random.rand(n, n)
b = np.random.rand(n, n)

start = time.time()

c = np.dot(a, b)

duration = time.time() - start
print(duration)
```

现在它只需要约 0.12 秒：比自动向量化的 C 版本快约 5 倍，比我们最初的 Python 实现快约 5250 倍！

你通常看不到如此戏剧性的提升。眼下我们还没准备好确切地告诉你这是如何实现的。OpenBLAS 中稠密矩阵乘法的实现是[5000 行手写汇编](https://github.com/xianyi/OpenBLAS/blob/develop/kernel/x86_64/dgemm_kernel_16x2_haswell.S)，并且针对*每一种*架构单独定制。在后面的章节里，我们会逐一讲解所有相关技术，然后[回到](/hpc/algorithms/matmul)这个例子，用不到 40 行 C 代码开发出我们自己的 BLAS 级实现。

### 要点

这里的关键教训是：使用原生、底层语言并不必然带给你性能；但它确实带给你对性能的*掌控*。

与「每秒 N 次操作」的简化相辅相成的是，许多程序员还有一个误解：使用不同的编程语言会以某种方式对这个数字产生乘数效应。以这种方式思考并[比较语言](https://benchmarksgame-team.pages.debian.net/benchmarksgame/index.html)的性能意义不大：编程语言从根本上说只是工具，它们以方便的抽象为代价，夺走了对性能的*部分*掌控。无论执行环境如何，充分利用硬件提供的机会，在很大程度上仍然是程序员的工作。