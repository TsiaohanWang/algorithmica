---
title: 可回滚结构
weight: 1
authors:
  - Сергей Слотин
date: {}
published: true
---

任何结构的状态都以某种方式存在于内存中：在某几个数组里，或者更一般地说，在内存中某些确定的地址处。为简单起见，设有一个大小为 $n$ 的数组 $a$，需要处理赋值和读取查询，偶尔还要把改动回滚回去。

### 改动列表

支持简单回滚状态的一种最简单通用的方式，是维护所有受影响元素的改动日志。

如果只需把改动回滚到某个过去状态（类似「ctrl+z」），可以建一个栈，存「哪个单元变了、它之前的值是什么」的 pair，回滚状态时按相反顺序遍历它、恢复原值。

```cpp
int a[N];

stack< pair<int, int> > s;

void change(int k, int x) {
    s.push({k, a[k]});
    a[k] = x;
}

void rollback() {
    while (!s.empty()) {
        auto [k, x] = s.top();
        a[k] = x;
        s.pop();
    }
}
```

这种做法会给所有操作加上小的常数开销，但能让结构回滚——要么回滚到给定初始状态，要么回滚到某个过去状态（如果除了位置和值之外，还在栈里存某种时间戳）。

### 版本数组

稍微重新表述问题。有一个初始全零的数组 $a$，需要支持两种操作：

1. 赋值 $a[k] = x$。
2. 把数组清零。

这个问题可以更优雅地解决。建一个全局时间计数器 $t$，以及一个与 $a$ 同大小、初始全零的*版本*数组 $v$：它存对应元素最后一次被修改的时间。

```cpp
int t = 1;
int a[N], v[N];
```

约定：如果元素版本等于当前时间 $t$，则它有效，否则元素为零：

```cpp
int get(int k) {
    return (v[k] == t ? a[k] : 0);
}
```

现在，赋值元素时更新它的版本：

```cpp
void change(int k, int x) {
    a[k] = x;
    v[k] = t;
}
```

清零数组时，只需把计数器 $t$ 加一：

```cpp
void rollback() {
    t++;
} 
```

这种做法编码更简单、开销更小，但适用性稍差。

### 「胖」节点

现在我们需要的不再是回滚改动，而是读取过去某时刻的某些元素。改动列表不行，因为对每次读取，最坏情况下要查看 $O(n)$ 次最近的改动。

为每个元素建一个*版本列表*，每次修改时把新版本及修改时间加到末尾。

```cpp
int t = 0;
vector< pair<int, int> > versions[N];

void change(int k, int x) {
    versions[k].push_back({t++, x});
}
```

读取时就可以只看影响所需单元的改动，而不必看全部。还能更快——列表元素按时间排序，因此可以用二分查找找出不超过查询时间的最新改动：

```cpp
int get(int k, int v) {
    auto it = upper_bound(versions[k].begin(), versions[k].end(), v);
    return (--it)->second;
}
```

这个解法每次修改 $O(1)$、每次查询 $O(\log n)$。

### 改动树

形式上，前面的方法已经实现了可持久化，但含义非常有限：我们无法快速回滚到任意版本并从它「分叉」，同时保留来自「另一个未来」的所有版本。

这个问题可以通过在每个改动旁存它分叉自的版本号 $p$ 来解决：

```cpp
struct Node {
    int k, x, p;
};

vector<Node> versions;

void change(int k, int x, int v) {
    versions.push_back({k, x, v});
}
```

要在时刻 $v$ 找单元 $k$ 的值，沿这个数组回溯：

```cpp
int get(int k, int v) {
    int res = 0;
    for (int u = v; u > v; u = u = versions[u].p)
        if (versions[u].k == k)
            res = versions[u].x;
    return res;
}
```

这个解法实现了完整的可持久化数组，但最坏情况下运行在 $O(n)$。

改动树可以用各种方式加速，用内存换时间。例如，可以在某些节点保存*检查点*——对应此刻数组状态的完整数组。

一种流行的做法是在每次读取查询时随机保存检查点——概率与从下一个检查点恢复数组所需的额外工作量成正比。
