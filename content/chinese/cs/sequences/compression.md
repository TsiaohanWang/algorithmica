---
title: 坐标压缩
authors:
- Сергей Слотин
weight: -1
date: 2022-04-20
---

把一串数字或某些其他对象转换成连续整数区段通常很有用——例如，把它的元素用作数组或某个其他结构的下标。

这个问题等价于给集合元素编号，可以用哈希表在 $O(n)$ 内完成：

```c++
vector<int> compress(vector<int> a) {
    unordered_map<int, int> m;

    for (int &x : a) {
        if (m.count(x))
            x = m[x];
        else
            m[x] = m.size();
    }

    return a;
}
```

元素按其在序列中首次出现的顺序获得编号。如果需要保持*顺序*——给较小的元素分配较小的编号——问题会稍复杂一些，可以用多种方式解决。

一种做法是排序数组，然后用哈希表遍历两遍——第一遍填充它，第二遍压缩数组本身：

```c++
vector<int> compress(vector<int> a) {
    vector<int> b = a;
    sort(b.begin(), b.end());

    unordered_map<int, int> m;

    for (int x : b)
        if (!m.count(x))
            m[x] = m.size();

    for (int &x : a)
        x = m[x];

    return a;
}
```

也可以从排序后的数组中（在线性时间内）去掉重复项，然后用它通过二分查找找出原数组中每个元素的下标：

```c++
vector<int> compress(vector<int> a) {
    vector<int> b = a;

    sort(b.begin(), b.end());
    b.erase(unique(b.begin(), b.end()), b.end());

    for (int &x : a)
        x = int(lower_bound(b.begin(), b.end(), x) - b.begin());

    return a;
}
```

两种方法都运行在 $O(n \log n)$。选你喜欢的那个用。
