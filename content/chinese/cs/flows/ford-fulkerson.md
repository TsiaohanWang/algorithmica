---
title: Ford–Fulkerson 算法
authors:
- Максим Иванов
draft: true
---

给定由 N 个顶点和 M 条边组成的网络 G。每条边（一般说来是有向的，但关于这一点见下文）都标有容量（非负整数）和沿该边流动的单位流量成本（某个整数）。图中标出源点 S 和汇点 T。给定某个流量值 K，要求找出大小为该值的流，并且在所有大小为该值的流中选出成本最小的一个（“min-cost-flow 问题”）。

有时问题会以略微不同的方式提出：要求找出成本最小的最大流（“min-cost-max-flow 问题”）。

这两个问题都可以用下文描述的增广路算法相当高效地解决。

描述
该算法与计算最大流的 Edmonds–Karp 算法非常相似。

最简单的情形
首先考虑最简单的情形：图是有向的，并且任意一对顶点之间至多有一条边（如果存在边 (i,j)，就不应当存在边 (j,i)）。

设 Uij 为边 (i,j) 的容量（如果该边存在）。设 Cij 为沿边 (i,j) 流动的单位流量成本。设 Fij 为沿边 (i,j) 的流量大小，初始时所有流量都为零。

按如下方式修改网络：对每条边 (i,j)，在网络中加入所谓的反向边 (j,i)，其容量 Uji = 0、成本 Cji = - Cij。由于按我们的假设，网络中此前没有边 (j,i)，这样修改后的网络仍然不是多重图。此外，在整个算法运行期间保持条件 Fji = - Fij 成立。

对某个固定的流 F，按如下方式定义残量网络（实际上与 Ford–Fulkerson 算法中的定义相同）：残量网络只包含未饱和的边（即满足 Fij < Uij 的边），而每条这样的边的残量容量为 UPIij = Uij - Fij。

min-cost-flow 算法本身如下。在算法的每轮迭代中，我们在残量网络中寻找从 S 到 T 的最短路径（相对于成本 Cij 而言最短）。如果没有找到路径，算法结束，流 F 即为所求。如果找到了路径，我们就沿它尽可能多地增加流量（即沿这条路径走一遍，找出这条路径所有边中最小的残量容量 MIN_UPI，然后把路径上每条边的流量增加 MIN_UPI，同时不要忘记把反向边上的流量减少同样的量）。如果在某个时刻流量达到了 K（题目给定的流量值），我们也同样停止算法（应当考虑到，此时在最后一轮迭代中沿路径增加流量时，需要让增加的流量保证最终流量不超过 K，但这很容易做到）。

不难看出，如果把 K 设为无穷大，算法就会找到成本最小的最大流，也就是说，同一个算法无需任何修改就能解决 min-cost-flow 和 min-cost-max-flow 这两个问题。

无向图与多重图的情形
无向图和多重图的情形在概念上与上述情形没有任何区别，因此算法本身也适用于这类图。不过，实现中会出现一些需要注意的困难。

无向边 (i,j) 实际上就是两条具有相同容量和成本的有向边 (i,j) 与 (j,i)。由于上述 min-cost-flow 算法要求为每条无向边创建与它相反的边，最终的结果就是一条无向边被拆分成 4 条有向边，我们实际上就落入多重图的情形。

多重边会带来哪些问题？首先，每条多重边上的流量必须分别保存。其次，在寻找最短路径时应当注意，按前驱恢复路径时选择哪一条多重边很重要。也就是说，除了每个顶点的前驱顶点外，我们还必须保存前驱顶点以及从它到达当前顶点的那条边的编号。第三，根据算法，当沿某条边增加流量时，需要减少反向边上的流量。由于可能存在多重边，因此必须为每条边保存与它相反的边的编号。

无向图和多重图没有其他困难了。

运行时间分析
与 Edmonds–Karp 算法的分析类似，我们得到这样的估计：O (N M) * T (N, M)，其中 T (N, M) 是在具有 N 个顶点和 M 条边的图中寻找最短路径所需的时间。如果使用最简单版本的 Dijkstra 算法来实现，那么整个 min-cost-flow 算法的估计为 O (N3 M)，不过 Dijkstra 算法必须修改，才能处理带负权边的图（这被称为带势的 Dijkstra 算法）。

也可以改用 Levit 算法，它虽然渐近上差得多，但实践中运行得非常快（大约与 Dijkstra 算法耗时相当）。

实现
这里给出基于 Levit 算法的 min-cost-flow 实现。

算法的输入是带有 N 个顶点和 M 条边的网络（无向多重图）以及 K——需要求出的流量大小。如果存在这样的流，算法求出大小为 K 的成本最小的流；否则求出达到最大值的成本最小的流。

程序中有专门用于添加有向边的函数。如果需要添加无向边，则需要按 (i,j) 和 (j,i) 两个方向各调用一次该函数。

const int INF = 1000*1000*1000;

struct rib {
	int b, u, c, f;
	size_t back;
};

void add_rib (vector < vector<rib> > & g, int a, int b, int u, int c) {
	rib r1 = { b, u, c, 0, g[b].size() };
	rib r2 = { a, 0, -c, 0, g[a].size() };
	g[a].push_back (r1);
	g[b].push_back (r2);
}

