---
title: 堆排序
authors:
- Денис Акилов
editors:
- Сергей Слотин
weight: 6
date: 2021-10-21
prerequisites:
- /cs/basic-structures/heap
- selection
---

[选择排序](/cs/sorting/selection)之所以运行在平方级时间，原因在于每一步都要线性地找最小值。

要优化算法的运行时间，我们可以引入一种专门的数据结构，它支持从无序元素集合中快速取出最小值：把整个原始数组加进去，然后逐个把最小值取到新的有序数组里。

这正是[二叉堆](/cs/basic-structures/heap)所做的——每次操作 $O(\log n)$。用它就得到 $O(n \log n)$ 的算法：

```cpp
void heapsort(int* a, int n) {
    // 把数组复制进堆
    t_n = n;
    copy(a, a + n, t + 1);
    build_heap();
    for (int i = 1; i <= n; i++) {
        // 删除最小值，它会留在 t[n + 1 - i] 位置
        swap(t[1], t[n + 1 - i]);
        t_n--;
        sift_down(1);
    }
    // 得到数组 t[1..n]，其中所有元素按降序排列
    reverse(t, t + n + 1);
    copy(t, t + n, a);
}
```

值得注意的是，在「几乎有序」数组的情形下，算法可以稍作加速。如果保证每个元素到它在有序数组中位置的距离不超过 $k$，那么我们只需维护一个大小为 $O(k)$ 的堆，把数组看成大小为 $k$ 的「窗口」，每次加入新元素后写出最小值。这样的算法运行在 $O(n \log k)$。
