---
title: 生日悖论
---

设 $f(n, d)$ 是 $n$ 人群体中没有任何两人生日相同的概率。假设生日在 1 到 $d$ 之间独立均匀分布。

$$
f(n, d) = (1-\frac{1}{d}) \times (1-\frac{2}{d}) \times ... \times (1-\frac{n-1}{d})
$$

尝试估计 $f$：

$$
\begin{aligned}
    e^x & = 1 + x + \frac{x^2}{2!} + \ldots & \text{(指数的泰勒级数)}
\\\ & \simeq 1 + x & \text{(对 $|x| \ll 1$ 的近似)}
\\\ e^{-\frac{n}{d}} & \simeq 1 - \frac{n}{d} & \text{(代入 $\frac{n}{d} \ll 1$)}
\\\ f(n, d) & \simeq e^{-\frac{1}{d}} \times e^{-\frac{2}{d}} \times \ldots \times e^{-\frac{n-1}{d}} &
\\\ & = e^{-\frac{n(n-1)}{2d}} &
\\\ & \simeq e^{-\frac{n^2}{2d}} &
\end{aligned}
$$

由公式可见，概率 $\frac{1}{2}$ 在 $n \approx \sqrt{d}$ 时达到，且在该点变化很快。

**推论**。需要往多重集中加入 $O(\sqrt{n})$ 个从 1 到 $n$ 的随机数，才会出现两个相同的数。
