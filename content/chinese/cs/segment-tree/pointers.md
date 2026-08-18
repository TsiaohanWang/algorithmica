---
title: 指针线段树
weight: 1
prerequisites:
- .
---

本文实现支持单点修改与区间求和的线段树。第一个实现用指针。它不是最快、最紧凑的，但最通用、最好懂。

**注记**。几乎处处我们都会用半开区间——记作 $[l, r)$——而不是闭区间。尽管反直觉，这会让代码略简单，而且总体上是编程中的好实践，类似从零开始编号。

### 内存存储

线段树的每个顶点是*结构体*，包含指向子节点的引用、自己的边界 $[l, r)$ 以及题目所需的额外信息——这里就是区间和。

顶点在构建时创建、没有固定顺序，因此子节点引用只是指向另一个相同结构体的指针。

```cpp
struct Segtree {
    int lb, rb; // 线段左右边界
    int s = 0; // 当前线段的和
    Segtree *l = 0, *r = 0; // 指向子节点的指针（0 表示没有子节点）
    
    Segtree(int lb, int rb) { /* 构造函数：创建时调用的方法 */ }
    void add(int k, int x) { /* 对 a[k] += x 作出反应 */ }
    int sum(int lq, int rq) { /* 输出 [lq, rq) 的和 */ }
};
```

在竞赛题中，查询常以「字符串 `0 k x` 表示加、`1 l r` 表示和」的格式给出。可以这样解析：

```cpp
int n, q;
cin >> n >> q;

Segtree s(0, n);

while (q--) {
    int t, x, y;
    cin >> t >> x >> y;
    if (t)
        s.add(x, y);
    else
        cout << s.sum(x, y) << endl;
}
```

剩下的就是实现构建和查询。

### 构建

线段树可以用递归构造函数构建，它创建子节点直到到达叶子：

```cpp
Segtree(int lb, int rb) : lb(lb), rb(rb) {
    if (lb + 1 < rb) {
        // 如果不是叶子，创建子节点
        int t = (lb + rb) / 2;
        l = new Segtree(lb, t);
        r = new Segtree(t, rb);
    }
}
```

如果初始数组非零，可以在建立引用的同时累加和：

```cpp
Segtree(int lb, int rb) : lb(lb), rb(rb) {
    if (lb + 1 == rb)
        s = a[lb];
    else {
        int t = (lb + rb) / 2;
        l = new Segtree(lb, t);
        r = new Segtree(t, rb);
        s = l->s + r->s;
    }
}
```

也可以之后再单独遍历数组，把每个数逐个加入。

### 修改

对加法查询，递归下潜直到到达对应元素 $k$ 的叶子，在所有中间顶点加 $x$：

```cpp
void add(int k, int x) {
    s += x;
    // 检查是否有子节点：
    if (l) {
        // 若 k 在左半
        if (k < l->rb)
            l->add(k, x);
        else
            r->add(k, x);
    }
}
```

### 求和

求和更复杂——需要分情况讨论查询区间与顶点区间如何相交：

```cpp
int sum(int lq, int rq) {
    if (lb >= lq && rb <= rq)
        // 如果完全在查询区间内，输出和
        return s;
    if (max(lb, lq) >= min(rb, rq))
        // 如果与查询区间不相交，输出零
        return 0;
    // 否则就复杂了 —— 从子节点出发，让它们自己决定
    return l->sum(lq, rq) + r->sum(lq, rq);
}
```

### 优化

这个实现简单、可扩展，但时间和内存上相当低效，尽管用它能通过约 90% 的竞赛题。

相对容易的优化：

- 可以不在节点里存线段边界 `lb` 和 `rb`，而在下潜时重算。
- 在 64 位系统上，不用 `new` 和指针，而改用数组/向量分配顶点、用相对下标更划算：它们只占 4 字节，而不是 8。

不过，指针实现慢的主要原因是需要反复沿引用走才能取到所需顶点的数据。事实证明，如果给顶点规定唯一编号并把它们按这个顺序排在数组上，就能完全去掉引用——更多细节可看[E-maxx](http://e-maxx.ru/algo/segment_tree)和[CodeForces](https://codeforces.com/blog/entry/18051)。
