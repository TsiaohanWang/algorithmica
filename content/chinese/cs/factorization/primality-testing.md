---
title: 素性测试
authors:
- Максим Иванов
weight: 5
draft: true
---

BPSW 算法是一种素性测试。该算法以发明者姓氏命名：Robert Baillie、Carl Pomerance、John Selfridge、Samuel Wagstaff。算法于 1980 年提出。至今未找到任何反例，也未找到证明。

BPSW 算法已在所有 $10^{15}$ 以内的数上检验。此外，有人用基于椭圆曲线的素性测试程序 PRIMO（见 [6]）尝试找反例。程序运行三年未找到任何反例，据此 Martin 猜测不存在小于 $10^{10000}$ 的 BPSW 伪素数（伪素数——算法给出「质数」结果的合数）。同时，Carl Pomerance 于 1984 年给出启发式证明：存在无穷多个 BPSW 伪素数。

BPSW 算法复杂度为 O (log3(N)) 位操作。与 Miller–Rabin 等其他测试比，BPSW 通常慢 3–7 倍。

算法在实践中常用。看来许多商业数学软件包完全或部分依赖 BPSW 做素性检查。

简介
算法有多种实现，仅细节不同。我们的版本：

1. 做以 2 为底的 Miller–Rabin 测试。

2. 做强 Lucas–Selfridge 测试，用 Selfridge 参数的 Lucas 序列。

3. 仅当两个测试都返回「质数」才返回「质数」。

+0. 另外，可在算法开头加平凡因数检查（例如到 1000）。这能加快合数上的速度，但稍减慢质数上的算法。

于是 BPSW 基于：

1. （事实）Miller–Rabin 与 Lucas–Selfridge 测试若出错，只往一个方向：某些合数被认成质数。反方向从不犯错。

2. （假设）Miller–Rabin 与 Lucas–Selfridge 测试若出错，从不在同一个数上同时出错。

其实第二个假设似乎并不成立——下面给出 Pomerance 的启发式证明-反驳。不过实践中至今未找到伪素数，因此可权当第二假设成立。

本文算法实现
本文所有算法用 C++ 实现。所有程序只在 Microsoft C++ 8.0 SP1 (2005) 编译器上测试过，也应能在 g++ 编译。

算法用模板（templates）实现，既可用于内置数值类型，也可用于实现高精度的自定义类。

本文只给最核心的函数，辅助函数文本可在文末附录下载。这里只给这些函数头与注释：

//! 64 位数取绝对值
long long abs (long long n);
unsigned long long abs (unsigned long long n);

//! n 为偶数则返回 true
template <class T>
bool even (const T & n);

//! 把数除以 2
template <class T>
void bisect (T & n);

//! 把数乘以 2
template <class T>
void redouble (T & n);

//! n 是某质数的完全平方则返回 true
template <class T>
bool perfect_square (const T & n);

//! 求数的根，向下取整
template <class T>
T sq_root (const T & n);

//! 返回数中位数
template <class T>
unsigned bits_in_number (T n);

//! 返回数第 k 位（从零编号）
template <class T>
bool test_bit (const T & n, unsigned k);

//! 做 a *= b (mod n)
template <class T>
void mulmod (T & a, T b, const T & n);

//! 算 a^k (mod n)
template <class T, class T2>
T powmod (T a, T2 k, const T & n);

//! 把数 n 化成 q*2^p 形式
template <class T>
void transform_num (T n, T & p, T & q);

//! 欧几里得算法
template <class T, class T2>
T gcd (const T & a, const T2 & b);

//! 算 jacobi(a,b) ——雅可比符号
template <class T>
T jacobi (T a, T b)

//! 算 pi(b) 个前质数。返回质数向量，pi 存 pi(b)
template <class T, class T2>
const std::vector & get_primes (const T & b, T2 & pi);

//! 平凡素性检查：枚举到 m 的所有因数。
//! 结果：1 若 n 确定质数，p 为找到的因数，0 若未知
template <class T, class T2>
T2 prime_div_trivial (const T & n, T2 m);
Miller–Rabin 测试
不展开讲 Miller–Rabin，它在许多来源（含俄文）都有描述（例如见 [5]）。

只提其速度为 O (log3(N)) 位操作，并给现成实现：

