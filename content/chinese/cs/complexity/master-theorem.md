---
title: 主定理
weight: 3
---

本文我们证明一大类「分治」算法复杂度的重要定理。在这类算法中，大小为 $n$ 的问题被分成 $a$ 个大小为 $b$ 分之一的问题，并用 $\Theta(n^c)$ 的「合并」处理。

**主定理**。 设给定递推式：

$$
T(n) = \begin{cases}
a T(\frac{n}{b}) + \Theta(n^c), & n > n_0
\\ \Theta(1), & n \leq n_0
\end{cases}
$$

那么：

* **A.** 若 $c > \log_b a$，则 $T(n) = \Theta(n^c)$。
* **B.** 若 $c = \log_b a$，则 $T(n) = \Theta(n^c \log n)$。
* **C.** 若 $c < \log_b a$，则 $T(n) = \Theta(n^{\log_b a})$。

---

![递归树](../img/divide-and-conquer.png)

---

**证明**。 考虑这个递推式的「递归树」。它有 $\log_b n$ 层。第 $k$ 层有 $a^k$ 个顶点，每个耗费 $\left(\frac{n}{b^k}\right)^c$ 次操作。把所有层上所有顶点的值加起来：

$$
T(n) = \sum_{k=0}^{\log_b n} a^k \left(\frac{n}{b^k}\right)^c = n^c \sum_{k=0}^{\log_b n} \left(\frac{a}{b^c}\right)^k
$$

**A.** 若 $c > \log_b a$，则 $\sum (\frac{a}{b^с})^k$ 是递减等比数列的和，它与 $n$ 无关，只是某个常数。因此 $T(n) = \Theta(n^c)$。

**B.** 若 $c = \log_b a$，则

$$
T(n) = n^c \sum_{k=0}^{\log_b n} \left(\frac{a}{b^c}\right)^k = n^c \sum_{k=0}^{\log_b n} 1^k = \Theta(n^c \log_b n)
$$

**C.** 若 $c < \log_b a$，则由于等比数列的和渐近等价于它的首项（最大项），

$$
T(n) = n^c \sum_{k=0}^{\log_b n} \left(\frac{a}{b^c}\right)^k = \Theta\left(n^c \left(\frac{a}{b^c}\right)^{\log_b n}\right) = \Theta\left(n^c \cdot \frac{a^{\log_b n}}{n^c}\right) = \Theta(a^{\log_b n}) = \Theta(n^{\log_b a})
$$

**注记**。 对于更精确的「合并」复杂度估计，定理不提供任何信息。例如，如果合并需要 $\Theta(n \log n)$ 且问题每次分成两部分，那么复杂度为：

$$
\sum_{k=0}^{\log n} n \log \frac{n}{2^k}
= \sum_{k=0}^{\log n} n (\log n - k)
= n \sum_{k=0}^{\log n} k
= \Theta (n \log^2 n)
$$

同时这个递推式不符合定理的条件。只能得到不精确的界 $\Omega (n \log n)$ 和 $O(n^{1+\varepsilon})$，分别代入 $c = 1$ 和 $c = 1 + \varepsilon$ 得到。注意，无论 $\varepsilon$ 多小，$n \log n$ 和 $n \log^2 n$ 都渐近小于 $n^{1+\varepsilon}$。
