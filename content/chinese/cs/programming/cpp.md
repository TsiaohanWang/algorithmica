---
title: C++ 快速入门
authors:
- Сергей Слотин
- Даниил Николенко
weight: 1
draft: true
---

C++ 的第一大优势是 STL，它包含大量算法和数据结构。要使用它，你需要写

```
using namespace std;
```

https://en.cppreference.com/ 是 C++ 语言的文档网站。在那里你可以找到关于该语言本身及其标准库的许多有用信息。而这里则是对 STL 中最有用部分的简明总结。

## 聊聊普通的 C 风格数组


```
T a[x]; // инициализация массива a типа T размера x
```

如果你是这样写的，请停手，这种方法有很多问题。让我们写出正确的实现，并讨论一下优缺点。


```
array<T, x> a;
a.begin(), a.end() // указатели (итераторы) на начало и конец массива соответственно (конец массива = после последнего элемента)
a.front(), a.back() // возвращает ссылку на первый и последний элемент соответственно
cout << a.at(5); // метод at позволяет узнать не вышли ли мы за границы массива
```

优点：

1) 指向开头和结尾的指针（迭代器）是很棒的东西，我们稍后会讨论

2) C 风格数组现在就已经与 C++ 的风格格格不入，将来人们甚至想彻底移除它们，所以最好现在就弃用

3) 可以轻松地从数组切换到 vector

缺点：

1) 很难戒掉旧数组的使用习惯。

## vector

`vector` 是*动态数组*。这意味着它的大小可以在程序运行期间改变，你可以向末尾添加元素等等。要声明一个能容纳类型 `T` 的整数的空 `vector`，需要使用如下结构：


```
vector<T> vector_name;
```

这里的 `T` 是 `vector` 中元素的类型，`vector_name` 则是 `vector` 本身的名字。与其他 C++ 容器一样，`vector` 不能容纳不同类型的元素！

要向 vector 末尾添加元素，需要用到 `push_back` 函数。这个函数平均复杂度为 $O(1)$。

访问 `vector` 有两种方式，我们已经在数组中讨论过这两种方式了。


```
vector<int> a;
cout << a[5];
cout << a.at(5);
```

除此之外，你可能会用到以下方法：

### vector 是如何工作的？

如前所述，向 vector 末尾添加元素的平均复杂度为 $O(1)$。这意味着，如果你执行 $n$ 次 `push_back` 操作，它们总共需要 $O(n)$ 时间。（但其中某些操作可能花了线性时间！）

`vector` 有两个重要的量：`size` 和 `capacity`——大小和容量。大小是指 vector 中当前有多少个元素；容量是指为多少个元素分配了内存。当 `size` < `capacity` 时，`push_back` 只是把新元素放到已分配内存的第一个空闲单元里，因此复杂度为 $O(1)$。当 `size` = `capacity` 时，就无法这样做了，于是会发生以下过程：
1. `capacity` 大约扩大为原来的 2 倍。
2. 分配一块能容纳 `capacity` 个元素的内存区域。
3. 把旧内存区域中的元素复制到新区域。
4. 释放旧内存区域。

我们来理解为什么 `push_back` 的均摊时间确实是 $O(1)$。假设当前 `capacity` = $n$。那么我们总共分配过 $n + \frac{n}{2} + \frac{n}{4} + \dots < 2n$ 的内存。复制操作也花费了不超过 $2n$ 次。因此，由于 `push_back` 操作至少有 $\frac{n}{2}$ 次，每次操作平均花费 $O(1)$ 时间。

## pair

`pair` 是包含一对值的类型，而且两个值可以是不同类型。声明 pair 的方式如下：


```
pair<T1, T2> p;
```

这里的 `T1` 和 `T2` 分别是第一种和第二种类型的名字。

pair 的第一个元素是 `p.first`；第二个是 `p.second`。

`make_pair(a, b)` 是创建 pair $(a, b)$ 的函数。

来看一个使用 `pair` 的例子。


```
pair<int, double> p = make_pair(1, 2.0);
pair<int, double> q = {1, 2.5}; // другой способ инициализировать пару
cout << p.first << " " << p.second << "\n";
```

