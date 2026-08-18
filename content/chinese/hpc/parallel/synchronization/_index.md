---
title: 同步原语
weight: 2
---

考虑下面的循环：

```cpp
int s = 0;

for (int i = 0; i < n; i++) {
    s += a[i];
}
```

我们可以这样把它并行化：

```cpp
int s = 0;

#pragma omp parallel for
for (int i = 0; i < n; i++) {
    s += a[i];
}
```

这段代码使用了 OpenMP，它将在下一章介绍。你现在需要知道的是，它会生成一批线程并在它们之间均匀地分配工作。你可以用 C++ 的线程写出等价的函数。

问题在于——