---
title: 并非零成本的抽象
weight: 7
draft: true
---

总的来说，抽象是很好的。运用得当的话，它们能减少代码量，减轻程序员的脑力负担。

但抽象往往要付出性能代价。当你使用一个共享库时，需要多花一些时钟周期来搬运数据，以便正确调用它的函数。当你调用一个虚方法时，无法可靠地预测接下来会执行哪段代码，实际上相当于遭受了一次分支预测失败。

C++ 和 Rust 这类语言大力推崇*零成本*抽象的理念：它们没有任何额外的运行时开销，至少原则上可以被编译器完全消除。但在实践中，并不存在所谓的零成本抽象——编译器技术还远没有发展到那一步。

**虚函数。** 任何形式的运行时多态。

**边界检查。** 不过编译器很擅长消除它们。

**一般来说任何复杂的代码。** 这里有一个令我本人头疼的例子：C++ 标准库中的 `std::min`。它的性能反复地比手写的取最小值要差，原因在于它并不是简单地实现为 `return (a < b ? a : b)`，而是为了通用性使用了可变参数初始化列表和迭代器：

```cpp
template<typename _Tp> GLIBCXX14_CONSTEXPR inline _Tp min(initializer_list<_Tp> __l) {
    return *std::min_element(__l.begin(), __l.end());
}
```

通常，把一个规模不大的程序改写得更直白、更贴近硬件并不难。只要你开始去掉一层层的抽象，编译器最终总会就范。

面向对象语言，尤其是函数式语言，有一些像这样很难捅破的抽象。正因如此，人们往往倾向于用更接近 C 的风格来编写性能关键的软件（解释器、运行时、数据库），而不是用更高级的语言。

留着浓密胡须的 C/汇编程序员。

### 内存

指针追逐。

```c++
typedef vector< vector<int> > matrix;
matrix a(n, vector<int>(n, 0));

int val = a[i][j];
```

这最多会慢上一倍：你首先需要取回

```c++
int a = new int[n * n];
memset(a, 0, 4 * n* n);

int val = a[i * n + j];
```

如果你确实想要抽象，可以写一个包装器：

```c++
template<typename T>
struct Matrix {
    int x, y, n, N;
    T* data;
    T* operator[](int i) { return data + (x + i) * N + y; }
};
```

例如，[缓存无关转置](/hpc/external-memory/oblivious)可以这样写：

```c++
Matrix<T> subset(int _x, int _y, int _n) { return {_n, _x, _y, N, data}; }

Matrix<T> transpose() {
    if (n <= 32) {
        for (int i = 0; i < n; i++)
            for (int j = 0; j < i; j++)
                swap((*this)[j][i], (*this)[i][j]);
    } else {
        auto A = subset(x, y, n / 2).transpose();
        auto B = subset(x + n / 2, y, n / 2).transpose();
        auto C = subset(x, y + n / 2, n / 2).transpose();
        auto D = subset(x + n / 2, y + n / 2, n / 2).transpose();
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                swap(B[i][j], C[i][j]);
    }

    return *this;
}
```

我个人更喜欢编写底层代码，因为更容易优化。

这样更干净吗？我不这么认为。