## queue


C++ 中已经实现了队列这种数据结构，它叫作 queue。


```
queue<T> q; //очередь типа T
```

队列是遵循 FIFO（先进先出）原则的结构，也就是说队列有两个基本操作：在末尾插入、从开头取出。


```
q.front(); // ссылка на первый элемент
q.back(); // ссылка на последний элемент
q.push(x); // добавить в конец
q.pop(); //удалить с начала
```

## deque

deque 是能同时操作头部和尾部的结构，即可以在两端进行插入和删除。



```
deque<T> name; // дек типа T с названием name
name.front(), name.back(); // первый и последний элемент соответственно
name.pop_front(), name.pop_back(); // удаление первого и последнего элемента
name.push_front(x), name.push_back(x); // вставка x в начало/конец
```

队列和 deque 将在后面的某节课中更详细地介绍。
## set

`set` 是包含**一组**唯一且有序元素的集合。

要向 `set` 添加元素，有 `insert` 函数。如果元素已经在集合中，则什么也不会发生。
要从 `set` 中删除元素，有 `erase` 函数（可以向它传入指向元素的迭代器，或直接传入元素）。如果元素不在集合中，则什么也不会发生。
要查看 `set` 中是否有某个元素，有 `count` 函数。如果元素不在集合中它返回 $0$，存在则返回 $1$。还有 `find` 方法，它返回指向该元素的迭代器；如果元素不存在则返回 `end`。

`set` 的所有元素操作（添加、删除、查找）复杂度均为 $O(\log n$)，其中 $n$ 是其中元素的数量，因为它是用平衡二叉搜索树实现的。

`set` 的迭代器属于 `BidirectionalIterator` 类别，类型为 `set<T>::iterator`。`set` 的开头可以用 `begin` 函数获得，结尾用 `end` 函数获得。与 vector 的情况一样，`end` 指向半开区间的结尾。`set` 迭代器的自增和自减同样花费对数时间。

值得一提的是，由于 `set` 中的元素是有序的，利用 `begin` 和 `end` 可以找到 `set` 中的最小/最大元素。
要找大于或等于给定值的最小元素，有 `lower_bound` 函数。
要找严格大于给定值的最小元素，有 `upper_bound` 函数。
这些函数都会返回指向目标元素的迭代器；如果不存在这样的元素，则返回 `end()`。

`set` 只能包含那些定义了 `<` 运算符的类型的元素，因为它需要元素之间的顺序。

来看一个 `set` 基本操作的例子。


```
set<int> s;

s.insert(3); // s = {3}
s.insert(2); // s = {2, 3}
cout << s.size() << "\n"; // выведет 2

s.insert(3); // 3 не будет добавлено ещё раз, так как уже присутствует в множестве
cout << s.size() << "\n"; // выведет 2

s.insert(5); // s = {2, 3, 5}
cout << s.count(3) << "\n"; // выведет 1
cout << s.count(4) << "\n"; // выведет 0

s.erase(3); // s = {2, 5}
s.insert(6); // s = {2, 5, 6}

set<int>::iterator it1 = s.find(5);
it1++;
cout << *it1 << "\n"; // выведет 6

auto it2 = s.lower_bound(1);
cout << *it2 << "\n"; // выведет 2, так как это первый элемент >= 1

auto it3 = s.upper_bound(2);
cout << *it3 << "\n"; // выведет 5, так как это первый элемент > 2.

auto it4 = s.upper_bound(10);
if (it4 == s.end()) {
    cout << "No element > 10\n"; // аккуратно, если разыменуете it4, получите undefined behaviour!
}

// вывод всех элементов сета с использованием итераторов; элементы следуют в порядке возрастания
for (auto it = s.begin(); it != s.end(); it++) {
    cout << *it << " ";
}
cout << "\n"; // но для таких целей лучше использовать range-based for loop!
```



### multiset

`multiset` 与 `set` 相同，但可以包含重复元素。

`count` 的复杂度为 $O(\log n + c)$，其中 $c$ 是要查找的元素数量。因此，要检查元素 $el$ 是否存在于 `multiset` `s` 中，应该用：`s.find(el) != s.end()`。

