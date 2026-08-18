---
title: Mergesort 树
draft: true
---

#### 题目

给定数组 $a_0,\\ \\ldots,\\ a_{n-1}$。需要回答 $q$ 个查询：

  - $?\\ l,\\ r,\\ x$ —— 在 $a_l,\\ \\ldots,\\ a_r$ 中小于 $x$ 的元素个数。

#### 解法

如果数组的子段已排序，那么我们能用[二分查找](Бинпоиск "wikilink")在 $O(\\log n)$ 内回答这样的查询。在数组上建一棵[线段树](Дерево_отрезков "wikilink")，在每个顶点里存对应子段的排序版本。于是查询的答案为 $O(\\log^2 n)$——我们做普通的线段树 get 查询，区别只在于拿到子段答案的地方要[二分查找](Бинпоиск "wikilink")。

#### 建树

要快速构建 merge sort tree，我们利用 [merge sort](Сортировка_слиянием "wikilink") 的思想（名字正来源于此）。对每个顶点存它子段的副本（内存开销后文再谈）。如果顶点对应长度为 1 的段，它的数组已排序。如果某顶点的两个儿子数组都已排序，就能在线性时间内把它们合并。

#### 运行时间与内存

每个数组元素会存在 $O(\\log n)$ 个数组里——在从叶子到根的路径上——因此我们的结构占用 $O(n \\log n)$ 内存。建树运行在 $O(n \\log n)$（见[这里](Сортировка_слиянием#Асимптотика "wikilink")），回答查询在 $O(\\log^2 n)$。

``` c++ numberLines
struct segtree {
    vector<int> val;
};

segtree t[4 * MAXN];

void build(int v, int tl, int tr) {
    if (tl + 1 == tr) {
        t[v].val.push_back(a[tl]);
        return;
    }
    int tm = (tl + tr) / 2;
    build(2 * v, tl, tm);
    build(2 * v + 1, tm, tr);
    t[v].val.resize(t[2 * v].val.size() + t[2 * v + 1].val.size());
    merge(t[2 * v].val.begin(), t[2 * v].val.end(),
              t[2 * v + 1].val.begin(), t[2 * v + 1].val.end(),
              t[v].val.begin());
}

int get(int v, int tl, int tr, int l, int r, int x) {
    if (tl >= r || l >= tr) {
        return 0;
    }
    if (l <= tl && tr <= r) {
        return lower_bound(t[v].val.begin(), t[v].val.end(), x - 1) - t[v].val.begin();
    }
    int tm = (tl + tr) / 2;
    return get(2 * v, tl, tm, l, r, x) + get(2 * v + 1, tm, tr, l, r. x);
}
```

带修改查询的版本需要[更重的结构](Двумерные_структуры_данных "wikilink")。

[分类：笔记](Категория:Конспект "wikilink") [分类：区间查询数据结构](Категория:Структуры_данных_для_запросов_на_отрезке "wikilink")