template <class T, class T2>
bool miller_rabin (T n, T2 b)
{

	// 先查平凡情形
	if (n == 2)
		return true;
	if (n < 2 || even (n))
		return false;

	// 检查 n 与 b 互素（否则出错）
	// 若不互素，则要么 n 非质，要么需增大 b
	if (b < 2)
		b = 2;
	for (T g; (g = gcd (n, b)) != 1; ++b)
		if (n > g)
			return false;

	// 分解 n-1 = q*2^p
	T n_1 = n;
	--n_1;
	T p, q;
	transform_num (n_1, p, q);

	// 算 b^q mod n；若等于 1 或 n-1，则 n 为质数（或伪素数）
	T rem = powmod (T(b), q, n);
	if (rem == 1 || rem == n_1)
		return true;

	// 现在算 b^2q, b^4q, ... , b^((n-1)/2)
	// 若其中某个等于 n-1，则 n 为质数（或伪素数）
	for (T i=1; i<p; i++)
	{
		mulmod (rem, rem, n);
		if (rem == n_1)
			return true;
	}

	return false;

}
强 Lucas–Selfridge 测试
强 Lucas–Selfridge 测试由两部分：Selfridge 算法（算某参数）与带该参数的强 Lucas 算法。

Selfridge 算法
在序列 5, -7, 9, -11, 13, ... 中找第一个使 J (D, N) = -1 且 gcd (D, N) = 1 的数 D，其中 J(x,y) 是雅可比符号。

Selfridge 参数是 P = 1 和 Q = (1 - D) / 4。

注意，完全平方数没有 Selfridge 参数。确实，若数是完全平方，D 的枚举会到 sqrt(N)，此处发现 gcd (D, N) > 1，即发现 N 为合数。

此外，对偶数和 1，Selfridge 参数会算错；不过检查这些情形不难。

因此算法开始前应确认 N 是大于 2 的奇数、不是完全平方；否则（任一条件不满足）立即以「合数」退出。

最后注意，若某数 N 的 D 太大，算法在计算上不可用。虽然实践中没见过（4 字节数已足够），但不该排除此可能。例如区间 [1; 106] 上 max(D) = 47，区间 [1019; 1019+106] 上 max(D) = 67。而且 Baillie 与 Wagstaff 于 1980 年分析证明了这个观察（见 Ribenboim, 1995/96, 第 142 页）。

强 Lucas 算法
Lucas 算法参数是数 D、P、Q，满足 D = P2 - 4*Q ? 0 且 P > 0。

（不难发现 Selfridge 算法算出的参数满足这些条件。）

Lucas 序列是序列 Uk 和 Vk，定义如下：

U0 = 0
U1 = 1
Uk = P Uk-1 - Q Uk-2
V0 = 2
V1 = P
Vk = P Vk-1 - Q Vk-2
再设 M = N - J (D, N)。

若 N 为质数且 gcd (N, Q) = 1，则：

UM = 0 (mod N)
特别地，当参数 D、P、Q 由 Selfridge 算法算出时：

UN+1 = 0 (mod N)
逆命题一般不成立。但该算法下伪素数并不多，这正构成 Lucas 算法基础。

于是 Lucas 算法就是算 UM 并与零比较。

还需找加速算 UK 的办法，否则算法没有实际意义。

有：

Uk = (ak - bk) / (a - b),
Vk = ak + bk,
其中 a、b 是二次方程 x2 - P x + Q = 0 的两个不同根。

下面等式可初等证明：

U2k = Uk Vk (mod N)
V2k = Vk2 - 2 Qk (mod N)
若把 M = E 2T（E 为奇数），易得：

UM = UE VE V2E V4E ... V2T-2E V2T-1E = 0 (mod N),
且至少一个因子模 N 为零。

显然，只需算 UE 和 VE，后续因子 V2E V4E ... V2T-2E V2T-1E 都可由它们得到。

剩下学会对奇数 E 快速算 UE 与 VE。

先看 Lucas 序列项加法的公式：

Ui+j = (Ui Vj + Uj Vi) / 2 (mod N)
Vi+j = (Vi Vj + D Ui Uj) / 2 (mod N)
注意除法在模 N 的域中进行。

这些公式证明很简单，这里略去。

有了 Lucas 序列项加法与加倍公式，就明白如何加速算 UE 与 VE。

确实，考虑数 E 的二进制表示。初始把结果 UE 与 VE 设为 U1 与 V1。从低到高遍历 E 的所有位，只跳过第一位（序列首项）。对第 i 位，用加倍公式由前一项算 U2 i 与 V2 i。另外，若当前第 i 位为 1，用加法公式把当前 U2 i 与 V2 i 加到答案。算法在 O (log(E)) 内结束，得到所求 UE 与 VE。

若 UE 或 VE 模 N 为零，则 N 为质数（或伪素数）。若二者都非零，则算 V2E, V4E, ... V2T-2E, V2T-1E。若其中至少一个模 N 同余零，则 N 为质数（或伪素数）。否则 N 为合数。

