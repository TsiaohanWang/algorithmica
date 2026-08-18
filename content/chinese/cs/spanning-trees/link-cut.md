---
title: Link-cut 树
draft: true
---

**Splay 树**（Tarjan–Sleator 树）是由 Robert Tarjan 和 Daniel Sleater 专门为加速另一种数据结构（我们稍后介绍）而发明的二叉搜索树。Splay 树通过把最近使用过的数据（顶点）「提升」到根来快速访问它们，摊还时间复杂度为 $\hat{O}(n\,log\,n)$。

## 性质

Splay 树中的基本操作是 $expose(v)$，它负责树的平衡。它通过一系列 $rotate$ 操作把顶点 $v$ 变成树的根。围绕边 $(v, u)$ 的*旋转*（其中 $u$ 是 $v$ 的祖先；我们把这个操作记为 $rotate(v)$）把 $v$「提升」一层，同时把 $u$「降下去」，并且不破坏二叉搜索树的性质。
![](https://neerc.ifmo.ru/wiki/images/2/24/Зиг.png)
本质上，splay 树是一个具有摊还时间的确定性[笛卡尔树](treap)（正因如此，无法高效地实现可持久化的 splay 树）。splay 树工作的基本函数是 $find(x)$——找到最大键不超过 $x$ 的顶点 $u$。$find(x)$ 的实现方式与其他搜索树相同——普通的下降，但之后一定要执行 $expose(u)$。通过 $find(x)$ 可以实现 $split$ 和 $merge$ 操作：
+ $split(x, k)$ ——与笛卡尔树中一样，接收原始树 $x$，返回两棵树 $l$ 和 $r$，其中 $l$ 中的所有键都小于 $k$，$r$ 中的所有键都不小于 $k$。在树 $x$ 中执行 $find(k)$ 后，找到的顶点 $u$ 成为 $x$ 的根；注意此时 $u$ 左子树（记为 $l$）中所有顶点的键都小于 $k$，也就是说我们可以把左子树从 $u$ 上「切下来」，返回二元组 ${l, u}$。
+ $merge(l, r)$ ——接收两棵树 $l$ 和 $r$（其中 $l$ 中的所有键都小于 $r$ 中的所有键），返回由 $l$ 和 $r$ 的所有顶点组成的新树 $x$。用 $find$ 在 $r$ 中找到键最小的顶点，它将成为 $r$ 的根；注意它没有左儿子，于是直接把整棵树 $l$ 作为它的左儿子即可。
其余操作都可以通过这三个操作实现（例如 $add(x)$、$remove(x)$ 等）。

## 实现 $expose(v)$

如果直接用一系列 $rotate(v)$ 旋转实现 $expose(v)$（直到 $v$ 成为根），可以构造出它每次都运行 $O(n)$ 时间的例子（例如，树是一条一端悬垂的链，而 $find$ 每次访问的都是链的另一端）。为了在实现 $expose(v)$ 时达到 $\hat{O}(n\,log\,n)$ 的复杂度，使用了三个辅助操作——*zig*、*zig-zig* 和 *zig-zag*——它们是 $rotate$ 操作的组合。

### $zig-zig(v)$

记 $p(x)$ 为顶点 $x$ 的祖先，$L(x)$ 为这样的函数：如果 $x$ 是 $p(x)$ 的左儿子或 $p(x)$ 不存在，则返回 0；如果 $x$ 是 $p(x)$ 的右儿子，则返回 1。$zig-zig(v)$ 在 $v$ 不是根的直接儿子且 $L(x)=L(p(x))$ 时使用。$zig-zig(v)$ 由两个操作 $rotate(v)$ 和 $rotate(w)$（其中 $w$ 是执行 $zig-zig(v)$ 之前 $v$ 的祖先）组成，并且必须按这个顺序执行。

### $zig-zag(v)$

$zig-zag(v)$ 在 $v$ 不是根的直接儿子且 $L(x)\neq L(p(x))$ 时使用。$zig-zag(v)$ 由两个操作 $rotate(w)$ 和 $rotate(v)$（其中 $w$ 是执行 $zig-zag(v)$ 之前 $v$ 的祖先）组成，并且必须按这个顺序执行。

### $zig(v)$

$zig(v)$ 在 $v$ 是根的直接儿子时使用，它就是一个 $rotate(v)$ 操作。

### 最终算法

这样，实现 $expose(v)$ 只需要在循环中直到 $v$ 成为根为止，处理三种情况：
1. $v$ 是根的直接儿子。那么执行 $zig(v)$。
2. $L(v) = L(p(v))$ ——那么执行 $zig-zig(v)$。
3. $L(v) \neq L(p(v)$ ——那么执行 $zig-zag(v)$。

## 隐式 splay 树

假设 splay 树存储了一个数组，其中 $x$ 左子树中的顶点所对应的数组元素都在 $x$ 的元素的左边，右子树中的都在右边——就像按隐式键的笛卡尔树一样。那么 $find(k)$ 就会在树中寻找对应数组中左起第 $k$ 个元素的顶点。这样，隐式 splay 树可以解决与隐式笛卡尔树相同的问题。实践中，由于常数很小（参见运行时间），splay 树通常比笛卡尔树快好几倍，所以如果笛卡尔树塞不进去，又有充足的时间和编写 splay 树的经验，可以尝试使用它（不过，再说一遍，可持久化是搞不定的）。

## 实现

```c++
struct node {
    int x, sz = 1;
    int p = -1, l = -1, r = -1;
    bool lft = 0;

    node() {}

    node(int x) : x(x) {}
};

node v[maxn];
int root = -1, mx = 0;

int gsz(int x) {
    return (x == -1 ? 0 : v[x].sz);
}

void upd(int x) {
    v[x].sz = 1 + gsz(v[x].l) + gsz(v[x].r);
}

// Отсоединяет вершину от предка, обновляя необходимые параметры

void disconnect(int x) {
    if (x == -1 || v[x].p == -1) return;
    if (v[v[x].p].l == x) v[v[x].p].l = -1;
    else v[v[x].p].r = -1;
    upd(v[x].p); v[x].p = -1; v[x].lft = 0;
}

// Делает вершину x левым или правым (в зависимости от lft) сыном y

void connect(int x, int y, bool lft) {
    if (x == -1 || y == -1) return;
    v[x].lft = lft; v[x].p = y;
    if (lft) v[y].l = x;
    else v[y].r = x;
    upd(y);
}

void rotate(int x) {
    int y = v[x].p, z = v[y].p, yl = v[y].lft, xl = v[x].lft;
    disconnect(x); disconnect(y);
    if (xl) {
        int b = v[x].r;
        disconnect(b); connect(b, y, 1); connect(y, x, 0);
    } else {
        int b = v[x].l;
        disconnect(b); connect(b, y, 0); connect(y, x, 1);
    }
    connect(x, z, yl);
}

// Если вместо expose написать splay, то больше людей поймут, что вы написали splay-дерево, посмотрев код посылки на кф 

void splay(int x) {
    if (x == -1) return;
    while (v[x].p != -1) {
        int y = v[x].p;
        if (v[y].p == -1) {
            rotate(x);
            break;
        }
        if (v[x].lft == v[y].lft) {
            rotate(y);
            rotate(x);
        } else {
            rotate(x);
            rotate(x);
        }
    }
    root = x;
}

// Функция find, которую я зачем-то назвал get

int get(int x, int k) {
    if (x == -1) return -1;
    while (1) {
        if (gsz(v[x].l) == k)
            break;
        if (k < gsz(v[x].l)) {
            x = v[x].l;
        } else {
            k -= (gsz(v[x].l) + 1);
            x = v[x].r;
        }
    }
    splay(x);
    return x;
}

pair<int, int> split(int x, int k) {
    if (x == -1) return {-1, -1};
    if (k == 0) return {-1, x};
    int aut = get(x, k - 1);
    int gg = v[aut].r;
    disconnect(gg);
    return {aut, gg};
}

int merge(int l, int r) {
    if (l == -1) return r;
    if (r == -1) return l;
    int bs = gsz(l);
    int aut = get(l, bs - 1);
    connect(r, aut, 0);
    return aut;
}
```

这是我写过的第一个也是最后一个 splay 树实现，所以代码这么长。最痛苦的是调试重挂接时顶点参数的更新。

## 运行时间

先引入必要的记号：$t_i$ 是 splay 树在第 $i$ 个查询上的运行时间，$T$ 是树在所有查询上的总运行时间。
运行时间的证明使用*势能法*。它大致是这样的：假设有一个大小为 $n$ 的数据结构，我们想估计它在 $q$ 个查询上的摊还时间。对结构的 $q+1$ 个状态各引入一个量 $\Phi_{i}$——势。再引入量 $a_i=t_i+\Phi_{i}-\Phi_{i-1}$——第 $i$ 次操作的*代价*。断言：如果 $a_i=O(f(n,q))$ 对某个函数 $f$ 成立，且 $\Phi_{i}=O(n\cdot f(n,q))$，那么 $T=O(f(n,q))$。这个事实的证明相当简单，我们不打算给出，直接进入 splay 树运行时间的证明。
记 $C(v)$ 为顶点 $v$ 的子树大小。那么把树的所有顶点 $v$ 的 $C(v)$ 的二进制对数之和称为我们这棵树的势 $\Phi$（简记 $r(v)=log_2\,C(v)$）。注意，这个量非负且不超过 $O(n\,log\,n)$。啊啊啊啊这什么鬼，我到底为啥要写这些啊，明明已经有了维基讲义（大概是觉得光贴代码太蠢了吧）

# Link-cut 树

考虑下面这个问题：

> 给定一个由 $n$ 个顶点组成的森林。请求有三种类型：
+ $link(u,\,v)$ ——用一条边连接顶点 $u$ 和 $v$
+ $cut(u,\,v)$ ——删除顶点 $u$ 和 $v$ 之间的边
+ $get(u,\,v)$ ——求 $u$ 和 $v$ 之间路径的长度
需要回答所有第三种类型的请求。保证每次请求之后图仍然是森林。

有一种数据结构能以 $O(n\,log\,n)$ 的摊还时间解决这个问题——**Link-Cut Tree**，由 Tarjan 和 Sleator 发明（正是为了达到这个界才发明了 splay 树）。

## 基本思想

把森林中的每棵树挂在某个顶点上，并把边定向为指向根。引入操作 $expose(x)$，它使顶点 $x$ 成为它所在树的根。设原来的根是顶点 $y$，我们执行了 $expose(x)$。之后需要把 $x$ 与 $y$ 之间路径上每条边的方向反过来，以免破坏结构。看看我们如何用这个处理请求：
+ $link(u, v)$ ——在顶点 $u$ 的树上执行 $expose(u)$，在顶点 $v$ 的树上执行 $expose(v)$，然后用一条边把 $u$ 和 $v$ 连起来，新边指向的那一侧的顶点将成为树的新根。
+ $cut(u, v)$ ——直接删除顶点 $u$ 和 $v$ 之间的边；边原来指向的那一侧的顶点留在旧树中，另一侧的顶点进入新树，应把它设为新树的根。
+ $get(u,\,v)$ ——执行 $expose(u)$ 并求出顶点 $v$ 的深度。
如果直接实现 $expose$ 操作，每个请求在最坏情况下需要 $O(n)$ 的时间；但借助数据结构可以实现摊还的 $O(n\,log^2\,n)$ 甚至 $O(n\,log\,n)$。

## 加速

我们已经粗略描述了算法；现在需要弄清楚如何快速执行这些操作。事实证明，如果把每棵树分解成一组顶点不相交的竖直路径，并用按隐式键的笛卡尔树维护这些路径，那么算法的总复杂度为 $O(n\,log^2\,n)$，这一点将在最后证明。但如果用 splay 树代替笛卡尔树，复杂度甚至可以达到 $O(n\,log\,n)$，而这个事实的证明我并不了解。下面来看看快速算法是如何工作的。
初始时把每棵树分解成路径，具体怎么分解无所谓，所以直接做成 $N$ 条长度为 1 的路径即可。路径以 splay 树集合的形式存储，对每条路径存储其最高顶点的祖先指针。当需要执行 $expose(x)$ 时，我们沿着路径向上「跳」，同时把它们合并成一条（即从顶点 $x$ 移动到 $x$ 所在路径的顶端；然后向上移动一个顶点，把新路径与旧路径合并（可能发生的情况是我们没有落在路径的末端而是中间，这时不得不在该处「截断」路径），然后沿着这条路径继续向上跳，依此类推）。然后直接反转合并后路径中对应路径 $(x; y)$ 的那一段。乍一看——完全不理解为什么这个算法比之前的更快。然而出现了一个非常有趣的事实：不管来什么样的请求，结构都会自己优化自己，最终复杂度无论如何都是 $O(n\,log^{(2)}\,n)$。

TODO