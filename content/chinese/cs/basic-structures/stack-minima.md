---
title: 修改栈与队列以找最小值
authors:
- Максим Иванов
draft: true
---

这里看三道题：修改栈以支持在 O (1) 内找最小元素，同样修改队列，以及把它们应用于在 O (N) 内找给定数组所有固定长度子段的最小值。

修改栈
要求支持在 O (1) 内找栈中最小值，同时保持加入与删除的复杂度不变。

为此在栈中不存元素本身，而存 pair：元素，以及从该元素及其以下起算的栈最小值。换句话说，如果把栈看成 pair 数组，则

stack[i].second = min { stack[j].first }
                 j = 0..i
显然，找整个栈最小值就只是取 stack.top().second。

同样显然，加入新元素时 second 等于 min (stack.top().second, new_element)。从栈中删除元素与普通栈没有区别，因为被删元素不可能影响剩余元素的 second。

实现：

stack< pair<int,int> > st;
加入元素：
int minima = st.empty() ? new_element : min (new_element, st.top().second);
st.push (make_pair (new_element, minima));
取出元素：
int result = st.top().first;
st.pop();
找最小值：
minima = st.top().second;
修改队列。方法 1
这里看一种简单的改法，但它的缺点是修改后的队列可能不实际存所有元素（即取出元素时要知道想取的元素的值）。显然这是很特殊的情形（队列通常正是用来得知下一个元素，而非相反），但这种方法胜在简单。它也适用于找子段最小值问题（见下）。

关键思想是队列中不存所有元素，而只存确定最小值所需的部分。具体说，让队列表示非降序列（即队头存最小值），当然不任意，而总是包含最小值。那么整个队列的最小值总是它的第一个元素。加入新元素前，做一次「裁剪」：只要队尾元素大于新元素，就把它从队列中删掉；然后把新元素加到队尾。这样一方面不破坏顺序，另一方面不丢失当前元素——如果它在之后的某步成为最小值。但从队头取元素时，它可能已经不在了——我们的修改队列可能在重建过程中把它丢掉了。因此删除元素时要知道被删元素的值——如果该值的元素在队头，就取它；否则什么都不做。

实现上述操作：

deque<int> q;
找最小值：
current_minimum = q.front();
加入元素：
while (!q.empty() && q.back() > added_element)
	q.pop_back();
q.push_back (added_element);
取出元素：
if (!q.empty() && q.front() == removed_element)
	q.pop_front();
显然，这些操作平均都在 O (1)。

修改队列。方法 2
这里看另一种支持 O (1) 找最小值的队列改法，它实现稍复杂，但没有前一种方法的主要缺点：队列中确实保存所有元素，因而取出元素时不必知道它的值。

思路是归结为已解决的栈问题。学会用两个栈模拟队列。

建两个栈：s1 和 s2；自然指支持 O (1) 找最小值的修改栈。新元素总是加入栈 s1，取元素只从栈 s2 取。若尝试从 s2 取时它为空，就把 s1 的所有元素转移到 s2（此时 s2 中元素顺序反转，正是取元素所需；s1 变空）。最后，找队列最小值就是取栈 s1 的最小值与栈 s2 的最小值中较小者。

这样我们仍以 O (1) 完成所有操作（理由很简单：每个元素最坏情况下加入 s1 1 次、转移到 s2 1 次、从 s2 取出 1 次）。

实现：

stack< pair<int,int> > s1, s2;
找最小值：
if (s1.empty() || s2.empty())
	current_minimum = s1.empty ? s2.top().second : s1.top().second;
else
	current_minimum = min (s1.top().second, s2.top().second);
加入元素：
int minima = s1.empty() ? new_element : min (new_element, s1.top().second);
s1.push (make_pair (new_element, minima));
取出元素：
if (s2.empty())
	while (!s1.empty()) {
		int element = s1.top().first;
		s1.pop();
		int minima = s2.empty() ? element : min (element, s2.top().second);
		s2.push (make_pair (element, minima));
	}
result = s2.top().first;
s2.pop();
求给定数组所有固定长度子段的最小值
设给长度 N 的数组 A 和数 M ≤ N。要求找出数组每个长度为 M 的子段的最小值，即求：

min A[i],    min A[i],    min A[i],    ...,    min A[i]
0≤i≤M-1      1≤i≤M        2≤i≤M+1              N-M≤i≤N-1
在线性时间 O (N) 内解决。

为此只需维护一个支持 O (1) 找最小值的修改队列（上文已讨论），本题两种实现都适用。解法已经清楚：把数组前 M 个元素加入队列，找出最小值并输出；然后加入下一个元素、取出第一个元素，再输出最小值，依此类推。由于所有队列操作平均在常数时间，整个算法复杂度为 O (N)。

值得注意的是，第一种修改队列的实现更简单，但可能需要存整个数组（因为第 i 步要知道数组第 i 个和第 (i-M) 个元素）。用第二种实现则不必显式存数组 A——只需能得知第 i 个元素。
