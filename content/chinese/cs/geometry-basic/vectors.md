---
title: 点与向量
weight: 1
published: true
---

指定了哪个端点是起点、哪个端点是终点的线段称为*向量*。平面上的向量可以用两个数表示——它的水平坐标和垂直坐标。

![](../img/vector.jpg)

**点 $\simeq$ 向量**。由于两者都只是一对数，可以把它们看作同一类对象，并把每个点与它的*位置向量*（radius-vector）对应起来——即从坐标原点指向该点的向量。

## 如何存储它们

创建一个负责所有向量操作的类。在 C++ 中有两种方式：`struct` 和 `class`。它们的主要区别在于 `class` 中所有字段默认是*私有的*——外部无法直接访问。这是为了额外保护，防止大型项目中有人不小心改坏东西；但在算法竞赛里这不太重要，所以我们用 `struct`。按照数学和物理学中[通行的](https://ru.wikipedia.org/wiki/%D0%A0%D0%B0%D0%B4%D0%B8%D1%83%D1%81-%D0%B2%D0%B5%D0%BA%D1%82%D0%BE%D1%80)记号，把它命名为 `r`。如果你愿意，也可以叫它 `point`、`pt`、`vec`——随你喜欢。

```c++
struct r {
    int x, y;
    r() {}
    r(int x, int y) : x(x), y(y) {}
};
```

与类或结构体同名的函数 `r` 会在对象初始化时被调用。它叫做*构造函数*，可以为不同的输入参数定义不同的版本。这里 `r()` 返回一个坐标未定义（取决于当时内存中的内容）的点，而 `r(x, y)` 返回坐标为 $(x, y)$ 的点。

一个重要的点是，我们选择了整数类型 `int` 来存储坐标。如果所有输入的坐标都是整数，我们将会看到，很多时候所有运算也都能在整数范围内完成，从而避免大量浮点数问题。

## 向量的运算

写一个接收向量并对其做点什么的函数。例如计算长度：

```c++
double len(r a) { return sqrt(a.x * a.x + a.y * a.y); }
// или:
double len(r a) { return hypot(a.x, a.y); }
```

这是 C 语言的做法。在 C++ 中更适合定义*方法*：

```c++
double r::len() { return hypot(x, y); }
// (альтернативно можно добавить функцию len() внутри самой структуры)
```

除了实现更整洁之外，调用语法也不同：`len(a)` 或 `a.len()`。

### 运算符

在 C++ 中可以*重载*几乎所有标准运算符，例如 `+`、`-`、`*` 等。

为将来需要，先重定义 `+` 和 `-`：

```c++
r operator+(r a, r b) { return {a.x + b.x, a.y + b.y}; }
r operator-(r a, r b) { return {a.x - b.x, a.y - b.y}; }
```

你觉得 `cin >> x` 实际上是怎么工作的？这也是运算符重载：`>>`。它是这样实现的：

```c++
istream& operator>>(istream &in, r &p) { 
    in >> p.x >> p.y;
    return in;
}

ostream& operator<<(ostream &out, r &p) { 
    out << p.x << " " << p.y << endl;
    return out;            
}
```

### 角度与旋转

要计算向量相对 $x$ 轴的角度，可以回忆单位圆，计算 $\frac{y}{x}$ 的反正切。

![](../img/trig.svg)

C++ 和 Python 中都有 `atan2` 函数，它比「先除法再取反正切」更快更精确：

```c++
double r::angle() {
    return atan2(y, x);
}
```

它返回 $[-\pi, +\pi]$ 区间内的一个数，单位为弧度。要换成度数需乘以 $\frac{180}{\pi}$。

向量旋转角度 $\alpha$ 由下面的矩阵方程给出：

$$
Rot_{\alpha}(\overline{(x, y)})
=
\begin{pmatrix}
    \cos(\alpha) & -\sin(\alpha)
\\  \sin(\alpha) & \cos(\alpha)
\end{pmatrix}
\begin{pmatrix}
    x
\\  y
\end{pmatrix}
=
\begin{pmatrix}
    \cos(\alpha) \cdot x - \sin(\alpha) \cdot y
\\  \sin(\alpha) \cdot x + \cos(\alpha) \cdot y
\end{pmatrix}
$$

特别地，$Rot_{90^{\circ}} (\overline{(x, y)}) = \overline{(-y,x)}$。

## 对资深选手：复数

[以上所有操作都可以用 std::complex 来实现](https://codeforces.com/blog/entry/22175?locale=ru)。