---
title: 因式分解的应用
weight: 4
draft: true
---

### 基础理论

任何自然数都能分解为质数的乘积（这由[算术基本定理](https://ru.wikipedia.org/wiki/%D0%9E%D1%81%D0%BD%D0%BE%D0%B2%D0%BD%D0%B0%D1%8F_%D1%82%D0%B5%D0%BE%D1%80%D0%B5%D0%BC%D0%B0_%D0%B0%D1%80%D0%B8%D1%84%D0%BC%D0%B5%D1%82%D0%B8%D0%BA%D0%B8)保证），用这种记法解题非常方便。

<b>例子：</b> $$11 = 11 = 11^1$$ $$100 = 2 \\times 2 \\times 5 \\times 5 = 2^2 \\times 5^2$$ $$126 = 2 \\times 3 \\times 3 \\times 7 = 2^1 \\times 3^2 \\times 7^1$$

考虑这样一道题：

<b>题意：</b> 需要把 $N$ 个人分成大小相同的组。我们想知道可以有哪些大小，以及有多少种分法。

<b>解法：</b> 本质上是要我们求出 $N$ 的不同因数的个数。看 $N$ 的质因数分解，一般形式为：

$$N= p_1^{a_1} \\times p_2^{a_2} \\times \\ldots \\times p_k^{a_k}$$

现在从组合角度想这个式子。要「生成」某个因数，需要给第 $i$ 个质数的指数代入 0 到 $a_i$（即 $a_i+1$ 种不同的值），对每个质数都这样。也就是说 $N$ 的因数形如：
$$M= p_1^{b_1} \\times p_2^{b_2} \\times \\ldots \\times p_k^{b_k}, \\ \\ 0 \\leq b_i \\leq a_i$$
因此答案是乘积 $(a_1+1) \\times (a_2+1) \\times \\ldots \\times (a_k + 1)$。

### 算法描述

应用[数素性测试的算法](Проверка_на_простоту_за_корень "wikilink")，我们容易找到 <b>N 的最小质因数</b>。显然，一旦找到 $N$ 的一个质因数，就能用 $N$ 除以它，继续找新的最小质因数。

像之前一样从 2 到 $N$ 的平方根枚举质因数，但若 $N$ 能被它整除，就直接除。而且可能需要除多次（$N$ 可能被该质因数的较大次幂整除）。这样我们就收集质因数，直到 $N$ 变成 $1$ 或变成质数（此时我们因走到它的平方根而停下）。第二种情况还要把 $N$ 本身加入答案。

``` C++ numberLines
vector<int> factorize(int N) {
    vector<int> result;
    for (int i = 2; i * i <= N; i++) {
        while (N % i == 0) {
            result.push_back(i);
            N /= i;
        }
    }
    if (N != 1) {
        result.push_back(N);
    }
    return result;
}
```

### 复杂度

注意 `for` 循环的迭代次数不超过 $\\bigl\\lceil\\sqrt{N}\\bigr\\rceil$，即 $O\\left(\\sqrt{N}\\right)$。除以某个质数时 $N$ 至少减半，因此 `while` 循环的总迭代次数不超过 $\\log N$。于是整个算法运行在 $O\\left(\\log N + \\sqrt{N}\\right) = O\\left(\\sqrt{N}\\right)$。
