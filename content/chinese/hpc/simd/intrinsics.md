---
title: 内建函数与向量类型
aliases: [/hpc/simd/x86-simd]
weight: 1
---

使用 SIMD 最底层的方式是直接使用汇编向量指令——它们与对应的标量指令并无不同——但我们不会这么做。相反，我们将使用现代 C/C++ 编译器提供的、映射到这些指令的*内建函数*（intrinsic）。

在本节中，我们将了解它们的基本语法；在本章其余部分，我们会大量使用它们来做一些真正有趣的事情。

## 准备工作

要使用 x86 内建函数，我们需要做一些基础工作。

首先，我们需要确定硬件支持哪些扩展。在 Linux 上，可以运行 `cat /proc/cpuinfo`；在其他平台上，最好去 [WikiChip](https://en.wikichip.org/wiki/WikiChip)，用 CPU 的名字查询。无论哪种方式，都会有一个 `flags` 部分，列出所有受支持的向量扩展的代号。

此外还有一种特殊的 [CPUID](https://en.wikipedia.org/wiki/CPUID) 汇编指令，可以查询有关 CPU 的各种信息，包括对特定向量扩展的支持。它主要用于在运行时获取这类信息，从而避免为每种微架构分别分发一个二进制文件。它的输出以便于压缩的特性掩码形式返回，因此编译器提供了内置方法来解读它。下面是一个例子：

```c++
#include <iostream>
using namespace std;

int main() {
    cout << __builtin_cpu_supports("sse") << endl;
    cout << __builtin_cpu_supports("sse2") << endl;
    cout << __builtin_cpu_supports("avx") << endl;
    cout << __builtin_cpu_supports("avx2") << endl;
    cout << __builtin_cpu_supports("avx512f") << endl;

    return 0;
}
```

其次，我们需要包含一个头文件，里面含有我们需要的那个内建函数子集。与 GCC 中的 `<bits/stdc++.h>` 类似，有一个包含全部内建函数的 `<x86intrin.h>` 头文件，所以我们直接用它就行。

最后，我们需要[告诉编译器](/hpc/compilation/flags)，目标 CPU 确实支持这些扩展。这可以通过 `#pragma GCC target(...)` [像我们之前做的那样](../) 来完成，也可以在编译选项中用 `-march=...` 标志。如果你在同一台机器上编译并运行代码，可以设置 `-march=native` 来自动检测微架构。

在之后的所有代码示例中，都假定它们以这几行开头：

```c++
#pragma GCC target("avx2")
#pragma GCC optimize("O3")

#include <x86intrin.h>
#include <bits/stdc++.h>

using namespace std;
```

本章将聚焦于 AVX2 及其之前的 SIMD 扩展，它们应该可以在 95% 的台式机和服务器上使用；不过，这些通用原理同样适用于 AVX512、Arm Neon 以及其他 SIMD 架构。

### SIMD 寄存器

SIMD 扩展之间最显著的区别是对更宽寄存器的支持：

- SSE（1999）增加了 16 个 128 位寄存器，名为 `xmm0` 到 `xmm15`。
- AVX（2011）增加了 16 个 256 位寄存器，名为 `ymm0` 到 `ymm15`。
- AVX512（2017）增加了[^mask] 16 个 512 位寄存器，名为 `zmm0` 到 `zmm15`。

[^mask]: AVX512 还新增了 8 个所谓的*掩码寄存器*，名为 `k0` 到 `k7`，用于数据的掩蔽（masking）与混合（blending）。我们不打算介绍它们，主要使用 AVX2 及其之前的标准。

从命名上，以及从 512 位已经占满一整条缓存行这个事实来看，你也能猜到，x86 的设计者们并不打算在短期内引入更宽的寄存器。

C/C++ 编译器实现了特殊的*向量类型*（vector type），用来指代存储在这些寄存器中的数据：

- 128 位的 `__m128`、`__m128d` 和 `__m128i` 类型，分别对应单精度浮点数、双精度浮点数以及各种整数数据；
- 256 位的 `__m256`、`__m256d`、`__m256i`；
- 512 位的 `__m512`、`__m512d`、`__m512i`。

寄存器本身可以容纳任何类型的数据：这些类型只用于类型检查。你可以像转换其他任何类型一样，把一个向量变量转换成另一种向量类型，而且不会有任何代价。

### SIMD 内建函数

*内建函数*不过是 C 风格的函数，对向量数据类型进行一些操作，通常只是简单地调用与之关联的汇编指令。

例如，下面这个循环用 AVX 内建函数把两个 64 位浮点数数组相加：

```c++
double a[100], b[100], c[100];

// iterate in blocks of 4,
// because that's how many doubles can fit into a 256-bit register
for (int i = 0; i < 100; i += 4) {
    // load two 256-bit segments into registers
    __m256d x = _mm256_loadu_pd(&a[i]);
    __m256d y = _mm256_loadu_pd(&b[i]);

    // add 4+4 64-bit numbers together
    __m256d z = _mm256_add_pd(x, y);

    // write the 256-bit result into memory, starting with c[i]
    _mm256_storeu_pd(&c[i], z);
}
```

使用 SIMD 的主要挑战，是把数据整理成适合加载到寄存器中的连续定长块。在上面的代码中，如果数组长度不能被块大小整除，我们通常就会遇到问题。对此有两种常见的解决方案：

1. 我们可以「越界」处理，无论如何都要遍历最后一个不完整的片段。为了确保不会因为读写不属于我们的内存区域而段错误（segfault），我们需要把数组填充到最近的块大小（通常填充某种「中性」元素，例如 0）。
2. 少做一次迭代，在末尾写一个小循环，用标量运算正常计算剩余部分。

人类偏好方式 #1，因为它更简单、代码更少；编译器偏好方式 #2，因为它们确实没有其他合法的选择。

### 指令参考

大多数 SIMD 内建函数遵循与 `_mm<size>_<action>_<type>` 类似的命名约定，并与命名相近的单条汇编指令一一对应。一旦你习惯了汇编的命名约定，它们就相对不言自明，尽管有时候这些名字看起来就像是猫咪在键盘上乱走生成的（你来解释一下这个：[punpcklqdq](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html#ig_expand=3037,3009,4870,4870,4872,4875,833,879,874,849,848,6715,4845,6046,3853,288,6570,6527,6527,90,7307,6385,5993,2692,6946,6949,5456,6938,5456,1021,3007,514,518,4875,7253,7183,3892,5135,5260,5259,6385,3915,4027,3873,7401&techs=AVX,AVX2&text=punpcklqdq)）。

这里再举几个例子，让你感受一下：

- `_mm_add_epi16`：把两个 128 位的 16 位*扩展打包整数*（extended packed integers）向量相加，简单说就是两个 `short` 向量。
- `_mm256_acos_pd`：对 4 个*打包的双精度数*（packed doubles）逐元素计算 $\arccos$。
- `_mm256_broadcast_sd`：把一个内存位置中的 `double` 广播（复制）到结果向量的全部 4 个元素。
- `_mm256_ceil_pd`：把 4 个 `double` 分别向上舍入到最近的整数。
- `_mm256_cmpeq_epi32`：比较 8+8 个打包的 `int`，返回一个掩码，在相等的元素对位置置 1。
- `_mm256_blendv_ps`：根据掩码从两个向量之一选取元素。

你可能已经猜到，内建函数的数量在组合意义上是极其庞大的；除此之外，有些指令还带有立即数——因此它们的内建函数需要编译期常量参数：例如，浮点比较指令[就有 32 种不同的修饰符](https://stackoverflow.com/questions/16988199/how-to-choose-avx-compare-predicate-variants)。

出于某些原因，有些操作对寄存器中存储的数据类型不敏感，却只接受特定的向量类型（通常是 32 位浮点）——要使用这类内建函数，你只能先转换过去再转换回来。为了简化本章的示例，我们将主要使用 256 位 AVX2 寄存器中的 32 位整数（`epi32`）。

x86 SIMD 内建函数的一个非常有用的参考是 [Intel Intrinsics Guide](https://software.intel.com/sites/landingpage/IntrinsicsGuide/)，它按类别和扩展分组，包含描述、伪代码、对应的汇编指令，以及它们在 Intel 微架构上的延迟与吞吐量。你可能想把那个页面加入书签。

当你确定某个指令存在、只想查它的名字或性能信息时，Intel 参考很有用。当你不知道它是否存在时，这份[速查表](https://db.in.tum.de/~finis/x86%20intrinsics%20cheat%20sheet%20v1.0.pdf)可能更合适。

**指令选择**。注意，编译器并不一定会选用你指定的那条指令。与我们[之前讨论过](/hpc/analyzing-performance/assembly)的标量 `c = a + b` 类似，也存在融合的向量加法指令，因此编译器[把上面的代码重写](https://godbolt.org/z/dMz8E5Ye8)成每轮循环 3 条指令的块，而不是 2+1+1=4 条：

```nasm
vmovapd ymm1, YMMWORD PTR a[rax]
vaddpd  ymm0, ymm1, YMMWORD PTR b[rax]
vmovapd YMMWORD PTR c[rax], ymm0
```

有时候——虽然很少见——编译器的这种干预会让事情变得更糟，所以最好经常[检查汇编代码](/hpc/compilation/stages)，仔细看看生成的向量指令（它们通常以「v」开头）。

此外，有些内建函数并不映射到单条指令，而是一小段指令序列，作为一种方便的捷径：[广播与提取](../moving#register-aliasing)就是一个典型的例子。

<!--

例如，用于从向量中取出单个元素的 `extract` 内建函数组：如 `_mm256_extract_epi32(x, 0)` 返回 8 整数向量中的第一个元素。一般来说，在「普通」寄存器和 SIMD 寄存器之间移动数据相当慢（约 5 个周期）。

-->

### GCC 向量扩展

如果你觉得 C 内建函数的设计很糟糕，你不是一个人。我花了数百小时编写 SIMD 代码、阅读 Intel Intrinsics Guide，至今仍记不住到底该输入 `_mm256` 还是 `__m256`。

内建函数不仅难用，而且既不可移植也不易维护。在好的软件中，你不会想为每种 CPU 维护不同的过程：你希望只实现一次，以一种与架构无关的方式。

有一天，GNU 项目的编译器工程师们也这么想，于是开发出一种定义自定义向量类型的方法：这些类型用起来更像数组，并重载了一些运算符来对应相关的指令。

在 GCC 中，下面是这样定义一个打包在 256 位（32 字节）寄存器中的 8 整数向量：

```c++
typedef int v8si __attribute__ (( vector_size(32) ));
// type ^   ^ typename          size in bytes ^ 
```

遗憾的是，这并不是 C 或 C++ 标准的一部分，因此不同的编译器使用不同的语法。

多少存在一种命名约定：把元素的大小和类型包含进类型名里。在上面的例子中，我们定义了一个「8 个有符号整数的向量」。但你可以随意选择任何名字，比如 `vec`、`reg` 等等。唯一不要做的是把它命名为 `vector`，因为和 `std::vector` 会带来太多混淆。

使用这些类型的主要优点是，对许多操作你都可以使用普通的 C++ 运算符，而不必查找相关的内建函数。

```c++
v4si a = {1, 2, 3, 5};
v4si b = {8, 13, 21, 34};

v4si c = a + b;

for (int i = 0; i < 4; i++)
    printf("%d\n", c[i]);

c *= 2; // multiply by scalar

for (int i = 0; i < 4; i++)
    printf("%d\n", c[i]);
```

借助向量类型，我们可以大幅简化之前用内建函数实现的「a + b」循环：

```c++
typedef double v4d __attribute__ (( vector_size(32) ));
v4d a[100/4], b[100/4], c[100/4];

for (int i = 0; i < 100/4; i++)
    c[i] = a[i] + b[i];
```

如你所见，与内建函数的噩梦相比，向量扩展要干净得多。它们的缺点在于，有些我们想做的事情无法用原生 C++ 结构表达，因此我们仍然需要内建函数。幸运的是，这并非二选一，因为向量类型支持与 `_mm` 类型之间的零成本转换：

```c++
v8f x;
int mask = _mm256_movemask_ps((__m256) x)
```

还有许多第三方库为不同语言提供了类似的能力，用于编写可移植的 SIMD 代码，而且总体上比内建函数和内置向量类型都好用。C++ 中著名的例子有 [Highway](https://github.com/google/highway)、[Expressive Vector Engine](https://github.com/jfalcou/eve)、[Vector Class Library](https://github.com/vectorclass/version2) 和 [xsimd](https://github.com/xtensor-stack/xsimd)。

推荐使用成熟的 SIMD 库，因为它能极大改善开发体验。不过，在本书中，我们会尽量贴近硬件，主要直接使用内建函数，在可以简化时偶尔切换到向量扩展。