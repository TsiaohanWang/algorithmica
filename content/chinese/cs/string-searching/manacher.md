---
title: Manacher 算法
authors:
- Сергей Слотин
created: 2019
weight: 3
---

设有一个字符串 $s$，我们想找出其中所有子回文。

我们立刻遇到一个明显困难：字符串里的子回文可能有 $O(n^2)$ 个，在字符串 $s = aa \ldots a$ 上就能看到。因此我们用下面的格式：对每个位置 $s_i$，找中心与 $s_i$ 重合的最大回文（偶数与奇数回文分开考虑）。它长度的一半（向下取整）称为*半径*。

朴素解法是枚举 $s_i$，对它用第二个循环找最大所需长度：

```c++
vector<int> pal_array(string s) {
    int n = s.size();

    // 用特殊字符把字符串围起来，避免处理越界
    s = "#" + s + "$";

    // 这个数组存从中心到回文边界的距离
    vector<int> t(n, 0);

    for(int i = 1; i <= n; i++)
        while (s[i - t[i - 1]] == s[i + t[i - 1]])
            r[i-1]++;

    return r;
}
```

同样的例子 $s = aa\dots a$ 说明这个实现在 $O(n^2)$ 内运行。

为优化，应用一个从 [z 函数](/cs/string-searching/z-function/) 算法中熟悉的思路：初始化 $t_i$ 时利用已算好的 $t$。具体说，维护 $(l, r)$——对应已找到的最右子回文的区间。于是可以说，以 $s_i$ 为中心、落在 $s_{l:r}$ 内的最大回文那部分，其半径至少为 $\min(r-i, \; t_{l+r-i})$。第一个量等于再往前就会越出 $s_{l:r}$ 的长度，第二个量是相对于回文 $s_{l:r}$ 中心对称位置处的半径值。

```c++

vector<int> manacher_odd(string s) {
    int n = (int) s.size();
    vector<int> d(n, 1);
    int l = 0, r = 0;
    for (int i = 1; i < n; i++) {
        if (i < r)
            d[i] = min(r - i + 1, d[l + r - i]);
        while (i - d[i] >= 0 && i + d[i] < n && s[i - d[i]] == s[i + d[i]])
            d[i]++;
        if (i + d[i] - 1 > r)
            l = i - d[i] + 1, r = i + d[i] - 1;
    }
    return d;
}
```

与 z 函数一样，算法运行在线性时间：`while` 循环只在 $t_i = r - i$ 时启动（否则回文已顶到某处），而且它的每次迭代都会使 $r$ 增加一。由于 $r \leq n$，这些循环总共做 $O(n)$ 次迭代。

对偶数回文的情形，只有下标变化：

```c++
vector<int> manacher_even(string s) {
    int n = (int) s.size();
    vector<int> d(n, 0);
    int l = -1, r = -1;
    for (int i = 0; i < n - 1; i++) {
        if (i < r)
            d[i] = min(r - i, d[l + r - i - 1]);
        while (i - d[i] >= 0 && i + d[i] + 1 < n && s[i - d[i]] == s[i + d[i] + 1])
            d[i]++;
        if (i + d[i] > r)
            l = i - d[i] + 1, r = i + d[i];
    }
    return d;
}
```

也可以不分别写两个实现，而用下面的技巧做替换：

$$
S = s_1 s_2 \dots s_n \to S^* = s_1 \# s_2 \# \dots \# s_n
$$

现在中心在 $s_i$ 的奇数回文对应原串的奇数回文，中心在 `#` 的奇数回文对应偶数回文。