`erase` 会删除所有具有该值的元素。要只删除一个，需要这样写：`s.erase(s.find(el)).


### 用 set 解题的例子

很多时候，用 set 可以解决那些本来也能用完全不同的方法解决的题目，那种方法有时更复杂，有时更简单。最常使用 set 的场景是需要处理与**不同元素的数量**或**某个集合的最小值或最大值**相关的事情。

#### 1) 题目「女孩还是男孩」

**题目链接**： http://codeforces.com/contest/236/problem/A

**题意简述**： 求字符串中不同字符个数的奇偶性。

**题解**： 把所有字符插入 set，然后检查 set 大小的奇偶性。

注意，这道题也可以轻松地用计数法解决（就像计数排序那样），因为字符的种类很少。

#### 2) A 与 B 与编译错误

**题目链接**： http://codeforces.com/contest/519/problem/B

**题意简述**： 从数组中恰好移除一个数并打乱元素，然后再做一次。找出消失的两个元素。

**题解**： 把所有数加入 3 个不同的 multiset，然后依次遍历它们，找出第一个在第二个 multiset 中数量比第一个少但仍然存在的元素。这样就找到了第一次的错误，第二次的错误同样处理。

注意，这道题也可以简单地把所有数排序解决，其渐近复杂度同样是 $O(N log N)$。

#### 3) 区间最小值

**题目链接**： https://informatics.msk.ru/mod/statements/view3.php?chapterid=756

**题意简述**： 求数组中每个长度为 $K$ 的区间的最小值。

**题解**： 先把前 $K$ 个元素放进 multiset。然后我们移动这个「窗口」：从右边加入新元素，移除最左边的元素。每次输出 set 中的最小值，它就位于 `s.begin()`。

这道题也可以用以下数据结构解决：

1) 单调队列（$O(N)$！）

2) 线段树

3) Sparse Table

4) 堆

但用 set 解决要简单得多。

## map

`map` 是关联容器：它包含*键值对*，且所有键都是唯一的。容器内部所有键按升序排列。与 `set` 一样，操作花费对数时间。

`map` 的声明方式如下：`map<T1, T2> map_name`，其中 `T1` 是键的类型，`T2` 是值的类型。

对 `map` 元素的访问通过运算符 `[]` 进行。与 `set` 类似，`map` 支持用 `find`、`lower_bound`、`upper_bound` 按键查找。解引用迭代器得到的是一个 pair，其第一个元素是键，第二个是值。

当用 `[]` 访问 `map` 中不存在的元素时，该值会被初始化为该类型的默认值。

通过例子来看 `map` 的用法：


```
map<int, int> a;
a[13] = 5;
a[2] = 7;
cout << a[2] << "\n"; // выведет 7
a[2]++;
cout << a[2] << "\n"; // выведет 8
a[100] = 42;

/* Этот цикл выведет 3 строки:
   2 8
   13 5
   100 42

   Обратите внимание, что ключи упорядочены.
*/
for (auto el : a) {
    cout << el.first << " " << el.second << "\n";
}


map<string, int> b;
b["Bob"]--;
b["Alice"] += 2;
b["Dan"] = 123;

/* Этот цикл выведет 2 строки:
   Alice 2
   Bob -1
   Dan 123
*/
for (auto el : b) {
    cout << el.first << " " << el.second << "\n";
}

