---
title: 现代硬件算法
menuTitle: 高性能计算
weight: 5
#authors:
#- Sergey Slotin
#created: "Feb 2021"
#date: 2021-09-16
noToc: true
---

这是一本即将出版的高性能计算书籍，书名为《现代硬件算法》（Algorithms for Modern Hardware），作者是 [Sergey Slotin](http://sereja.me/)。

本书的目标读者包括性能工程师、实践型算法研究者，以及刚学完高级算法课程的计算机科学本科生——他们想学到比把复杂度从 $O(n \log n)$ 降到 $O(n \log \log n)$ 更实用的加速程序的方法。

本书的全部材料都[托管在 GitHub](https://github.com/algorithmica-org/algorithmica) 上，代码放在[单独的仓库](https://github.com/sslotin/scmm-code)里。这不是一个协作项目，但非常欢迎任何贡献与反馈。

### 常见问题

**Bug/笔误修正**。如果你在任意页面发现错误，请按以下优先级顺序采取其中一种方式：

- 立即修复：点击任意页面右上角的铅笔图标（会打开 [Prose](https://prose.io/) 编辑器），或者用更传统的方式——直接在 GitHub 上修改对应页面（源码链接也在右上角）；
- 在 GitHub 上创建一个 [issue](https://github.com/algorithmica-org/algorithmica/issues)；
- 直接[告诉我](http://sereja.me/)；

或者在我被提到的其他网站上留言——[HackerNews](https://news.ycombinator.com/from?site=algorithmica.org)、[CodeForces](https://codeforces.com/profile/sslotin) 和 [Twitter](https://twitter.com/sergey_slotin) 上的相关讨论串我基本都会看。

**发布日期**。本书分为几个部分，我计划按顺序完成，中间会有较长的间隔。截至 2022 年 3 月，第一部分「性能工程」已完成约 75%，希望到今年夏天能完成 95% 以上。

对这样一本开源书籍而言，「发布」本质上意味着：

- 完成所有必要章节并填满所有 TODO，
- 基本冻结目录（案例研究除外），
- 做最后一轮大幅度的文字润色（希望能有专业编辑帮忙——我至今没搞懂英语里逗号该怎么用），
- 绘制插图（现在页面上展示的插图有很多是我偷来的），
- 制作一个适合打印的 PDF 版本，并想清楚分发它的最佳方式。

在那之后，我主要会修复错误，只做一些反映技术变化或算法新进展的小修改。电子版/印刷版很可能会以“随心付费”的方式出售，而且无论如何，网页版都会一直免费完整地放在网上。

**预订 / 资助本书**。由于我不幸的国籍和出生地，你做不到——除非我找到一种既能同时遵守国际制裁、又不资助[这场战争](https://en.wikipedia.org/wiki/2022_Russian_invasion_of_Ukraine)、还不会让我因逃税而坐牢的方式。

所以，不用费心了。如果你想支持这本书，分享它、帮忙改改错别字就够了。

**翻译**。网站有独立的功能来创建和管理翻译——已经有一些好心人联系我，愿意把这本书翻译成意大利语和中文（我个人也会至少把其中一部分翻译成我的母语俄语）。

不过，由于本书仍在不断演进，至少在第一部分完成之前就着手翻译可能不是最好的主意。话虽如此，我非常鼓励你翻译任何文章并发布在自己的博客上——把链接发给我即可，等集中翻译开始时我们就可以把它合并回来。

**“翻译”俄语版**。[ru.algorithmica.org/cs/](https://ru.algorithmica.org/cs/) 上托管的文章并不是关于高级性能工程的，而主要是经典计算机科学算法——不讨论如何在渐近复杂度之外对它们进行加速。那里的大部分信息并非独一无二，互联网上其他地方已经有英文版本：例如，风格相近的 [cp-algorithms.com](https://cp-algorithms.com/)。

**在大学里教授性能工程**。我写这本书的目标之一是改变计算机科学——更准确地说是算法设计——在大学里的教学方式。让我详细说说这一点。

大多数计算机科学课程都建立在两本影响深远的教科书之上。两本书无疑都很出色，但[其中一本](https://en.wikipedia.org/wiki/The_Art_of_Computer_Programming)已有 50 年历史，[另一本](https://en.wikipedia.org/wiki/Introduction_to_Algorithms)则有 30 年历史，而[计算机自那以后发生了巨大变化](/hpc/complexity/hardware)。渐近复杂度不再是唯一的决定因素。在现代的实用算法设计中，你会选择能更好地利用硬件中各类并行性的方案，而不是那个在星系规模的输入上理论上执行更少原始操作的方案。

然而，大多数大学的计算机科学课程完全忽视了这一转变。虽然也有一些旨在纠正这一点的优秀课程——例如麻省理工学院的《[软件系统性能工程](https://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-172-performance-engineering-of-software-systems-fall-2018/)》、阿尔托大学的《[并行计算机编程](https://ppc.cs.aalto.fi/)》，以及一些非学术课程，比如 Denis Bakhvalov 的《[性能忍者](https://github.com/dendibakh/perf-ninja)》——但大多数计算机科学毕业生仍然把现代硬件当成 1990 年代的东西。

我真正想实现的是，让性能工程在学完算法导论之后紧接着被教授。写出一本关于该主题的第一本综合性教科书是其中很大一部分工作，这也是我急着在夏天前完成它的原因，这样大学就能在下一个学年采用它。但要创建一门新课程，光有这些还不够：你需要均衡的课程大纲、课程基础设施、讲稿、实验作业……所以在完成主线书籍之后的一段时间里，我会致力于开发和*教授*性能工程相关的课程材料与工具——我也期待与那些同样想把它变成现实的人合作。

<!--

在过去，你依靠摩尔定律替你完成剩下的部分——而且你大多是对的——但如今我们已经触及了单个 CPU 核心的能力上限。

接下来要做的是创建基础设施，它。

我希望这本书成为计算机科学学生在读完 TAOCP 和 CLRS 之后读的书。

有一些不错的尝试，例如，以及，但这些更像是例外，而且深度也不足以把人们带到前沿。

我过去曾经从零开始创建过课程。我已经收到，并且期待更多的合作。这也是我急着在夏天前完成它的原因之一——这样大学就能采纳这个想法。

在我看来，竞技编程走错了方向。他们在做无用的事，但他们擅长把错误的事做好，性能工程社区应该向他们学习。

-->

### 第一部分：性能工程

第一部分涵盖计算机体系结构的基础知识以及单线程算法的优化。

它系统地讲解了 CPU 优化的主要主题，如缓存、SIMD 和流水线，并给出用 C++ 编写的简要示例，随后是大型案例研究，在其中我们通常能比某些 STL 算法或数据结构获得显著的加速。

规划中的目录：

```
0. Preface
1. Complexity Models
 1.1. Modern Hardware
 1.2. Programming Languages
 1.3. Models of Computation
 1.4. When to Optimize
2. Computer Architecture
 1.1. Instruction Set Architectures
 1.2. Assembly Language
 1.3. Loops and Conditionals
 1.4. Functions and Recursion
 1.5. Indirect Branching
 1.6. Machine Code Layout
 1.7. System Calls
 1.8. Virtualization
3. Instruction-Level Parallelism
 3.1. Pipeline Hazards
 3.2. The Cost of Branching
 3.3. Branchless Programming
 3.4. Instruction Tables
 3.5. Instruction Scheduling
 3.6. Throughput Computing
 3.7. Theoretical Performance Limits
4. Compilation
 4.1. Stages of Compilation
 4.2. Flags and Targets
 4.3. Situational Optimizations
 4.4. Contract Programming
 4.5. Non-Zero-Cost Abstractions
 4.6. Compile-Time Computation
 4.7. Arithmetic Optimizations
 4.8. What Compilers Can and Can't Do
5. Profiling
 5.1. Instrumentation
 5.2. Statistical Profiling
 5.3. Program Simulation
 5.4. Machine Code Analyzers
 5.5. Benchmarking
 5.6. Getting Accurate Results
6. Arithmetic
 6.1. Floating-Point Numbers
 6.2. Interval Arithmetic
 6.3. Newton's Method
 6.4. Fast Inverse Square Root
 6.5. Integers
 6.6. Integer Division
 6.7. Bit Manipulation
(6.8. Data Compression)
7. Number Theory
 7.1. Modular Inverse
 7.2. Montgomery Multiplication
(7.3. Finite Fields)
(7.4. Error Correction)
 7.5. Cryptography
 7.6. Hashing
 7.7. Random Number Generation
8. External Memory
 8.1. Memory Hierarchy
 8.2. Virtual Memory
 8.3. External Memory Model
 8.4. External Sorting
 8.5. List Ranking
 8.6. Eviction Policies
 8.7. Cache-Oblivious Algorithms
 8.8. Spacial and Temporal Locality
(8.9. B-Trees)
(8.10. Sublinear Algorithms)
(9.13. Memory Management)
9. RAM & CPU Caches
 9.1. Memory Bandwidth
 9.2. Memory Latency
 9.3. Cache Lines
 9.4. Memory Sharing
 9.5. Memory-Level Parallelism
 9.6. Prefetching
 9.7. Alignment and Packing
 9.8. Pointer Alternatives
 9.9. Cache Associativity
 9.10. Memory Paging
 9.11. AoS and SoA
10. SIMD Parallelism
 10.1. Intrinsics and Vector Types
 10.2. Moving Data
 10.3. Reductions
 10.4. Masking and Blending
 10.5. In-Register Shuffles
 10.6. Auto-Vectorization and SPMD
11. Algorithm Case Studies
 11.1. Binary GCD
(11.2. Prime Number Sieves)
 11.3. Integer Factorization
 11.4. Logistic Regression
 11.5. Big Integers & Karatsuba Algorithm
 11.6. Fast Fourier Transform
 11.7. Number-Theoretic Transform
 11.8. Argmin with SIMD
 11.9. Prefix Sum with SIMD
 11.10. Reading Decimal Integers
 11.11. Writing Decimal Integers
(11.12. Reading and Writing Floats)
(11.13. String Searching)
 11.14. Sorting
 11.15. Matrix Multiplication
12. Data Structure Case Studies
 12.1. Binary Search
 12.2. Static B-Trees
(12.3. Search Trees)
 12.4. Segment Trees
(12.5. Tries)
(12.6. Range Minimum Query)
 12.7. Hash Tables
(12.8. Bitmaps)
(12.9. Probabilistic Filters)
```

以下是我们将加速的一些炫酷内容：

- GCD 快 2 倍（相比 `std::gcd`）
- 二分查找快 8–15 倍（相比 `std::lower_bound`）
- 线段树快 5–10 倍（相比树状数组）
- 哈希表快 5 倍（相比 `std::unordered_map`）
- popcount 快 2 倍（相比反复调用 `popcnt`）
- 解析整数序列快 35 倍（相比 `scanf`）
- 排序快 ? 倍（相比 `std::sort`）
- 求和快 2 倍（相比 `std::accumulate`）
- 前缀和快 2–3 倍（相比朴素实现）
- argmin 快 10 倍（相比朴素实现）
- 数组查找快 10 倍（相比 `std::find`）
- 搜索树快 15 倍（相比 `std::set`）
- 矩阵乘法快 100 倍（相比朴素的三重 for 循环）
- 最优的字长整数分解（每个 60 位整数约 0.4 ms）
- 最优的 Karatsuba 算法
- 最优的 FFT

篇幅：450–600 页  
发布日期：Q3 2022

### 第二部分：并行算法

并发、并行模型、上下文切换、绿色线程、并发运行时、缓存一致性、同步原语、OpenMP、归约、扫描、列表排名、图算法、无锁数据结构、异构计算、CUDA、kernel、warp、block、矩阵乘法、排序。

篇幅：150–200 页  
发布日期：2023–2024 年？

### 第三部分：分布式计算

<!-- （从这之后我可能需要一些帮助。） -->

网络、消息传递、Actor 模型、受通信约束的算法、分布式原语、全归约（all-reduce）、MapReduce、流处理、查询规划、存储、分片、压缩、分布式数据库、一致性、可靠性、调度、工作流引擎、云计算。

发布日期：???（完成的可能性更大）

### 第四部分：软件与硬件

<!-- (TODO: 想一个更好的标题——一个能强调这部分主要讲软件与硬件的边界、而不是编程语言/集成电路设计的标题) -->

LLVM IR、编译器优化与后端、解释器、JIT 编译、Cython、JAX、Numba、Julia、OpenCL、DPC++、oneAPI、XLA、（基础）Verilog、FPGA、ASIC、TPU 以及其他 AI 加速器。

发布日期：???（完成的可能性较小）

### 致谢

本书在很大程度上基于许多人的博客文章、研究论文、会议演讲和其他工作：

- [Agner Fog](https://agner.org/optimize/)
- [Daniel Lemire](https://lemire.me/en/#publications)
- [Andrei Alexandrescu](https://erdani.com/index.php/about/)
- [Chandler Carruth](https://twitter.com/chandlerc1024)
- [Wojciech Muła](http://0x80.pl/articles/index.html)
- [Malte Skarupke](https://probablydance.com/)
- [Travis Downs](https://travisdowns.github.io/)
- [Brendan Gregg](https://www.brendangregg.com/blog/index.html)
- [Andreas Abel](http://embedded.cs.uni-saarland.de/abel.php)
- [Jakob Kogler](https://cp-algorithms.com/)
- [Igor Ostrovsky](http://igoro.com/)
- [Steven Pigeon](https://hbfs.wordpress.com/)
- [Denis Bakhvalov](https://easyperf.net/notes/)
- [Paul Khuong](https://pvk.ca/)
- [Pat Morin](https://cglab.ca/~morin/)
- [Victor Eijkhout](https://www.tacc.utexas.edu/about/directory/victor-eijkhout)
- [Robert van de Geijn](https://www.cs.utexas.edu/~rvdg/)
- [Edmond Chow](https://www.cc.gatech.edu/~echow/)
- [Peter Cordes](https://stackoverflow.com/users/224132/peter-cordes)
- [Geoff Langdale](https://branchfree.org/)
- [Matt Kulukundis](https://twitter.com/JuvHarlequinKFM)
- [Georg Sauthoff](https://gms.tf/)
- [Danila Kutenin](https://danlark.org/author/kutdanila/)
- [Ivica Bogosavljević](https://johnysswlab.com/author/ibogi/)
- [Matt Pharr](https://pharr.org/matt/)
- [Jan Wassenberg](https://research.google/people/JanWassenberg/)
- [Marshall Lochbaum](https://mlochbaum.github.io/publications.html)
- [Pavel Zemtsov](https://pzemtsov.github.io/)
- [Gustavo Duarte](https://manybutfinite.com/)
- [Nyaan](https://nyaannyaan.github.io/library/)
- [Nayuki](https://www.nayuki.io/category/programming)
- [Konstantin](http://const.me/)
- [InstLatX64](https://twitter.com/InstLatX64)
- [ridiculous_fish](https://ridiculousfish.com/blog/)
- [Z boson](https://stackoverflow.com/users/2542702/z-boson)
- [Creel](https://www.youtube.com/c/WhatsACreel)

### 免责声明：技术选型

本书中的示例使用 C++、GCC、x86-64、CUDA 和 Spark，不过所传达的基本原理并不局限于这些技术。

为求心安，我直说我对这些选择并不满意：这些技术只是恰好是目前最普及、最稳定的，因此对读者更有帮助。我本来会分别选择 C / Rust / [Carbon?](https://github.com/carbon-language/carbon-lang)、LLVM、arm、OpenCL 和 Dask；也许将来会有第二版，届时部分技术栈会有所更换。