int main()
{
	int n, m, k;
	vector < vector<rib> > g (n);
	int s, t;
	... чтение графа ...

	int flow = 0,  cost = 0;
	while (flow < k) {
		vector<int> id (n, 0);
		vector<int> d (n, INF);
		vector<int> q (n);
		vector<int> p (n);
		vector<size_t> p_rib (n);
		int qh=0, qt=0;
		q[qt++] = s;
		d[s] = 0;
		while (qh != qt) {
			int v = q[qh++];
			id[v] = 2;
			if (qh == n)  qh = 0;
			for (size_t i=0; i<g[v].size(); ++i) {
				rib & r = g[v][i];
				if (r.f < r.u && d[v] + r.c < d[r.b]) {
					d[r.b] = d[v] + r.c;
					if (id[r.b] == 0) {
						q[qt++] = r.b;
						if (qt == n)  qt = 0;
					}
					else if (id[r.b] == 2) {
						if (--qh == -1)  qh = n-1;
						q[qh] = r.b;
					}
					id[r.b] = 1;
					p[r.b] = v;
					p_rib[r.b] = i;
				}
			}
		}
		if (d[t] == INF)  break;
		int addflow = k - flow;
		for (int v=t; v!=s; v=p[v]) {
			int pv = p[v];  size_t pr = p_rib[v];
			addflow = min (addflow, g[pv][pr].u - g[pv][pr].f);
		}
		for (int v=t; v!=s; v=p[v]) {
			int pv = p[v];  size_t pr = p_rib[v],  r = g[pv][pr].back;
			g[pv][pr].f += addflow;
			g[v][r].f -= addflow;
			cost += g[pv][pr].c * addflow;
		}
		flow += addflow;
	}

	... вывод результата ...

}

---

### 一点理论

作为练习，请给出把最小割的寻找归约到最大流寻找的方法。

### Ford–Fulkerson 算法

算法的思想是：初始时 $\\forall{v, u}: f(v, u) = 0$，我们沿增广路迭代地增加它：

1.  对所有边设 $f(v, u) = 0$
2.  如果汇点在残量网络中从源点不可达（沿满足 $c_f(v, u) \> 0$ 的边），算法结束
3.  在 $G_f$ 中寻找增广路，并沿它推送 $\\underset{(v, u) \\in P}{min} c_f(v, u)$ 的流量
4.  转到第 2 步

如果算法结束，那么残量网络中没有增广路，也就是说它找到了最大流。在大多数问题中容量是整数，因此算法的每轮迭代至少使流量增加 1；增广路可以用 $dfs$ 寻找，因此运行时间为 $O(|F|\*(V + E))$。

### C++ 示例实现

``` c++ numberLines
struct Edge {
    int v; // вершина, куда ведёт ребро
    int flow; // поток, текущий по ребру
    int capacity; // пропускная способность ребра

    Edge(int v, int capacity)
        : v(v), flow(0), capacity(capacity) {}

    int get_capacity() { // пропускная способность ребра в остаточной сети
        return capacity - flow;
    }
};

const int INF = (int)(1e9) + 666;
const int N = 666;
int S, T; // сток и исток

vector<Edge> edges;
vector<int> graph[N]; // в списке смежности храним не рёбра, и индексы в списке рёбер
int used[N];
int timer = 1; // для быстрого зануления used-а

// Будем поддерживать список рёбер в таком состоянии, что для i ребра, (i ^ 1) будет обратным
void add_edge(int v, int u, int capacity) {
    graph[v].emplace_back(edges.size()); // номер ребра в списке
    edges.emplace_back(u, capacity); // прямое ребро
    graph[u].emplace_back(edges.size()); // номер ребра
    edges.emplace_back(v, 0); // обратное ребро
}
int dfs(int v, int min_capacity) {
    if (v == T) {
        // нашли увеличивающий путь, вдоль которого можно пустить min_capacity потока
        return min_capacity;
    }
    used[v] = timer;
    for (int index : graph[v]) {
        if (edges[index].get_capacity() == 0) {
            continue; // ребро отсутсвует в остаточной сети
        }
        if (used[edges[index].v] == timer) {
            continue;
        }
        int x = dfs(edges[index].v, min(min_capacity, edges[index].get_capacity()));
        if (x) { // нашли путь по которому можно пустить x потока
            edges[index].flow += x;
            edges[index ^ 1].flow -= x;
            return x;
        }
    }
    // не существует пути из v в T
    return 0;
}

int main() {
    int n, m;
    cin >> n >> m >> S >> T;
    for (int i = 0; i < m; ++i) {
        int v, u, capacity;
        cin >> v >> u >> capacity;
        add_edge(v, u, capacity);
    }
    while (dfs(S, INF)) {  // ищем увеличивающий путь
        ++timer
    }
    // увеличивающего пути нет, следовательно максимальный потока найден
    int result = 0;
    for (int index : graph[S]) {
        result += edges[index].flow;
    }
    cout << result << endl;
    return 0;
}
```

[分类：讲义](Категория:Конспект "wikilink") [分类：网络流](Категория:Потоки_в_сети "wikilink")