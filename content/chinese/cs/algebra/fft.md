---
title: 快速傅里叶变换
authors:
  - Сергей Слотин
  - Александр Кульков
created: 2019
weight: 6
date: 2021-09-14
prerequisites:
  - polynomials
  - interpolation
published: true
---

快速傅里叶变换是 20 世纪最重要的算法之一，如果不是最重要的话。

正如可以猜到的那样，它用于计算[傅里叶变换](https://ru.wikipedia.org/wiki/%D0%9F%D1%80%D0%B5%D0%BE%D0%B1%D1%80%D0%B0%D0%B7%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5_%D0%A4%D1%83%D1%80%D1%8C%D0%B5)，而傅里叶变换又用于音频处理、电磁波、光学问题、数据压缩、物理模拟以及其他复杂的数学和物理问题。

而在本文中，我们将从另一个角度出发，在竞赛中[经常遇到](../polynomials)的数和多项式乘法问题的背景下考察快速傅里叶变换算法。

### 通过插值做乘法

$(n - 1)$ 次多项式[可以唯一确定](/cs/algebra/interpolation/)——不仅可以用它的系数，还可以用它在 $n$ 个不同点处的取值。

直接用系数表示的多项式相乘需要 $O(n^2)$ 次运算。但如果多项式是用它们在 $2n$ 个点处的取值给出的，那么相乘只需 $O(n)$：乘积多项式 $A(x) \cdot B(x)$ 在点 $x_i$ 处的值恰好等于 $A(x_i) \cdot B(x_i)$。

**算法的主要思想**在于：如果我们在某个 $(n + m)$ 个互不相同的点上分别计算两个多项式 $A$ 和 $B$ 的值，那么把它们两两相乘后，用 $O(n + m)$ 次运算就能得到乘积多项式 $A(x) \cdot B(x)$ 在这些相同点上的值，再用插值法就能还原出乘积多项式的系数，从而解决问题。

```c++
vector<int> poly_multiply(vector<int> a, vector<int> b) {
    vector<int> A = evaluate(a);
    vector<int> B = evaluate(b);
    for (int i = 0; i < A.size(); i++)
        A[i] *= B[i];
    return interpolate(A);
}
```

如果我们假装 `evaluate` 和 `interpolate` 能在线性时间内工作，那么这个乘法也能在线性时间内完成。但遗憾的是，直接计算点值需要 $O(n^2)$ 次运算，而插值——无论用高斯消元还是用符号计算拉格朗日多项式——甚至更慢，需要 $O(n^3)$。

但如果我们能更快地计算点值并完成插值呢？事实证明，只要不取任意点、而只取一种特殊的点——复数单位根——就能做到。

### 单位根

**事实.** 对任意正整数 $n$，恰好存在 $n$ 个「单位根」，即满足下式的数 $w_k$：

$$
w_k^n = 1
$$

具体来说，它们是如下形式的数：

$$
w_k = e^{i \tau \frac{k}{n}}
$$

其中 $\tau$ 表示 $2 \pi$，即「整个圆」。[这是一种比较新的记号](https://tauday.com/tau-manifesto)。

在复平面上，这些数等距地分布在单位圆上：

![9 次单位根的全部 9 个复数根](https://www.kylem.net/math/242_roots_unity_9.png)

第一个根 $w_1$（更准确地说，是第二个——我们把 1 当作第零个根）被称为 $n$ 次单位根的*本原根*。把它自乘第零次、第一次、第二次……就能生成所需的全部单位根序列，并且序列在第 $n$ 个元素处循环：

$$
w_n = e^{i \tau \frac{n}{n}} = e^{i \tau} = e^{i \cdot 0} = w_0 = 1
$$

我们把 $w_1$ 简记为 $w$。

## 离散傅里叶变换

*离散傅里叶变换*指的就是计算多项式在复数单位根处的取值：

$$
y_j = \sum_{k=0}^{n-1} x_k e^{i\tau \frac{kj}{n}} = \sum_{k=0}^{n-1} x_k w_1^{kj}
$$

正如可以猜到的那样，*离散傅里叶逆变换*就是它的逆运算——根据值 $y_i$ 插值出系数 $x_i$。

**结论.** 逆离散傅里叶变换可以用下面的公式计算：

$$
x_j = \frac{1}{n} \sum_{k=0}^{n-1} y_k e^{-i\tau \frac{kj}{n}} = \frac{1}{n} \sum_{k=0}^{n-1} y_k w_{n-1}^{kj}
$$

**证明.** 计算傅里叶变换时，我们实际上是在对向量施加一个矩阵：

$$
\begin{pmatrix}
    w^0 & w^0 & w^0 & w^0 & \dots & w^0
\\  w^0 & w^1 & w^2 & w^3 & \dots & w^{-1}
\\  w^0 & w^2 & w^4 & w^6 & \dots & w^{-2}
\\  w^0 & w^3 & w^6 & w^9 & \dots & w^{-3}
\\  \vdots & \vdots & \vdots & \vdots & \ddots & \vdots
\\  w^0 & w^{-1} & w^{-2} & w^{-3} & \dots & w^1
\end{pmatrix}
\begin{pmatrix} a_0 \\ a_1 \\ a_2 \\ a_3 \\ \vdots \\ a_{n-1} \end{pmatrix}
= \begin{pmatrix} y_0 \\ y_1 \\ y_2 \\ y_3 \\ \vdots \\ y_{n-1} \end{pmatrix}
$$

也就是说，傅里叶变换就是对向量的一种线性运算：$W a = y$。因此，逆变换可以写成 $a = W^{-1}y$。

这个 $W^{-1}$ 长什么样呢？作者不打算装作能逻辑严密地推导出它，直接给出结果：

$$
W^{-1} =
\dfrac 1 n \begin{pmatrix}
    w^0 & w^0 & w^0 & w^0 & \dots & w^0
\\  w^0 & w^{-1} & w^{-2} & w^{-3} & \dots & w^{1}
\\  w^0 & w^{-2} & w^{-4} & w^{-6} & \dots & w^{2}
\\  w^0 & w^{-3} & w^{-6} & w^{-9} & \dots & w^{3}
\\  \vdots & \vdots & \vdots & \vdots & \ddots & \vdots
\\  w^0 & w^{1} & w^{2} & w^{3} & \dots & w^{-1}
\end{pmatrix}
$$

验证一下，$W$ 与 $W^{-1}$ 相乘确实得到单位矩阵：

1. 第 $i$ 个对角元素的值等于 $\frac{1}{n} \sum_k w^{ki} w^{-ki} = \frac{1}{n} n = 1$。
2. 任意非对角（$i \neq j$）元素 $(i, j)$ 的值等于

$$
\frac{1}{n} \sum_k w^{ik} w^{-jk} = \frac{1}{n} \sum_k w^k w^{i-j} = \frac{w^{i-j}}{n} \sum_k w^k = 0
$$

最后一步成立，因为所有复数单位根之和为零，即 $\sum w^k = 0$。

细心的读者会发现 $W$ 与 $W^{-1}$ 的形式、以及正逆变换公式之间的对称性。这个对称性会大大简化我们的生活：计算逆傅里叶变换时可以使用同样的算法，只需把 $w^k$ 换成 $w^{-k}$，最后把结果除以 $n$ 即可。

## 算法

回忆一下，我们最初的目的是用下面的算法来乘多项式：

1. 在两个多项式的 $(n+m)$ 个任意点上计算值。
2. 用 $O(n + m)$ 的时间把这些值两两相乘。
3. 通过插值得到乘积多项式。

一般情况下，快速插值乃至仅仅快速计算点值都是不可能的，但对单位根却可以。只要学会了快速计算单位根处的值并快速插值（正、逆傅里叶变换），就能解决最初的问题。

这个算法就是*快速傅里叶变换*（英文 *fast Fourier transform*）。它采用「分治」策略，时间复杂度为 $O(n \log n)$。

### 库利–图基算法（Cooley–Tukey）

通常，「分治」类算法把问题分成两半：前 $\frac{n}{2}$ 个元素和后 $\frac{n}{2}$ 个元素。这里我们换一种做法：把所有元素分成奇数和偶数两类。

把多项式写成 $P(x)=A(x^2)+xB(x^2)$ 的形式，其中 $A(x)$ 由 $x$ 的偶次幂的系数组成，$B(x)$ 由 $x$ 的奇次幂的系数组成。

设 $n = 2k$。那么注意，对任意整数 $t$ 有

$$
w^{2t}
= w^{2t \bmod n}
= w^{2t \bmod 2k}
= w^{2(t \bmod k)}
$$

据此，多项式在 $w^t$ 处取值的原公式可以改写为：

$$
P(w^t)
= A(w^{2t}) + w^t B(w^{2t})
= A\left(w^{2(t\bmod k)}\right)+w^tB\left(w^{2(t\bmod k)}\right)
$$

关键观察：计算时需要的形如 $w^{2t}$ 的不同根的数量会减少一半，而且两个多项式里的系数数量也都各减少一半——也就是说，我们刚刚成功地把问题拆成了两个规模各减半的子问题。

算法的过程如下：递归地计算 $A$ 和 $B$ 的 FFT，再用上面的公式合并答案。递归时，需要计算的不再是 $n$ 次单位根、而是 $k = \frac{n}{2}$ 次单位根处的值，也就是 $n$ 次单位根中所有「偶数」根（形如 $w^{2t}$）处的值。注意，如果 $w$ 是 $n = 2k$ 次单位根中的本原根，那么 $w^2$ 就是 $k$ 次单位根中的本原根，也就是说，递归时只需传入另一个本原根的值即可。

于是我们把规模为 $n$ 的变换化归为两个规模为 $\dfrac n 2$ 的变换，因此 FFT 的总计算时间为

$$
T(n)=2T\left(\dfrac n 2\right)+O(n)=O(n\log n)
$$

还要注意，$n$ 能被 2 整除这个假设至关重要。也就是说，除了最后一层以外，$n$ 在每一层都必须是偶数，由此可知 $n$ 必须是 2 的幂。

### 实现

下面给出按库利–图基算法计算 FFT 的代码：

```cpp
typedef complex<double> ftype;
const double pi = acos(-1);

// принимает массив и n-ный корень из единицы, и заменяет его на значения в корнях
void fft(vector<ftype> &p, ftype wn) {
    int n = (int) p.size();
    if (n == 1)
        return;
    // разделяем массив на четный и нечетный
    vector<ftype> a(n / 2), b(n / 2);
    for (int i = 0; i < n / 2; i++) {
        a[i] = p[2 * i];
        b[i] = p[2 * i + 1];
    }
    // рекурсивно считаем БПФ
    fft(a, wn * wn);
    fft(b, wn * wn);
    // объединяем результат по формуле
    ftype w = 1;
    for (int i = 0; i < n / 2; i++) {
        // можно не использовать модуль, а сразу раскрыть его для двух половин
        p[i] = a[i] + w * b[i];
        p[i + n / 2] = a[i] - w * b[i]; // w^(i+n/2) = -w^i
        w *= wn;
    }
}
```

初次调用时，需要先把数组补齐到 2 的幂：

```cpp
vector<ftype> evaluate(vector<int> p) {
    while (__builtin_popcount(p.size()) != 1)
        p.push_back(0);
    return fft(p, polar(1., 2 * pi / p.size()));
}
```

如前所述，逆傅里叶变换可以很方便地用正变换来表达：

```c++
vector<int> interpolate(vector<ftype> p) {
    int n = p.size();
    auto inv = fft(p, polar(1., -2 * pi / n));
    vector<int> res(n);
    for(int i = 0; i < n; i++)
        // мы хотим получать целые числа, для этого результаты нужно округлить
        res[i] = round(real(inv[i]) / n);
    return res;
}
```

现在我们已经能用 $O(n \log n)$ 的时间相乘两个多项式了：

```c++
vector<int> poly_multiply(vector<int> a, vector<int> b) {
    vector<ftype> A = evaluate(a);
    vector<ftype> B = evaluate(b);
    for (int i = 0; i < A.size(); i++)
        A[i] *= B[i];
    return interpolate(A);
}
```

上面这段代码虽然正确且具有 $O(n \log n)$ 的渐近复杂度，但常数非常大——主要来自递归和额外的内存分配。

### 优化版本

试试彻底去掉内存分配。目前分配的发生是因为我们每次都要把数组分成两份。如果不创建新的数组，而是直接把所有偶数元素移到左半部分、奇数元素移到右半部分，然后递归处理两个半部分，会怎样呢？

**观察.** 递归最后一层中下标为 `k` 的元素会被写到 `revbits(k)` 这个位置，其中函数 `revbits(x)` 把数字 $x$ 的二进制位「反转」。

确实如此：第一次划分时，所有偶数元素（最低位为 0）会被写进前半部分（最高位为 0 的位置），奇数元素则相反。接下来，所有次低位为 0 的元素会在各自半区内被写进较小的那一半（次高位为 0 的位置），以此类推。

![](../img/fft-shuffle.png)

既然知道每个元素最终会落在哪里，那干脆不在递归里做任何交换，而是在一开始就一次性完成重排，递归函数里只需对两个半部分递归调用即可。

```cpp
void solve(ftype *a, int n, ftype wn) {
    if (n > 1) {
        int k = (n >> 1);
        solve(a, k, wn * wn);
        solve(a + k, k, wn * wn);
        ftype w = 1;
        for (int i = 0; i < k; i++) {
            // тут нужно быть чуть аккуратней с перезаписыванием,
            // потому что мы читаем и пишем из одного и того же массива
            ftype t = w * a[i + k];
            a[i + k] = a[i] - t; 
            a[i] = a[i] + t;
            w *= wn;
        }
    }
}

void fft(ftype *a, int n, int inverse) {
    const int logn = __lg(n);

    for (int i = 0; i < n; i++) {
        // переворачиваем биты числа i
        int k = 0;
        for (int l = 0; l < logn; l++)
            k |= ((i >> l & 1) << (logn - l - 1));
        // делаем только один swap -- из того элемента, который идет раньше
        if (i < k)
            swap(a[i], a[k]);
    }

    ftype wn = polar(1., inverse * 2 * pi / n); // inverse = {-1, +1}
    solve(a, n, wn);
}
```

这个算法有相当不错的数值稳定性，但在竞赛题中经常需要计算很大的整数答案，或者对答案取模。不过这个问题也可以解决。

### 数论变换（Number-theoretic transform）

实际上，我们需要的复数性质只有一个：1 有 $n$ 个「根」。其实，除复数外，还有别的代数对象也具备这个性质——例如模剩余类环中的元素。

找一对 $m$ 和 $g$（$g$ 扮演 $w_n^1$ 的角色），使得 $g$ 是生成元：即 $g^n \equiv 1 \pmod m$，并且对所有 $k < n$，$g^k$ 在模 $m$ 下互不相同。实践中，$m$ 常常特意取一些「方便」的模数，例如

$$
m = 998244353 = 7 \cdot 17 \cdot 2^{23} + 1
$$

这个数是质数，而且恰好比一个能被较大的 2 的幂整除的数大 1。当 $n=2^{23}$ 时，合适的 $g$ 是 $31$。注意，与复数的情况类似：如果对某个 $n=2^k$，$g$ 是原根，那么对 $n=2^{k-1}$，原根就是 $(g^2 \bmod m)$。因此，对于 $m=998244353$ 和 $n=2^k$，原根等于 $g=31^{2^{23-k}} \bmod m$。

实现上几乎没什么区别：只需在所有运算中使用模运算，并对 $w$ 和 $w^{-1}$ 使用那些吓人的预计算常数。

另外，最近一些出题人开始使用这个模数来代替标准的 $10^9+7$，以此暗示（或迷惑）选手这道题是 FFT 相关题目。

<!--
Реализация практически не отличается.

```c++
const int MAXN = (1 << 19),
      INV2 = 499122177; // обратное к двум по модулю MOD
const int MOD = 998244353;
W = 805775211, // W -- первообразный корень MAXN-ной степени из 1,
IW = 46809892; // IW -- обратное по модулю MOD к W

// INV2 - обратное к двум по модулю MOD
// Данная реализация FFT перемножает два целых числа длиной до 250000 цифр за ~0.13 секунд без проблем с точностью и занимает всего 30 строк кода

int pws[MAXN + 1], ipws[MAXN + 1];

void init() {
    pws[MAXN] = W; ipws[MAXN] = IW;
    for (int i = MAXN / 2; i >= 1; i /= 2) {
        pws[i] = (pws[i * 2] * 1ll * pws[i * 2]) % MOD;
        ipws[i] = (ipws[i * 2] * 1ll * ipws[i * 2]) % MOD;
    }
}

void fft(vector<int> &a, vector<int> &ans, int l, int cl, int step, int n, bool inv) {
    if (n == 1) { ans[l] = a[cl]; return; }
    fft(a, ans, l, cl, step * 2, n / 2, inv);
    fft(a, ans, l + n / 2, cl + step, step * 2, n / 2, inv);
    int cw = 1, gw = (inv ? ipws[n] : pws[n]);
    for (int i = l; i < l + n / 2; i++) {
        int u = ans[i], v = (cw * 1ll * ans[i + n / 2]) % MOD;
        ans[i] = (u + v) % MOD;
        ans[i + n / 2] = (u - v) % MOD;
        if (ans[i + n / 2] < 0) ans[i + n / 2] += MOD;
        if (inv) {
            ans[i] = (ans[i] * 1ll * INV2) % MOD;
            ans[i + n / 2] = (ans[i + n / 2] * 1ll * INV2) % MOD;
        }
        cw = (cw * 1ll * gw) % MOD;
    }
}
```
-->