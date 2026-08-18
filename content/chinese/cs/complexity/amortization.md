---
title: 均摊分析
weight: 4
draft: true
---

## BogoSort

## 驻点

## 最小值更新

```cpp
int m = 1e9, cnt = 0;
for (int i = 0; i < n; i++)
    if (a[i] < m)
        m = i, cnt++;
```

$O(\log n)$