---
title: 快速求倒数平方根
weight: 4
---

浮点数的倒数平方根 $\frac{1}{\sqrt x}$ 常用于计算归一化向量，而归一化向量又被广泛用于各类仿真场景，例如计算机图形学（比如为模拟光照而计算入射角与反射角）。

$$
\hat{v} = \frac{\vec v}{\sqrt {v_x^2 + v_y^2 + v_z^2}}
$$

直接计算倒数平方根——先求平方根再用 $1$ 除以它——会非常慢，因为即使这两种运算都在硬件中实现，它们本身依然很慢。

但存在一个出奇准确的近似算法，它利用了浮点数在内存中的存储方式。事实上它准到已经被[实现在硬件里](https://www.felixcloutier.com/x86/rsqrtps)，因此这个算法本身对软件工程师已不再有意义，但我们将仍然完整地走一遍，因为它有着内在的美感和极高的教学价值。

除了方法本身，它的诞生历史也相当有趣。人们把它归功于游戏工作室 *id Software*，他们在其 1999 年的标志性游戏《雷神之锤 III 竞技场》中使用了它；不过显然，它是通过一条「我从一个人那里学来的，而那个人又从另一个人那里学来」的传播链传进去的，这条链的尽头似乎指向威廉·卡汉（William Kahan）——正是那位负责 IEEE 754 和卡汉求和算法的人。

它大约在 2005 年流行于游戏开发社区，当时 id Software 公布了这款游戏的源代码。这是[其中的相关片段](https://github.com/id-Software/Quake-III-Arena/blob/master/code/game/q_math.c#L552)，连同注释一起：

```c++
float Q_rsqrt(float number) {
    long i;
    float x2, y;
    const float threehalfs = 1.5F;

    x2 = number * 0.5F;
    y  = number;
    i  = * ( long * ) &y;                       // evil floating point bit level hacking
    i  = 0x5f3759df - ( i >> 1 );               // what the fuck? 
    y  = * ( float * ) &i;
    y  = y * ( threehalfs - ( x2 * y * y ) );   // 1st iteration
//  y  = y * ( threehalfs - ( x2 * y * y ) );   // 2nd iteration, this can be removed

    return y;
}
```

我们将一步步剖析它的工作原理，但在此之前，我们需要稍作迂回。

### 近似对数

在计算机（或者说至少是买得起的计算器）成为日常用品之前，人们使用对数表来计算乘法及相关运算——先查出 $a$ 和 $b$ 的对数，把它们相加，再求出结果的反对数。

$$
a \times b = 10^{\log a + \log b} = \log^{-1}(\log a + \log b)
$$

计算 $\frac{1}{\sqrt x}$ 时也可以玩同样的把戏，利用恒等式：

$$
\log \frac{1}{\sqrt x} = - \frac{1}{2} \log x
$$

快速求倒数平方根正是基于这个恒等式，因此它需要极快地算出 $x$ 的对数。事实证明，只需把 32 位的 `float` 重新解释成整数，就能近似得到它。

[回想一下](../float)，浮点数按顺序存放符号位（对正数来说为 0，这里正是这种情况）、指数 $e_x$ 和尾数 $m_x$，它们对应于

$$
x = 2^{e_x} \cdot (1 + m_x)
$$

因此它的对数为

$$
\log_2 x = e_x + \log_2 (1 + m_x)
$$

由于 $m_x \in [0, 1)$，右边的对数可以用下式近似

$$
\log_2 (1 + m_x) \approx m_x
$$

该近似在区间两端是精确的，但为了照顾平均情况，需要用一个小的常数 $\sigma$ 对它做平移，因此

$$
\log_2 x = e_x + \log_2 (1 + m_x) \approx e_x + m_x + \sigma
$$

现在，把上述近似记在心里，并定义 $L=2^{23}$（`float` 的尾数位数）和 $B=127$（指数偏置），当我们把 $x$ 的位模式重新解释为整数 $I_x$ 时，本质上得到

$$
\begin{aligned}
I_x &= L \cdot (e_x + B + m_x)
\\  &= L \cdot (e_x + m_x + \sigma +B-\sigma )
\\  &\approx L \cdot \log_2 (x) + L \cdot (B-\sigma )
\end{aligned}
$$

（把整数乘以 $L=2^{23}$ 等价于把它左移 23 位。）

当你把 $\sigma$ 调到使均方误差最小，就会得到一个出奇精确的近似。

![把浮点数 $x$ 重新解释为整数（蓝色）与缩放平移后的对数的对比（灰色）](../img/approx.svg)

现在，从这个近似中解出对数，得到

$$
\log_2 x \approx \frac{I_x}{L} - (B - \sigma)
$$

很好。我们刚才说到哪儿了？哦，对，我们想算倒数平方根。

### 近似结果

要利用恒等式 $\log_2 y = - \frac{1}{2} \log_2 x$ 计算 $y = \frac{1}{\sqrt x}$，可以把它代入我们的近似公式，得到

$$
\frac{I_y}{L} - (B - \sigma)
\approx
- \frac{1}{2} ( \frac{I_x}{L} - (B - \sigma) )
$$

解出 $I_y$：

$$
I_y \approx \frac{3}{2} L (B - \sigma) - \frac{1}{2} I_x
$$

事实证明，我们甚至一开始就不需要计算对数：上式只是一个常数减去 $x$ 的整数重新解释的一半。它写在代码里就是：

```cpp
i = * ( long * ) &y;
i = 0x5f3759df - ( i >> 1 );
```

第一行我们把 `y` 重新解释为整数，第二行把它代入公式，其中第一项是魔法常数 $\frac{3}{2} L (B - \sigma) = \mathtt{0x5F3759DF}$，第二项则用二进制移位而非除法来计算。

### 用牛顿法迭代

接下来是一连串手工编码的牛顿法迭代，其中 $f(y) = \frac{1}{y^2} - x$，并且初值非常好。它的更新规则为

$$
f'(y) = - \frac{2}{y^3} \implies y_{i+1} = y_{i} (\frac{3}{2} - \frac{x}{2} y_i^2) = \frac{y_i (3 - x y_i^2)}{2}
$$

写进代码里就是

```cpp
x2 = number * 0.5F;
y  = y * ( threehalfs - ( x2 * y * y ) );
```

初始近似已经非常好，对游戏开发而言只要迭代一次就足够了。仅仅第一次迭代后，它就落在正确答案的 99.8% 以内；还可以继续迭代以提高精度——硬件正是这么做的：[x86 指令](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html#ig_expand=3037,3009,5135,4870,4870,4872,4875,833,879,874,849,848,6715,4845,6046,3853,288,6570,6527,6527,90,7307,6385,5993&text=rsqrt&techs=AVX,AVX2) 会做几次这样的迭代，并保证相对误差不超过 $1.5 \times 2^{-12}$。

### 延伸阅读

[维基百科上关于快速求倒数平方根的文章](https://en.wikipedia.org/wiki/Fast_inverse_square_root#Floating-point_representation)。
