---
title: 哈希表
weight: 8
draft: true
---


## 哈希表

![](https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Hash_table_3_1_1_0_1_0_0_SP.svg/2560px-Hash_table_3_1_1_0_1_0_0_SP.svg.png =500x)

----

### 链地址法（Chaining）

![](https://upload.wikimedia.org/wikipedia/commons/d/d0/Hash_table_5_0_1_1_1_1_1_LL.svg =500x)

大量的链表（linked list）或可增长的数组

----

### 开放寻址（Open Addressing）

![](https://upload.wikimedia.org/wikipedia/commons/b/bf/Hash_table_5_0_1_1_1_1_0_SP.svg =500x)

固定数量的槽位，以及一个决定第 $i$ 步去哪里查找的哈希函数 $f_i(x)$

----

使用循环数组的实现：

```cpp
struct hashmap {
    const int size = (1<<24);
    int a[size] = {-1}, b[size];

    static inline int h(int x) { return (x^179)*7; }

    void add(int x, int y) {
        int k = h(x) % size;
        while (a[k] != -1 && a[k] != x)
            k = (k + 1) % size;
        a[k] = x, b[k] = y; 
    }

    int get(int x) {
        for (int k = h(x) % size; a[k] != -1; k = (k + 1) % size)
            if (a[k] == x)
                return b[k];
        return -1;
    }
};
```

渐近复杂度相同，但实际速度有 2–3 倍的差距

----

![](https://upload.wikimedia.org/wikipedia/commons/1/1c/Hash_table_average_insertion_time.png =500x)

唯一的缺点是，你需要更频繁地重新哈希（rehash）