map<string, vector<int>> c;
c["wow"].push_back(2);
c["abc"] = {2, -1, 17};
cout << c["abc"].size() << "\n"; // выведет 3
```

## Unordered 数据结构

set 和 map 唯一的问题在于它们的时间复杂度为 $O(\log n)$，在某些题目中这太慢了。于是人们想到不用二叉树来实现它们，而改用哈希表（你们会在二年级学到它），这样 unordered_set 支持 $O(1)$ 的插入和删除，唯一的问题是它按无序存放元素，也就是说我们无法再找最小值、最大值了。

Python 内置的 set 和 dict 正是 unordered_set 和 unordered_map 的对应物。Python 中没有有序的 set 和 map。


```
unordered_set<int> a;
a.insert(x);
a.erase(x);
```

## algorithm 中的实用函数

### swap
`swap(a, b)` 交换变量 `a` 和 `b` 的值。


```
int a = 5;
int b = 3;
cout << a << " " << b << "\n"; // выведет 5 3
swap(a, b);
cout << a << " " << b << "\n"; // выведет 3 5
```

### min_element 和 max_element
`min_element(first, last)` 返回半开区间 `[first; last)` 上最小值的迭代器。
`max_element(first, last)` 返回半开区间 `[first; last)` 上最大值的迭代器。


如果有多个最小值/最大值，返回第一个出现的位置。


```
vector<int> numbers = {5, 3, 1, 2, 1};
auto it = min_element(numbers.begin(), numbers.end());
cout << *it << " " << (it - numbers.begin()) << "\n"; // выведет 1 2
```

### reverse
`reverse(first, last)` 翻转半开区间 `[first; last)`（元素变为逆序）。


```
vector<int> a = {5, 2, 3, 10, 17};
reverse(a.begin(), a.begin() + 3);
for (int x : a) {
    cout << x << " ";
}
cout << "\n";
```

这个例子会输出 `3 2 5 10 17 `。

### sort、unique 与比较器

`sort(first, last)` 对半开区间 `[first; last)` 排序。


```
vector<int> a = {5, 2, 10, 11, 2, 3};
sort(a.begin(), a.end()); // сортируем весь вектор
for (int x : a) {
    cout << x << " ";
}
cout << "\n";
```

这个例子会输出 `2 2 3 5 10 11`。

`sort` 函数可以接受第三个参数——*比较器*。比较器是一个接受两个对象并返回 `true`（当第一个*严格小于*第二个时）或 `false` 的函数。

假设我们想按数字的个位数字升序排序，个位相同时再按数值本身排序。那么可以写如下代码：


```
bool cmp(int a, int b) {
    return make_pair(a % 10, a) < make_pair(b % 10, b);
}

// это внутри main
vector<int> a = {30, 32, 12, 7, 15};
sort(a.begin(), a.end(), cmp);
for (int x : a) {
    cout << x << " ";
}
cout << "\n";
```

在这个例子中，正如我们所愿，会输出 `30 12 32 15 7`。

`unique(first, last)` 接受一个半开区间并删除其中所有连续的重复元素。函数返回指向去重后元素对应半开区间末尾的迭代器。该半开区间之后元素的值将变得不确定。因此建议将 `unique` 与 `resize` 等函数搭配使用。


```
vector<int> a = {5, 5, 5, 1, 5, 4, 4, 7, 1};
a.resize(unique(a.begin(), a.end()) - a.begin());
for (int x : a) {
    cout << x << " ";
}
cout << "\n";
```

这个例子会输出 `5 1 5 4 7 1`。

经常需要先对元素排序，再去除所有重复。这可以通过下面的组合实现：


```
sort(a.begin(), a.end());
a.resize(unique(a.begin(), a.end()) - a.begin());
```

### nth_element

该函数把数组排序后本应位于指定位置的元素放到该位置（线性时间）。


```
nth_element(begin, need, end); // need - позиция отсортированного массива, 
//begin, end - итераторы на начало и конец места, которое надо сортировать.
```

### next_permutation、prev_permutation

生成数组在区间 l 到 r 上的下一个和上一个排列；


```
next_permutation(l, r);//l, r - итераторы
prev_permutation(a.begin(), a.end());
```

### merge


```
merge(начало первой последовательности, конец первой последовательности, начало 
второй последовательности, конец второй последовательности, куда вставлять);
```

合并两个数组，用于归并排序。

### lower_bound、upper_bound、binary_search

这些函数都接受半开区间 `[first; last)` 和一个值 `value`。半开区间必须按 `element < value` 关系排序（满足该关系的元素在前，其余在后）。

`lower_bound` 返回第一个大于或等于 `value` 的元素。
`upper_bound` 返回第一个严格大于 `value` 的元素。
`binary_search` 返回 `value` 是否存在于该半开区间中。


```
vector<int> a = {1, 5, 5, 6, 7, 10};

auto it1 = lower_bound(a.begin(), a.end(), 5);
cout << (it1 - a.begin()) << "\n"; // выведет 1

