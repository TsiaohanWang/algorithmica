---
title: Ford–Bellman 算法
authors:
- Максим Иванов
weight: 5
draft: true
---

设给一个带 $n$ 个顶点、$m$ 条边的有向带权图 $G$，并指定某个顶点 $v$。要求求从顶点 $v$ 到所有其他顶点的最短路径长度。

与 Dijkstra 算法不同，这个算法也适用于含负权边的图。不过，若图含负环，那么显然到某些顶点的最短路可能不存在（因为最短路权重应等于负无穷）；不过这个算法可以修改，让它报告负权环的存在，甚至输出这个环本身。

算法以两位美国科学家命名：Richard Bellman 和 Lester Ford。Ford 实际上在 1956 年研究另一数学问题时发明了这个算法，其子问题归结为图的最短路，Ford 给出了解决它的算法草稿。Bellman 于 1958 年发表专论最短路问题的文章，其中他清晰陈述了如今我们所知的这个算法。

算法描述
我们认为图不含负权环。含负环的情形稍后单独一节讨论。

建距离数组 $d[0 \ldots n-1]$，算法结束后它将含答案。开始时这样填：$d[v] = 0$，其余所有 $d[]$ 元素等于无穷 $\infty$。

Ford–Bellman 算法本身由若干阶段组成。每阶段查看图的所有边，算法试图沿每条权为 $c$ 的边 $(a,b)$ 做松弛（relax，放松）。沿边的松弛是尝试用 $d[a] + c$ 改进 $d[b]$。实际上这意味着我们尝试用边 $(a,b)$ 和顶点 $a$ 的当前答案改进顶点 $b$ 的答案。

断言：只需 $n-1$ 个阶段即可正确算出图中所有最短路长度（重申，我们假设没有负权环）。对不可达顶点，距离 $d[]$ 保持无穷 $\infty$。

实现
对 Ford–Bellman 算法，与许多其他图算法不同，更方便把图表示成所有边的一个列表（而非每个顶点一个出边列表）。下面的实现为边建结构 \rm edge。算法输入是数 $n$、$m$、边列表 $e$ 和起始顶点 $v$。所有顶点编号从 0 到 $n-1$。

最简单的实现
常数 \rm INF 表示「无穷」——要选得它肯定大于所有可能的路径长度。

struct edge {
	int a, b, cost;
};
 
int n, m, v;
vector<edge> e;
const int INF = 1000000000;
 
void solve() {
	vector<int> d (n, INF);
	d[v] = 0;
	for (int i=0; i<n-1; ++i)
		for (int j=0; j<m; ++j)
			if (d[e[j].a] < INF)
				d[e[j].b] = min (d[e[j].b], d[e[j].a] + e[j].cost);
	// 输出 d，例如到屏幕
}
检查 "if (d[e[j].a] < INF)" 只在图含负权边时需要：没有这个检查，就会从还没找到路径的顶点做松弛，出现 $\infty - 1$、$\infty - 2$ 之类的不正确距离。

改进的实现
这个算法可以稍作加速：答案往往几阶段就已找到，剩余阶段不做任何有用工作，只是白白查看所有边。因此存一个标志：当前阶段是否有变化，若某阶段什么都没发生就停止算法。（这个优化不改进复杂度，即某些图上仍需全部 $n-1$ 阶段，但显著加速算法「平均」行为，即随机图上。）

有了这个优化，就完全不必手动把阶段数限制为 $n-1$——它会在所需阶段数后自己停下。

void solve() {
	vector<int> d (n, INF);
	d[v] = 0;
	for (;;) {
		bool any = false;
		for (int j=0; j<m; ++j)
			if (d[e[j].a] < INF)
				if (d[e[j].b] > d[e[j].a] + e[j].cost) {
					d[e[j].b] = d[e[j].a] + e[j].cost;
					any = true;
				}
		if (!any)  break;
	}
	// 输出 d，例如到屏幕
}
路径恢复
现在看如何修改 Ford–Bellman 算法，使它不仅求最短路长度，还能恢复最短路本身。

