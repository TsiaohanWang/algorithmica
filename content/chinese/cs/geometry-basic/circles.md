---
title: 圆
weight: 5
draft: true
---

圆与直线的交点
给一个圆（由圆心坐标与半径）和一条直线（由其方程）。求它们交点（一个、两个或没有）。

解
不形式化解方程组，而从几何角度入手（这样数值稳定性上解更精确）。

不一般性假设圆心在原点（否则平移到那里，相应修正直线方程中的常数 C）。即圆心在 (0,0)、半径 r 的圆和直线 Ax + By + C = 0。

先找离圆心最近的直线点——坐标 (x0,y0)。第一，它到原点距离应为：

    |C|
----------
sqrt(A2+B2)
第二，因向量 (A,B) 垂直于直线，该点坐标应与该向量成比例。已知原点到所求点距离，只需把向量 (A,B) 归一化到该长度，得：

        A C
x0 = - -----
       A2+B2

        B C
y0 = - -----
       A2+B2
（这里只有 '负号' 不明显，但代入直线方程易验证得零）

知道离圆心最近的直线点后，就能判断答案含多少点，甚至直接给出 0 或 1 点的答案。

确实，若 (x0, y0) 到原点距离（已用公式表达）大于半径，则答案 0 点。若等于半径，则答案 1 点——(x0,y0)。剩余情形 2 点，需求其坐标。

我们知道 (x0, y0) 在圆内。所求点 (ax,ay) 和 (bx,by) 除属直线外，还应距 (x0, y0) 同一距离 d，该距离易求：

                  C2
d = sqrt ( r2 - ----- )
                A2+B2
注意向量 (-B,A) 与直线平行，因此所求点 (ax,ay)、(bx,by) 可由 (x0,y0) 加向量 (-B,A)（归一化到长度 d，得一个点）和减该向量（得另一个点）得到。

最终解：

                d2
mult = sqrt ( ----- )
              A2+B2

ax = x0 + B mult
ay = y0 - A mult
bx = x0 - B mult
by = y0 + A mult
若纯代数解此题，多半得到另一形式、误差更大。因此这里描述的「几何」法除直观外还更精确。

实现
如开头所说，假设圆在原点。

因此输入是圆半径和直线方程系数 A,B,C。

double r, a, b, c; // 输入

double x0 = -a*c/(a*a+b*b),  y0 = -b*c/(a*a+b*b);
if (c*c > r*r*(a*a+b*b)+EPS)
	puts ("no points");
else if (abs (c*c - r*r*(a*a+b*b)) < EPS) {
	puts ("1 point");
	cout << x0 << ' ' << y0 << '\n';
}
else {
	double d = r*r - c*c/(a*a+b*b);
	double mult = sqrt (d / (a*a+b*b));
	double ax,ay,bx,by;
	ax = x0 + b * mult;
	bx = x0 - b * mult;
	ay = y0 - a * mult;
	by = y0 + a * mult;
	puts ("2 points");
	cout << ax << ' ' << ay << '\n' << bx << ' ' << by << '\n';
}

两圆交点
给两圆，各由圆心坐标与半径确定。求它们所有交点（一点、两点、没有或两圆重合）。

解
把问题归结为圆与直线交点问题。

不一般性假设第一圆心在原点（否则平移到原点，输出答案时再加回圆心坐标）。于是有方程组：

x2 + y2 = r12
(x - x2)2 + (y - y2)2 = r22
第二个方程减第一个以消去变量平方：

x2 + y2 = r12
x (-2x2) + y (-2y2) + (x22 + y22 + r12 - r22) = 0
于是把两圆交点归结为第一圆与如下直线的交点：

Ax + By + C = 0,
A = -2x2,
B = -2y2,
C = x22 + y22 + r12 - r22.
后者解法见相应文章。

唯一需单独处理的退化情形——两圆心重合。确实，此时不是直线方程而是 0 = С 形式（C 是某数），处理会出错。因此单独处理：若半径相等，答案无穷；否则无交点。

