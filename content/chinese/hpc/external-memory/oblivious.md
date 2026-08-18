---
title: 缓存无关算法
weight: 7
---

在[外部存储模型](../model)的语境下，高效算法分为两种类型：

- *缓存感知*算法：对*已知*的 $B$ 和 $M$ 高效。
- *缓存无关*算法：对*任意*的 $B$ 和 $M$ 都高效。

例如，[外部归并排序](../sorting)是一种缓存感知算法，但不是缓存无关算法：我们需要知道系统的内存特性，即可用内存与块大小的比值，才能找到合适的 $k$ 来执行 $k$ 路归并排序。

缓存无关算法之所以有趣，是因为它们会自动对缓存层级中的所有内存层级达到最优，而不仅仅是它们专门调优过的那一层。在本文中，我们考虑它们在矩阵计算中的一些应用。

## 矩阵转置

假设我们有一个大小为 $N \times N$ 的方阵 $A$，需要把它转置。按定义直接实现的朴素方法大致是这样的：

```cpp
for (int i = 0; i < n; i++)
    for (int j = 0; j < i; j++)
        swap(a[j * N + i], a[i * N + j]);
```

这里我们用指向内存区域起始处的单个指针，而不是二维数组，以便更清楚地展示其内存操作。

这段代码的 I/O 复杂度是 $O(N^2)$，因为写入不是顺序的。如果你尝试交换迭代变量，情况会反过来，但结果是一样的。

### 算法

*缓存无关*算法依赖于下面的分块矩阵恒等式：

$$
\begin{pmatrix}
A & B \\
C & D
\end{pmatrix}^T=
\begin{pmatrix}
A^T & C^T \\
B^T & D^T
\end{pmatrix}
$$

它让我们可以用分治方法递归地解决这个问题：

1. 把输入矩阵分成 4 个更小的矩阵。
2. 递归地转置每个矩阵。
3. 通过交换角落的结果子矩阵来合并结果。

在矩阵上实现分治比在数组上略复杂一些，但主要思想是一样的。我们不想显式复制子矩阵，而是希望对它们使用「视图」；同时，当数据开始能装进 L1 缓存时，就切换到朴素方法（如果你事先不知道 L1 缓存大小，可以选一个小值，比如 $32 \times 32$）。当 $n$ 为奇数、无法把矩阵分成 4 个相等的子矩阵时，我们还需要小心处理。

```cpp
void transpose(int *a, int n, int N) {
    if (n <= 32) {
        for (int i = 0; i < n; i++)
            for (int j = 0; j < i; j++)
                swap(a[i * N + j], a[j * N + i]);
    } else {
        int k = n / 2;

        transpose(a, k, N);
        transpose(a + k, k, N);
        transpose(a + k * N, k, N);
        transpose(a + k * N + k, k, N);
        
        for (int i = 0; i < k; i++)
            for (int j = 0; j < k; j++)
                swap(a[i * N + (j + k)], a[(i + k) * N + j]);
        
        if (n & 1)
            for (int i = 0; i < n - 1; i++)
                swap(a[i * N + n - 1], a[(n - 1) * N + i]);
    }
}
```

该算法的 I/O 复杂度为 $O(\frac{N^2}{B})$，因为在每个合并阶段我们只需要触及大约一半的内存块，也就是说每个阶段我们的问题都会变小。

把这个代码推广到非方阵的一般情况，就留给读者作为练习了。

## 矩阵乘法

接下来，我们考虑稍微复杂一点的问题：矩阵乘法。

$$
C_{ij} = \sum_k A_{ik} B_{kj}
$$

朴素算法只是把它的定义直接翻译成代码：

```cpp
// don't forget to initialize c[][] with zeroes
for (int i = 0; i < n; i++)
    for (int j = 0; j < n; j++)
        for (int k = 0; k < n; k++)
            c[i * n + j] += a[i * n + k] * b[k * n + j];
```

它总共需要访问 $O(N^3)$ 个块，因为每次标量乘法都需要一次单独的块读取。

一个众所周知的优化是先转置 $B$：

```cpp
for (int i = 0; i < n; i++)
    for (int j = 0; j < i; j++)
        swap(b[j][i], b[i][j])
// ^ or use our faster transpose from before

for (int i = 0; i < n; i++)
    for (int j = 0; j < n; j++)
        for (int k = 0; k < n; k++)
            c[i * n + j] += a[i * n + k] * b[j * n + k]; // <- note the indices
```

无论转置是用朴素方法还是用我们之前开发的缓存无关方法完成，只要其中一个矩阵被转置，矩阵乘法就可以在 $O(N^3/B + N^2)$ 内完成，因为此时所有内存访问都是顺序的。

看起来我们无法做得更好了，但事实证明我们可以。

### 算法

缓存无关的矩阵乘法本质上依赖与转置相同的技巧。我们需要不断地划分数据，直到它能装进最底层的缓存（即 $N^2 \leq M$）。对矩阵乘法来说，这意味着使用下面的公式：

$$
\begin{pmatrix}
A_{11} & A_{12} \\
A_{21} & A_{22} \\
\end{pmatrix} \begin{pmatrix}
B_{11} & B_{12} \\
B_{21} & B_{22} \\
\end{pmatrix} = \begin{pmatrix}
A_{11} B_{11} + A_{12} B_{21} & A_{11} B_{12} + A_{12} B_{22}\\
A_{21} B_{11} + A_{22} B_{21} & A_{21} B_{12} + A_{22} B_{22}\\
\end{pmatrix}
$$

