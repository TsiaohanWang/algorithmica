---
title: 费马小定理
---

**定理**。 对所有不被 $p$ 整除的 $a$，有 $a^p \equiv a \pmod p$。

**证明**。（对理解不重要，可跳过）

$$
\begin{aligned}
a^p &= (\underbrace{1+1+\ldots+1+1}_\text{$a$ 个})
\\  &= \sum_{x_1+x_2+\ldots+x_a = p} P(x_1, x_2, \ldots, x_a) & \text{(按定义展开)}
\\  &= \sum_{x_1+x_2+\ldots+x_a = p} \frac{p!}{x_1! x_2! \ldots x_a!} & \text{(哪些项不被 $p$ 整除？)}
\\  &\equiv P(p, 0, \ldots, 0) + \ldots + P(0, 0, \ldots, p) & \text{(其余项不能消掉分母中的 $p$)}
\\  &= a
\end{aligned}
$$

其中 $P(x_1, x_2, \ldots, x_n) = \frac{k}{\prod (x_i!)}$ 是多项式系数——即展开 $(a_1 + a_2 + \ldots + a_n)^k$ 时元素 $a_1^{x_1} a_2^{x_2} \ldots a_n^{x_n}$ 出现的次数。

现在把我们的结果「除」两次。

$$ a^p \equiv a \implies a^{p-1} \equiv 1 \implies a^{p-2} \equiv a^{-1} $$

于是 $a^{p-2}$ 表现得像 $a^{-1}$，这正是我们需要的。
可以用快速幂在 $O(\log p)$ 内算 $a^{p-2}$。

---

{{ 命题 |名称=费马小定理 |显示名称=1
|命题=设 $p$ 是质数，$a$ 是不被 $p$ 整除的整数。则 $a^{p - 1} \\equiv 1 \\mod p$。 |证明=考虑数 $a, 2a, 3a, ... ,(p - 1)a$。注意这组数含有从 1 到 $p - 1$ 的所有余数（证明留给读者作练习）。

把这组数相乘：左边保持原样，右边利用这组数含有 1 到 $p - 1$ 的所有余数这一事实。

$a \\cdot 2a \\cdot 3a \\dots \\cdot (p-1)a \\equiv 1 \\cdot 2 \\cdot 3 \\dots \\ \\cdot (p - 1) \\mod p$

$(p-1)\!a^{p-1} \\equiv (p-1)\! \\mod p$

由于 $p$ 是质数，它与 1 到 $p - 1$ 的任何数都互素，也就与 $(p - 1)\!$ 互素。因此可以约去等式两边的阶乘。得到：

$a^{p-1} \\equiv 1 \\mod p$。 }}

[分类：笔记](Категория:Конспект "wikilink") [分类：数论](Категория:Теория_чисел "wikilink")
