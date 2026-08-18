---
title: 离散对数
authors:
- Максим Иванов
draft: true
---

离散对数问题是要对给定整数 a、b、m 解方程：

 a^x = b \pmod m, 

其中 a 与 m 互素（注：若不互素，下面算法不正确；不过推测可以修改使其仍工作）。

这里描述的是 Shanks 于 1971 年提出、运行在 O (\sqrt{m} \log m) 的算法，俗称 "baby-step-giant-step algorithm"。常也直接叫 "meet-in-the-middle" 算法（因为它是该技术的一个经典应用：「把问题对半切」）。

算法
于是我们解方程：

 a^x = b \pmod m, 

其中 a 与 m 互素。

变换方程。令

 x = np - q, 

其中 n 是预先选定的常数（如何根据 m 选取稍后会明白）。有时把 p 叫 "giant step"（因为它加一会让 x 立刻增加 n），相对地 q 叫 "baby step"。

显然任何 x（在 [0;m) 内——显然这个取值范围足够）都能这样表示，为此需要：

 p \in \left[ 1; \left\lceil \frac{m}{n} \right\rceil \right], \quad q \in [0; n]

方程变为：

 a^{np-q} = b \pmod m, 

利用 a 与 m 互素，得：

 a^{np} = b a^q \pmod m. 

要解原方程，需找相应的 p 和 q 使左右两边相等。换句话说，要解方程：

 f_1(p) = f_2(q). 

这个问题用 meet-in-the-middle 如下解。算法第一阶段：对所有自变量 p 算 f_1 的值并排序。第二阶段：枚举第二变量 q，算 f_2，用二分查找在预计算的 f_1 值中找它。

复杂度
先估计函数 f_1(p) 与 f_2(q) 的计算时间。二者都含幂运算，可用快速幂。于是都能在 O(\log m) 内算。

算法第一阶段含对每个可能的 p 算 f_1(p) 并排序，复杂度：

 O\left( \left\lceil \frac{m}{n} \right\rceil \log m \right)

第二阶段含对每个可能的 q 算 f_2(q) 并在 f_1 值数组中二分查找，复杂度：

 O\left( n \left( \log m + \log \left\lceil \frac{m}{n} \right\rceil \right) \right)

把两个复杂度相加，得到 \log m 乘以 n 与 m/n 之和，显然最小值在 n \approx m/n 处取得，即最优工作常数 n 应取：

 n \approx \sqrt{m}. 

于是算法复杂度为：

 O\left( \sqrt{m} ~ \log m \right). 

注。我们可以交换 f_1 与 f_2 的角色（即第一阶段算 f_2、第二阶段算 f_1），但容易看出结果不变，复杂度也不能这样改进。

实现
最简单的实现
函数 \rm powmod 做模 m 的快速幂，见快速幂。

函数 \rm solve 实际解问题，返回答案（[0;m) 内的数），准确说是一个答案。若无解返回 -1。

int powmod (int a, int b, int m) {
	int res = 1;
	while (b > 0)
		if (b & 1) {
			res = (res * a) % m;
			--b;
		}
		else {
			a = (a * a) % m;
			b >>= 1;
		}
	return res % m;
}
 
int solve (int a, int b, int m) {
	int n = (int) sqrt (m + .0) + 1;
	map<int,int> vals;
	for (int i=n; i>=1; --i)
		vals[ powmod (a, i * n, m) ] = i;
	for (int i=0; i<=n; ++i) {
		int cur = (powmod (a, i, m) * b) % m;
		if (vals.count(cur)) {
			int ans = vals[cur] * n - i;
			if (ans < m)
				return ans;
		}
	}
	return -1;
}
这里为方便，实现第一阶段时用了 "map"（红黑树）结构，对每个 f_1(i) 值存达到它的自变量 i。若同一值出现多次，存最小自变量。这样做是为了让第二阶段能找出 [0;m) 内的答案。

考虑到第一阶段自变量从 1 到 n、第二阶段自变量从 0 到 n 枚举，最终我们覆盖了所有可能答案，因为区间 [0; n^2] 包含 [0;m)。且答案不可能为负，而大于等于 m 的答案可以忽略——反正 [0;m) 内一定有对应答案。

若需要找离散对数的所有解，可把这个函数改造：把 "map" 换成能对一个自变量存多个值的结构（例如 "multimap"），并相应改第二阶段代码。

改进的实现
优化速度可以这样做。

第一，第二阶段里显然不需要快速幂。可以建一个变量，每次乘 a。

第二，同样可以去掉第一阶段的快速幂：只需一次算 a^n，然后不断乘它。

这样复杂度里仍有对数，但只是与 map<> 结构相关的对数（即算法术语里的排序与二分查找）——即 \sqrt{m} 的对数，实践中有明显加速。

int solve (int a, int b, int m) {
	int n = (int) sqrt (m + .0) + 1;
 
	int an = 1;
	for (int i=0; i<n; ++i)
		an = (an * a) % m;
 
	map<int,int> vals;
	for (int i=1, cur=an; i<=n; ++i) {
		if (!vals.count(cur))
			vals[cur] = i;
		cur = (cur * an) % m;
	}
 
	for (int i=0, cur=b; i<=n; ++i) {
		if (vals.count(cur)) {
			int ans = vals[cur] * n - i;
			if (ans < m)
				return ans;
		}
		cur = (cur * a) % m;
	}
	return -1;
}
最后，如果模 m 足够小，可以彻底去掉复杂度里的对数——用普通数组代替 map<>。

也可以想起哈希表：平均也 O(1)，整体复杂度 O (\sqrt{m})。
