---
title: 延迟构建
weight: 5
prerequisites:
- pointers
- lazy-propagation
---

来看我们最熟悉的子段求和问题，不过现在所有下标不再限于 $10^5$ 或 $10^6$，而是达到 $10^9$ 甚至 $10^{18}$。

所有渐近复杂度我们仍然大体可以接受：

$$
    \log_2 10^6 \approx 20
\\  \log_2 10^9 \approx 30
\\  \log_2 10^{18} \approx 60
$$

唯一的问题是构建阶段，它需要与 $n$ 线性相关的时间和内存。

解决办法是不在一开始就显式创建树的所有顶点。初始只创建根，其余顶点在需要写入非默认值时再现场创建——就像 [懒标记传播](../lazy-propagation) 那样：

```cpp
struct Segtree {
    int lb, rb;
    int s = 0;
    Segtree *l = 0, *r = 0;

    Segtree(int lb, int rb) : lb(lb), rb(rb) {
        // а тут ничего нет
    }

    // создает детей, если нужно
    void extend() {
        if (!l && lb + 1 < rb) {
            int t = (lb + rb) / 2;
            l = new segtree(lb, t);
            r = new segtree(t, rb);
        }
    }
    
    // ...
};
```

现在仿照 `push`，在所有方法的开头检查子节点是否已创建，如果没有就创建它们。

```cpp
void add(int k, int x) {
    extend();
    s += x;
    if (l) {
        if (k < l->rb)
            l->add(k, x);
        else
            r->add(k, x);
    }
}

int sum(int lq, int rq) {
    if (lb >= lq && rb <= rq)
        return s;
    if (max(lb, lq) >= min(rb, rq))
        return 0;
    extend();
    return l->sum(lq, rq) + r->sum(lq, rq);
}
```

这种方法主要适用于指针实现；如果使用索引，则可以不把顶点存在数组里，而是存在哈希表中：查询会变慢，但渐近复杂度不变。另外注意，无论哪种方式，每次查询都需要 $O(\log n)$ 的额外内存来创建新顶点，因此内存的渐近复杂度通常是 $O(q \log n)$。

另外，如果所有查询事先已知，可以在处理前把它们的坐标压缩。作者通常这样做：

```cpp
vector<int> compress(vector<int> a) {
    vector<int> b = a;
    sort(b.begin(), b.end());
    b.erase(unique(b.begin(), b.end()), b.end());
    for (int &x : a) 
        x = int(lower_bound(b.begin(), b.end(), x) - b.begin());
    return a;
}
```

大多数情况下，使用动态构建就像杀鸡用牛刀。先试试更简单的方法：也许直接放进 `set` 就够了。