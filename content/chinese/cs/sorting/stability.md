---
title: 稳定排序
weight: 9
draft: true
---

设给定一个 pair 数组 `[{1, 'a'}, {3, 'b'}, {1, 'c'}]`，我们要按 pair 的第一个元素（数字）升序排序。

我们可以改造计数排序

```cpp
void count_sort(int *a, int n) {
    int c[100] = {0};

    for (int i = 0; i < n; i++)
        c[a[i]]++;

    int k = 0;
    for (int i = 0; i < 100; i++)
        while (c[i]--)
            a[k++] = i;
}
```

数组 $cnt$ 形如 `[0, 2, 0, 1]`，数组 $pref$ 形如 `[0, 2, 2, 3]`。看最后一层循环每次迭代会发生什么。

1.  $i = 0,\\ pref\[a\[i\].first\] - 1 = 1 \\Longrightarrow res =
    \\text{\[null, \\{1, 'a'\\}, null\]},\\ pref = \[0, 1, 2, 3\]$
2.  $i = 1,\\ pref\[a\[i\].first\] - 1 = 2 \\Longrightarrow res =
    \\text{\[null, \\{1, 'a'\\}, \\{3, 'b'\\}\]},\\ pref = \[0, 1, 2,
    2\]$
3.  $i = 2,\\ pref\[a\[i\].first\] - 1 = 0 \\Longrightarrow res =
    \\text{\[\\{1, 'c'\\}, \\{1, 'a'\\}, \\{3, 'b'\\}\]},\\ pref = \[0,
    0, 2, 2\]$

元素 `{1, 'a'}` 和 `{1, 'c'}` 现在顺序颠倒了。为什么会这样？当我们处理元素 $i$ 时，把 $pref\[a\[i\]\]$ 中的值减一，也就是说，当我们再遇到具有相同值的元素（例如下标为 $j \> i$）时，它的 $pref\[a\[j\]\]$ 会更小，而元素 $a\[j\]$ 在有序数组中会占据下标更小的位置。为了避免这种情况，把最后一层循环的方向改成 $n-1\\ldots0$。于是代码变成：

``` Python
for i=0..n-1:
    cnt[a[i]]++
pref[0] = 0
for i = 1..C:
   pref[i] = pref[i - 1] + cnt[i]
for i=n-1..0:
    res[pref[a[i]] - 1] = a[i]
    pref[a[i]]--
```
