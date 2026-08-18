---
title: 离散开方
authors:
- Максим Иванов
draft: true
---

离散开方问题（与离散对数问题类似）描述如下。给定 n（n 为质数）、a、k，要求找出所有满足条件的 x：

 x^k \equiv a \pmod{n} 

解法算法
我们通过把问题归结为离散对数问题来解。

为此应用模 n 原根的概念。设 g 是模 n 的原根（因 n 为质数，故存在）。求它可以按相应文章描述，在 O( {\rm Ans} \cdot \log \phi(n) \cdot \log n) = O( {\rm Ans} \cdot \log^2 n) 内完成，加上分解 \phi(n) 的时间。

先丢掉 a=0 的情形——此时立即得到答案 x=0。

由于本情形（n 为质数）下 1 到 n-1 的任何数都能表示成原根的幂，离散开方问题可以表示为：

 {\left( g^y \right)}^k \equiv a \pmod{n} 

其中
 x \equiv g^y \pmod{n} 

平凡变换得：
 {\left( g^k \right)}^y \equiv a \pmod{n} 

这里待求量是 y，于是我们回到了纯粹的离散对数问题。这个问题可以用 Shanks 的 baby-step-giant-step 算法在 O( \sqrt{n} \log n ) 内解决，即求出这个方程的一个解 y_0（或发现该方程无解）。
设我们找到某个解 y_0，那么离散开方问题的一个解是 x_0 = g^{y_0} \pmod{n}。

已知一个解求所有解
为完整解决问题，需要学会根据一个找到的 x_0 = g^{y_0} \pmod{n} 求出其余所有解。

为此回想：原根的阶总是 \phi(n)（见原根一文），即使 g 的某次幂为 1 的最小幂次是 \phi(n)。因此在指数上加 \phi(n) 的倍数不改变结果：

 x^k \equiv g^{ y_0 \cdot k + l \cdot \phi(n) } \e[...]

由此所有解形如：
 x = g^{ y_0 + \frac{ l \cdot \phi(n) }{ k } } \pm[...]

其中 l 选为使分数 \frac{ l \cdot \phi(n) }{ k } 为整数。要使分数为整数，分子须是 \phi(n) 与 k 的最小公倍数的倍数，由此（回想两个数的最小公倍数 {\rm lcm}(a,b) = \frac{ a \cdot b }{ {\rm gcd}(a,b) }），得：
 x = g^{ y_0 + i \frac{ \phi(n) }{ {\rm gcd}(k,\ph[...]

这是最终方便的公式，给出离散开方问题所有解的一般形式。
实现
给出完整实现，包括求原根、离散对数、求并输出所有解。

int gcd (int a, int b) {
	return a ? gcd (b%a, a) : b;
}
 
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
 
int main() {
 
	int n, k, a;
	cin >> n >> k >> a;
	if (a == 0) {
		puts ("1\n0");
		return 0;
	}
 
	int g = generator (n);
 
	int sq = (int) sqrt (n + .0) + 1;
	vector < pair<int,int> > dec (sq);
	for (int i=1; i<=sq; ++i)
		dec[i-1] = make_pair (powmod (g, int (i * sq * 1ll * k % (n - 1)), n), i);
	sort (dec.begin(), dec.end());
	int any_ans = -1;
	for (int i=0; i<sq; ++i) {
		int my = int (powmod (g, int (i * 1ll * k % (n - 1)), n) * 1ll * a % n);
		vector < pair<int,int> >::iterator it =
			lower_bound (dec.begin(), dec.end(), make_pair (my, 0));
		if (it != dec.end() && it->first == my) {
			any_ans = it->second * sq - i;
			break;
		}
	}
	if (any_ans == -1) {
		puts ("0");
		return 0;
	}
 
	int delta = (n-1) / gcd (k, n-1);
	vector<int> ans;
	for (int cur=any_ans%delta; cur<n-1; cur+=delta)
		ans.push_back (powmod (g, cur, n));
	sort (ans.begin(), ans.end());
	printf ("%d\n", ans.size());
	for (size_t i=0; i<ans.size(); ++i)
		printf ("%d ", ans[i]);
 
}
