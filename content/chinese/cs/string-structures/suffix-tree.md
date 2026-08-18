---
title: 后缀树
draft: true
---

本文是临时占位，不含任何说明。

Ukkonen 算法的描述可以在例如 Gasfield 的《算法中的字符串、树与序列》里找到。

Ukkonen 算法的实现
这个算法在 O (n \log k) 内为给定长度 n 的字符串构建后缀树，其中 k 是字母表大小（若视为常数，复杂度为 O (n)）。

算法的输入是字符串 s 及其长度 n，以全局变量传入。

主函数是 \rm build\_tree，它构建后缀树。树存成结构数组 \rm node，其中 {\rm node}[0] 是后缀树根。

为简化代码，边存在同一结构里：对每个顶点，在其 \rm node 结构里记录从祖先进入它的边的数据。总之每个 \rm node 存：(l,r)，定义进入祖先的边标签 s[l..r-1]，\rm par ——祖先顶点，\rm link ——后缀链接，\rm next ——出边列表。

string s;
int n;
 
struct node {
	int l, r, par, link;
	map<char,int> next;
 
	node (int l=0, int r=0, int par=-1)
		: l(l), r(r), par(par), link(-1) {}
	int len()  {  return r - l;  }
	int &get (char c) {
		if (!next.count(c))  next[c] = -1;
		return next[c];
	}
};
node t[MAXN];
int sz;
 
struct state {
	int v, pos;
	state (int v, int pos) : v(v), pos(pos)  {}
};
state ptr (0, 0);
 
state go (state st, int l, int r) {
	while (l < r)
		if (st.pos == t[st.v].len()) {
			st = state (t[st.v].get( s[l] ), 0);
			if (st.v == -1)  return st;
		}
		else {
			if (s[ t[st.v].l + st.pos ] != s[l])
				return state (-1, -1);
			if (r-l < t[st.v].len() - st.pos)
				return state (st.v, st.pos + r-l);
			l += t[st.v].len() - st.pos;
			st.pos = t[st.v].len();
		}
	return st;
}
 
int split (state st) {
	if (st.pos == t[st.v].len())
		return st.v;
	if (st.pos == 0)
		return t[st.v].par;
	node v = t[st.v];
	int id = sz++;
	t[id] = node (v.l, v.l+st.pos, v.par);
	t[v.par].get( s[v.l] ) = id;
	t[id].get( s[v.l+st.pos] ) = st.v;
	t[st.v].par = id;
	t[st.v].l += st.pos;
	return id;
}
 
int get_link (int v) {
	if (t[v].link != -1)  return t[v].link;
	if (t[v].par == -1)  return 0;
	int to = get_link (t[v].par);
	return t[v].link = split (go (state(to,t[to].len()), t[v].l + (t[v].par==0), t[v].r));
}
 
void tree_extend (int pos) {
	for(;;) {
		state nptr = go (ptr, pos, pos+1);
		if (nptr.v != -1) {
			ptr = nptr;
			return;
		}
 
		int mid = split (ptr);
		int leaf = sz++;
		t[leaf] = node (pos, n, mid);
		t[mid].get( s[pos] ) = leaf;
 
		ptr.v = get_link (mid);
		ptr.pos = t[ptr.v].len();
		if (!mid)  break;
	}
}
 
void build_tree() {
	sz = 1;
	for (int i=0; i<n; ++i)
		tree_extend (i);
}
压缩实现
再给出 freopen 提出的如下紧凑的 Ukkonen 算法实现：

const int N=1000000,INF=1000000000;
string a;
int t[N][26],l[N],r[N],p[N],s[N],tv,tp,ts,la;
 
