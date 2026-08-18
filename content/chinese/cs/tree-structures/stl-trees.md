---
title: STL 中的树
weight: -1
published: true
---

STL 中二叉树的具体实现由 `set` 结构表示，它支持唯一元素的有序集合。

### 基本操作

`set<T>` 可以由任何实现了比较运算符的类型声明——特别是对 pair 和 tuple，比较运算符会自动实现为字典序比较。

```cpp
set<int> s;

s.insert(3); // s = {3}
s.insert(2); // s = {2, 3}
s.size();    // 返回 |s| = 2

s.insert(3); // 3 不会被再次加入，因为它已经在集合中
s.size();    // |s| = 2

// 集合中是否存在该元素：
s.count(3);  // 返回 1
s.count(5);  // 返回 0

s.erase(3);  // s = {2}
s.insert(6); // s = {2, 6}
```

由于 `set` 实现为平衡二叉搜索树——具体说是[红黑树](https://neerc.ifmo.ru/wiki/index.php?title=%D0%9A%D1%80%D0%B0%D1%81%D0%BD%D0%BE-%D1%87%D0%B5%D1%80%D0%BD%D0%BE%D0%B5_%D0%B4%D0%B5%D1%80%D0%B5%D0%B2%D0%BE)——对其元素的所有操作都运行在 $O(\log n)$。

### 迭代器

`set` 和所有 STL 容器一样支持迭代器。

`set` 的开头（最小元素）可以用 `.begin()` 获得，结尾用 `.end()`。注意 `.end()` 与所有迭代器一样，指向半开区间的末尾——即指向最后一个元素之后的一个不存在的元素。

```cpp
auto it = s.find(2); // 返回指向该元素的迭代器，若无此元素则返回 `end`
++it;                // 找下一个元素
int x = *it;         // x = 6 

s.lower_bound(1); // 返回 2，因为它是第一个 >= 1 的元素
s.upper_bound(2); // 返回 6，因为它是第一个 > 2 的元素

auto it = s.upper_bound(10);
if (it == s.end()) {
    // 小心：如果你解引用 it，会得到 undefined behavior！
}

// 用迭代器按升序输出 set 的所有元素
for (auto it = s.begin(); it != s.end(); ++it)
    cout << *it << " ";

// 但这种目的更适合用 range-based for 循环
for (int x : s)
    cout << x << " ";
```

迭代器的递增和递减运行在对数时间。

### 相关结构

STL 中有几个功能相似的结构：

- `map` 把值与键关联起来，并允许像无限数组一样访问：`m[x] = y`。
- `multiset` 支持元素重复。它的 `.count(x)` 返回具有给定键的元素个数，而不仅是 0 或 1。它可以实现为用值存元素个数的 `map`。
- `multimap` 按键返回多个不同的值而不是一个，并允许遍历它们（等价于用 `map<A, vector<B>>`）。

另外所有这些容器都有基于哈希表而非树的对应物：`unordered_set`、`unordered_map`、`unordered_multiset` 和 `unordered_multimap`。它们中查找、删除、插入平均在常数时间，但没有 `lower_bound` 和有序遍历。
