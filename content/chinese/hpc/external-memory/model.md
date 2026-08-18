---
title: 外部存储模型
weight: 3
---

要分析内存受限算法的性能，我们需要建立一种成本模型：它要对昂贵的块 I/O 操作足够敏感，但又不能过于严格，以免失去实用性。

### 缓存感知模型

在[标准 RAM 模型](/hpc/complexity)中，我们忽略了基本操作完成所需时间并不相等的事实。最重要的是，它不区分对不同类型内存的操作，等同于把现实中耗时约 50ns 的 RAM 读取，与耗时约 5ms——约为前者的 $10^5$ 倍——的 HDD 读取相提并论。

与此思路类似，在*外部存储模型*中，我们干脆忽略一切非 I/O 操作。更具体地说，我们只考虑缓存层级中的某一层，并对硬件和问题做出如下假设：

- 数据集的大小为 $N$，全部存储在*外部*存储器中；我们可以按块读写这种存储器，每块 $B$ 个元素，单位时间内完成一块（读一整块与只读一个元素耗时相同）。
- 我们可以在*内部*存储器中存储 $M$ 个元素，即最多可以存放 $\left \lfloor \frac{M}{B} \right \rfloor$ 块。
- 我们只关心 I/O 操作：读写之间进行的任何计算都是免费的。
- 此外我们还假设 $N \gg M \gg B$。

在该模型中，我们以算法高层级的 *I/O 操作*，即 *IOPS*，来衡量其性能——也就是执行过程中从外部存储器读写的块总数。

我们将主要关注内部存储器为 RAM、外部存储器为 SSD 或 HDD 的情形，不过我们将要建立的基础分析技术同样适用于缓存层级中的任何一层。在这些设定下，合理的块大小 $B$ 约为 1MB，内部存储器大小 $M$ 通常为几 GB，而 $N$ 最多可达几 TB。

### 数组扫描

<!-- 外部存储模型可以在不牺牲简单性的前提下得到高效利用。 -->

举个简单的例子：当我们逐元素遍历数组并计算其和时，实际上是按大小为 $O(B)$ 的块隐式地加载它；用外部存储模型的话说，就是一块接一块地处理这些数据：

$$
\underbrace{a_1, a_2, a_3,} _ {B_1}
\underbrace{a_4, a_5, a_6,} _ {B_2}
\ldots
\underbrace{a_{n-3}, a_{n-2}, a_{n-1}} _ {B_{m-1}}
$$

因此，在外部存储模型中，求和及其他线性数组扫描的复杂度为

$$
SCAN(N) \stackrel{\text{定义}}{=} O\left(\left \lceil \frac{N}{B} \right \rceil \right) \; \text{IOPS}
$$

你可以像这样显式地实现外部数组扫描：

```c++
FILE *input = fopen("input.bin", "rb");

const int M = 1024;
int buffer[M], sum = 0;

// while the file is not fully processed
while (true) {
    // read up to M of 4-byte elements from the input stream
    int n = fread(buffer, 4, M, input);
    //  ^ the number of elements that were actually read

    // if we can't read any more elements, finish
    if (n == 0)
        break;
    
    // sum elements in-memory
    for (int i = 0; i < n; i++)
        sum += buffer[i];
}

fclose(input);
printf("%d\n", sum);
```

注意，在大多数情况下，操作系统会自动完成这种缓冲。即使数据只是从普通文件重定向到标准输入，操作系统也会缓冲其数据流，并（默认）按约 4KB 的块来读取。