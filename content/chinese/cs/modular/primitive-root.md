---
title: 原根
authors:
- Максим Иванов
draft: true
---

定义
模 n 的原根（primitive root modulo n）是这样的数 g：它的所有幂模 n 遍历所有与 n 互素的数。数学上这样表述：如果 g 是模 n 的原根，那么对任意满足 {\rm gcd}(a,n)=1 的整数 a，都存在整数 k，使 g^k \equiv a \pmod{n}。

特别地，对素数 n，原根的幂遍历 1 到 n-1 的所有数。

存在性
模 n 的原根存在当且仅当 n 是某个奇素数的幂，或是某个素数的幂的两倍，以及 n=1、n=2、n=4 的情形。

这个定理（由高斯于 1801 年完整证明）在此不证。

与欧拉函数的关系
设 g 是模 n 的原根。那么可以证明使 g^k \equiv 1 \pmod{n} 的最小的数 k（即 g 的阶 multiplicative order）等于 \phi(n)。而且反过来也成立，这个事实将用于下面的原根算法。

此外，如果模 n 至少有一个原根，那么共有 \phi( \phi(n) ) 个（因为一个有 k 个元素的循环群有 \phi(k) 个生成元）。

求原根的算法
朴素算法对每个测试值 g 都要花 O(n) 时间算它的所有幂并检查它们是否互异。这太慢了，下面用数论中几个已知定理得到更快的算法。

上面给出定理：如果使 g^k \equiv 1 \pmod{n} 的最小数 k（即 g 的阶）等于 \phi(n)，那么 g 是原根。由于对任何与 n 互素的数 a 有欧拉定理（a^{\phi(n)} \equiv 1 \pmod{n}），要检查 g 是否为原根，只需检查对所有小于 \phi(n) 的 d 有 g^d \not\equiv 1 \pmod{n}。但这还是太慢。

由拉格朗日定理，任何数模 n 的阶都是 \phi(n) 的因数。因此只需检查对所有真因数 d\ |\ \phi(n) 有 g^d \not\equiv 1 \pmod{n}。这已经快得多，但还能进一步。

把 \phi(n) = p_1^{a_1} \ldots p_s^{a_s} 分解。证明在前面的算法中只需把形如 \frac{ \phi(n) }{ p_i } 的数作为 d。确实，设 d 是 \phi(n) 的任意真因数。显然存在某个 j 使 d\ |\ \frac{ \phi(n) }{ p_j }，即 d \cdot k = \frac{ \phi(n) }{ p_j }。但如果 g^d \equiv 1 \pmod{n}，就会得到：

 g^{\frac{ \phi(n) }{ p_j }} \equiv g^{d \cdot k} [...]

即仍然会在形如 \frac{ \phi(n) }{ p_i } 的数中找到一个不满足条件的，证毕。
因此求原根的算法如下。求 \phi(n) 并分解它。然后枚举所有数 g = 1 \ldots n，对每个算所有 g^{ \frac{ \phi(n) }{ p_i } } \pmod{n}。如果对当前 g 所有这些数都不等于 1，那么这个 g 就是所求的原根。

算法运行时间（假设 \phi(n) 有 O \left( \log \phi(n) \right) 个因数，且幂用二进制快速幂算，即 O(\log n)）为 O \left( {\rm Ans} \cdot \log \phi(n) \cdot \log n \right) 加上分解 \phi(n) 的时间，其中 \rm Ans 是结果，即所求原根的值。

关于原根随 n 增长的速率，只有近似估计。已知原根是相对较小的量。一个著名估计是 Shoup 的估计：在黎曼猜想成立的假设下，原根是 O (\log^6 n)。

实现
函数 powmod() 做二进制模幂，函数 generator (int p) 求素数模 p 的原根（这里 \phi(n) 的分解用最简单的 O( \sqrt{ \phi(n) } ) 算法）。

要让这个函数适用于任意 p，只需加算变量 phi 中的欧拉函数，并筛掉与 n 不互素的 res。

int powmod (int a, int b, int p) {
	int res = 1;
	while (b)
		if (b & 1)
			res = int (res * 1ll * a % p),  --b;
		else
			a = int (a * 1ll * a % p),  b >>= 1;
	return res;
}
 
int generator (int p) {
	vector<int> fact;
	int phi = p-1,  n = phi;
	for (int i=2; i*i<=n; ++i)
		if (n % i == 0) {
			fact.push_back (i);
			while (n % i == 0)
				n /= i;
		}
	if (n > 1)
		fact.push_back (n);
 
	for (int res=2; res<=p; ++res) {
		bool ok = true;
		for (size_t i=0; i<fact.size() && ok; ++i)
			ok &= powmod (res, phi / fact[i], p) != 1;
		if (ok)  return res;
	}
	return -1;
}
