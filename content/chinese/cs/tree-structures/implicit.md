---
title: 隐式键
prerequisites:
- treap
weight: 2
---

普通 treap（笛卡尔树）是用于集合的结构，其中每个元素都有某个键。这些键在集合上定义了顺序，所有对 treap 的查询通常都以某种方式与这个顺序相关。

但如果我们有非平凡地改变这个顺序的查询呢？例如，我们有一个数组，需要支持：

1. 输出任意区间上的和，
2. 「翻转」任意区间，即把从 $l$ 到 $r$ 的元素按相反顺序重新排列，不改变其余部分。

如果没有第二个操作，我们只需把元素下标当作键，但有了翻转操作，就没有办法快速保持键的最新。

解决办法：扔掉键，转而维护能在需要时隐式恢复键的信息。具体说，在每个顶点旁存它子树的大小：

```c++
struct Node {
    int prior, size = 1;
    //         ^ 子树大小
    // ...
};
```

于是键（元素的位置）可以恢复为它左侧的元素个数——可以在沿树下降时重算。

子树大小像和一样维护——写一个辅助函数，在每次顶点结构变化后调用它。

```c++
int size(Node *v) { return v ? v->size : 0; }

void upd(Node *v) { v->size = 1 + size(v->l) + size(v->r); }
```

`merge` 操作不变，因为它任何地方都不用键；而 `split` 需要用根的位置代替它的键。现在把 `split` 理解为「切出前 `k` 个元素」更合适：

```c++
pair<Node*, Node*> split(Node *p, int k) {
    if (!p) return {0, 0};
    if (size(p->l) + 1 <= k) {
        auto [l, r] = split(p->r, k - size(p->l) - 1);
        //                        ^ 右儿子不知道自己左侧有多少顶点
        p->r = l;
        upd(p);
        return {p, r};
    }
    else {
        auto [l, r] = split(p->l, k);
        p->l = r;
        upd(p);
        return {l, p};
    }
}
```

完事。现在我们就有了一个很棒的灵活结构，可以随意剪切，而不依赖键。

### 例子：ctrl+x、ctrl+v

```c++
Node* ctrlx(int l, int r) {
    auto [T, R] = split(root, r);
    auto [L, M] = split(T, l);
    root = merge(L, R);
    return M;
}
```

```c++
void ctrlv(Node *v, int k) {
    auto [l, r] = split(root, k);
    root = merge(l, merge(v, r));
}
```

### 例子：翻转

回到最初的问题：需要在 $O(\log n)$ 内处理任意子串的翻转查询：把 $a_l$ 与 $a_r$ 交换，$a_{l+1}$ 与 $a_{r-1}$ 交换，依此类推。

在每个顶点存一个标志 `rev`，表示它的子段被翻转了：

```c++
struct Node {
    bool rev;
    // ...
};
```

与[线段树](/cs/segment-tree)中延迟操作技巧类似——当我们遇到这样的顶点时，交换它两个子节点的引用，并把标志传给它们自己：

```c++
void push(node *v) {
    if (v->rev) {
        swap(v->l, v->r);
        if (v->l)
            v->l->rev ^= 1;
        if (v->r)
            v->r->rev ^= 1;
    }
    v->rev = 0;
}
```

类似地，在 `merge` 和 `split` 开头调用这个函数。

`reverse` 函数这样实现：切出所需区间，翻转标志。

```c++
void reverse(int l, int r) {
    auto [T, R] = split(root, r);
    auto [L, M] = split(T, l);
    M->rev ^= 1;
    root = merge(L, merge(M, R));
}
```
