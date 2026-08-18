---
title: 稀疏表
authors:
- Сергей Слотин
weight: 3
---

稀疏表（英文 *sparse table*）是支持在 $O(1)$ 内回答区间最小值查询、以 $O(n \log n)$ 时间与内存预计算的数据结构。

**定义**。 稀疏表是大小为 $\log n \times n$ 的二维数组：

$$
t[k][i] = \min \{ a_i, a_{i+1}, \ldots, a_{i+2^k-1} \}
$$

即对每个长度为 $2^k$ 的区间算最小值。

这个数组可以按其大小计算，按 $i$ 或 $k$ 迭代：

$$
t[k][i] = \min(t[k-1][i], t[k-1][i+2^{k-1}])
$$

有了这个数组，就能对任意区间快速算最小值。注意任意区间都有两个长度是 2 的幂的区间相交、且完全覆盖它（只覆盖它）。于是只需取这两个区间对应值的 min。

![](../img/sparse-table.png)

最后一个细节：要让查询常数真正为常数，需要学会在常数内算对数。可用 GCC 提供的 `__lg` 函数。它内部用 `clz`（"count leading zeros"）指令，多数现代处理器都有，返回二进制中第一个 1 之前的零个数，据此可在几个处理器周期内得到所需的取整对数。

```cpp
int a[maxn], mn[logn][maxn];

int rmq(int l, int r) { // 半开区间 [l; r)
    int t = __lg(r - l);
    return min(mn[t][l], mn[t][r - (1 << t)]);
}

// 这在 main 开头几行计算：

memcpy(mn[0], a, sizeof a);

for (int l = 0; l < logn - 1; l++)
    for (int i = 0; i + (2 << l) <= n; i++)
        mn[l+1][i] = min(mn[l][i], mn[l][i + (1 << l)]);
```

对大表，迭代顺序与内存布局对构建速度影响很大——这与缓存工作有关。但多数情形构建时间不关键。

**练习**。 想想其他 4 种迭代与布局方式的缺点。

### 应用

稀疏表是静态数据结构，即不能便宜地更新（但可以边走边补建——见 ROI-2017 题「[反物质](http://neerc.ifmo.ru/school/archive/2016-2017/ru-olymp-roi-2017-editorial.pdf)」）。

稀疏表常用于[最近公共祖先](/cs/trees/lca-rmq)，因为可归结为 RMQ。

## 2d Static RMQ

这个结构也能推广到更高维度。假设要在子方形上算 RMQ。则用数组 `t[k][i][j]`，其中存的是同样 2 的幂次*方形*上的最小值。任意方形上的最小值就分解为四个 $2^k$ 方形的最小值。

一般情形是对 $d$ 维数组的矩形求最小值。则做类似上一情形的预计算，只是现在要 $O(n \log^d n)$ 内存与时间——需要存所有边长为 2 的幂的超矩形上的最小值。

## 对运算的限制

稀疏表不仅可用于最小值或最大值。只要求运算满足结合律（$a ∘ (b ∘ c) = (a ∘ b) ∘ c$）、交换律（$a ∘ b = b ∘ a$）和幂等律（$a ∘ a = a$）。例如可用于求 $\gcd$。

若运算不幂等，可这样求结果：取顶到查询左边界的最长区间，加入答案，把指针移到它的右端，继续直到处理完整个查询。

```c++
int sum(int l, int r) { // [l, r)
    int res = 0;
    for (int d = logn - 1; d >= 0; d--) {
        if (l + (1 << d) < r) {
            res += t[l][d];
            l += (1 << d);
        }
    }
    return res;
}
```

这比例如[线段树](/cs/segment-tree)快，但也是 $O(\log n)$ 复杂度，还费额外内存。但有办法加速。

## Disjoint Sparse Table

我们想要一种能在区间上算函数 $f$、而 $f$ 不满足幂等性的结构。标准稀疏表不行——它找不到 $O(1)$ 个不相交区间。

这样办：心算在数组上建线段树，（实算地）对它的每个区间 $[l, r)$，从其中间元素——下标 $m = \lfloor \frac{l + r}{2} \rfloor$ 的元素——到所有其他元素 $k \in [l, r)$ 算 $f$。对每个数组元素有 $O(\log n)$ 个中心，因此总计仍需 $O(n \log n)$ 时间与内存。

**命题**。 任意查询 $[l, r)$ 分解为 $O(1)$ 个不相交的预计算区间。

**证明**。 取属于查询的最高中心元素 $m$。它的区间完全覆盖查询——否则最高的就不是 $m$，而是它的某个边界。既然查询区间 $[l, r)$ 被完全覆盖、$m$ 在它内部，那么 $[l, r)$ 可分解为预计算的 $[l, m)$ 和 $[m, r)$。

解法正是这样：找所需中心元素，从它做两个查询。

### 实现

难的部分——在常数内找中心元素——如果只处理长度为 2 的幂的数组、对应完整线段树，会简单些。长度不合适的数组用依赖操作本身的特殊中性元素补齐到最近的 2 的幂（加法用 $0$，乘法用 $1$）。

把整个结构（区间预计算值）存进数组 `t[logn][maxn]`，第一参数是线段树层数（长度为 $2^d$ 的区间的 $d$），第二参数是对应区间的边界（数 $k$）。这些信息足以唯一恢复区间。

回答查询只需找所需中心元素的层。要高效找，需要想一下线段树的性质。

注意第 $k$ 层的任何顶点对应某区间 $[l, l + 2^k)$，且 $l$ 被 $2^k$ 整除。该区间所有下标二进制都有某个公共前缀，最后 $k$ 位不同。

要找所需中心元素的层，就是找元素 $l$ 与 $r$ 的最小公共区间的层。由上一事实，所需层等于 $l$ 与 $r$ 中最显著不同的位的位置。若预先算好对数，可用表达式 $h_{[l,r)]} = \lfloor \log_2 (l \oplus r) \rfloor$ 在常数内找到。

例如，为按合数模的乘法建 DST：

```cpp
const int maxn = (1 << logn);
int a[maxn], lg[maxn], t[logn][maxn];

const int neutral = 1;
int f(int a, int b) {
    return (a * b) % 1000;
}

void build(int l, int r, int level = logn - 1) {
    int m = (l + r) / 2;

    int cur = neutral;
    for (int i = m + 1; i < r; i++) {
        cur = f(cur, a[i]);
        t[level][i] = cur;
    }

    cur = neutral;
    for (int i = m; i >= l; i--) {
        cur = f(cur, a[i]);
        t[level][i] = cur;
    }

    if (r - l > 1) {
        build(l, mid, level+1);
        build(mid, r, level+1);
    }
}

int rmq(int l, int r) { // [l, r)
    int level = lg[l ^ r];
    int res = t[level][l];
    // 并且，若右区间非空：
    if (r & ((1 << lg[l ^ r]) - 1)))
        res = f(res, t[level][r]);
    return res;
}
```

注：很可能这里有 bug。