不过实现起来稍微难一些，因为现在我们总共有 8 次递归矩阵乘法：

```cpp
void matmul(const float *a, const float *b, float *c, int n, int N) {
    if (n <= 32) {
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                for (int k = 0; k < n; k++)
                    c[i * N + j] += a[i * N + k] * b[k * N + j];
    } else {
        int k = n / 2;

        // c11 = a11 b11 + a12 b21
        matmul(a,     b,         c, k, N);
        matmul(a + k, b + k * N, c, k, N);
        
        // c12 = a11 b12 + a12 b22
        matmul(a,     b + k,         c + k, k, N);
        matmul(a + k, b + k * N + k, c + k, k, N);
        
        // c21 = a21 b11 + a22 b21
        matmul(a + k * N,     b,         c + k * N, k, N);
        matmul(a + k * N + k, b + k * N, c + k * N, k, N);
        
        // c22 = a21 b12 + a22 b22
        mul(a + k * N,     b + k,         c + k * N + k, k, N);
        mul(a + k * N + k, b + k * N + k, c + k * N + k, k, N);

        if (n & 1) {
            for (int i = 0; i < n; i++)
                for (int j = 0; j < n; j++)
                    for (int k = (i < n - 1 && j < n - 1) ? n - 1 : 0; k < n; k++)
                        c[i * N + j] += a[i * N + k] * b[k * N + j];
        }
    }
}
```

由于这里涉及许多其他因素，我们不打算对这个实现做基准测试，而只对外部存储模型中的理论性能做分析。

### 分析

算法的算术复杂度保持不变，因为递推式

$$
T(N) = 8 \cdot T(N/2) + \Theta(N^2)
$$

的解为 $T(N) = \Theta(N^3)$。

看起来我们还没「征服」什么，但让我们思考一下它的 I/O 复杂度：

$$
T(N) = \begin{cases}
O(\frac{N^2}{B}) & N \leq \sqrt M & \text{（我们只需读取它）} \\
8 \cdot T(N/2) + O(\frac{N^2}{B}) & \text{否则}
\end{cases}
$$

该递推式由 $O((\frac{N}{\sqrt M})^3)$ 个基本情况主导，也就是说总复杂度为

$$
T(N) = O\left(\frac{(\sqrt{M})^2}{B} \cdot \left(\frac{N}{\sqrt M}\right)^3\right) = O\left(\frac{N^3}{B\sqrt{M}}\right)
$$

这比单纯的 $O(\frac{N^3}{B})$ 更好，而且好得多。

### Strassen 算法

与 Karatsuba 算法的精神类似，矩阵乘法可以分解为 7 次大小为 $\frac{n}{2}$ 的矩阵乘法；主定理告诉我们，这种分治算法的时间复杂度为 $O(n^{\log_2 7}) \approx O(n^{2.81})$，在外部存储模型中也有类似的渐近复杂度。

这种被称为 Strassen 算法的技术同样把每个矩阵分成 4 块：

$$
\begin{pmatrix}
C_{11} & C_{12} \\
C_{21} & C_{22} \\
\end{pmatrix}
=\begin{pmatrix}
A_{11} & A_{12} \\
A_{21} & A_{22} \\
\end{pmatrix}
\begin{pmatrix}
B_{11} & B_{12} \\
B_{21} & B_{22} \\
\end{pmatrix}
$$

然后它计算 $\frac{N}{2} \times \frac{N}{2}$ 矩阵的中间乘积，并把它们组合起来得到矩阵 $C$：

$$
\begin{aligned}
   M_1 &= (A_{11} + A_{22})(B_{11} + B_{22})   & C_{11} &= M_1 + M_4 - M_5 + M_7
\\ M_2 &= (A_{21} + A_{22}) B_{11}             & C_{12} &= M_3 + M_5
\\ M_3 &= A_{11} (B_{21} - B_{22})             & C_{21} &= M_2 + M_4
\\ M_4 &= A_{22} (B_{21} - B_{11})             & C_{22} &= M_1 - M_2 + M_3 + M_6
\\ M_5 &= (A_{11} + A_{12}) B_{22}
\\ M_6 &= (A_{21} - A_{11}) (B_{11} + B_{12})
\\ M_7 &= (A_{12} - A_{22}) (B_{21} + B_{22})
\end{aligned}
$$

如果你愿意，可以通过简单的代入验证这些公式。

据我所知，主流优化线性代数库中没有一个使用 Strassen 算法，不过确实有一些对 2000 阶左右以上的矩阵高效的[原型实现](https://arxiv.org/pdf/1605.01078.pdf)。

这种技术已经并且实际上确实被多次扩展，通过考虑更多的子矩阵乘积来进一步降低渐近复杂度。截至 2020 年，当前的世界纪录是 $O(n^{2.3728596})$。你是否能在 $O(n^2)$ 甚至至少 $O(n^2 \log^k n)$ 时间内完成矩阵乘法，仍是一个开放问题。

## 延伸阅读

想获得扎实的理论视角，可以考虑阅读 Erik Demaine 的《[Cache-Oblivious Algorithms and Data Structures](https://erikdemaine.org/papers/BRICS2002/paper.pdf)》。