Selfridge 算法的讨论
现在看完 Lucas 算法，可更详细看它的参数 D,P,Q，Selfridge 算法正是它们的求法之一。

回忆参数基本要求：

P > 0,
D = P2 - 4*Q ? 0.
继续研究这些参数。

D 不应是 (mod N) 下的完全平方。

确实，否则有：

D = b2，从而 J(D,N) = 1，P = b + 2，Q = b + 1，从而 Un-1 = (Qn-1 - 1) / (Q - 1)。

即若 D 是完全平方，Lucas 算法几乎变成普通概率测试。

避免这种情况最好方法之一是要求 J(D,N) = -1。

例如，可选序列 5, -7, 9, -11, 13, ... 中第一个满足 J(D,N) = -1 的数 D。再设 P = 1。则 Q = (1 - D) / 4。此方法由 Selfridge 提出。

不过也有其他选 D 的方法。可从序列 5, 9, 13, 17, 21, ... 中选。再设 P 为超过 sqrt(D) 的最小奇数。则 Q = (P2 - D) / 4。

显然，Lucas 参数的具体求法影响结果——不同选法伪素数可能不同。实践证明 Selfridge 提出的算法很成功：所有 Lucas–Selfridge 伪素数都不是 Miller–Rabin 伪素数，至少没找到反例。

强 Lucas–Selfridge 算法的实现
剩下只需实现算法：

template <class T, class T2>
bool lucas_selfridge (const T & n, T2 unused)
{

	// 先查平凡情形
	if (n == 2)
		return true;
	if (n < 2 || even (n))
		return false;

	// 检查 n 不是完全平方，否则算法出错
	if (perfect_square (n))
		return false;

	// Selfridge 算法：找第一个满足下面条件的数 d：
	// jacobi(d,n)=-1 且属于序列 { 5,-7,9,-11,13,... }
	T2 dd;
	for (T2 d_abs = 5, d_sign = 1; ; d_sign = -d_sign, ++++d_abs)
	{
		dd = d_abs * d_sign;
		T g = gcd (n, d_abs);
		if (1 < g && g < n)
			// 找到因数 - d_abs
			return false;
		if (jacobi (T(dd), n) == -1)
			break;
	}

	// Selfridge 参数
	T2
		p = 1,
		q = (p*p - dd) / 4;
	
	// 分解 n+1 = d*2^s
	T n_1 = n;
	++n_1;
	T s, d;
	transform_num (n_1, s, d);

	// Lucas 算法
	T
		u = 1,
		v = p,
		u2m = 1,
		v2m = p,
		qm = q,
		qm2 = q*2,
		qkd = q;
	for (unsigned bit = 1, bits = bits_in_number(d); bit < bits; bit++)
	{
		mulmod (u2m, v2m, n);
		mulmod (v2m, v2m, n);
		while (v2m < qm2)
			v2m += n;
		v2m -= qm2;
		mulmod (qm, qm, n);
		qm2 = qm;
		redouble (qm2);
		if (test_bit (d, bit))
		{
			T t1, t2;
			t1 = u2m;
			mulmod (t1, v, n);
			t2 = v2m;
			mulmod (t2, u, n);
			
			T t3, t4;
			t3 = v2m;
			mulmod (t3, v, n);
			t4 = u2m;
			mulmod (t4, u, n);
			mulmod (t4, (T)dd, n);

			u = t1 + t2;
			if (!even (u))
				u += n;
			bisect (u);
			u %= n;

			v = t3 + t4;
			if (!even (v))
				v += n;
			bisect (v);
			v %= n;
			mulmod (qkd, qm, n);
		}
	}

	// 确定为质数（或伪素数）
	if (u == 0 || v == 0)
		return true;

	// 补算剩余项
	T qkd2 = qkd;
	redouble (qkd2);
	for (T2 r = 1; r < s; ++r)
	{
		mulmod (v, v, n);
		v -= qkd2;
		if (v < 0) v += n;
		if (v < 0) v += n;
		if (v >= n) v -= n;
		if (v >= n) v -= n;
		if (v == 0)
			return true;
		if (r < s-1)
		{
			mulmod (qkd, qkd, n);
			qkd2 = qkd;
			redouble (qkd2);
		}
	}

	return false;

}
BPSW 代码
剩下只需组合三个测试的结果：小平凡因数检查、Miller–Rabin 测试、强 Lucas–Selfridge 测试。

template <class T>
bool baillie_pomerance_selfridge_wagstaff (T n)
{

	// 先检查平凡因数——例如到 29
	int div = prime_div_trivial (n, 29);
	if (div == 1)
		return true;
