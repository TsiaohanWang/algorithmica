---
title: Prüfer 序列
authors:
- Максим Иванов
weight: 99
draft: true
---

本文我们将讨论所谓的 Prüfer 序列（код Прюфера），它是一种用数字序列来无歧义地编码带标号树的方式。

借助 Prüfer 序列可以证明凯莱公式（给出完全图中生成树的数量），也可以解决这样的问题：计算向给定图添加多少条边才能使其连通的方案数。

注。我们不讨论只含单个顶点的树——那是一个特殊情况，很多结论在那种情况下都会退化。

Prüfer 序列
Prüfer 序列是 n 个顶点的带标号树与 n-2 个整数（取值范围为 [1;n]）组成的序列之间的一一对应关系。换言之，Prüfer 序列是完备图的所有生成树与数字序列之间的双射。

虽然由于表示方式的特殊性，用 Prüfer 序列来存储和操作树并不划算，但 Prüfer 序列在解决组合问题中很有用。

提出者——海因茨·普吕弗（Heinz Prüfer）——于 1918 年提出该序列，作为凯莱公式的证明（见下文）。

给定树构造 Prüfer 序列
Prüfer 序列按如下方式构造。重复 n-2 次如下过程：选择编号最小的叶子节点，把它从树中删除，并把与该叶子相连的顶点编号加入 Prüfer 序列。最后树中只剩下 2 个顶点，算法到此结束（这两个顶点的编号不会明确写入序列）。

因此，给定树的 Prüfer 序列是由 n-2 个数组成的序列，其中每个数都是当时最小叶子所连顶点的编号——也就是 [1;n] 范围内的一个数。

计算 Prüfer 序列的算法很容易实现为 O (n \log n) 复杂度，只需维护一个支持取出最小值的数据结构（例如 C++ 中的 \rm set<> 或 \rm priority\_queue<>），其中存放当前所有叶子的列表：

const int MAXN = ...;
int n;
vector<int> g[MAXN];
int degree[MAXN];
bool killed[MAXN];
 
vector<int> prufer_code() {
	set<int> leaves;
	for (int i=0; i<n; ++i) {
		degree[i] = (int) g[i].size();
		if (degree[i] == 1)
			leaves.insert (i);
		killed[i] = false;
	}
 
	vector<int> result (n-2);
	for (int iter=0; iter<n-2; ++iter) {
		int leaf = *leaves.begin();
		leaves.erase (leaves.begin());
		killed[leaf] = true;
 
		int v;
		for (size_t i=0; i<g[leaf].size(); ++i)
			if (!killed[g[leaf][i]])
				v = g[leaf][i];
 
		result[iter] = v;
		if (--degree[v] == 1)
			leaves.insert (v);
	}
	return result;
}
不过，构建 Prüfer 序列也可以做到线性时间，这一点将在下一节介绍。

在线性时间内为给定树构造 Prüfer 序列
这里给出一个 O(n) 复杂度的简单算法。

算法的要点是维护一个移动指针 ptr，它只会向顶点编号增大的方向移动。

乍一看这是不可能的，因为在构造 Prüfer 序列的过程中，叶子的编号既可能增大也可能减小。但容易注意到，减小只会在一种情况下发生：删除当前叶子后，它的父节点编号更小（这个父节点将成为最小叶子，并在 Prüfer 序列的下一步被删除）。这样，减少的情况可以在 O(1) 时间内处理，因此不会妨碍我们构造线性复杂度的算法：

const int MAXN = ...;
int n;
vector<int> g[MAXN];
int parent[MAXN], degree[MAXN];
 
void dfs (int v) {
	for (size_t i=0; i<g[v].size(); ++i) {
		int to = g[v][i];
		if (to != parent[v]) {
			parent[to] = v;
			dfs (to);
		}
	}
}
 
