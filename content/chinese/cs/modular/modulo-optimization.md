---
title: 模运算优化
authors:
- Иван Сафонов
weight: 100
draft: true
---

让我们弄清楚如何计算模意义下的表达式值，使其所需的处理器操作最少。

如果相加的每个值都小于 $MOD$，那么可以不对它们取模，而用 `if` 和减法来处理：

``` c++ numberLines
int res = a + b;
if (res >= MOD) {
    res -= MOD;
}
```

在某些需要计算若干小于 $MOD$ 的量之积的和的题目里，下面这个<i>非渐近</i>的优化会很有用：把所有乘积按模 $MOD^2$ 计算，对这些量的求和用前面的技巧处理，最后对答案只取一次模 $MOD$。这个技巧在例如[矩阵乘幂](Возведение_матрицы_в_степень "wikilink")时很有用：

``` c++ numberLines
matrix multiple(matrix& a, matrix &b) {
    int n = a.size();
    int m = b[0].size();
    int k = b.size();
    matrix c(n, m);
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < m; j++) {
            int res = 0;
            for (int t = 0; t < k; t++) {
                res += a[i][t] * b[t][j];
                if (res >= MOD2) {
                   res -= MOD2;
                }
            }
            c[i][j] = res % MOD;
        }
    }
    return res;
}
```
