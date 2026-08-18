---
title: Graham 算法
weight: 3
---

Graham 算法是对 Jarvis 算法的优化，基于如下观察：如果把所有点相对于点 $p_0$ 按极角排序，那么凸包就是这种排序后点数组的某个子序列。

算法逐个为排序后数组的每个前缀构建凸包。可以注意到，往凸包中加入第 $i$ 个点时，只需删除一些最后加入的、不会进入新凸包的点，即那些被新点和它前一个点「覆盖」的点。

![](../img/graham.gif)

为了高效地做这种删除，我们可以把凸包存在栈里，在 `while` 循环中看最后三个点，检查它们是否构成右转。如果是，就应删除中间的点——我们找到了一个包含 $p_{i-1}$ 的三角形 $(p_0, p_i, p_{i-2})$，因此可以删除它。

每个点被加入一次、至多被删除一次，这只需常数次操作。因此运行时间取决于排序的时间，即 $O(n \log n)$。

```c++
vector<r> graham(vector<r> points) {
    // 像之前一样找 p0
    r p0 = points[0];
    for (r p : points)
        if (p.x < p0.x || (p.x == p0.x && p.y < p0.y))
            p0 = p;

    // 按极角排序点
    sort(points.begin(), points.end(), [&](r a, r b){
        return (a - p0) ^ (b - p0) > 0;
    });

    vector<r> hull;
    for (r p : points) {
        // 只要栈顶构成非凸，就删除它
        while (hull.size() >= 2) {
            r new_vector = p - hull.back();
            r last_vector = hull.back() - hull[hull.size() - 2];
            // 如果最后两个向量向左绕，删除最后那个点
            if (new_vector ^ last_vector > 0)
                hull.pop_back();
            else
                break;
        }
        hull.push_back(p);
    }
    return hull;
}
```

[交互式可视化](https://visualgo.net/en/convexhull)，可以在给定点集上运行算法的所有步骤。
