---
title: 求阶乘中某因数的幂次
authors:
- Максим Иванов
---

给两个数：n 和 k。要求计算因数 k 以多少次幂进入 n!，即求最大的 x，使 n! 被 k^x 整除。

k 为质数的情形
先看 k 为质数的情形。

把阶乘显式写出来：

 n! = 1\ 2\ 3\ \ldots\ (n-1)\ n 

注意这个乘积中每个第 k 项都被 k 整除，即给答案 +1；这样的项数是 \lfloor n/k \rfloor。

接着，这个数列中每个第 k^2 项被 k^2 整除，即再给答案 +1（考虑 k 的一次幂之前已经计入）；这样的项数是 \lfloor n/k^2 \rfloor。

依此类推，每个第 k^i 项给答案 +1，这样的项数是 \lfloor n/k^i \rfloor。

于是答案等于：

 \frac{n}{k} + \frac{n}{k^2} + \ldots + \frac{n}{k[...]

这个和当然不是无穷的，因为只有前大约 \log_k n 项非零。因此这种算法的复杂度是 O(\log_k n)。

实现：

int fact_pow (int n, int k) {
	int res = 0;
	while (n) {
		n /= k;
		res += n;
	}
	return res;
}
k 为合数的情形
这里不能直接套用同样的思路。

但我们可以分解 k，对它的每个质因数解决该问题，然后取各答案的最小值。

更形式化地说，设 k_i 是 k 的第 i 个因数，它按幂 p_i 进入 k。用上面的公式在 O (\log n) 内对 k_i 解问题；设得到答案 {\rm Ans}_i。那么对合数 k，答案是各量 {\rm Ans}_i / p_i 的最小值。

由于最简单的分解在 O (\sqrt{k}) 内完成，最终复杂度为 O (\sqrt{k})。