void ukkadd (int c) {
	suff:;
	if (r[tv]<tp) {
		if (t[tv][c]==-1) { t[tv][c]=ts;  l[ts]=la;
			p[ts++]=tv;  tv=s[tv];  tp=r[tv]+1;  goto suff; }
		tv=t[tv][c]; tp=l[tv];
	}
	if (tp==-1 || c==a[tp]-'a') tp++; else {
		l[ts+1]=la;  p[ts+1]=ts;
		l[ts]=l[tv];  r[ts]=tp-1;  p[ts]=p[tv];  t[ts][c]=ts+1;  t[ts][a[tp]-'a']=tv;
		l[tv]=tp;  p[tv]=ts;  t[p[ts]][a[l[ts]]-'a']=ts;  ts+=2;
		tv=s[p[ts-2]];  tp=l[ts-2];
		while (tp<=r[ts-2]) {  tv=t[tv][a[tp]-'a'];  tp+=r[tv]-l[tv]+1;}
		if (tp==r[ts-2]+1)  s[ts-2]=tv;  else s[ts-2]=ts; 
		tp=r[tv]-(tp-r[ts-2])+2;  goto suff;
	}
}
 
void build() {
	ts=2;
	tv=0;
	tp=0;
	fill(r,r+N,(int)a.size()-1);
	s[0]=1;
	l[0]=-1;
	r[0]=-1;
	l[1]=-1;
	r[1]=-1;
	memset (t, -1, sizeof t);
	fill(t[1],t[1]+26,0);
	for (la=0; la<(int)a.size(); ++la)
		ukkadd (a[la]-'a');
}
同一段代码，带注释：

const int N=1000000,    // 后缀树中顶点的最大数
	INF=1000000000; // "无穷大"常数
string a;       // 要建树的输入字符串
int t[N][26],   // 转移数组（状态, 字母）
	l[N],   // 左
	r[N],   // 和右边界：进入顶点的边对应的 a 子串
	p[N],   // 顶点祖先
	s[N],   // 后缀链接
	tv,     // 当前后缀的顶点（如果在边中间，则为边下端顶点）
	tp,     // 对应边上位置（从 l[tv] 到 r[tv] 含）的字符串位置
	ts,     // 顶点数
	la;     // 当前字符串字符
 
void ukkadd(int c) { // 向树追加字符 c
	suff:;      // 每次转移到后缀后回到这里（并重新加字符）
	if (r[tv]<tp) { // 检查是否越出当前边
		// 若越出，找下一条边。若没有——建叶子并挂到树上
		if (t[tv][c]==-1) {t[tv][c]=ts;l[ts]=la;p[ts++]=tv;tv=s[tv];tp=r[tv]+1;goto suff;}
		tv=t[tv][c];tp=l[tv]; // 否则直接转移到下一条边
	}
	if (tp==-1 || c==a[tp]-'a') tp++; else { // 如果边上字母与 c 相同则沿边走，否则
		// 把边分成两段。中间是顶点 ts
		l[ts]=l[tv];r[ts]=tp-1;p[ts]=p[tv];t[ts][a[tp]-'a']=tv;
		// 放叶子 ts+1。它对应按 c 的转移。
		t[ts][c]=ts+1;l[ts+1]=la;p[ts+1]=ts;
		// 更新当前顶点参数。别忘从祖先 tv 到 ts 的转移。
		l[tv]=tp;p[tv]=ts;t[p[ts]][a[l[ts]]-'a']=ts;ts+=2;
		// 准备下降：沿边上去并走后缀链接。
		// tp 会标出当前后缀中的位置。
		tv=s[p[ts-2]];tp=l[ts-2];
		// 只要当前后缀没结束，就向下走
		while (tp<=r[ts-2]) {tv=t[tv][a[tp]-'a'];tp+=r[tv]-l[tv]+1;}
		// 如果到了顶点，就把后缀链接设到它；否则设到 ts
		// （因为下轮迭代会创建 ts）。
		if (tp==r[ts-2]+1) s[ts-2]=tv; else s[ts-2]=ts; 
		// 把 tp 设到新边，去给后缀加字符。
		tp=r[tv]-(tp-r[ts-2])+2;goto suff;
	}
}
 
void build() {
	ts=2;
	tv=0;
	tp=0;
	fill(r,r+N,(int)a.size()-1);
	// 初始化树根数据
	s[0]=1;
	l[0]=-1;
	r[0]=-1;
	l[1]=-1;
	r[1]=-1;
	memset (t, -1, sizeof t);
	fill(t[1],t[1]+26,0);
	// 逐个字母把文本加进树
	for (la=0; la<(int)a.size(); ++la)
		ukkadd (a[la]-'a');
}
