---
title: 动态数组
weight: 3
authors:
- Сергей Слотин
---

*数组*是一组同类型变量，通过下标访问。

*动态*或*可扩展*数组是能根据元素个数改变大小的数组。

动态数组通常用于难以或无法预先预测数组大小的情况。在这种语境下，动态数组除访问和修改任意元素外，还有三种操作：

1. 在数组末尾添加元素 $x$。
2. 删除数组的最后一个元素。
3. 查询数组大小。

所有操作都应在 $O(1)$ 内完成——不必最坏情形，但需均摊。

## 实现

与本节的几乎所有结构一样，各种编程语言里都有动态数组，但为了彻底理解，非常推荐从零学写，因为它们之后会用于实现所有其他结构。

普通数组只是内存中的连续区域，而动态数组通常实现为一个结构体，包含：

- 指向数组 $t$ 的指针，
- 该数组的大小，
- 当前元素个数（小于数组 $t$ 的大小）。

当内部数组 $t$ 被填满、还需要再加元素时，就扩展它（重新分配更大的数组）。可选地，当已填元素比例变小时可以压缩数组——这样能归还未使用的内存。

```cpp
template <typename T>
struct dynamic_array {
    T *t;
    int size = 0, capacity;
    
    dynamic_array(int capacity) : capacity(capacity) {
        t = new T[capacity];
    }

    void resize(int new_capacity) {
        T *new_t = new T[new_capacity];
        memcpy(new_t, t, sizeof(T) * size);
        delete[] t;
        t = new_t;
    }

    T get(int k) {
        return t[k];
    }

    T set(int k, T x) {
        t[k] = x;
    }

    void add(T x) {
        if (size == capacity)
            resize(2 * capacity);
        t[size++] = x;
    }

    void del() {
        // 如果想省内存：
        if (4 * size < capacity)
            resize(capacity / 2);
        size--;
    }
};
```

## 运行时间

在*最坏*情形下，添加和删除操作运行在线性时间，因为需要重新创建整个 $O(n)$ 大小的数组。但*均摊*下所有操作运行在 $O(1)$。用预付法证明。

### add

设一次操作的成本是 1 枚硬币。那么每次不需要复制的 `add` 操作，付 3 枚硬币：1 枚用于该操作本身，2 枚作为储备——如果添加了第 $k$ 个元素，就分别在编号 $k$ 和 $(k−\frac{n}{2})$ 的元素旁各放 1 枚。

到数组被填满时，每个元素旁都放着 1 枚硬币，正好用它支付把元素复制进新数组的费用。因此每次 `add` 操作的均摊成本是 3，平均运行时间 $O(1)$。

### del

每次普通 `del` 操作付 2 枚硬币。1 枚用于实际删除最后一个（第 $k$）元素，另 1 枚放在位于 $(k \bmod \frac{n}{4})$ 位置的元素旁。那么即使在最坏情形——刚扩展过、随后从末尾删除 $\frac{n}{4}$ 个元素——前 $\frac{n}{4}$ 个元素的每个旁也有硬币，用来支付它们的迁移。

## 各种语言中的实现

### std::vector

C++ 中动态数组由标准库的 `vector` 结构实现。

```cpp
// 创建空 vector
vector<int> a;

// 把 x 插入 a 末尾
a.push_back(x);

// 返回 vector a 的大小
a.size();

// 把 vector 大小设为 x
// 要么删除末尾元素，要么添加零
a.resize(x);

// 把 vector 大小设为 x，添加 y
a.resize(x, y);

// 初始化时可以指定大小和元素
vector<int> a(8);         // {0, 0, 0, 0, 0, 0, 0, 0}
vector<int> b(5, 42);     // {42, 42, 42, 42, 42}
vector<int> c = {1, 2, 3} // {1, 2, 3}
```

当内存完全填满、试图写入新元素时，会发生扩容——用 GCC 编译时翻倍，用 MSVC 编译时扩大 1.5 倍。删除元素时不会缩小数组。

`vector` 的 `capacity` 可以用同名函数获得：

```cpp
vector<int> a;
for (int i = 0; i < 10; i++) {
    a.push_back(i);
    cout << "size: " << a.size() << ", capacity " << a.capacity() << endl;
}
```

输出：

```
size: 1, capacity 1
size: 2, capacity 2
size: 3, capacity 4
size: 4, capacity 4
size: 5, capacity 8
size: 6, capacity 8
size: 7, capacity 8
size: 8, capacity 8
size: 9, capacity 16
size: 10, capacity 16
```

默认初始化的 `vector` 初始大小（`capacity`）为 0，但很多在内部使用它的结构常预留某个初始大小——例如 16 或 32 个元素——以节省时间，因为假设那里不会只存一个元素。

### Python

在 Python 中，普通 list 充当可扩展数组。

```python
a = [1, 2, 3]
a.append(4)
```