为此再建数组 $p[0 \ldots n-1]$，对每个顶点存它的「祖先」，即通向它的最短路径上的倒数第二个顶点。确实，到某顶点 $a$ 的最短路是到某顶点 $p[a]$ 的最短路，末尾接上顶点 $a$。

注意 Ford–Bellman 算法正按同样逻辑工作：假设到某顶点最短距离已算好，尝试改进到另一顶点的最短距离。因此，改进时只需在 $p[]$ 记住这次改进来自哪个顶点。

给出带恢复到给定顶点 $t$ 路径的 Ford–Bellman 实现：

void solve() {
	vector<int> d (n, INF);
	d[v] = 0;
	vector<int> p (n, -1);
	for (;;) {
		bool any = false;
		for (int j=0; j<m; ++j)
			if (d[e[j].a] < INF)
				if (d[e[j].b] > d[e[j].a] + e[j].cost) {
					d[e[j].b] = d[e[j].a] + e[j].cost;
					p[e[j].b] = e[j].a;
					any = true;
				}
		if (!any)  break;
	}
 
	if (d[t] == INF)
		cout << "No path from " << v << " to " << t << ".";
	else {
		vector<int> path;
		for (int cur=t; cur!=-1; cur=p[cur])
			path.push_back (cur);
		reverse (path.begin(), path.end());
 
		cout << "Path from " << v << " to " << t << ": ";
		for (size_t i=0; i<path.size(); ++i)
			cout << path[i] << ' ';
	}
}
这里先沿祖先走，从顶点 $t$ 开始，把整个走过的路径存入列表 \rm path。这个列表里是从 $v$ 到 $t$ 的最短路，但是逆序的，因此我们对它调用 \rm reverse 再输出。

算法证明
第一，立刻注意，对从 $v$ 不可达的顶点算法工作正确：它们的 $d[]$ 标记保持无穷（因为 Ford–Bellman 算法会找到到所有从 $s$ 可达顶点的某些路径，其余顶点上松弛一次都不发生）。

现在证明下面命题：执行 $i$ 个阶段后，Ford–Bellman 算法正确求出所有长度（按边数）不超过 $i$ 的最短路。

换句话说，对任何顶点 $a$，记 $k$ 为到它的最短路的边数（若有多条，任取）。则命题说：$k$ 个阶段后这条最短路保证被找到。

证明。考虑任意从起始顶点 $v$ 可达的顶点 $a$，看它的最短路：$(p_0=v, p_1, \ldots, p_k=a)$。第一阶段前，到顶点 $p_0=v$ 的最短路正确。第一阶段的边 $(p_0,p_1)$ 被 Ford–Bellman 算法查看，因此到 $p_1$ 的距离在第一阶段后正确。把此断言重复 $k$ 次，得到第 $k$ 阶段后到 $p_k=a$ 的距离正确，证毕。

最后要注意：任何最短路不能有超过 $n-1$ 条边。因此算法只需 $n-1$ 个阶段。此后任何松弛都保证不能改进某顶点距离。

负环情形
上面我们都假设图中无负环（澄清：我们关心从起始顶点 $v$ 可达的负环，不可达环不改变上述算法）。若有，则出现额外困难：这个环上所有顶点的距离，以及从这个环可达的顶点的距离，都未定义——应等于负无穷。

不难理解，Ford–Bellman 算法会在这个环及从它可达的顶点之间无限做松弛。因此若不限阶段数为 $n-1$，算法会无限运行，不断改进这些顶点的距离。

由此得到可达负权环存在的判据：若 $n-1$ 个阶段后我们再执行一个阶段，且它发生至少一次松弛，则图含从 $v$ 可达的负权环；否则没有。

而且，若发现这种环，可修改 Ford–Bellman 算法，让它输出这个环本身（进入环的顶点序列）。为此只需记住第 $n$ 阶段发生松弛的顶点 $x$。这个顶点要么在负权环上，要么从它可达。为得到保证在环上的顶点，只需从 $x$ 沿祖先走 $n$ 次。得到在环上的顶点 $y$ 后，从它沿祖先走，直到回到同一个 $y$（这必然发生，因为负权环上的松弛是循环的）。

