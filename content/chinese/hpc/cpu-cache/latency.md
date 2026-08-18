---
title: 内存延迟
weight: 2
---

尽管[带宽](../bandwidth)是更复杂的概念，但它比延迟更容易观测和测量：你可以简单地执行一长串相互独立的读或写请求，调度器由于预先知道这些请求，会重新排序并将它们重叠起来，从而隐藏其延迟并最大化总吞吐量。

要测量*延迟*，我们需要设计一个实验，让 CPU 无法通过预先知道我们将要请求的内存位置来作弊。一种确保做到这一点的方法是生成一个大小为 $N$ 的随机排列，使其对应一个环，然后反复沿排列走：

```cpp
int p[N], q[N];

// generating a random permutation
iota(p, p + N, 0);
random_shuffle(p, p + N);

// this permutation may contain multiple cycles,
// so instead we use it to construct another permutation with a single cycle
int k = p[N - 1];
for (int i = 0; i < N; i++)
    k = q[k] = p[i];

for (int t = 0; t < K; t++)
    for (int i = 0; i < N; i++)
        k = q[k];
```

与线性迭代相比，用这种方式访问数组的所有元素要*慢得多*——慢几个数量级。它不仅使 [SIMD](/hpc/simd) 无法使用，还会[让流水线停滞](/hpc/pipelining)，造成指令的大规模堵车，所有指令都在等待从内存中取回单个数据。

这种性能反模式被称为*指针追逐*（pointer chasing），在数据结构中非常常见，尤其是在用高级语言编写的、大量使用堆分配对象与指向它们的指针（动态类型所需的）的数据结构中。

![](../img/latency-throughput.svg)

谈到延迟时，用周期或纳秒来表示比用吞吐量单位更有意义，所以我们用它的倒数替换这张图：

![](../img/permutation-latency.svg)

注意，两张图上的峭壁不像带宽图那样清晰。这是因为即使数组无法完全装进某个缓存层，我们仍然有一定概率命中上一层的缓存。

### 理论延迟

更形式化地说，如果缓存层次结构中有 $k$ 层，大小分别为 $s_i$、延迟分别为 $l_i$，那么期望延迟将不是等于最慢的那次访问，而是：

$$
E[L] = \frac{
      s_1 \cdot l_1
    + (s_2 - s_1) \cdot l_2
%    + (s_3 - s_2) \cdot l_3
    + \ldots
    + (N - s_k) \cdot l_{RAM}
    }{N}
$$

如果我们把最慢缓存层之前发生的一切都抽象掉，可以把公式化简成这样：

$$
E[L] = \frac{N \cdot l_{last} - C}{N} = l_{last} - \frac{C}{N}
$$

随着 $N$ 增大，期望延迟逐渐逼近 $l_{last}$；如果你眯起眼睛仔细看，吞吐量（延迟的倒数）的图形应该大致看起来像由几条经过平移和缩放的双曲线组成：

$$
\begin{aligned}
E[L]^{-1} &= \frac{1}{l_{last} - \frac{C}{N}}
\\        &= \frac{N}{N \cdot l_{last} - C}
\\        &= \frac{1}{l_{last}} \cdot \frac{N + \frac{C}{l_{last}} - \frac{C}{l_{last}}}{N - \frac{C}{l_{last}}}
\\        &= \frac{1}{l_{last}} \cdot \left(\frac{1}{N \cdot \frac{l_{last}}{C} - 1} + 1\right)
\\        &= \frac{1}{k \cdot (x - x_0)} + y_0
\end{aligned}
$$

要得到实际的延迟数值，我们可以迭代地应用第一个公式，先推出 $l_1$，再推出 $l_2$，依此类推。或者直接看峭壁之前的值——它们应该与真实延迟相差在 10-15% 以内。

还有更直接的延迟测量方法，包括使用[非临时读](../bandwidth)，不过这个基准测试更能代表实际的访问模式。

<!--

E[L] \approx \frac{s_{k} \cdot l_{k} + (N - s_k) \cdot l_{k+1}}{N}
= l_{k+1} - \frac{s_k \cdot (l_{k+1} - l_k)}{N} 

-->

### 频率缩放

与带宽类似，所有 CPU 缓存的延迟都随其时钟频率成比例缩放，而内存则不然。我们也可以通过开启睿频来改变频率，观察这一差异。

![](../img/permutation-boost.svg)

如果把它画成相对加速比，这张图就更容易理解了。

![](../img/permutation-boost-speedup.svg)

你会期望完全能装进 CPU 缓存的数组大小有 2 倍的差异，而存储在内存中的数组则大致持平。但实际情况并非完全如此：即使对于内存访问，低频运行时也存在一个很小的固定延迟开销。这是因为 CPU 在向主内存派发读请求之前，必须先检查自己的缓存——以便为其他可能需要的进程节省内存带宽。

内存延迟还会受到[虚拟内存实现](../paging)和[内存特有时序](../mlp)的一些细节的轻微影响，我们将在后面讨论。