---
title: 用多项式逼近函数
---

1.  假设有一个一元函数 $f(x)$。

2.  我们已知它在某个点集（称为**训练集**）上的值，带有一定的偏差（噪声）$\varepsilon(x)$。

3.  想要学会（至少近似地）恢复这个函数。

我们要找一组系数 $(\overline a_0, \overline a_1, \dots, \overline a_n)$，「逼近」原函数。设
$$P(x) = \overline a_0 + \overline a_1 x + \overline a_2 x^2 + \dots + \overline a_n x^n \approx f(x)$$

由于训练集的值并非完美地逼近原函数，我们无法精确确定所求的系数集合。

这个问题引出新定义。引入新函数 $L(P)$，用它判断我们的「模型」$P(x)$ 逼近原函数 $f(x)$ 有多好。

把 $L(P)$ 称为**误差函数**或**损失函数**。我们认为 $L(P)$ 越小，模型逼近 $f(x)$ 越好。

于是，最小化 $L(P)$ 就能得到 $f(x)$ 的最佳逼近。

看最常用的损失函数：
$$L(P) = \frac{1}{n}\sum^n_{i=0} (P(x_i) - f(x_i))^2 \hspace{10pt} \text{--- MSE}$$
$$L(P) = \sqrt{\frac{1}{n}\sum^n_{i=0} (P(x_i) - f(x_i))^2} \hspace{10pt} \text{--- RMSE}$$
$$L(P) = \frac{1}{n}\sum^n_{i=0} |P(x_i) - f(x_i)| \hspace{10pt} \text{--- L1 loss}$$
