---
title: Prim 算法
weight: 2
prerequisites:
  - safe-edge
published: true
---

安全边引理告诉我们，可以逐步构造最小生成树，每次加入一条我们确切知道对连接某个割而言是最小的边。

利用这一点的方法之一就是 *Prim 算法*：

- 初始时，生成树是任意一个顶点。
- 在最小生成树找到之前，反复选择一条权重最小的边，它从当前生成树的某个顶点出发，连到一个尚未加入的顶点。把这条边加入生成树，然后重新开始，直到生成树构造完成。

这个算法与 Dijkstra 算法非常相似，只不过我们选择下一个顶点时使用的权重函数不同——用的是连接它的最小边的权重，而不是到它的总距离。

完全朴素的实现是 $O(nm)$——每次都遍历所有边：

```c++
const int maxn = 1e5, inf = 1e9;
vector from, to, weight;
bool used[maxn]

// считать все рёбра в массивы

used[0] = 1;
for (int i = 0; i < n-1; i++) {
    int opt_w = inf, opt_from, opt_to;
    for (int j = 0; j < m; j++)
        if (opt_w > weight[j] && used[from[j]] && !used[to[j]])
            opt_w = weight[j], opt_from = from[j], opt_to = to[j]
    used[opt_to] = 1;
    cout << opt_from << " " << opt_to << endl;
}
```

$O(n^2)$ 的实现：

```c++
const int maxn = 1e5, inf = 1e9;
bool used[maxn];
vector< pair<int, int> > g[maxn];
int min_edge[maxn] = {inf}, best_edge[maxn];
min_edge[0] = 0;

// ...

for (int i = 0; i < n; i++) {
    int v = -1;
    for (int u = 0; u < n; u++)
        if (!used[u] && (v == -1 || min_edge[u] < min_edge[v]))
            v = u;

    used[v] = 1;
    if (v != 0)
        cout << v << " " << best_edge[v] << endl;

    for (auto e : g[v]) {
        int u = e.first, w = e.second;
        if (w < min_edge[u]) {
            min_edge[u] = w;
            best_edge[u] = v;
        }
    }
}
```

和 Dijkstra 算法一样，也可以不做最优顶点的线性查找，而是用优先队列维护它。这样就得到 $O(m \log n)$ 的实现：

```c++
set< pair<int, int> > q;
int d[maxn];

while (q.size()) {
    v = q.begin()->second;
    q.erase(q.begin());

    for (auto e : g[v]) {
        int u = e.first, w = e.second;
        if (w < d[u]) {
            q.erase({d[u], u});
            d[u] = w;
            q.insert({d[u], u});
        }
    }
}
```

$O(n^2)$ 的算法也不该忘记——在稠密图的情况下它表现更好。