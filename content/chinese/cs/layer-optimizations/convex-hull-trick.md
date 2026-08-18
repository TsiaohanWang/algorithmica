---
# TODO: 更新实现
title: Convex Hull Trick
weight: 3
prerequisites:
- .
---

*本文是[一个系列](../)中的一篇。建议先阅读前面的所有文章*。

取 $f$ 的原始公式，展开 `cost` 中的括号：

$$
\begin{aligned}
f[i, j] &= \min_{k < i} \{ f[k, j-1] + (x_{i-1}-x_k)^2 \}
\\      &= \min_{k < i} \{ f[k, j-1] + x_{i-1}^2 - 2x_{i-1} x_k + x_k^2 \}
\end{aligned}
$$

注意 $x_{i-1}^2$ 与 $k$ 无关，可以提出来。最小值里面剩下的只有

$$
\underbrace{(f[k, j-1] + x_k^2)}_{a_k}
+
\underbrace{(-2 x_k)}_{b_k} \cdot x_{i-1}
$$

重新分组后，原来的表达式可以改写为

$$
f[i, j] = \min_k \{ (a_k, b_k) \cdot (1, x_{i-1}) \}
$$

其中「$\cdot$」指[点积](/cs/geometry-basic/products)。

### 算法

设我们要为 $f[i, j]$ 找最优的 $k$。把上一层所有已算好的相关动态值表示成平面上的点 $(a_k, b_k)$。

要高效地找出其中点积最小的点，可以维护它们的*下包络线*——向量 $(1, x_{i-1})$ 永远「朝上」，所以我们只关心它——并在其上二分查找最优的点。

下包络线可以简单地存在栈里。由于加入的点按 $x$ 排序，它的构建是线性的，整个算法的复杂度取决于二分查找，即 $O(n m \log n)$。

```c++
struct line {
    int k, b;
    line() {}
    line(int a, int _b) { k = a, b = _b; }
    int get(int x) { return k * x + b; }
};

vector<line> lines; // 存下包络线的直线
vector<int> dots; // 存下包络线各点的 x 坐标
//     ^ 实数的第一条规则
//      假设 dots 里存的是向下取整的 x 坐标

int cross(line a, line b) { // 求交点
                            // 假设 a.k > b.k
    int x = (b.b - a.b) / (a.k - b.k);
    if (b.b < a.b) x--; // 处理负数取整
    return x;
}


void add(line cur) {
    while (lines.size() && lines.back().get(dots.back()) > cur.get(dots.back())) {
        lines.pop_back();
        dots.pop_back();
    }
    if (lines.empty())
        dots.push_back(-inf);
    else 
        dots.push_back(cross(lines.back(), cur));
    lines.push_back(cur);
}

int get(int x) {
    int pos = lower_bound(dots.begin(), dots.end(), x) - dots.begin() - 1;
    return lines[pos].get(x);
}

```

在我们这道具体题目里，算法还可以进一步优化：回想 $opt[i, j] \leq opt[i][j+1]$，即最优的点总是在「更右」。这让我们可以用双指针代替二分查找，从而把解法优化到 $O(n m)$。
