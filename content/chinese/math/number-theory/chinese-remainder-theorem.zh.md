---
title: 中国剩余定理
authors:
- Максим Иванов
---

表述
在现代表述中，该定理内容如下：

设 p = p_1 \cdot p_2 \cdot \ldots \cdot p_k，其中 p_i 为两两互质的数。

把任意数 a (0 \le a < p) 与元组 (a_1, \ldots, a_k) 对应，其中 a_i \equiv a \pmod {p_i}：

 a \Longleftrightarrow (a_1, \ldots, a_k). 

那么这一对应（数与元组之间）是一一对应的。而且，对数 a 进行的运算可以等价地改为对相应元组进行——即对每个分量独立地进行同样的运算。

也就是说，如果

 a \Longleftrightarrow \Big( a_1, \ldots, a_k \Big[...]
 b \Longleftrightarrow \Big( b_1, \ldots, b_k \Big[...]

那么成立：

 {(a+b) \pmod p} \Longleftrightarrow \Big( {(a_1+b[...]
 {(a-b) \pmod p} \Longleftrightarrow \Big( {(a_1-b[...]
 {(a \cdot b) \pmod p} \Longleftrightarrow \Big( {[...]

该定理最初由中国古代数学家孙子（Sun Tzu）于公元 100 年前后证明。他具体证明了在特殊情形下，求解模方程组的等价性可以归结为求解一个模方程（见下文推论 2）。

推论 1
模方程组：

 \cases{
{x \equiv a_1 \pmod {p_1}}, \cr
\ldots,[...]

在模 p 下有唯一解。

（与上文相同，p = p_1 \cdot \ldots \cdot p_k，p_i 两两互质，而 a_1, \ldots, a_k 为任意整数集合）

推论 2
推论给出了模方程组与对应单个模方程之间的联系：

方程：

 x \equiv a \pmod p 

等价于方程组：

 \cases{
{x \equiv a \pmod {p_1}}, \cr
\ldots, \[...]

（与上文相同，这里假设 p = p_1 \cdot \ldots \cdot p_k，p_i 两两互质，而 a 为任意整数）

Garner 算法
由中国剩余定理可知，对数的运算可以替换为对元组的运算。回忆一下，每个数 a 对应一个元组 (a_1, \ldots, a_k)，其中：

 { a_i \equiv a \pmod {p_i} } . 

这在实际中有广泛的应用（除了直接用于按各模的余数还原数之外），因为这样一来，我们可以把大整数运算替换为对“短”数数组的运算。例如，1000 个元素的数组足以表示约 3000 位的数（如果把前 1000 个质数选作 p_i）；如果选接近十亿的质数作 p_i，则足以表示约 9000 位的数。但当然，这时要会按元组还原数 a。由推论 1 可知，这样的还原是可能的，而且是唯一的（在 0 \le a < p_1 \cdot p_2 \cdot \ldots \cdot p_k 的条件下）。Garner 算法正是能够相当高效地完成这一还原的算法。

寻找形如以下形式的解：

 a = x_1 + x_2 \cdot p_1 + x_3 \cdot p_1 \cdot p_2[...]

即以 p_1, p_2, \ldots, p_k 为位权的混合进制表示。

记 r_{ij} (i=1 \ldots k-1, j=i+1 \ldots k) 为 p_i 在模 p_j 下的逆元（模环中求逆元的做法参见此处：

 r_{ij} = (p_i) ^ {-1} \pmod {p_j} . 

把 a 的混合进制表达式代入方程组的第一式，得：

 a_1 \equiv x_1. 

再把该表达式代入第二式：

 a_2 \equiv x_1 + x_2 \cdot p_1 \pmod {p_2}. 

两边减去 x_1 并除以 p_1，整理该式：

 a_2 - x_1 \equiv x_2 \cdot p_1 \pmod {p_2}; 
 (a_2 - x_1) \cdot r_{12} \equiv x_2 \pmod {p_2}; 
 x_2 \equiv (a_2 - x_1) \cdot r_{12} \pmod {p_2}. 

代入第三式，类似地可得：

 a_3 \equiv { x_1 + x_2 \cdot p_1 + x_3 \cdot p_1 [...]
 (a_3 - x_1) \cdot r_{13} \equiv x_2 + x_3 \cdot p[...]
 ((a_3 - x_1) \cdot r_{13} - x_2) \cdot r_{23} \eq[...]
 x_3 \equiv ((a_3 - x_1) \cdot r_{13} - x_2) \cdot[...]

其中的规律已经相当明显，用代码来表达最为简洁：

for (int i=0; i<k; ++i) {
	x[i] = a[i];
	for (int j=0; j<i; ++j) {
		x[i] = r[j][i] * (x[i] - x[j]);
 
		x[i] = x[i] % p[i];
		if (x[i] < 0)  x[i] += p[i];
	}
}
这样，我们就学会了在 O (k^2) 时间内求出系数 x_i，而答案本身——数 a——可按公式还原：

 a = x_1 + x_2 \cdot p_1 + x_3 \cdot p_1 \cdot p_2[...]

值得指出的是，实际中几乎总是需要用大整数算术（big integer arithmetic）来计算答案，但系数 x_i 本身仍可用内建类型计算，因此整个 Garner 算法相当高效。

Garner 算法的实现
该算法最方便用 Java 实现，因为 Java 自带标准的大整数运算，因此在把数从模系表示转换回普通数时不会遇到任何麻烦（使用标准类 BigInteger）。

下面给出的 Garner 算法实现支持加法、减法和乘法，并且支持负数运算（详见代码后的说明）。代码实现了普通十进制表示与模系表示之间的互相转换。

本示例取 10^9 之后的 100 个质数，可以处理约 10^{900} 以内的数。

final int SZ = 100;
int pr[] = new int[SZ];
int r[][] = new int[SZ][SZ];
 
void init() {
	for (int x=1000*1000*1000, i=0; i<SZ; ++x)
		if (BigInteger.valueOf(x).isProbablePrime(100))
			pr[i++] = x;
 
	for (int i=0; i<SZ; ++i)
		for (int j=i+1; j<SZ; ++j)
			r[i][j] = BigInteger.valueOf( pr[i] ).modInverse(
					BigInteger.valueOf( pr[j] ) ).intValue();
}
 
 
class Number {
 
	int a[] = new int[SZ];
 
	public Number() {
	}
 
	public Number (int n) {
		for (int i=0; i<SZ; ++i)
			a[i] = n % pr[i];
	}
 
	public Number (BigInteger n) {
		for (int i=0; i<SZ; ++i)
			a[i] = n.mod( BigInteger.valueOf( pr[i] ) ).intValue();
	}
 
	public Number add (Number n) {
		Number result = new Number();
		for (int i=0; i<SZ; ++i)
			result.a[i] = (a[i] + n.a[i]) % pr[i];
		return result;
	}
 
	public Number subtract (Number n) {
		Number result = new Number();
		for (int i=0; i<SZ; ++i)
			result.a[i] = (a[i] - n.a[i] + pr[i]) % pr[i];
		return result;
	}
 
	public Number multiply (Number n) {
		Number result = new Number();
		for (int i=0; i<SZ; ++i)
			result.a[i] = (int)( (a[i] * 1l * n.a[i]) % pr[i] );
		return result;
	}
 
	public BigInteger bigIntegerValue (boolean can_be_negative) {
		BigInteger result = BigInteger.ZERO,
			mult = BigInteger.ONE;
		int x[] = new int[SZ];
		for (int i=0; i<SZ; ++i) {
			x[i] = a[i];
			for (int j=0; j<i; ++j) {
				long cur = (x[i] - x[j]) * 1l * r[j][i];
				x[i] = (int)( (cur % pr[i] + pr[i]) % pr[i] );					
			}
			result = result.add( mult.multiply( BigInteger.valueOf( x[i] ) ) );
			mult = mult.multiply( BigInteger.valueOf( pr[i] ) );
		}
 
		if (can_be_negative)
			if (result.compareTo( mult.shiftRight(1) ) >= 0)
				result = result.subtract( mult );
 
		return result;
	}
}
关于负数的支持需要特别说明（函数 {\rm bigIntegerValue}() 的标志 \rm can\_be\_negative）。模系方案本身并不区分正数与负数。但可以注意到：如果在具体问题中答案按模计算后不超过所有质数乘积的一半，那么正数与负数的区别就在于，正数会小于这个中点，而负数会大于它。因此，我们在经典的 Garner 算法之后把结果与中点比较，若结果更大，则输出负号，并对结果取补（即用所有质数的乘积减去它，然后输出）。