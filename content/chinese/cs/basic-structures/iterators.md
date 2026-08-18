---
title: 迭代器
weight: 2
---

迭代器是一个*指向*某个容器中元素的对象。

迭代器是对指针概念的抽象。指针只作用于连续数据（数组），而迭代器可以作用于任意容器——例如链表或搜索树——而且语法统一，这对库开发者避免代码重复大有帮助。

### 语法

要取出迭代器 `it` 指向的元素，用解引用运算符：`*it`。要移到下一个元素用自增：`++it`（迭代器没有后缀自增）。

所有容器都有某个首元素和末元素。指向首元素的迭代器用 `a.begin()` 获得，`a.end()` 返回指向末元素之后某个虚构元素的迭代器。因此，从 `a.begin()` 遍历到 `a.end()`（不含），就能走遍容器的所有元素。

```cpp
vector<int> a = {1, 2, 3, 4, 5};

// 迭代器类型必须包含容器信息
// 所以对 int 向量是 "vector<int>::iterator"
for (vector<int>::iterator it = a.begin(); it != a.end(); ++it)
    cout << *it << endl;

// 现代 C++ 可以用 "auto" 代替
for (auto it = a.begin(); it != a.end(); ++it)
    cout << *it << endl;

// 如果要遍历整个数组，也能压缩成这样
for (int x : a)
    cout << x << endl;

// 如果要修改元素，可以按引用传
for (int &x : a)
    x *= 2;

for (x : a)
    cout << x << endl;

for (const int &x : a)
    cout << x << endl;

// （也可以用 auto 代替 int）

// the initializer may be a braced-init-list
for (int x : {1, 2, 3, 4, 5})
    cout << x << endl;

// the initializer may be an array
int b[] = {1, 2, 3, 4, 5};
for (int x : b)
    cout << x << endl;

array<int, 5> c = {1, 2, 3, 4, 5};
for (int x : c)
    cout << x << endl;
```

### 迭代器类别

迭代器是容器接口中非常重要的一部分。迭代器可以传给标准库的各种算法，这些算法不必知道容器的内部构造，但需要知道可能的数据访问模式。

因此，根据内部结构，容器的迭代器可能属于几个具有不同保证等级的抽象类别之一：

- `input_iterator`，只支持解引用和自增操作——甚至不保证自增后它之前的值仍有效。从名字可以看出，用于流式输入。

- `forward_iterator`，除前面的保证外，还保证对某个特定元素的迭代器可以随便自增多少次而不必担心它们消失（这使它们可用于多次遍历数据的算法）。

- `bidirectional_iterator`，除前面的外还支持自减（`it--`）——即移到前一个元素。

- `random_access_iterator`，除前面的外还支持跳到相距 $k$ 的元素——`it + k`、`it - k`、`it += k`、`it -= k`——以及求两个迭代器所指位置之间的距离：例如表达式 `a - b` 返回整数——集合中两个元素（对应迭代器 `a` 和 `b`）之间的距离。

### STL 算法

例如，`std::vector` 的迭代器属于 `random_access_iterator`，如果调用标准库的 `lower_bound` 函数，它会按元素做[二分查找](/cs/interactive/binary-search/)（假设它们按非递减顺序排序）：

```cpp
vector<int> a = {1, 2, 3, 5, 8, 13};

// 返回 8
cout << *lower_bound(a.begin(), a.end(), 7) << endl;
```

`lower_bound` 函数返回指向第一个不小于给定值的元素的迭代器。还有 `upper_bound`，返回第一个严格更大的元素（对 `int` 来说等价于求 `x + 1` 的 `lower_bound`）。

知道向量的迭代器支持随机访问，二分查找会运行在 $O(n \log n)$——抱歉，是 $O(\log n)$——但其他结构可能就不一定了。

也正因如此，与其用 C 风格数组，往往更值得用 `std::array`，它是同样固定长度的数组，但支持迭代器及随之而来的全部 STL 算法：

```cpp
array<int, 3> a = {4, 2, 1, 3};

// 返回 1
cout << *min_element(a.begin(), a.end()) << endl;
```

<!-- 更多有用的 STL 算法见 [C++ 速成](../../programming/cpp)。 -->
