---
title: 找环
authors:
- Сергей Слотин
weight: 4
---

回忆一下，图 $G$ 中的*环*是从顶点 $v$ 出发又回到它自身的非零路径。如果图中没有环，则称该图为无环图。

为了找环，考虑另一种深度优先遍历方式：

```cpp
void dfs(int v, int p = -1) {
    for (int u : g[v])
        if (u != p)
            dfs(u, v);
}
```

这里我们不用数组 `used`，而是向递归传入参数 $p$，它等于我们来自的顶点的编号；如果遍历是从这个顶点开始的，则为 $-1$。

这种方式只对树是正确的——检查 `u != p` 保证我们不会沿着边原路返回，但如果图中有环，那么就会在某个时刻用完全相同的参数第二次调用 `dfs`，从而陷入无限循环。

如果我们能判断是否进入了无限循环，那恰好就是我们需要的。修改 `dfs`，使我们能判断进入环的时刻。为此，把数组 `used` 加回来，但用它检查我们是否曾经到过打算访问的顶点——如果到过，就说明存在环。

```cpp
const int maxn = 1e5;
bool used[maxn];

void dfs(int v, int p = -1) {
    if (used[v]) {
        cout << "Graph has a cycle" << endl;
        exit(0);
    }
    used[v] = true;
    for (int u : g[v])
        if (u != p)
            dfs(u, v);
}
```

如果需要还原环本身，可以不让程序结束，而是从递归中多次返回并输出顶点，直到回到发现环的那个顶点为止。

```cpp
// возвращает -1, если цикл не нашелся, и вершину начала цикла в противном случае
int dfs(int v, int p = -1) {
    if (used[v]) {
        cout << "Graph has a cycle, namely:" << endl;
        return v;
    }
    used[v] = true;
    for (int u : g[v]) {
        if (u != p) {
            int k = dfs(u, v);
            if (k != -1) {
                cout << v << endl;
                if (k == v)
                    exit(0);
                return k;
            }
        }
    }
    return -1;
}
```

和所有遍历一样，如果图有多个连通分量，或者图是有向的，就需要从不同分量的顶点多次启动 `dfs`。

```cpp
for (int v = 0; v < n; v++)
    if (!used[v])
        dfs(v);
```