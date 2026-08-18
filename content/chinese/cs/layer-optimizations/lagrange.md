---
title: 离散拉格朗日法
weight: 4
prerequisites:
- .
---

*本文是[一个系列](../)中的一篇。建议先阅读前面的所有文章。*

作为最后的优化，我们介绍受[拉格朗日乘子法](https://ru.wikipedia.org/wiki/%D0%9C%D0%B5%D1%82%D0%BE%D0%B4_%D0%BC%D0%BD%D0%BE%D0%B6%D0%B8%D1%82%D0%B5%D0%BB%D0%B5%D0%B9_%D0%9B%D0%B0%D0%B3%D1%80%D0%B0%D0%BD%D0%B6%D0%B0)启发的方法，在竞赛圈里也叫「lambda 优化」。

### 改造题目

考虑原题稍作修改的版本。设我们仍要覆盖同样的点，但现在不再对线段数量做硬性限制，而是对每多用一段付出某个常数 $\lambda$ 的惩罚。

于是我们优化的函数 $g$ 可以这样用 $f$ 表示：

$$
g[i] = \min_{k < i} \{f[i, k] + k \cdot \lambda \}
$$

但它可以用更优的公式计算，不必归结为计算 $f$：

$$
g[i] = \lambda + \min_{k < i} \{g[k] + (x_{i-1} - x_k)^2 \}
$$

这个动态规划可以在 $O(n)$ 内算：这正是上一篇文章[Convex Hull Trick](../convex-hull-trick)里做的。

### 思路

**观察 1。** 如果对某个 $\lambda$，$g_i$ 的最优解恰好用了 $k$ 段，那么这个解对 $f[i, k]$ 也是最优的。

**观察 2。** 如果减小 $\lambda$，$g_i$ 的最优线段数会增大。

优化核心：对 $\lambda$ 做二分查找，在内部对给定 $\lambda$ 求 $g_i$ 的最优解。如果得到的最优 $k^\star$ 大于 $k$，下一个 $\lambda$ 应更小，反之更大。当 $k^\star$ 与 $k$ 相等时，直接输出得到的解的净成本（不含惩罚）。

于是问题在 $O(n \log n + n \log m)$ 内解决，前提是 CHT 的排序在二分查找外预先完成。

### 实现

```c++
pair<ll, int> dp[maxn]; // dp[i] - (答案, 线段数)

void init() {
    for (int i = 0; i < maxn; i++) {
        dp[i] = make_pair(inf, 0);
    }
}

pair<ll, int> check(ll x) { // 这可以优化
    init();
    dp[0] = make_pair(0ll, 0); // 1-下标
    for (int i = 1; i <= n; i++) {
        for (int j = 0; j < i; j++) {
            dp[i] = min(dp[i], {dp[j].first + cost[j + 1][i] + x, dp[j].second + 1});
        }
    }
    return dp[n];
}

ll solve() {
    ll l = -1e14; // 边界要非常仔细地挑选！
    ll r = 1;
    while (l + 1 < r) {
        ll mid = (l + r) / 2;
        pair<ll, int> x = check(mid);
        if (x.second >= k)
            l = mid;
        else
            r = mid;
    }
    pair<ll, int> result = check(l);
    return result.first - l * return.second; // 减去惩罚
}
```

作者为实现的粗糙道歉，并呼吁读者重写并提交。

### 解的存在性

我们跳过一个细节：为什么存在这样的 $\lambda$，使得最优 $k^\star = k$？

一般来说，函数 $k^\star(\lambda)$ 可能「跳过」这个值，这确实是个问题：仅有单调性不足以用这种方法解任意的带对象数量约束的问题。

但在我们的题目里可以注意到：函数 $f[i, j]$ 关于第二个参数是非严格凹的（上凸），即

$$
f[i, j] - f[i, j-1] \leq f[i, j+1] - f[i, j]
$$

换句话说，每多加一段带来的额外「收益」不增加。

现在，改造后的动态规划表达式

$$
g[i] = \min_{k < i} \{f[i, k] + k \cdot \lambda \}
$$

可以看作最小化点 $(f[i, k], k)$ 与向量 $(1, \lambda)$ 的点积。

由于点 $(f[i, k], k)$ 的上包络线是凸的，对每个点都存在某个 $\lambda$ 顶到它，因此保证能找到 $k^\star = k$。