实现：

void solve() {
	vector<int> d (n, INF);
	d[v] = 0;
	vector<int> p (n, -1);
	int x;
	for (int i=0; i<n; ++i) {
		x = -1;
		for (int j=0; j<m; ++j)
			if (d[e[j].a] < INF)
				if (d[e[j].b] > d[e[j].a] + e[j].cost) {
					d[e[j].b] = max (-INF, d[e[j].a] + e[j].cost);
					p[e[j].b] = e[j].a;
					x = e[j].b;
				}
	}
 
	if (x == -1)
		cout << "No negative cycle from " << v;
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
由于有负环时 $n$ 次迭代后距离可能远降到负数（看来会到 $-2^n$ 量级的负数），代码中对整数溢出采取了额外措施：

d[e[j].b] = max (-INF, d[e[j].a] + e[j].cost);
上面实现找从某起始顶点 $v$ 可达的负环；但可修改算法，让它找图中任意负环。为此把 $d[i]$ 全设为 0 而非无穷——仿佛我们同时从所有顶点找最短路；这不影响负环检测的正确性。

本题相关补充——见单独文章「找图中的负环」。

---

### 题目

给带指定顶点 $s$ 的有向图 $G=(V, E)$。边权可为任意。要为每个顶点求从 $s$ 到它的最短距离。

#### 有向性

图的有向性重要，因为无向带负权图的最短路不能用 Ford–Bellman 算法解。但可归结为图（不必二分）中最小费用匹配。[详见](https://vk.com/away.php?to=http%3A%2F%2Facm.math.spbu.ru%2F%7Esk1%2Fdownload%2Fpapers%2Fshort_path.pdf&post=5333_4200&cc_key=)

### 动态规划

用动态规划解：

  - $sp\[k\]\[v\]$ —— 从 $s$ 到 $v$、路径含 $k$ 条边的最短距离。
  - 初始值
      - $ sp\[0\]\[s\] = 0 $
      - $ sp\[0\]\[V \\setminus \\{s\\} \] = INF $
      - $ sp\[1...|V|\]\[\*\] = INF $
  - $ sp\[k\]\[v\] = \\min_{u \\in N(v)} sp\[k-1\]\[u\] + w(u, v) $
  - 重算顺序：

<!-- end list -->

``` C++

for (int k = 0; k < vertices_count; ++k) {
  for (int v = 0; v < vertices_count; ++v) {
    // ...
  }
}
```

  - 答案：$dist\[v\] = \\min_{k} sp\[k\]\[v\]$
  - 恢复答案：要么对每个状态记从哪来，要么重新枚举。

### 从顶点转到边

注意，内层枚举邻居的顶点循环可换成边循环，得

``` C++

void relax(int& old_value, int new_value) {
  old_value = min(old_value, new_value);
}

// 初始化动态
for (int k = 0; k < vertices_count; ++k) {
  for (auto&& [from, to, w] : edges) {
    relax(sp[k][to], sp[k-1][from] + w);
  }
}
```

### 去掉一个维度

我们得到使用大小 $|V| \\times |V|$ 数组的解。可以改成 2 个长度为 $|V|$ 的数组——只需注意，算 $sp\[k\]\[\*\]$ 只需知道 $sp\[k-1\]\[\*\]$，因此只需存最后两层动态。

### 只留一个数组

上一节可放弃两个数组、只留 $sp\[v\]$。则 $sp\[v\] = \\min_{u \\in N(v)} sp\[u\] + w(u, v)$。但现在 $sp\[v\]$ 里存的值会丢失之前给它的值，因为重算一层动态时可能用到新层的值。

但可证明，$k$ 次迭代后 $sp\[v\]$ 中必已考虑从 $s$ 到 $v$ 长度至少 $k$ 条边的路径（可能还有更长路径）（归纳证明，读者练习）。由此，$|V| - 1$ 次迭代后 $sp\[v\]$ 已考虑 $s$ 到 $v$ 的所有可能路径 $\\implies$ $sp\[v\]$ 存 $s$ 到 $v$ 的最短距离。

### 加速算法（SPFA 算法）

注意：

1.  若某次外层循环迭代中 $sp\[\*\]$ 没变，则已找到所有最短距离，可停止算法。
2.  每步不必看所有边，只需看 $sp$ 至少对某个端点变化的边。

这些简单推理带来如下最终代码：

``` C++

typedef int Vertex;
typedef long long dist_t;

bool try_relax(dist_t& old_value, dist_t new_value) {
  old_value = min(old_value, new_value);
  return old_value == new_value;
}

vector<dist_t> SPFA(int start) {
  vector<dist_t> sp(n, INF);
  sp[start] = 0;

  vector<Vertex> updated_vertices = { start };

  for (int k = 0; k < vertices_count; ++k) {
    vector<Vertex> newly_updated_vertices;

    for (auto& v : updated_vertices) {
      for (auto&& [to, w] : edge_from[v]) {
        if (try_relax(sp[to], sp[v] + w)) {
          newly_updated_vertices.push_back(to);
        }
      }
    }

    if (newly_updated_vertices.empty()) {
      break;
    }

    updated_vertices.swap(newly_updated_vertices);
  }

 return sp;
}
```

## 带 random_shuffle 的 Ford–Bellman

若你突然忘了 SPFA，仍可随机打乱边来加速 Ford–Bellman。详见：<http://codeforces.com/blog/entry/58825>

## 找负权环

### 定理

图中有从 $s$ 可达的负权环 $\\iff$ 算法第 $|V|$ 次迭代后 $updated \\_ vertices$ 非空。

证明：

$\\implies$：设图中有负环 $v_0 \\rightarrow v_1 \\rightarrow \\dots \\rightarrow v_k = v_0$。若环中有边 $v_i \\rightarrow v_{i+1}$ 使第 $|V|$ 步 $sp\[v_{i+1}\] \> sp\[v_{i}\] + w(v_{i}, v_{i+1})$，则 $v_{i+1}$ 会进入 $updated\\_ vertices$，命题成立。设没有这样的边，即 $$ \\forall i \\in \[0 \\dots k\]: sp\[v_{i+1}\] \\leq sp\[v_{i}\] + w(v_{i}, v_{i+1}) $$

把这些不等式相加，注意 $\\sum_{0 \\leq i \\leq k-1} sp\[v_{i+1}\] = \\sum_{0 \\leq i \\leq k-1} sp\[v_{i}\]$（因为是循环移位后的同一和，记住 $v_k = v_0$）。

于是约去后得：$$ 0 \\leq \\sum_{0 \\leq i \\leq k-1} w(v_{i}, v_{i+1}) $$

即我们的环根本没有负权。矛盾。

$\\impliedby$：若第 $|V|$ 次迭代某顶点距离减小，则存在从 $s$ 到某顶点 $v$ 的至少 $|V|$ 条边的序列，其距离小于第 $(|V| - 1)$ 次迭代时的值。因边数不少于 $|V|$，序列中有环。若此环权非负，可把它从序列中删去、得更短的边序列，这应在算法前几步被考虑 $\\implies$ 第 $|V|$ 次迭代距离不可能沿含环序列减小。故环确有负权，正是所求。∎

由引理，为检查负权环存在，只需让算法再多跑一次迭代、检查什么都没变。

### 恢复负权环

要恢复环，只需对每个顶点 $v$ 记 $prev\[v\]$ —— 最后一次松弛到 $v$ 的边所经顶点。则恢复负权环只需取第 $|V|$ 步被松弛的任一条边，从它开始展开环。

此算法正确，因为任何在第 $|V|$ 步被松弛的边都位于负权环上 $\\implies$ 从边末端出发会沿负权环走回它。