用三分查找求凸多边形内切圆
给 N 个顶点的凸多边形。求最大内切圆的圆心坐标与半径。

这里描述用两个三分查找的简单方法，运行 O (N log2 C)，C 是由坐标量级与所需精度决定的系数（见下）。

算法
定义函数 Radius (X, Y)，返回以点 (X;Y) 为圆心内切于该多边形的圆半径。假设 X、Y 在多边形内（或边界上）。显然该函数易在 O (N) 内实现——遍历多边形所有边，对每条算到圆心距离（距离可取直线到点，不必看作线段），返回所得距离的最小值——它显然就是最大半径。

于是要最大化这个函数。注意由于多边形凸，该函数对两个参数都适合三分查找：固定 X0（当然使直线 X=X0 与多边形相交）时，函数 Radius(X0, Y) 作为单变量 Y 的函数先增后减（也只考虑 (X0, Y) 属于多边形的 Y）。而且 max (по Y) { Radius (X, Y) } 作为单变量 X 的函数也先增后减。这些性质由几何直观清楚。

因此做两个三分查找：对 X、其内对 Y，最大化 Radius 值。唯一特殊点是要正确选三分边界，因为多边形外算 Radius 不正确。对 X 无困难，取最左与最右点的横坐标。对 Y，找当前 X 落入的多边形边，求这些边在横坐标 X 处的纵坐标（不看竖边）。

估复杂度。设坐标最大值为 C1，所需精度量级 10-C2，令 C = C1 + C2。则每个三分查找需 O (log C) 步，总复杂度：O (N log2 C)。

实现
常数 steps 决定两个三分查找的步数。

实现中为每条边预计算直线方程系数并立刻归一化（除以 sqrt(A2+B2)），避免三分内部多余操作。

const double EPS = 1E-9;
int steps = 60;

struct pt {
	double x, y;
};

struct line {
	double a, b, c;
};

double dist (double x, double y, line & l) {
	return abs (x * l.a + y * l.b + l.c);
}

double radius (double x, double y, vector<line> & l) {
	int n = (int) l.size();
	double res = INF;
	for (int i=0; i<n; ++i)
		res = min (res, dist (x, y, l[i]));
	return res;
}

double y_radius (double x, vector<pt> & a, vector<line> & l) {
	int n = (int) a.size();
	double ly = INF,  ry = -INF;
	for (int i=0; i<n; ++i) {
		int x1 = a[i].x,  x2 = a[(i+1)%n].x,  y1 = a[i].y,  y2 = a[(i+1)%n].y;
		if (x1 == x2)  continue;
		if (x1 > x2)  swap (x1, x2),  swap (y1, y2);
		if (x1 <= x+EPS && x-EPS <= x2) {
			double y = y1 + (x - x1) * (y2 - y1) / (x2 - x1);
			ly = min (ly, y);
			ry = max (ry, y);
		}
	}
	for (int sy=0; sy<steps; ++sy) {
		double diff = (ry - ly) / 3;
		double y1 = ly + diff,  y2 = ry - diff;
		double f1 = radius (x, y1, l),  f2 = radius (x, y2, l);
		if (f1 < f2)
			ly = y1;
		else
			ry = y2;
	}
	return radius (x, ly, l);
}

int main() {

	int n;
	vector<pt> a (n);
	... 读取 a ...

	vector<line> l (n);
	for (int i=0; i<n; ++i) {
		l[i].a = a[i].y - a[(i+1)%n].y;
		l[i].b = a[(i+1)%n].x - a[i].x;
		double sq = sqrt (l[i].a*l[i].a + l[i].b*l[i].b);
		l[i].a /= sq,  l[i].b /= sq;
		l[i].c = - (l[i].a * a[i].x + l[i].b * a[i].y);
	}

	double lx = INF,  rx = -INF;
	for (int i=0; i<n; ++i) {
		lx = min (lx, a[i].x);
		rx = max (rx, a[i].x);
	}

	for (int sx=0; sx<stepsx; ++sx) {
		double diff = (rx - lx) / 3;
		double x1 = lx + diff,  x2 = rx - diff;
		double f1 = y_radius (x1, a, l),  f2 = y_radius (x2, a, l);
		if (f1 < f2)
			lx = x1;
		else
			rx = x2;
	}

	double ans = y_radius (lx, a, l);
	printf ("%.7lf", ans);

}



