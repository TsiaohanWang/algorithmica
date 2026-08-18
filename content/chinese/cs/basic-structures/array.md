---
title: 数组与元组
weight: 1
---

在 C++ 中，有几种方法可以把一组固定大小的变量合并到同一个变量中。

### C 语言中的数组

在 C 语言中有三种定义数组的主要方式：

```cpp
int a[100];

int main() {
    int b[100];
    int *c = new int[100];
    del[] c;
    return 0;
}
```

得到的这些变量在功能上是等价的，但略有区别：

- 全局定义的数组 `a` 存放在预先分配的内存区域中，在程序运行的整个期间都存在。所有元素初始都填有默认值（对于 `int` 来说是 0）。
- 在函数内部定义的数组 `b` 存放在*栈（stack）*上——一块专门存放临时变量的内存区域——当函数（或任何其他代码块，如循环体或 `if` 块）结束时，它会立即被释放。由于执行栈的大小有限，不能这样分配大数组（$>10^6$）。它初始填的是当时内存中残留的随机内容——要填充为零，可以写 `int x[100] = {}`；要用指定值填充所有元素，可以写 `int y[5] = {4, 8, 15, 23, 42}`。
- 通过 `new` 运算符定义的数组 `c` 是*动态*分配的。在通过 `del[]` 运算符显式删除之前，它会一直存在。它同样填的是当时内存中残留的内容。与前两种方式不同，它可以是任意大小，甚至可以事先不知道大小。

**注意。**前两种方式中，数组的大小必须是编译期已知的常量。GCC 编译器可以编译 `int a[n]` 这样的写法，并且确实会分配一个非常量大小的数组，因此 IDE 可能不会标红它，尽管这并不属于标准的一部分。

数组的所有元素在内存中是连续存放的，而 `a`、`b`、`c` 这些变量实际上是指向数组首元素的*指针*。方括号只是一种「语法糖」：

```cpp
a[k]  <=>  *(a + k)
```

在 C 中，初始化和复制分别有两个有用的函数：`memset` 和 `memcpy`。

第一个函数接收「目标」指针、「源」指针以及需要复制的字节数：

```cpp
memcpy(dest, src, sizeof src);
```

第二个函数接收「目标」指针和一个字节——即要填充到整个数组中的值。

```cpp
memset(arr, 0, sizeof arr);
```

**注意。**`memset` 操作的是原始字节，而不是 `int` 或 `float` 这样的类型。因此，通过 `memset` 只能把整型数组填充为「按字节重复」的值，比如 $0$ 和 $-1$（-1 的[二进制表示](/cs/arithmetic/bit-representation)形如 `111..111`）。

还要记住，这两个函数的最后一个参数都是字节数，而不是元素个数。对于非常量大小的数组，可以把类型大小乘以数组大小：

```cpp
memcpy(dest, src, sizeof(int) * n)
```

这里 `sizeof(int) = 4`。不直接写 4 而这样写是为了让代码具有自注释性。

### std::array

C++11 增加了用于常量大小数组的类：

```cpp
// int a[3] = {1, 2, 3};
array<int, 3> a = {1, 2, 3};
```

对它的所有操作与 C 风格数组类似。主要区别在于它是 STL 容器，也就是说它拥有[迭代器](../iterators)，并且标准库中的所有算法都能作用于它。

```cpp
sort(a.begin(), a.end());
```

不过普通数组也可以——指针会自动转换为迭代器：

```cpp
sort(a, a + 3);
```

STL 数组和普通的常量大小数组一样支持迭代遍历：

```cpp
for (int x : a)
    cout << x << endl;
```

还可以用下面的语法在迭代过程中修改数组元素：

```cpp
for (int &x : a)
    x *= 2;
```

STL 中还有一个比 `memset` 更不容易出错的替代品——`std::fill`：

```cpp
fill(a.begin(), a.end(), 42);
```

它按完整类型工作，不过会稍微慢一些。

### std::pair 和 std::tuple

`pair<T1, T2>` 类型保存一对变量，两者的类型不必相同：

```cpp
pair<int, int> interval = {0, 42};
pair<int, double> index_and_value = {7, 3.1415};
```

第一个元素通过 `.first` 字段访问，第二个元素通过 `.second` 访问。

它的推广形式 `tuple` 可以保存任意数量的变量：

```cpp
tuple<int, int, int> coords_xyz = {1, 2, 3};
```

对于 `tuple`，不能使用 `.first`、`.second`、`.third` 等，而需要使用索引。

从函数中返回 pair 和 tuple 很方便：

```cpp
typedef tuple<double, double, double> point;

point rotate(point p) {
    return {p[1], p[2], p[0]};
}
```

遍历它们的数组也很方便：

```cpp
point points[100];

for (auto [x, y, z] : points)
    cout << x << y << z << endl;
```

### struct

强烈建议在可能的情况下用结构体代替 pair 和 tuple。

```cpp
struct point {
    double x, y, z;
};
```

不必再与 `.first`、`.second` 或索引打交道，你可以得到命名字段，还可以定义自己的方法和重载运算符：

```cpp
point::length() {
    return sqrt(x * x + y * y + z * z);
}

point operator+(point a, point b) {
    return {a.x + b.x, a.y + b.y, a.z + b.z};
}
```

结构体唯一的缺点是：pair 和 tuple 已经内置了比较和哈希函数，因此可以直接把它们作为键放进 `set` 或 `unordered_set` 这类 STL 容器中，而结构体则需要自己编写这些函数。