vector<int> prufer_code() {
	parent[n-1] = -1;
	dfs (n-1);
 
	int ptr = -1;
	for (int i=0; i<n; ++i) {
		degree[i] = (int) g[i].size();
		if (degree[i] == 1 && ptr == -1)
			ptr = i;
	}
 
	vector<int> result;
	int leaf = ptr;
	for (int iter=0; iter<n-2; ++iter) {
		int next = parent[leaf];
		result.push_back (next);
		--degree[next];
		if (degree[next] == 1 && next < ptr)
			leaf = next;
		else {
			++ptr;
			while (ptr<n && degree[ptr] != 1)
				++ptr;
			leaf = ptr;
		}
	}
	return result;
}
我们来解释一下这段代码。核心函数是 \rm prufer\_code()，它返回用全局变量 n（顶点数）和 g（邻接表给出的图）所描述的树的 Prüfer 序列。首先，我们为每个顶点找到它的父节点 {\rm parent}[i]——即该顶点在被删出树时将要拥有的父节点（所有这些都可以预先求出，利用最大编号顶点 n-1 永远不会被删出树这一点）。同时，我们还为每个顶点计算它的度数 {\rm degree}[i]。变量 \rm ptr 是移动指针（最小叶子的“候选”），它只向增大的方向变化。变量 \rm leaf 是当前编号最小的叶子。于是，Prüfer 序列的每一次迭代就是把 \rm leaf 加入答案，并检查 \rm parent[leaf] 是否比当前候选 \rm ptr 更小：如果更小，就直接令 \rm leaf = parent[leaf]，否则把指针 \rm ptr 移动到下一个叶子。

从代码容易看出，算法的复杂度确实是 O(n)：指针 \rm ptr 只会变化 O(n) 次，其余部分显然都是线性时间。

Prüfer 序列的一些性质
构造完 Prüfer 序列后，树中会剩下两个未被删除的顶点。
其中必然有一个是编号最大的顶点——n-1，而另一个顶点则没有任何确定的信息。

每个顶点在 Prüfer 序列中出现的次数等于它的度数减一。
这很容易理解：只要注意到顶点是在它的度数为 1 的时刻被删出树的——也就是说，到那时所有与它相邻的边中，除了一条外都已被删除。（对于构造完成后剩下的两个顶点，这个结论同样成立。）

由 Prüfer 序列恢复树
要恢复树，只需从前一点注意到：所求树中所有顶点的度数我们都已经知道（可以计算并保存在某个数组 degree[] 中）。因此，我们可以找出所有叶子，进而求出最小叶子的编号——它就是在第一步被删除的那个。这个叶子与 Prüfer 序列第一个元素所记录的顶点相连。

这样，我们找到了 Prüfer 序列删掉的第一条边。把这条边加入答案，然后减小该边两个端点的度数 degree[]。

重复这一操作，直到处理完整个 Prüfer 序列：找到 degree = 1 的最小顶点，把它与 Prüfer 序列中的下一个顶点相连，减小两端点的 degree[]。

最后我们只剩两个 degree = 1 的顶点——正是 Prüfer 算法留下来没有删除的那两个。用一条边把它们连起来。

算法结束，所求的树就构造好了。

用 O (n \log n) 的时间实现这个算法很容易：在支持取出最小值的结构（例如 C++ 中的 \rm set<> 或 \rm priority\_queue<>）中维护所有 degree=1 的顶点编号，每次取出最小值。

下面是相应实现（函数 prufer\_decode() 返回所求树的边列表）：

vector < pair<int,int> > prufer_decode (const vector<int> & prufer_code) {
	int n = (int) prufer_code.size() + 2;
	vector<int> degree (n, 1);
	for (int i=0; i<n-2; ++i)
		++degree[prufer_code[i]];
 
	set<int> leaves;
	for (int i=0; i<n; ++i)
		if (degree[i] == 1)
			leaves.insert (i);
 
	vector < pair<int,int> > result;
	for (int i=0; i<n-2; ++i) {
		int leaf = *leaves.begin();
		leaves.erase (leaves.begin());
 
		int v = prufer_code[i];
		result.push_back (make_pair (leaf, v));
		if (--degree[v] == 1)
			leaves.insert (v);
	}
	result.push_back (make_pair (*leaves.begin(), *--leaves.end()));
	return result;
}
在线性时间内由 Prüfer 序列恢复树
要得到线性复杂度的算法，可以运用与构造线性时间 Prüfer 序列算法时相同的技巧。

事实上，求编号最小的叶子并不需要支持取最小值的数据结构。替代方案是注意到：在我们找到并处理当前叶子后，它只会引入一个新的候选顶点。因此，我们只需一个移动指针，再加上一个存储当前最小叶子的变量：

