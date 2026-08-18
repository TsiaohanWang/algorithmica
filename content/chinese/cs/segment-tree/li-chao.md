---
title: Li Chao 线段树
draft: true
---

Li Chao 树是能处理两类查询的数据结构：

  - 向集合 $X$ 加入线性函数 $f(x) = ax + b$。
  - 对给定 $x$，求所有 $f \in X$ 中 $f(x)$ 的最大值。

#### 树的结构

在全部坐标集上（若坐标是实数，则在具一定精度的整个集合上）建一棵类似[线段树](дерево_отрезков "wikilink")的树。每个顶点存某条线性函数（初始为中性函数）。

对坐标 $x$ 的 $get$ 查询定义如下：

  - 沿树下潜到对应坐标 $x$ 的叶子
  - 记下所有访问过的顶点
  - 取所有这些函数的最大值

现在设计这样的 $add$ 查询，使执行后 $get$ 正确：

  - 设要加入函数 $f$。
  - 考虑顶点 $v$，使<i>在区间</i> $[l, r]$ 之外（该区间对应顶点 $v$）$f$ 永不最大。
  - 看该区间中点 $m = \frac{l + r}{2}$ 和 $v$ 里存的函数 $g$。
  - 若 $f(m) > g(m)$，交换 $f, g$。
  - 注意现在函数 $f$ 可能最大**要么**在 $[l, m - 1]$**、要么**在 $[m + 1, r]$（实数则 $m \pm \epsilon$）。
  - 在相应子树递归解。

#### 实现

这种树常常要用[隐式](динамические_структуры_данных "wikilink")形式实现。

``` c++ numberLines

struct line {
    int k = 0, m = 0;
    line() {}
    line(int k, int m): k(k), m(m) {}
    int get(int x) {
        return k * x + m;
    }
};

line t[4 * MAXN];

void upd(int v, int tl, int tr, line L) {
    if (tl > tr) {
        return;
    }
    int tm = (tl + tr) / 2;
    bool l = L.get(tl) > t[v].get(tl);
    bool mid = L.get(tm) > t[v].get(tm);
    if (mid) {
        swap(L, t[v]);
    }
    if (l != mid) {
        upd(2 * v, tl, tm - 1, L);
    }
    else {
        upd(2 * v + 1, tm + 1, tr, L);
    }
}

int get(int v, int tl, int tr, int x) {
    if (tl > tr) {
        return 0;
    }
    int tm = (tl + tr) / 2;
    if (x == tm) {
        return t[v].get(x);
    }
    if (x < tm) {
        return max(t[v].get(x), get(2 * v, tl, tm - 1, x));
    }
    else {
        return max(t[v].get(x), get(2 * v + 1, tm + 1, tr, x));
    }
}
```

[分类：笔记](Категория:Конспект "wikilink")
[分类：动态优化](Категория:Оптимизации_динамики "wikilink")

---


### Li Chao 线段树

对 Convex Hull Trick 还有另一种理解方式：不把它看成点与点积优化，而看成直线与在点处对直线族求最小值。

