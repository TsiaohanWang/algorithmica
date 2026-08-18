---
title: 找负环
authors:
- Максим Иванов
weight: 6
draft: true
---

给定一个有 $n$ 个顶点、$m$ 条边的有向带权图 G。要求找出其中任意一个负权环，如果存在的话。

另一种提法——要求找出所有这样的顶点对，它们之间存在长度任意小的路径。

这两个问题适合用不同算法解决，因此下面两种都会讨论。

这个问题一个常见的「现实」提法如下：已知货币汇率，即一种货币兑换成另一种的汇率。要求判断能否通过一串兑换获利，即从某一货币的一个单位出发，最终得到大于一个单位的同种货币。

用 Bellman–Ford 算法解决
Bellman–Ford 算法可以判断图中是否存在负权环，若存在则找出其中一个。

这里不深入细节（在 Bellman–Ford 算法的文章里有说明），只给出结论——算法如何工作。

对图做 Bellman–Ford 算法的 $n$ 次迭代，如果最后一次迭代没有任何变化——则图中没有负权环。否则取一个距离发生变化的顶点，从它沿前驱走，直到进入环；这个环就是所求的负环。

实现：

struct edge {
	int a, b, cost;
};
 
int n, m;
vector<edge> e;
const int INF = 1000000000;
 
void solve() {
	vector<int> d (n);
	vector<int> p (n, -1);
	int x;
	for (int i=0; i<n; ++i) {
		x = -1;
		for (int j=0; j<m; ++j)
			if (d[e[j].b] > d[e[j].a] + e[j].cost) {
				d[e[j].b] = max (-INF, d[e[j].a] + e[j].cost);
				p[e[j].b] = e[j].a;
				x = e[j].b;
			}
	}
 
	if (x == -1)
		cout << "No negative cycle found.";
	else {
		int y = x;
		for (int i=0; i<n; ++i)
			y = p[y];
 
		vector<int> path;
		for (int cur=y; ; cur=p[cur]) {
			path.push_back (cur);
			if (cur == y && path.size() > 1)  break;
		}
		reverse (path.begin(), path.end());
 
		cout << "Negative cycle: ";
		for (size_t i=0; i<path.size(); ++i)
			cout << path[i] << ' ';
	}
}
用 Floyd–Warshall 算法解决
Floyd–Warshall 算法可以解决第二种提法——需要找出所有顶点对 (i,j)，它们之间不存在最短路（即最短路具有无限小的量）。

同样，更详细的解释见 Floyd–Warshall 算法的描述，这里只给结论。

Floyd–Warshall 算法对输入图运行结束后，枚举所有顶点对 (i,j)，对每一对检查从 i 到 j 的最短路是否无限小。为此枚举第三个顶点 t，如果 d[t][t]<0（即它位于负权环中），且它从 i 可达、从它可达 j——则路径 (i,j) 可能有无限小的长度。

实现：

for (int i=0; i<n; ++i)
	for (int j=0; j<n; ++j)
		for (int t=0; t<n; ++t)
			if (d[i][t] < INF && d[t][t] < 0 && d[t][j] < INF)
				d[i][j] = -INF;