## 如何给定圆？

用圆心和半径。

## 圆与直线交点

可能情形：

  - 圆 $\\omega$ 与直线 $L$ 不相交 $\\iff$ [圆心到直线的距离](Прямые#Расстояние_от_точки_до_прямой "wikilink") $O$ 到 $L$ 严格大于圆半径
  - $\\omega$ 与 $L$ 相切 $\\iff$ $\\rho(O, L) = R(\\omega) = :R$
  - $\\omega$ 与 $L$ 有 2 个交点 $\\iff \\rho(O, L) \< R$

学会求交点。记为 $A$ 和 $B$（暂不会求，但不妨碍画图）。从 $O$ 向 $L$[作垂线](Прямые#Проекция_точки_на_прямую "wikilink")——垂足 $H$。在 $\\Delta AOH$ 中已知 $|AO| = R, OH = \\rho(O, L) \\implies$ 可由勾股定理求 $|AH|$。注意 $A$ 与 $B$ 关于 $OH$ 对称，由此得求 $A$、$B$ 的算法：

1.  作垂线 $OH$。
2.  给 $H$ 加 $\\pm$(直线 $L$ 的方向向量，归一化并缩放到长度 $AH$)。

## 两圆交点

两圆相对位置的可能：

1.  两圆重合（平凡）
2.  一圆圆心 $O_2$（圆 $\\omega_2$）位于另一圆 $\\omega_1$ 内，且
    1.  圆不相交 $\\iff d(=\\rho(O_2O_1)) + R_2 \< R_1$
    2.  圆相切 $\\iff d + R_2 = R_1$
    3.  圆有 2 个交点 $\\iff d + R_2 \> R_1$
3.  圆心不位于另一圆内，且
    1.  圆不相交 $\\iff d \> R_1 + R_2$
    2.  圆相切 $\\iff d = R_1 + R_2$
    3.  圆有 2 个交点 $\\iff d \< R_2 + R_1$

*以上比较都精确到 EPS！*

除 2.3 和 3.3 外所有情形都平凡。解 3.3：

设交点 $A$ 和 $B$。在 $\\Delta O_1O_2A$ 中已知全部 3 边 $\\implies$ 可用余弦定理求 $\\angle O_2O_1A = \\angle O_2O_1B(= :\\alpha)$。现在求 $A$、$B$ 只需把 $\\overline{(O_1O_2)$ [旋转](Векторы#Поворот_вектора "wikilink") $\\pm \\alpha$、缩放到长度 $|O_1A|$，结果加到 $O_1$。

## 从点引圆的切线

可能情形：

1.  点 $P$ 在圆 $\\omega$ 内——此时无切线。
2.  $P$ 在 $\\omega$ 上——切线恰好一条，向量 $\\overline{OP}$ 垂直于该切线 $\\implies$ 已为该直线知道一点和方向向量，之后[小事一桩](Прямые#Важные_переходы_между_способами_хранения "wikilink")。
3.  $P$ 在 $\\omega$ 外 $\\implies$ 从 $P$ 到 $\\omega$ 有 2 条切线。单独解此情形。

记切点为 $A$ 和 $B$。注意在 $\\Delta POA$ 中已知斜边和一条直角边 $\\implies$ 可由勾股定理求 $|PA|$。于是 $A$、$B$ 可作为 $\\omega$ 与以 $P$ 为心、半径 $|PA|$ 的圆的交点。这个我们已会做。
