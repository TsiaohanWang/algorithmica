---
title: Kruskal 算法
prerequisites:
- safe-edge
- /cs/set-structures/dsu
weight: 3
---

另一种使用安全边引理的方式——把所有边排序，并按权重递增的顺序尝试把它们加入初始为空的生成树。

如果下一条边连接的是已经连通的两个顶点，就忽略它。否则它就是安全边，因为它是连接某两个不同分量的边中最小的，可以加入。

听起来很简单：把所有边排序，循环遍历它们，并检查端点是否在不同的分量中。但用 `dfs` 从每条边的两端做朴素检查会花费 $O(nm)$。如果把检查换成[并查集](/cs/set-structures/dsu)，复杂度可以改进到 $O(m \log m)$——即排序边的开销。

除了并查集的实现之外，代码非常短：

```c++
struct Edge {
    int from, to, weight;
};

vector<Edge> edges;

sort(edges.begin(), edges.end(), [](Edge a, Edge b) {
    return a.weight < b.weight;
});

for (auto [a, b, w] : edges) {
    // компоненты разные, если лидеры разные
    if (p(a) != p(b)) {
        // добавим ребро (a, b)
        unite(a, b);
    }
}
```

由于生成树是[拟阵](/cs/combinatorial-optimization/matroid)的特殊情形，Kruskal 算法也就是 Rado–Edmonds 算法的特殊情形。