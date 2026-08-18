---
title: 基数排序
weight: 9
authors:
- Сергей Слотин
---

基数排序是把计数排序的思想应用到较大键上的一种方式。

假设要排序一个很大的 `int` 数组——比如说 $10^5$ 个元素。我们可以先用稳定的计数排序按前两个字节排序（即用 $\lfloor x / 2^{16} \rfloor$ 作为键），再把得到的序列按后两个字节排序（用 $x \bmod 2^{16}$ 作为键）。

使用向量数组计数的实现：

```cpp
const int c = (1<<16);

void radix_sort(vector<int> &a) {
    int n = (int) a.size();
    vector<int> b[c];

    for (int i = 0; i < n; i++)
        b[a[i] % c].push_back(a[i]);
    
    int k = 0;
    for (int i = 0; i < c; i++) {
        for (size_t j = 0; j < b[i].size(); j++)
            a[k++] = b[i][j];
        b[i].clear();
    }

    for (int i = 0; i < n; i++)
        b[a[i]/c].push_back(a[i]);
    
    k = 0;
    for (int i = 0; i < c; i++)
        for (size_t j = 0; j < b[i].size(); j++)
            a[k++] = b[i][j];
}
```

这个方法可以推广到任意类型和任意大小的键。
