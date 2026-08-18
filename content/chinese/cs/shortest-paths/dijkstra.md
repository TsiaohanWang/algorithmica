---
title: Dijkstra 算法
authors:
- Максим Иванов
editors:
- Сергей Слотин
weight: 3
---

Dijkstra 算法（英文 *Dijkstra's algorithm*）在无负权边的图中求从给定顶点 $s$ 到所有其他顶点的最短路。

有两个主要变体，运行时间 $O(n^2)$ 和 $O(m \log n)$，其中 $n$ 是顶点数、$m$ 是边数。

## 核心思想

建数组 $d$，对每个顶点 $v$ 存当前从 $s$ 到 $v$ 的最短路长度 $d_v$。初始 $d_s = 0$，其余顶点距离为无穷（或任何肯定大于最大可能距离的数）。

算法运行中逐步更新这个数组，找更优路径、减小距离。当得知到某顶点 $v$ 的路径已最优时，标记该顶点——在初始全零的数组 $a$ 中置一（$a_v=1$）。

算法由 $n$ 次迭代组成，每次选尚未标记、$d_v$ 最小的顶点 $v$：

$$
v = \argmin_{u | a_u=0} d_u 
$$

（注意第一次迭代会选中起始顶点 $s$。）

所选顶点在数组 $a$ 中标记，然后从 $v$ 做*松弛*：看所有出边 $(v,u)$，对每个 $u$ 尝试改进 $d_u$，做赋值

$$
d_u = \min (d_u, d_v + w)
$$

其中 $w$ 是边 $(v, u)$ 的长度。

![](../img/dijkstra.gif)

当前迭代结束，算法进入下一次：再选 $d$ 最小的顶点、从它松弛，依此类推。$n$ 次迭代后，图所有顶点都被标记，算法结束。

## 正确性

记 $l_v$ 为从 $s$ 到 $v$ 的距离。要证明算法结束时对所有顶点 $d_v = l_v$（不可达顶点除外——它们的距离保持无穷）。

先注意，对任意顶点 $v$ 总成立 $d_v \ge l_v$：算法不可能找到比所有现有最短路更短的路径（因为我们只做松弛）。

算法正确性证明基于下面命题。

**命题**。 某顶点 $v$ 被标记后，到它的当前距离 $d_v$ 已是最短，不再变化。

**证明** 用归纳。对第一次迭代显然成立——对 $s$ 有 $d_s=0$，即到它的最短路长度。

设该命题对之前所有迭代成立——即所有已标记顶点。证明当前迭代后仍成立，即所选顶点 $v$ 的最短路长度 $l_v$ 确实等于 $d_v$。

考虑到 $v$ 的任意最短路。记这条路径上第一个未标记顶点为 $y$，其前一个已标记顶点为 $x$（它们存在，因为 $s$ 已标记、$v$ 未标记）。记边 $(x, y)$ 的权重为 $w$。

![](../img/dijkstra-proof.png)

由于 $x$ 已标记，由归纳假设 $d_x = l_x$。因 $(x,y)$ 在最短路，$l_y=l_x+w$，恰好等于 $d_y=d_x+w$：我们在某时刻从已标记顶点 $x$ 做过松弛。

现在，可能 $y \ne v$ 吗？不可能，因为我们每次迭代选 $d_v$ 最小的顶点，而路径上任何在 $y$ 之后的顶点到 $s$ 的距离都更大。于是 $v = y$，$d_v = d_y = l_y = l_v$，证毕。

## 运行时间与实现

算法中唯一影响复杂度的可变部分是具体如何找 $d_v$ 最小的 $v$。

### 稠密图

若 $m \approx n^2$，则每次迭代只需遍历整个数组找 $\argmin d_v$。

```cpp
const int maxn = 1e5, inf = 1e9;
vector< pair<int, int> > g[maxn];
int n;

vector<int> dijkstra(int s) {
    vector<int> d(n, inf), a(n, 0);
    d[s] = 0;
    for (int i = 0; i < n; i++) {
        // 找尚未标记、d[v] 最小的顶点
        int v = -1;
        for (int u = 0; u < n; u++)
            if (!a[u] && (v == -1 || d[u] < d[v]))
                v = u;
        // 标记它并沿所有出边松弛
        a[v] = true;
        for (auto [u, w] : g[v])
            d[u] = min(d[u], d[v] + w);
    }
    return d;
}
```