auto it2 = upper_bound(a.begin(), a.end(), 5);
cout << *it2 << "\n"; // выведет 6

if (binary_search(a.begin(), a.end(), 7)) {
    cout << "There is an element = 7\n"; // это будет выведено
}
```

#### 注意！
不要在 `set`/`map` 上使用 `lower_bound`、`upper_bound`、`binary_search`！它们会退化为线性时间。请使用它们自己的成员函数：`set::lower_bound`（通过 `.` 调用）等等。

## 加速输入输出

标准的 `cin` 和 `cout` 工作*非常*慢。要解决这个问题，请在 `main` 函数开头写以下代码：


```
ios::sync_with_stdio(0);
cin.tie(0);
cout.tie(0);
```

这能把输入输出加速好几倍！

另外强烈不建议使用 `endl`（交互题除外）。请使用 `"\n"`。它们的区别在于 `endl` 会刷新（flush）输出缓冲区，也就是立即输出你想输出的内容。如果使用 `"\n"`，输出会先累积，然后一次性输出，这样快得多。

## 作业

这些就是竞赛题，但几乎任何题目中都可以使用 STL 来简化生活。

* 在 informatics 的竞赛中尽可能多地解题：https://informatics.msk.ru/mod/statements/view3.php?id=34778&chapterid=756#1
* 在 Codeforces 的竞赛中尽可能多地解题：
http://codeforces.com/group/g92L0id9Yb/contest/229989


### swap

`swap(a, b)` 交换变量 `a` 和 `b` 的值。

``` c++ numberLines
int a = 1, b = 2;
cout << a << ' ' << b << '\n'; // выведет 1 2
swap(a, b);
cout << a << ' ' << b << '\n'; // выведет 2 1
```

### min_element 和 max_element

`min_element(first, last)` 返回半开区间 `[first; last)` 上最小值的迭代器。`max_element(first, last)` 返回半开区间 `[first; last)` 上最大值的迭代器。

如果有多个最小值/最大值，返回第一个出现的位置。

``` C++
vector<int> numbers = {5, 3, 1, 2, 1};
auto it = min_element(numbers.begin(), numbers.end());
cout << *it << " " << (it - numbers.begin()) << "\n"; // выведет 1 2
```

### nth_element

`nth_element(first, need, last)` 把排序半开区间 `[first; last)` 中所有元素后本应位于 `need` 位置的元素放到该位置。`first`、`need` 和 `last` 是迭代器。函数为线性时间。

### sort 与比较器

`sort(first, last)` 对半开区间 `[first; last)` 排序。

``` C++
vector<int> a = {5, 2, 10, 11, 2, 3};
sort(a.begin(), a.end()); // сортируем весь вектор
for (int x : a) {
    cout << x << " ";
}
cout << "\n";
// будет выведено 2 2 3 5 10 11
```

`sort` 函数可以接受第三个参数——比较器。比较器是一个接受两个对象并返回 `true`（当第一个严格小于第二个时）或 `false` 的函数。

假设我们想按数字的个位数字升序排序，个位相同时再按数值本身排序。那么可以写如下代码：

``` C++
bool cmp(int a, int b) {
    return make_pair(a % 10, a) < make_pair(b % 10, b);
}