vector < pair<int,int> > prufer_decode_linear (const vector<int> & prufer_code) {
	int n = (int) prufer_code.size() + 2;
	vector<int> degree (n, 1);
	for (int i=0; i<n-2; ++i)
		++degree[prufer_code[i]];
 
	int ptr = 0;
	while (ptr < n && degree[ptr] != 1)
		++ptr;
	int leaf = ptr;
 
	vector < pair<int,int> > result;
	for (int i=0; i<n-2; ++i) {
		int v = prufer_code[i];
		result.push_back (make_pair (leaf, v));
 
		--degree[leaf];
		if (--degree[v] == 1 && v < ptr)
			leaf = v;
		else {
			++ptr;
			while (ptr < n && degree[ptr] != 1)
				++ptr;
			leaf = ptr;
		}
	}
	for (int v=0; v<n-1; ++v)
		if (degree[v] == 1)
			result.push_back (make_pair (v, n-1));
	return result;
}
树与 Prüfer 序列之间的一一对应关系
一方面，每棵树都对应唯一的 Prüfer 序列（这由 Prüfer 序列的定义直接得出）。

另一方面，由 Prüfer 序列恢复树的算法的正确性可知，任意 Prüfer 序列（即 n-2 个数的序列，其中每个数都在 [1;n] 范围内）都对应某棵树。

因此，所有树与所有 Prüfer 序列构成一一对应。

凯莱公式
凯莱公式指出，n 个顶点的完全带标号图中的生成树数量为：

 n^{n-2}. 

这个公式有很多种证明，但利用 Prüfer 序列的证明直观且具有构造性。

的确，[1;n] 范围内的任意 n-2 个数的组合都唯一对应一棵 n 个顶点的树。不同的 Prüfer 序列总数为 n^{n-2}。由于 n 个顶点的完全图中任意树都可以作为生成树，所以生成树的数量就是 n^{n-2}，证毕。

使图连通的方案数
Prüfer 序列的强大之处在于，它能得到比凯莱公式更一般的公式。

设有 n 个顶点、m 条边的图；设 k 为该图的连通分量数。要求计算添加 k-1 条边使图连通的方案数（显然，k-1 条边是使图连通所需的最少边数）。

下面推导这个问题的完整公式。

记 s_1, \ldots, s_k 为该图各连通分量的大小。由于不允许在连通分量内部添加边，问题看起来与求 k 个顶点的完全图中的生成树数量很相似：但区别在于，每个顶点都有自己的“权重” s_i：每条与第 i 个顶点相邻的边都会使答案乘以 s_i。

因此，在计算方案数时，各顶点在生成树中的度数很重要。要得到问题的公式，需要对所有可能的度数求和。

设 d_1, \ldots, d_k 为生成树中各顶点的度数。顶点度数之和等于边数的两倍，因此：

 \sum_{i=1}^k d_i = 2k-2. 

如果第 i 个顶点的度数为 d_i，那么它在 Prüfer 序列中出现 d_i-1 次。k 个顶点的树的 Prüfer 序列长度为 k-2。选择 n-2 个数组成的序列、其中数字 i 恰好出现 d_i-1 次的方案数等于多项式系数（与二项式系数类似）：

 \binom{ k-2 }{ d_1-1, ~ d_2-1, ~ \ldots ~ , d_k-1[...]

考虑到每条与第 i 个顶点相邻的边都会使答案乘以 s_i，在顶点度数分别为 d_1, \ldots, d_k 的条件下，答案为：

 s_1^{d_1} \cdot s_2^{d_2} \cdot \ldots \cdot s_k^[...]

要对问题求最终答案，需要对该公式在所有可行的集合 \{ d_i \}_{i=1}^{i=k} 上求和：

 \sum_{ \substack{ d_i \ge 1, \\ \sum_{i=1}^k d_i [...]

为化简这个公式，我们利用多项式系数的定义：

 (x_1 + \ldots x_m)^p = \sum_{ \substack{ c_i \ge [...]

把该公式与上一个公式比较，如果引入记号 e_i = d_i-1：

 \sum_{ \substack{ e_i \ge 0, \\ \sum_{i=1}^k e_i [...]

那么化简后，问题的答案等于：

 s_1 \cdot s_2 \cdot \ldots \cdot s_k \cdot (s_1 +[...]

（k=1 时该公式也成立，尽管从证明中并不能形式上直接得出这一点）