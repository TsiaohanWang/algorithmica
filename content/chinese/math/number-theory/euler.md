---
title: 欧拉函数
authors:
- Максим Иванов
---

定义
欧拉函数 \phi (n)（有时记作 \varphi(n) 或 {\it phi}(n)）是从 1 到 n 中与 n 互质的数的个数。换言之，它是区间 [1; n] 中与 n 的最大公约数为 1 的数的个数。

该函数的头几个值（OEIS 百科中的 A000010）：

 \phi (1)=1, 
 \phi (2)=1, 
 \phi (3)=2, 
 \phi (4)=2, 
 \phi (5)=4. 

性质
欧拉函数下面三个简单性质，足以让我们学会对任意数计算它：

如果 p 是质数，则 \phi (p)=p-1。
（这是显然的，因为除了 p 本身以外，任何数与 p 都互质。）

如果 p 是质数，a 是自然数，则 \phi (p^a)=p^a-p^{a-1}。
（因为与 p^a 不互质的只有形如 pk (k \in \mathcal{N}) 的数，这样的数共有 p^a / p = p^{a-1} 个。）

如果 a 与 b 互质，则 \phi(ab) = \phi(a) \phi(b)（欧拉函数的“可乘性”）。
（这一事实可由中国剩余定理推出。考察任意数 z \le ab。记 x 和 y 分别为 z 除以 a 和 b 的余数。那么 z 与 ab 互质当且仅当 z 分别与 a 和 b 互质，即 x 与 a 互质且 y 与 b 互质。应用中国剩余定理可知，任意一对数 x 和 y (x \le a, ~ y \le b) 都一一对应于一个数 z (z \le ab)，由此完成证明。）

由此，可以通过 \it n 的分解（把 n 分解为质因数）求出任意 \it n 的欧拉函数：

如果

 n = p_1^{a_1} \cdot p_2^{a_2} \cdot \ldots \cdot [...]

（其中所有 p_i 均为质数），则

 \phi(n) = \phi(p_1^{a_1}) \cdot \phi(p_2^{a_2}) \[...]
 = (p_1^{a_1} - p_1^{a_1-1}) \cdot (p_2^{a_2} - p_[...]
 = n \cdot \left( 1-{1\over p_1} \right) \cdot \le[...]

实现
下面是最简单的代码，用朴素方法在 O (\sqrt n) 时间内分解质因数并求出欧拉函数：

int phi (int n) {
	int result = n;
	for (int i=2; i*i<=n; ++i)
		if (n % i == 0) {
			while (n % i == 0)
				n /= i;
			result -= result / i;
		}
	if (n > 1)
		result -= result / n;
	return result;
}
计算欧拉函数的关键在于求出 n 的分解。这可以在远小于 O(\sqrt{n}) 的时间内完成：参见高效分解算法。

欧拉函数的应用
欧拉函数最著名也最重要的性质由欧拉定理给出：

 a^{\phi(m)} \equiv 1 \pmod m, 

其中 \it a 与 \it m 互质。
当 \it m 为质数时，欧拉定理即化为所谓的费马小定理：

 a^{m-1} \equiv 1  \pmod m 

欧拉定理在实际应用中相当常见，例如，参见模域中的逆元。