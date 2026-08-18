---
title: 笛卡尔树（treap）
authors:
  - Сергей Слотин
date: 2022-01-22
created: '2018'
prerequisites:
  - .
  - ../basic-structures/heap
  - /math/probability/expectation
weight: 1
published: true
---

勒内·笛卡尔（法语 *René Descartes*）是 17 世纪伟大的法国数学家和哲学家。

笛卡尔不是笛卡尔树的创建者，但他创建了我们熟知并喜爱的笛卡尔坐标系。

笛卡尔树这样定义和构建：

* 在平面上放置 $n$ 个点。它们的 $x$ 称为*键*，$y$ 称为*优先级*。
* 选最高的点（$y$ 最大，多个则任取），称它为*根*。
* 对根左侧（$x$ 更小）的所有顶点递归运行同样过程。若左侧至少有一个顶点，把左部分的根接为当前根的左儿子。
* 类似对右部分，给根加右儿子。

注意若所有 $y$ 和 $x$ 都不同，树唯一确定。

若把所得结构画到平面上，确实得到一棵树——按惯例根在上：

![树的顶点及其坐标表示](../img/treap.png)

因此笛卡尔树同时是 $x$ 上的*二叉树*和 $y$ 上的*堆*。所以它有好多别名：

- 堆树（дерамида，дерево + пирамида）
- 树堆（дуча）
- 堆叉树（пиВо）
- 堆树（куРево）
- Treap（tree + heap）

英文通常叫 *cartesian* 或 *treap*，俄文常简写为「ДД」。

### 作为二叉搜索树

稍加修改，笛卡尔树能做任何[二叉搜索树](../)能做的事，例如：

- 向集合加数 $x$；
- 判断集合中是否有数 $x$；
- 找第一个不小于 $x$ 的数——类似 `lower_bound`；
- 求区间 $[l, r]$ 中的数的个数。

与所有平衡搜索树一样，所有操作按树高运行：$O(\log n)$。

## 优先级与复杂度

笛卡尔树的对数高度不是靠不变量和启发式保证，而是靠概率论：事实证明，若所有优先级（$y$）随机选，则顶点平均深度是对数的。因此 treap 也叫*随机化*搜索树。

**定理**。笛卡尔树中顶点深度的期望是 $O(\log n)$。

**证明**。 引入函数 $a(x, y)$，若 $x$ 是 $y$ 的祖先则为 1，否则为 0。这类函数叫*指示变量*。

顶点深度等于其祖先数，因此

$$
d_i = \sum_{j=1}^n a(j, i)
$$

其期望为

$$
E[d_i] = E[\sum_{j \neq i} a(j, i)] = \sum_{j \neq i} E[a(j, i)] = \sum_{j \neq i} p(j, i)
$$

其中 $p(x, y)$ 是 $a(x, y) = 1$ 的概率，即顶点 $x$ 是 $y$ 祖先的概率。这里用了期望线性这个重要性质。

现在只需对所有可能祖先算这些概率并求和。但先要一个辅助命题。

**引理**。顶点 $x$ 是 $y$ 的祖先，如果它的优先级大于半开区间 $(x, y]$ 中所有顶点（不一般性设 $x < y$）。

**必要性**。若 $x$ 不是最高的，则 $x$ 与 $y$ 之间存在优先级比 $x$ 高的顶点。它不可能是 $x$ 的后代，因此 $x$ 和 $y$ 会被它分开。

**充分性**。若区间右侧有某个优先级更高的顶点，那么它的左儿子会是 $x$ 的某个祖先。因此 $y$ 右侧的一切都不影响。

任何区间上的顶点成为最高优先级顶点的概率相同。结合此事实与引理结果，可得所求概率的表达式——顶点 $x$ 要为 $y$ 的祖先，其优先级须大于 $x$ 到 $y]$ 区间上其余 $|x - y|$ 个顶点：

$$
p(x, y) = \frac{1}{|x-y|+1}
$$

现在，为求期望深度，把这些概率求和：

$$
E[d_i] = \sum_{j \neq i} p(j, i)
       = \sum_{j \neq i} \frac{1}{|i-j|+1}
       = \sum_{j < i} \frac{1}{i - j} + \sum_{j > i} \frac{1}{j - i}
       \leq 2 \cdot \sum_{k=2}^n \frac{1}{k}
       = O(\log n)
$$

最后一步前得到的是调和级数和。

值得注意的是，顶点期望深度与其位置有关：中间的顶点约比两端的深一倍。