![](https://i.imgur.com/TqfVWDD.png)

对我们题目，表达式 $\min_k (a_k, b_k) \cdot (1, x_{i-1})$ 可展开为 $\min_k (a_k + b_k \cdot x_{i-1})$，并理解成在一组形如 $y = a_k + b_k \cdot x$ 的直线中求点处最小值。

*Li Chao 线段树*（英文 *Li Chao segment tree*，中 李超段树）是覆盖所有可能 $x$ 的线段树的改造，其每个顶点存一条这样的直线，使得沿根到相应叶子的路径走时，该点的最大值是路径上最大的值。

![](https://raw.githubusercontent.com/e-maxx-eng/e-maxx-eng/mastimg/li_chao_vertex.png)

设某顶点收到更新——直线 *new*。若顶点为空，把 *new* 写入并退出。若已存某条直线 *old*，则二者之一至少在某一半「支配」另一个，在另一半要么相交、要么也支配。

若一条直线完全支配另一条，直接写入顶点、忘掉另一条。若直线只在一半支配，则写入它，把「败者」递归传给它可能支配的那一半。

```c++
typedef int ftype;
typedef complex<ftype> point;
#define x real
#define y imag

ftype dot(point a, point b) {
    return (conj(a) * b).x();
}

ftype f(point f, ftype x) {
    return dot(f, {x, 1});
}

const int inf = 1e6 + 42;

point ln[8 * inf];
void add_line(point nw, int v = 1, int l = -inf, int r = inf) {
    point ol = ln[v];
    int m = (l + r) / 2;
    bool lef = f(nw, l) > f(ol, l);
    bool mid = f(nw, m) > f(ol, m);
    ln[v] = mid ? nw : ol;
    if(r - l == 1)
        return;
    if(lef != mid)
        add_line(mid ? ol : nw, 2 * v, l, m);
    else
        add_line(mid ? ol : nw, 2 * v + 1, m, r);
}

int get(int x, int v = 1, int l = -inf, int r = inf) {
    if(r - l == 1)
        return f(ln[v], x);
    int m = (l + r) / 2;
    if(x < m)
        return max(f(ln[v], x), get(x, 2 * v, l, m));
    else
        return max(f(ln[v], x), get(x, 2 * v + 1, m, r));
}
```

值得比较 CHT 与 Li Chao 树，明白何时该用哪个。合理的 CHT 实现需要特殊条件——点须按 $x$ 排序。若满足，算法会比 Li Chao 树快得多；Li Chao 树解决更一般的问题，但每次查询 $O(\log MAXC)$，且 $MAXC$ 很大时常需隐式实现（与[隐式线段树](segtree)类似）。

---

考虑下面这道题：

<i>瓦夏在吹气球。每秒他可以选择再吹一下，或什么都不做。若他在第 $i$ 秒吹，半径增加 $a_i$，但之后半径每秒减少 $b_i$ 直到下次吹。求 $n$ 秒内能得到的气球最大半径。</i>

可用动态规划解。$dp_i$ 是 $i$ 秒后能得到的最佳半径。则 $$dp_i = \\max_{j=1}^{i-1} dp_j + a_j - b_j \\cdot (i - j) = \\max_{j=1}^{i-1} (-b_j) \\cdot i + (dp_j + a_j + b_j \\cdot j) = \\max_{j=1}^{i-1} A_j \\cdot i + B_j$$ 其中 $A, B$ 只依赖 $j$。即可以认为要在点 $i$ 求一组线性函数的最小值。

#### Convex hull

维护一种数据结构，支持：

  - 添加线性函数
  - 在点 $x$ 求该函数族中的最大值

注意该函数会呈上包络线状。新线性函数与包络线的交至多两个点。于是要学从包络线中删除那些完全消失的直线，再加入新直线与交点。

这些操作确实能做：把所有直线放进 `std::set`，用[二分查找](бинарный_поиск "wikilink")找需与新直线相交的直线，删除它们之间的所有直线。这运行在 $O(n \\log n)$，但写起来很麻烦、且不常需要。另外，这类题可用[Li Chao 树](дерево_Li_Chao "wikilink")。

更常见的是题里有直线斜率（本例 $-b_i$）单调变化的限制。那么直线只能加到数据结构末尾，而非任意位置。此时可用[栈](стек "wikilink")代替 `std::set`。求交点不必二分，而逐步删除「无用」直线。于是若 $x$ 查询也排序，结构可 $O(n)$ 实现（否则查询 $O(\\log n)$）。

#### 实现

本实现存两个量：直线数组 $lines$ 与变化点数组 $pr$。认为 $lines_i$ 在区间 $\[pr_i, pr_{i + 1}\]$ 上最小。

``` c++ numberLines
struct Line {
    int k, m;
};

vector<int> pr; // 若交点向下取整，可用整数存
vector<Line> lines;

int get(int x) {
    int l = 0;
    int r = lines.size();
    while (l + 1 < r) {
        int mid = (l + r) / 2;
        if (pr[mid] <= x) {
            l = mid;
        }
        else {
            r = mid;
        }
    }
    return lines[l].k * x + lines[l].m;
}

void upd(Line line) {
    while (lines.size() && line.k * pr.back() + line.m < lines.back().k * pr.back() + lines.back().m) {
        pr.pop_back();
        lines.pop_back();
    }
    int coord;
    if (lines.empty()) {
        coord = -INF;
    } else {
        coord = cross(line, lines.back()); // 需实现直线相交
    }
    pr.push_back(coord);
    lines.push_back(line);
}
```

[分类：笔记](Категория:Конспект "wikilink")
[分类：动态优化](Категория:Оптимизации_динамики "wikilink")