// это внутри main
vector<int> a = {30, 32, 12, 7, 15};
sort(a.begin(), a.end(), cmp);
for (int x : a) {
    cout << x << " ";
}
cout << "\n";
// будет выведено 30 12 32 15 7
```

### stable_sort

TODO

### unique

`unique(first, last)` 接受一个半开区间并删除其中所有连续的重复元素。函数返回指向去重后元素对应半开区间末尾的迭代器。该半开区间之后元素的值将变得不确定。因此建议将 `unique` 与 `resize` 等函数搭配使用。

``` C++
vector<int> a = {5, 5, 5, 1, 5, 4, 4, 7, 1};
a.resize(unique(a.begin(), a.end()) - a.begin());
for (int x : a) {
    cout << x << " ";
}
cout << "\n";
// будет выведено 5 1 5 4 7 1
```

如果需要删除所有重复的元素（不只是相邻的），需要先对它们排序，做法如下：

``` C++
sort(a.begin(), a.end());
a.resize(unique(a.begin(), a.end()) - a.begin());
```

### merge

merge(first1, last1, first2, last2, d_first) 将两个已排序的半开区间 `[first1; last1)` 和 `[first2; last2)` 合并成一个，从 `d_first` 开始写入，并返回指向最后一个元素之后位置的迭代器。

### back_inserter

一个典型任务：把已排序的 vector `vec1`、`vec2` 合并到 vector `res` 中。可以这样实现：

``` C++
vector<int> res;
merge(vec1.begin(), vec1.end(), vec2.begin(), vec2.end(), back_inserter(res));
```

这里用到了 `back_inserter`。更多细节可以阅读[这里](http://www.cplusplus.com/reference/iterator/back_insert_iterator/)。
如果不使用 back_inserter，代码会是这样：

``` C++
vector<int> res(vec1.size() + vec2.size());
merge(vec1.begin(), vec1.end(), vec2.begin(), vec2.end(), res.begin());
```

第一种写法代码更漂亮，但运行更慢，因为 `res` 会多次扩容。请根据题目限制决定使用哪种方法。

### reverse

`reverse(first, last)` 翻转半开区间 `[first; last)`（元素变为逆序）。

``` C++
vector<int> a = {5, 2, 3, 10, 17};
reverse(a.begin(), a.begin() + 3);
for (int x : a) {
    cout << x << " ";
}
cout << "\n";
// будет выведено 3 2 5 10 17
```

### rotate

`rotate(first, n_first, last)` 重排半开区间 `[first; last)` 中的元素，使 `n_first` 成为第一个元素，`n_first - 1` 成为最后一个。例如，把 vector `v` 循环左移一位可以这样实现：

``` C++
rotate(v.begin(), v.begin() + 1, v.end());
```

### next_permutation 和 prev_permutation

生成下一个和上一个排列。例如，要枚举 vector `a` 的所有不同排列，可以这样写：

``` C++
sort(a.begin(), a.end());
do {
  ... // тело цикла
} while (next_permutation(a.begin(), a.end()));
```

### lower_bound、upper_bound、binary_search

这些函数都接受半开区间 `[first; last)` 和一个值 `value`。半开区间必须按 `element < value` 关系排序（满足该关系的元素在前，其余在后）。

`lower_bound` 返回指向第一个大于或等于 `value` 的元素的指针。`upper_bound` 返回指向第一个严格大于 `value` 的元素的指针。`binary_search` 返回 `value` 是否存在于该半开区间中。

``` C++
vector<int> a = {1, 5, 5, 6, 7, 10};

auto it1 = lower_bound(a.begin(), a.end(), 5);
cout << (it1 - a.begin()) << "\n"; // выведет 1

auto it2 = upper_bound(a.begin(), a.end(), 5);
cout << *it2 << "\n"; // выведет 6

if (binary_search(a.begin(), a.end(), 7)) {
    cout << "There is an element = 7\n"; // это будет выведено
}
```

<b>注意！</b>

不要在 `set`/`map` 上使用 `lower_bound`、`upper_bound`、`binary_search`！它们会退化为线性时间。请使用它们自己的成员函数：`set::lower_bound`（调用方式为 `s.lower_bound(elem)`）等等。

### fill

`fill(first, last, value)` 把值 `value` 赋给半开区间 `[first; last)` 中的所有元素。

### copy

`copy(first, last, d_first)` 把半开区间 `[first; last)` 中的元素复制到从 `d_first` 开始的范围。

标准的 `cin` 和 `cout` 工作得非常慢。要把它们加速好几倍（并可能借此战胜 TLE），请在 `main` 开头写以下代码（交互题中<b>不要</b>这样做）：

``` C++
ios::sync_with_stdio(0);
cin.tie(0);
cout.tie(0);
```

另外强烈不建议使用 `endl`（交互题除外）。请使用 `"\n"`。它们的区别在于 `endl` 会刷新（flush）输出缓冲区，也就是立即输出你想输出的内容。如果使用 `"\n"`，输出会先累积，然后一次性输出，这样快得多。