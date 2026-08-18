---
title: 扩展欧几里得算法
weight: 2
prerequisites:
- euclid
---

只是求 $\gcd$ 甚至不需要知道欧几里得算法怎么运作——编译器里就有。

**扩展欧几里得算法**除了求出 $g = \gcd(a, b)$，还找到整数系数 $x$ 和 $y$，使得

$$
a \cdot x + b \cdot y = g
$$

注意解有无穷多个：有了解 $(x, y)$，可以把 $x$ 加 $b$、$y$ 减 $a$，等式仍然成立。

## 核心思想

算法也是递归的。设我们在递归求 $\gcd(b, a \bmod b)$ 时已经算出了所需的系数 $x'$ 和 $y'$。换句话说，对 pair $(b, a \bmod b)$ 有解 $(x', y')$：

$$
b \cdot x' + (a \bmod b) \cdot y' = g
$$

要为原来的 pair 求解，把 $(a \bmod b)$ 按定义写成 $(a - \lfloor \frac{a}{b} \rfloor \cdot b)$，代入上面的等式：

$$
b \cdot x' + (a - \Big \lfloor \frac{a}{b} \Big \rfloor \cdot b) \cdot y' = g
$$

现在对各项重新分组（按原来的 $a$ 和 $b$ 分组），得到：

$$
a \cdot \underbrace{y'}_x + b \cdot \underbrace{(x' - \Big \lfloor \frac{a}{b} \Big \rfloor \cdot y')}_y = g
$$

与原来的表达式比较，可得对原来的 $x$ 和 $y$，$a$ 和 $b$ 前的系数即所求。

### 实现

```c++
int gcd(int a, int b, int &x, int &y) {
    if (a == 0) {
        x = 0;
        y = 1;
        return b;
    }
    int x1, y1;
    int d = gcd(b % a, a, x1, y1);
    x = y1 - (b / a) * x1;
    y = x1;
    return d;
}
```

这个递归函数仍返回 $\gcd(a, b)$，但此外还把所求系数写入按引用传递的变量 $x$ 和 $y$。

## 应用

这个改进之所以有趣，是因为可以用它求[模逆元](../reciprocal)：即满足 $a \cdot a^{1} \equiv 1$ 的元素 $a^{-1}$——这等价于求如下方程组的整数解：

$$
a^{-1} \cdot a + k \cdot m = 1
$$

还可以用扩展欧几里得算法解*线性丢番图方程*——求

$$
a \cdot x + b \cdot y = c
$$

的整数解。为此只需检查 $c$ 是否被 $g = \gcd(a, b)$ 整除；如果是，就把算法得到的 $x$ 和 $y$ 乘以 $\frac{c}{g}$。
