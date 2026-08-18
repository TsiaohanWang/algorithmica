---
title: 向量化
authors:
- Сергей Слотин
created: 2019
date: 2021-08-22
weight: 100
---

考虑下面这个计算一维整数数组之和的程序：

```c++
#pragma GCC optimize("O3")
// ^ 开启最"激进"的优化级别
// 等价于在命令行编译时加 "-O3" 标志

#include <iostream>
using namespace std;

const int n = 1e5;
int a[n], s = 0;

int main() {
    for (int t = 0; t < 100000; t++)
        for (int i = 0; i < n; i++)
            s += a[i];

    return 0;
}
```

如果在 GCC 下不做任何额外设置编译这段代码并运行，它耗时 2.43 秒。

现在在程序最开头加上这条魔法指令：

```c++
#pragma GCC target("avx2")
// ...其余部分与之前完全一样
```

在相同条件下编译并运行，程序在 1.24 秒内完成。这几乎快了一倍，而我们并没有改变代码本身和优化级别。

原因在于现代处理器里有特殊的「向量」指令，它们可以把某个操作一次应用到一块连续的多个元素上，而不是每次只处理一个标量。这种模型称为 [SIMD](https://en.wikipedia.org/wiki/SIMD) 并行（英文 *single instruction, multiple data*）。

![](../img/simd-vs-scalar.gif)

不同微架构对 SIMD 指令的支持不同。除了指令集本身，向量寄存器的大小也不同——现在可以是 128、256 或 512 位。

在 x86 架构上（绝大多数桌面和服务器 CPU 使用它），所有 SIMD 扩展大体保持向后兼容：更新的意味着包含所有更旧的。C++ 编译器默认只假设目标（运行程序的计算机）支持「SSE2」指令集——这对本世纪出现的几乎所有 CPU 都成立。

大多数现代 CPU 支持 AVX2，其关键区别在于它所使用的向量寄存器增大了一倍——从 128 到 256 位——因此一次操作可以相加的不再是 4 个、而是 8 个 `int`。相应地，当我们把额外的微架构信息告诉优化编译器（通过 `#pragma GCC target("avx2")` 或 `-mavx2`、`-march=native` 等标志）时，它就能访问更宽的寄存器，把我们的程序加速预期的两倍。

![](../img/intel-isa.png)

<!--
然而向量化的微妙之处远不止加几个 pragma——本文我们不会深入细节，只尝试讨论它们。要更系统地了解，作者推荐《Algorithms for Modern Hardware》的[相应章节](https://en.algorithmica.org/hpc/simd/)。
-->

然而向量化的微妙之处远不止加几个 pragma——要更系统地了解，作者推荐《Algorithms for Modern Hardware》的[相应章节](https://en.algorithmica.org/hpc/simd/)。