这种算法复杂度 $O(n^2)$：每次迭代 $O(n)$ 找 argmin、$O(n)$ 松弛。

注意也可做少于 $n$ 次迭代。第一，最后一次迭代可以不做（那里已无可松弛）。第二，遇到不可达顶点（$d_v = \infty$）可立即结束。

### 稀疏图

若 $m \approx n$，找最小可更快。不线性遍历，而用能加元素、找最小值的结构——例如 `std::set` 可以。

在该结构中维护对 $(d_v, v)$，松弛时删旧 $(d_u, u)$、加新 $(d_v + w, u)$，找最优 $v$ 时取最小值（第一个元素）。

现在不需要数组 $a$：找最小值的结构本身充当尚未考察顶点集。

```cpp
vector<int> dijkstra(int s) {
    vector<int> d(n, inf);
    d[root] = 0;
    set< pair<int, int> > q;
    q.insert({0, s});
    while (!q.empty()) {
        int v = q.begin()->second;
        q.erase(q.begin());
        for (auto [u, w] : g[v]) {
            if (d[u] > d[v] + w) {
                q.erase({d[u], u});
                d[u] = d[v] + w;
                q.insert({d[u], u});
            }
        }
    }
    return d;
}
```

对每条边要向存 $O(n)$ 元素的二叉搜索树做两次查询，每次 $O(\log n)$，因此复杂度 $O(m \log n)$。注意完全图时这等于 $O(n^2 \log n)$，所以别忘前面的算法。

### 用堆

与其用二叉搜索树，「正确」的是用更专门、只支持加元素与找最小值的结构：堆。删任意元素稍麻烦，因此只忽略所有重复顶点。

```cpp
vector<int> dijkstra(int s) {
    vector<int> d(n, inf);
    d[root] = 0;
    // 声明用于*最小值*的优先队列（默认找最大值）
    using pair<int, int> Pair;
    priority_queue<Pair, vector<Pair>, greater<Pair>> q;
    q.push({0, s});
    while (!q.empty()) {
        auto [cur_d, v] = q.top();
        q.pop();
        if (cur_d > d[v])
            continue;
        for (auto [u, w] : g[v]) {
            if (d[u] > d[v] + w) {
                d[u] = d[v] + w;
                q.push({d[u], u});
            }
        }
    }
}
```

实践中 `priority_queue` 变体稍快。

除普通二叉堆，也可用其他堆。从理论角度看，[斐波那契堆](https://neerc.ifmo.ru/wiki/index.php?title=%D0%A4%D0%B8%D0%B1%D0%BE%D0%BD%D0%B0%D1%87%D1%87%D0%B8%D0%B5%D0%B2%D0%B0_%D0%BA%D1%83%D1%87%D0%B0)特别有意思：几乎所有操作 $O(1)$，但删除元素 $O(\log n)$。这能把松弛降为 $O(1)$，代价是取最小值增至 $O(\log n)$，得到 $O(n \log n + m)$ 而非 $O(m \log n)$。

### 路径恢复

常不仅要知道最短路长度，还要得到路径本身。

为此建数组 $p$，单元 $p_v$ 存顶点 $v$ 的*父节点*——最后一次沿边 $(p_v, v)$ 松弛的顶点。

可以随数组 $d$ 一起更新。例如在最后实现里：

```cpp
if (d[u] > d[v] + w) {
    d[u] = d[v] + w;
    p[u] = v; // <-- 到 u 的最短路经边 (v, u)
    q.push({d[u], u});
}
```

恢复路径只需沿 $v$ 的祖先走：

```cpp
void print_path(int v) {
    while (v != s) {
        cout << v << endl;
        v = p[v];
    }
    cout << s << endl;
}
```

注意这段代码按相反顺序打印路径。
