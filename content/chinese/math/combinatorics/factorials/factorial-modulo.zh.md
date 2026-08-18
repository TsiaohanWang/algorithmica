---
title: 按模计算阶乘
authors:
- Максим Иванов
---

有时需要按某个质数模 p 计算复杂公式，其中可能含有阶乘。这里看模 p 相对较小的情形。显然，只有阶乘既出现在分子又出现在分母时才值得做这件事。确实，p! 及其后的阶乘按模 p 都化为零，但在分式中所有含 p 的因子可能约去，所得表达式按模 p 就不再为零。

形式化地说，任务如下。要求按质数模 p 计算 n!，同时不计入阶乘中所有为 p 的倍数因子。学会高效计算这样的阶乘后，我们就能快速计算各种组合公式（例如二项式系数）。

算法
把这个「修改版」阶乘显式写出来：

 n!_{\%p} = 
 = 1 \cdot 2 \cdot 3 \cdot \ldots \cdot (p-2) \cdo[...]
 \cdot (p^2-1) \cdot \underbrace{1}_{p^2} \cdot (p[...]
 = 1 \cdot 2 \cdot 3 \cdot \ldots \cdot (p-2) \cdo[...]
 \cdot 1 \cdot 2 \cdot \ldots \cdot (n\%p) \pmod p[...]

这样写可以看出，「修改版」阶乘分解成若干长度为 p 的块（最后一块可能更短），除最后一个元素外它们都相同：

 n!_{\%p} = \underbrace{ 1 \cdot 2 \cdot \ldots \c[...]
 \cdot \underbrace{ 1 \cdot 2 \cdot \ldots \cdot ([...]

块的公共部分容易算——就是 (p-1)!\ \rm{mod}\ p，可以用程序算，或用威尔逊（Wilson）定理直接得到 (p-1)!\ {\rm mod}\ p = p-1。要把所有块的公共部分相乘，需把所得值按模 p 取幂，可在 O(\log n) 次操作内完成（见快速幂；不过也可注意到我们实际上是在把负一取某个幂次，因此结果总是 1 或 p-1，取决于指数的奇偶性）。最后一块（不完整）的值也可单独用 O(p) 算出。剩下的只是每块最后一个元素，仔细看它们：

 n!_{\%p} = \underbrace{ \ldots \cdot 1 } \cdot \u[...]

于是我们又回到了「修改版」阶乘，但维度更小（有多少完整块，就是 \left\lfloor n / p \right\rfloor 个）。于是用 O(p) 次操作把 n!_{\%p} 的计算归结为 (n/p)!_{\%p}。展开这个递推，递归深度为 O (\log_p n)，最终算法复杂度为 O(p \log_p n)。

实现
实现时显然不必显式使用递归：由于递归是尾递归，很容易展开成循环。

int factmod (int n, int p) {
	int res = 1;
	while (n > 1) {
		res = (res * ((n/p) % 2 ? p-1 : 1)) % p;
		for (int i=2; i<=n%p; ++i)
			res = (res * i) % p;
		n /= p;
	}
	return res % p;
}
这个实现运行在 O(p \log_p n)。