**练习**。 仿照这个推理推导 quicksort 的复杂度。

## 实现

笛卡尔树最方便用指针和结构体写。

创建 `Node` 结构，存键、优先级、左右儿子指针：

```c++
struct Node {
    int key, prior;
    Node *l = 0, *r = 0;
    Node(int key) : key(key), prior(rand()) {}
};
```

指向根的指针足以标识整棵树。因此当我们说「函数接受两棵树」，实际指指向它们根的指针。把零指针看作「空」树。

声明两个改变树结构的辅助函数：一个分裂树、一个合并树。如后所见，几乎所有需要的函数都能轻易用它们表达。

### Merge

接受两棵树（两个根 $L$ 和 $R$），已知左树所有顶点键都小于右树所有顶点。要把它们合并成一颗不破坏性质的树：按键仍是树、按优先级仍是堆。

先选哪个顶点做根。只有两个候选——左根 $L$ 或右根 $R$——取优先级更大的。

为确定起见设是左根。那么最终树根的左儿子应是 $L$ 的左儿子。右儿子更麻烦：可能需要与 $R$ 合并。因此递归做 `merge(l->r, r)` 并把结果作为右儿子。

```c++
Node* merge(Node *l, Node *r) {
    if (!l) return r;
    if (!r) return l;
    if (l->prior > r->prior) {
        l->r = merge(l->r, r);
        return l;
    }
    else {
        r->l = merge(l, r->l);
        return r;
    }
}
```

### Split

接受树 $P$ 和键 $x$，按它把树分成两棵：$L$ 应含所有不大于 $x$ 的键，$R$ 应含所有大于 $x$ 的键。

该函数先决定根应属于哪棵，再递归分裂它的右或左半、接好：

```c++
pair<Node*, Node*> split(Node *p, int x) {
    if (!p) return {0, 0};
    if (p->key <= x) {
        auto [l, r] = split(p->r, x);
        p->r = l;
        return {p, r};
    }
    else {
        auto [l, r] = split(p->l, x);
        p->l = r;
        return {l, p};
    }
}
```

### 例子：插入

`merge` 和 `split` 本身不太有用，但能帮写其余一切。

例如，要往树里加数 $x$，可以用 `split` 按 $x$ 切开、创建含单个数 $x$ 的新顶点、再用 `merge` 把三棵树粘起来：

```c++
Node *root = 0;

void insert(int x) {
    auto [l, r] = split(root, x);
    Node *t = new Node(x);
    root = merge(l, merge(t, r));
}
```

### 例子：区间和修改

有时需为更高级操作写一些修改。

例如可能想算区间上的数的和。为此顶点还要存自己的数与「区间」上的和：

```c++
struct Node {
    int val, sum;
    // ...
};
```

`merge` 和 `split` 时要让这个和保持最新。

与其按需改 `merge` 和 `split`，写个辅助函数 `upd`，在更新顶点子节点时调用：

```c++
int sum(Node* v) { return v ? v->sum : 0; }
// 对空指针访问会报错

void upd(Node* v) { v->sum = sum(v->l) + sum(v->r) + v->val; }
```

在 `merge` 和 `split` 里只需在返回顶点前调用 `upd`，就不会坏：

```c++
Node* merge(Node *l, Node *r) {
    // ...
    if (...) {
        l->r = merge(l->r, r);
        upd(l);
        return l;
    }
    else {
        // ...
    }
}

pair<Node*, Node*> split(Node *p, int x) {
    // ...
    if (...) {
        // ...
        upd(p);
        return {p, r};
    }
    else {
        // ...
    }
}
```

那么求和查询只需切出所需区间、求其和：

```c++
int sum(int l, int r) {
    auto [T, R] = split(root, r);
    auto [L, M] = split(T, l);
    int res = sum(M);
    root = merge(L, merge(M, R));
    return res;
}
```

### 小重构

大多数操作的实现总差不多——切出 $l$ 到 $r$ 区间、对它做点什么、再粘回去。

重复代码不好。用 C++ 的能力定义接受另一个函数（它会在所需区间上做有用的事）的函数：

```c++
int apply(int l, int r, auto f) {
    auto [T, R] = split(root, r);
    auto [L, M] = split(T, l);
    int res = f(M);
    root = merge(L, merge(M, R));
    return res;
}
```

这样用：

```c++
apply(l, r, sum);
```

对多数操作，方便传 lambda，如果它还没为 `upd` 实现。
