---
title: 阿达马变换
draft: true
---

## $xor$-卷积

如果有 $n = 2^k$，以及两个长度为 $n$ 的数组 $a$ 和 $b$，那么数组 $c$ 被称为 $a$ 和 $b$ 的 $xor$-卷积，如果 $$c\[i\] = \\sum_{j\\,xor\\,k=i}^{n - 1} a\[j\] \\cdot b\[k\]$$ 也就是说，取所有满足其按位 $xor$ 等于 $i$ 的 $j$ 和 $k$，并把所有这样的 $a\[j\] \\cdot b\[k\]$ 加到 $c\[i\]$ 上。

## 阿达马变换

如果有 $n = 2^k$ 和长度为 $n$ 的数组 $a$。那么数组 $b$ 被称为数组 $a$ 的阿达马变换，如果 $$b\[i\] = \\sum_{j=0}^{n - 1} a\[j\] \\cdot -1^{popcnt(i\\\&j)}$$ $popcnt(a)$ 是数字 $a$ 的二进制表示中 1 的个数。

也就是说，取所有的 $j$，对每个 $j$ 计算其与 $i$ 的按位与，统计结果 $i\\\&j$ 的二进制表示中 1 的个数：如果这个数是偶数，就把 $a\[j\]$ 加到 $b\[i\]$ 上，否则从 $b\[i\]$ 中减去。

把数组 $a$ 的阿达马变换记为 $Adamar(a)$。

阿达马变换可以从矩阵的角度来看。可以说我们把数组 $a$ 看作一个水平向量：$$\\begin{bmatrix}a_0 & a_1 & \\cdots & a_{n - 1}\\end{bmatrix}$$ 然后用一个由 $-1$ 和 $1$ 组成的矩阵去乘它，得到 $Adamar(a)$。这样的矩阵称为阿达马矩阵，我们把它记为 $M_{A(n)}$。

来试着找出这个矩阵。首先取一个全由 1 组成的 $n \\times n$ 矩阵。

$$\\begin{bmatrix} 1 & 1 & \\cdots & 1 \\\\ \\vdots & \\vdots &\\ddots &\\vdots \\\\ 1 & 1 &\\cdots & 1 \\end{bmatrix}$$

现在注意，如果我们取第 $y$ 行第 $x$ 列中的 1，把它替换成 $-1^{popcnt(x\\\&y)}$，就得到我们想要的东西。

接下来还需要用简洁的语言描述阿达马矩阵长什么样。我们通过更小的矩阵递归地展示它。

$n = 1$ 时的阿达马矩阵就是仅含一个 1 的矩阵。

现在来求 $n = 2^k$ 的阿达马矩阵。注意，如果 $x \< n / 2$ 且 $y \< n / $，那么 $(x + n / 2)\\\&y = x\\\&y$、$x\\&(y + n / 2) = x\\\&y$，而 $(x + n / 3)\\&(y + n / 2) = x\\\&y + n / 2$。于是如果把 $n$ 的阿达马矩阵分成 4 块，那么右上、左上、左下三块都相同，只有右下那一块等于它们中的每一块、再把其中的 1 换成 -1、-1 换成 1。

也就是说，阿达马矩阵的例子有：

$$\\begin{bmatrix} 1 & 1 \\\\ 1 & -1 \\\\ \\end{bmatrix}$$
$$\\begin{bmatrix} 1 & 1 & 1 & 1 \\\\ 1 & -1 & 1 & -1 \\\\ 1 & 1 & -1 & -1 \\\\ 1 & -1 & -1 & 1 \\\\ \\end{bmatrix}$$ 并且每个下一个矩阵都是上一个矩阵在水平方向重复 2 次、垂直方向重复 2 次（也就是总共 4 次），再把右下那一块乘以 $-1$。$$M_{A(n)} = \\begin{bmatrix} M_{A(n / 2)} & M_{A(n / 2)} \\\\ M_{A(n / 2)} & -1 \\cdot M_{A(n / 2)} \\\\ \\end{bmatrix}$$

于是阿达马变换可以写成如下形式：

$$Adamar(a) = \\begin{bmatrix}a_0 & a_1 & \\cdots & a_{n - 1}\\end{bmatrix} \\cdot M_{A(n)}$$

## 通过阿达马变换计算 $xor$-卷积

设 $c$ 是 $a$ 和 $b$ 的 $xor$-卷积，即

$$c\[i\] = \\sum_{j\\,xor\\,k=i}^{n - 1} a\[j\] \\cdot b\[k\]$$

现在对 $c$ 应用阿达马变换，得到

$$Amdamar(c)\[i\] = \\sum_{x=0}^{n - 1} c\[x\] \\cdot -1^{popcnt(i\\\&x)} = \\sum_{x=0}^{n - 1} \\left(\\sum_{y\\,xor\\,z=x}^{n - 1} a\[y\] \\cdot b\[z\]\\right) \\cdot -1^{popcnt(i\\\&x)}$$

接下来，每一对 $y$ 和 $z$ 只会出现在一个 $x$ 中，因为恰好存在一个数等于 $y\\,xor\\,z$。于是前面那一大堆式子等于：

$$\\sum_{y=0}^{n - 1} \\sum_{z=0}^{n - 1} a\[y\] \\cdot b\[z\] \\cdot -1^{popcnt(i\\&(y\\,xor\\,z))}$$

现在注意，$i\\&(y\\,xor\\,z) = (i\\\&y)xor(i\\\&z)$。于是 $popcnt(i\\&(y\\,xor\\,z)) = popcnt((i\\\&y)xor(i\\\&z))$。而 $popcnt(a\\,xor\\,b)$ 模 2 等于 $popcnt(a) = popcnt(b)$。于是 $-1^{popcnt(i\\&(y\\,xor\\,z))} = -1^{popcnt(i\\\&y)} \\cdot -1^{popcnt(i\\\&z)}$。那么前面那一大堆式子等于

$$\\sum_{y=0}^{n - 1} a\[y\] \\cdot -1^{popcnt(i\\\&y)} \\cdot \\sum_{z=0}^{n - 1} b\[y\] \\cdot -1^{popcnt(i\\\&z)} = Adamar(a)\[i\] \\cdot Adamar(b)\[i\]$$。

于是 $Adamar(c)\[i\] = Adamar(a)\[i\] \\cdot Adamar(b)\[i\]$。再由前面的结论可得 $$Adamar(c) = \\frac{Adamar(Adamar(a) \\cdot Adamar(b))}{n}$$。

因此，只要能快速完成阿达马变换，就能快速计算 $xor$-卷积。

[分类：讲义](Категория:Конспект "wikilink")