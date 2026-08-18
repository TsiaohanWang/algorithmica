---
title: 二分查找
weight: 1
published: true
---

<!-- 提一下插值搜索和基数树？ -->

虽然提升面向用户的应用的速度是性能工程的最终目标，但人们对某些数据库中 5–10% 的改进并不那么兴奋。是的，这正是软件工程师该拿薪水去做的事，但这类优化往往过于精巧、过于依赖具体系统，难以轻易推广到其他软件。

相反，性能工程最引人入胜的展示是对教科书算法的多倍优化：那种人人皆知、被认为简单到根本不会想到去优化的算法。这些优化简单且有教育意义，完全可以移植到别处。而令人惊讶的是，它们并不像你想的那样罕见。

<!-- 然而，以惊人的周期性，这些算法可以被优化到荒谬的性能水平。 -->

在本节中，我们专注于这样一个基础算法——*二分查找*——并实现它的两个变体，根据问题规模的不同，它们比 `std::lower_bound` 快最多 4 倍，而代码不到 15 行。

第一个算法通过去除[分支](/hpc/pipelining/branching)实现这一点，第二个算法还优化了内存布局，以获得更好的[缓存系统](/hpc/cpu-cache)性能。这严格来说使它不能成为 `std::lower_bound` 的直接替代品，因为它需要在开始回答查询之前置换数组的元素——但我想不出多少场景是你拿到一个有序数组，却负担不起线性时间的预处理。

<!--

- *无分支二分查找*：在小数组上最多快 3 倍，可以充当 `std::lower_bound` 的直接替代品。
- *Eytzinger 二分查找*：以缓存友好的方式重排有序数组的元素，在小数组上也快 3 倍，在大数组上快 2 倍。

-->

惯常的免责声明：CPU 是 [Zen 2](https://www.7-cpu.com/cpu/Zen2.html)，内存是 [DDR4-2666](/hpc/cpu-cache/)，我们默认使用的编译器是 Clang 10。你机器上的性能可能不同，所以我强烈鼓励你[亲自去测试一下](https://godbolt.org/z/14rd5Pnve)。

<!--

它在能装进缓存较低层的数组规模上表现稍差，但在低带宽环境下它可以快最多 3 倍（或比 `std::lower_bound` 快 7 倍）。GCC 在所有基准测试上都很糟糕，所以我们主要使用 Clang（10.0）。CPU 是 Zen 2，不过结果应该可以移植到其他平台，包括大多数基于 Arm 的芯片。

CPU 是 Zen 2，和往常一样，结果有点依赖架构，不过结果应该可以移植到其他平台，包括大多数基于 Arm 的芯片。

这是一篇长文章，会变成几个小时的阅读。如果你觉得在没有任何上下文的情况下阅读大量 [intrinsic](/hpc/simd/intrinsics) 代码毫无压力，可以略读前四个实现，直接跳到最后一节。

循序渐进地建立理解，但你可以跳过它们。

-->

## 二分查找

<!--

对于我们的基准测试，我们创建一个大小为 `n` 的随机整数数组并排序。然后，每种实现都可以做一些预处理：

```c++
void prepare(int *a, int n);
int lower_bound(int x);
```

已经排序好的数组 `t`，大小为 `n`。

我们将创建一个名为 `a` 的数组，进入名为 `t` 的数组。

-->

这是在大小为 `n` 的有序整数数组 `t` 中搜索第一个不小于 `x` 的元素的标准方法，你可以在任何计算机科学入门教材中找到：

```c++
int lower_bound(int x) {
    int l = 0, r = n - 1;
    while (l < r) {
        int m = (l + r) / 2;
        if (t[m] >= x)
            r = m;
        else
            l = m + 1;
    }
    return t[l];
}
```

<!-- 我们维护可能是答案的第一个和最后一个元素的下标，把中间的元素与键 `x` 比较，然后根据比较结果把搜索区间缩小一半。简单之美。 -->

找到搜索范围的中点元素，与 `x` 比较，把范围缩小一半。简单之美。

`std::lower_bound` 采用了类似的方法，只是它需要更通用，以支持具有非随机访问迭代器的容器，因此使用搜索区间的第一个元素和大小，而不是它的两个端点。为此，[Clang](https://github.com/llvm-mirror/libcxx/blob/78d6a7767ed57b50122a161b91f59f19c9bd0d19/include/algorithm#L4169) 和 [GCC](https://github.com/gcc-mirror/gcc/blob/d9375e490072d1aae73a93949aa158fcd2a27018/libstdc%2B%2B-v3/include/bits/stl_algobase.h#L1023) 的实现都使用了这个元编程怪物：

```c++
template <class _Compare, class _ForwardIterator, class _Tp>
_LIBCPP_CONSTEXPR_AFTER_CXX17 _ForwardIterator
__lower_bound(_ForwardIterator __first, _ForwardIterator __last, const _Tp& __value_, _Compare __comp)
{
    typedef typename iterator_traits<_ForwardIterator>::difference_type difference_type;
    difference_type __len = _VSTD::distance(__first, __last);
    while (__len != 0)
    {
        difference_type __l2 = _VSTD::__half_positive(__len);
        _ForwardIterator __m = __first;
        _VSTD::advance(__m, __l2);
        if (__comp(*__m, __value_))
        {
            __first = ++__m;
            __len -= __l2 + 1;
        }
        else
            __len = __l2;
    }
    return __first;
}
```

如果编译器成功去除了抽象，它会编译成大致相同的机器码，产生大致相同的平均延迟，后者[如预期那样](/hpc/cpu-cache/latency)随数组大小增长：

![](../img/search-std.svg)

由于大多数人不会手写二分查找，我们将使用 Clang 的 `std::lower_bound` 作为基线。

### 瓶颈

在跳到优化实现之前，让我们简要讨论一下二分查找一开始为什么慢。

如果你用 [perf](/hpc/profiling/events) 运行 `std::lower_bound`，你会看到它把大部分时间花在一条[条件跳转](/hpc/architecture/loops)指令上：

```nasm
       │35:   mov    %rax,%rdx
  0.52 │      sar    %rdx
  0.33 │      lea    (%rsi,%rdx,4),%rcx
  4.30 │      cmp    (%rcx),%edi
 65.39 │    ↓ jle    b0
  0.07 │      sub    %rdx,%rax
  9.32 │      lea    0x4(%rcx),%rsi
  0.06 │      dec    %rax
  1.37 │      test   %rax,%rax
  1.11 │    ↑ jg     35
```

这个[流水线停顿](/hpc/)阻止了搜索的推进，它主要由两个[因素](/hpc/pipelining/hazards)造成：

- 我们遭受*控制冒险*（control hazard），因为我们的[分支](/hpc/pipelining/branching)无法预测（查询和键是独立随机抽取的），处理器每次分支预测失误都要停顿 10–15 个周期来清空流水线并重新填满。
- 我们遭受*数据冒险*（data hazard），因为我们必须等待前一次比较完成，而这次比较又要等待它的一个操作数从内存中取回——根据它所在的位置，这[可能需要](/hpc/cpu-cache/latency) 0 到 300 个周期不等。

现在，让我们尝试逐一消除这些障碍。

## 去除分支

我们可以用[谓词化（predication）](/hpc/pipelining/branchless)取代分支。为了让任务更简单，我们可以采用 STL 的方法，用搜索区间的第一个元素和大小（而不是它的首尾元素）重写循环：

```c++
int lower_bound(int x) {
    int *base = t, len = n;
    while (len > 1) {
        int half = len / 2;
        if (base[half - 1] < x) {
            base += half;
            len = len - half;
        } else {
            len = half;
        }
    }
    return *base;
}
```

注意，在每次迭代中，`len` 基本上只是减半，然后根据比较结果向下或向上取整。这个条件更新看起来没必要；为了避免它，我们可以简单地说它总是向上取整：

```c++
int lower_bound(int x) {
    int *base = t, len = n;
    while (len > 1) {
        int half = len / 2;
        if (base[half - 1] < x)
            base += half;
        len -= half; // = ceil(len / 2)
    }
    return *base;
}
```

这样，我们每次迭代只需要用[条件移动（cmov）](/hpc/pipelining/branchless/)更新搜索区间的第一个元素，并把它的长度减半：

```c++
int lower_bound(int x) {
    int *base = t, len = n;
    while (len > 1) {
        int half = len / 2;
        base += (base[half - 1] < x) * half; // will be replaced with a "cmov"
        len -= half;
    }
    return *base;
}
```

<!-- 为下一次迭代预计算 base 指针？ -->

注意，这个循环并不总是等价于标准的二分查找。由于它总是对搜索区间的长度向*上*取整，它会访问略有不同的元素，可能比需要的多执行一次比较。除了简化每次迭代的计算外，如果数组长度恒定，它还使迭代次数恒定，从而完全消除分支预测失误。

作为谓词化的典型特征，这个技巧对编译器优化非常敏感——取决于编译器和函数的调用方式，它可能仍然留下分支或生成次优代码。它在 Clang 10 上运行良好，在小数组上带来 2.5–3 倍的提升：

<!-- todo: 更新数据 -->

![](../img/search-branchless.svg)

一个有趣的细节是，它在大型数组上表现更差。这看起来很奇怪：总延迟由内存延迟主导，而且它执行的内存访问与标准二分查找大致相同，所以应该大致相同，甚至稍微好一点。

你真正需要问的问题不是为什么无分支实现更差，而是为什么有分支的版本更好。这是因为当你有分支时，CPU 可以[推测执行](/hpc/pipelining/branching/)其中一个分支，在确认哪一边是正确的之前就开始取左键或右键——这实际上起到了隐式[预取](/hpc/cpu-cache/prefetching)的作用。

对于无分支实现，这不会发生，因为 `cmov` 与其他任何指令一样被对待，分支预测器不会试图窥探它的操作数来预测未来。为了弥补这一点，我们可以显式地请求左、右子键，在软件层面预取数据：

```c++
int lower_bound(int x) {
    int *base = t, len = n;
    while (len > 1) {
        int half = len / 2;
        len -= half;
        __builtin_prefetch(&base[len / 2 - 1]);
        __builtin_prefetch(&base[half + len / 2 - 1]);
        base += (base[half - 1] < x) * half;
    }
    return *base;
}
```

<!-- todo: 这个也重跑一遍 -->

有了预取，大型数组上的性能变得大致相同：

![](../img/search-branchless-prefetch.svg)

这张图仍然增长得更快，因为有分支的版本还预取了"孙子辈"、"曾孙辈"等节点——尽管每次新的推测性读取的用处会指数级衰减，因为预测正确的可能性越来越低。

在无分支版本中，我们也可以提前预取超过一层，但我们需要发出的取数次数也会指数增长。相反，我们将尝试另一种方法来优化内存操作。

## 优化内存布局

我们在二分查找期间执行的内存请求形成了一个非常特殊的访问模式：

![](../img/binary-search.png)

每次请求的元素被缓存的可能性有多大？它们的[数据局部性](/hpc/external-memory/locality/)有多好？

- *空间局部性*对最后 3 到 4 次请求来说看起来还不错，它们很可能在同一条[缓存行](/hpc/cpu-cache/cache-lines)上——但所有之前的请求都需要巨大的内存跳跃。
- *时间局部性*对前十几个左右的请求来说看起来不错——这个长度的不同比较序列并没有那么多，所以我们会一遍又一遍地与相同的中位元素比较，它们很可能被缓存。

为了说明第二种缓存共享有多重要，让我们尝试在每次迭代时从搜索区间的元素中随机挑选一个元素来比较，而不是中间那个：

```c++
int lower_bound(int x) {
    int l = 0, r = n - 1;
    while (l < r) {
        int m = l + rand() % (r - l);
        if (t[m] >= x)
            r = m;
        else
            l = m + 1;
    }
    return t[l];
}
```

[理论上](#appendix-random-binary-search)，这种随机二分查找预计要比普通的多做 30–40% 的比较，但在真实计算机上，大型数组上的运行时间增加了约 6 倍：

![](../img/search-random.svg)

这不仅仅是 `rand()` 调用慢造成的。你可以清楚地看到 L2–L3 边界上的转折点，在那里内存延迟超过了随机数生成和[取模](/hpc/arithmetic/division)的开销。性能下降是因为所有被取回的元素都不太可能被缓存，而不仅仅是其中一小部分后缀。

另一个潜在的负面影响是[缓存组相联性](/hpc/cpu-cache/associativity)。如果数组大小是某个较大的 2 的幂的倍数，那么这些"热点"元素的下标也会被一些较大的 2 的幂整除，映射到同一条缓存行，互相把对方踢出去。例如，对大小为 $2^{20}$ 的数组做二分查找，每次查询约需 ~360 纳秒，而对大小为 $(2^{20} + 123)$ 的数组只需 ~300 纳秒——20% 的差异。有一些[方法](https://en.wikipedia.org/wiki/Fibonacci_search_technique)可以修复这个问题，但为了不被更紧迫的事情分心，我们干脆忽略它：我们使用的所有数组大小都形如 $\lfloor 1.17^k \rfloor$（$k$ 为整数），这样任何缓存副作用都不太可能发生。

我们内存布局的真正问题在于，它没有最有效地利用时间局部性，因为它把热点元素和冷点元素混在一起。例如，我们很可能把 $\lfloor n/2 \rfloor$——每次查询最先请求的元素——与几乎从不请求的 $\lfloor n/2 \rfloor + 1$ 存在同一条缓存行里。

<!--  （有时字面意义上从不——如果它是三个元素搜索区间的第一个元素，而且它确实是下界，我们只需与中间元素比较，就能推断出它必须是第一个元素，甚至根本不需要取它）——这不是真的 -->

这是一张热力图，展示了 31 元素数组的预期比较频率：

![](../img/binary-heat.png)

所以，理想情况下，我们希望一种内存布局，其中热点元素与热点元素分在一组，冷点元素与冷点元素分在一组。如果我们通过重新编号的方式以更缓存友好的方式置换数组，就能做到这一点。我们将使用的编号方式其实已有半千年历史，而且你很可能已经知道它。

### Eytzinger 布局

**Michaël Eytzinger** 是 16 世纪的奥地利贵族，以谱系学工作著称，特别是名为 *ahnentafel*（德语"祖先表"）的祖先编号系统。

在那个年代血统非常重要，但把这些数据写下来很昂贵。*Ahnentafel* 允许紧凑地展示一个人的家谱，而不用浪费额外空间画图。

它按固定的升序序列列出一个人的直系祖先。首先，本人编号为 1，然后递归地，对于每个编号为 $k$ 的人，其父亲编号为 $2k$，母亲编号为 $(2k+1)$。

下面以[保罗一世](https://en.wikipedia.org/wiki/Paul_I_of_Russia)为例，他是[彼得大帝](https://en.wikipedia.org/wiki/Peter_the_Great)的曾孙：

1. 保罗一世
2. 彼得三世（保罗的父亲）
3. [叶卡捷琳娜二世](https://en.wikipedia.org/wiki/Catherine_the_Great)（保罗的母亲）
4. 卡尔·弗里德里希（彼得的父亲、保罗的祖父）
5. 安娜·彼得罗芙娜（彼得的母亲、保罗的祖母）
6. 克里斯蒂安·奥古斯特（叶卡捷琳娜的父亲、保罗的外祖父）
7. 约翰娜·伊丽莎白（叶卡捷琳娜的母亲、保罗的外祖母）

除了紧凑之外，它还有一些不错的性质，比如所有偶数编号的人都是男性，所有奇数编号的人（可能除 1 外）都是女性。人们还可以仅凭后代性别的知识找到某个特定祖先的编号。例如，彼得大帝的血统是保罗一世 → 彼得三世 → 安娜·彼得罗芙娜 → 彼得大帝，所以他的编号应该是 $((1 \times 2) \times 2 + 1) \times 2 = 10$。

**在计算机科学中**，这种编号已被广泛用于堆、线段树和其他二叉树结构的隐式（无指针）实现——它存储的是底层数组项，而不是名字。

下面是这种布局应用于二分查找时的样子：

![注意树稍微不平衡（因为最后一层是连续的）](../img/eytzinger.png)

在这种布局中搜索时，我们只需从数组的第一个元素开始，然后每次迭代根据比较结果跳到 $2 k$ 或 $(2k + 1)$：

![](../img/eytzinger-search.png)

你可以立刻看到它的时间局部性更好（而且事实上是理论最优的），因为离根越近的元素离数组开头越近，因此更可能从缓存中取回。

![](../img/eytzinger-heat.png)

另一种看待它的方式是：我们把所有偶数下标的元素写到新数组的末尾，然后把剩余元素中所有偶数下标的元素写在它们前面，依此类推，直到把根放在第一个元素的位置。

### 构造

要构造 Eytzinger 数组，我们可以做这种奇偶[过滤](/hpc/simd/shuffling/#permutations-and-lookup-tables) $O(\log n)$ 次——而且，也许这是最快的方法——但为了简洁，我们将改为遍历原始搜索树来构建它：

```c++
int a[n], t[n + 1]; // the original sorted array and the eytzinger array we build
//              ^ we need one element more because of one-based indexing

void eytzinger(int k = 1) {
    static int i = 0; // <- careful running it on multiple arrays
    if (k <= n) {
        eytzinger(2 * k);
        t[k] = a[i++];
        eytzinger(2 * k + 1);
    }
}
```

这个函数接受当前节点编号 `k`，递归地写出搜索区间中点左侧的所有元素，写出我们接下来要比较的当前元素，然后递归地写出右侧的所有元素。它看起来有点复杂，但要说服自己它是对的，你只需要三个观察：

- 它为从 `1` 到 `n` 的每个 `k` 恰好进入一次 `if` 的函数体，写出恰好 `n` 个元素。
- 它每次递增 `i` 指针，按顺序写出原始数组中的元素。
- 当我们写节点 `k` 的元素时，它左侧的所有元素（恰好 `i` 个）已经被写出。

尽管是递归的，它实际上相当快，因为所有内存读取都是顺序的，而内存写入每次只涉及 $O(\log n)$ 个不同的内存块。不过，维护置换在逻辑上和计算上都更难：向有序数组添加一个元素只需要把其后缀元素右移一位，而 Eytzinger 数组实际上需要从头重建。

注意，这种遍历和由此产生的置换并不完全等同于朴素二分查找的"树"：例如，左子树可能比右子树大——最多大两倍——但这关系不大，因为两种方法都会产生相同的 $\lceil \log_2 n \rceil$ 树深。

还要注意，Eytzinger 数组是从 1 开始的——这对以后的性能很重要。你可以把当 lower bound 不存在时希望返回的值放在第 0 个元素里（类似于 `std::lower_bound` 的 `a.end()`）。

### 搜索实现

我们现在可以只用下标下降这个数组：我们从 $k=1$ 开始，如果需要向左走就执行 $k := 2k$，需要向右走就执行 $k := 2k + 1$。我们甚至不再需要存储和重算搜索边界。这种简洁性也让我们避免了分支：

```c++
int k = 1;
while (k <= n)
    k = 2 * k + (t[k] < x);
```

唯一的问题出现在我们需要恢复结果元素的下标时，因为 $k$ 并不直接指向它。考虑这个例子（其对应的树列在上面）：

<!--
    array:  0 1 2 3 4 5 6 7 8 9                           
eytzinger:  6 3 7 1 5 8 9 0 2 4                           
1st range:  -------------------  k := 1                    
2nd range:  -------------        k := 2*k     = 2   (6 ≥ 3)
3rd range:  -------              k := 2*k     = 4   (3 ≥ 3)
4th range:      ---              k := 2*k + 1 = 9   (1 < 3)
5th range:        -              k := 2*k + 1 = 19  (2 < 3)
-->

<pre class='center-pre'>
    array:  0 1 2 3 4 5 6 7 8 9                            
eytzinger:  <u>6</u> <u>3</u> 7 <u>1</u> 5 8 9 0 <u>2</u> 4                            
1st range:  ------------?------  k := 2*k     = 2   (6 ≥ 3)
2nd range:  ------?------        k := 2*k     = 4   (3 ≥ 3)
3rd range:  --?----              k := 2*k + 1 = 9   (1 < 3)
4th range:      ?--              k := 2*k + 1 = 19  (2 < 3)
5th range:        !                                        
</pre>

<!-- 我们需要最后一次比较吗？ -->

这里我们查询 $[0, …, 9]$ 数组关于 $x=3$ 的 lower bound。我们依次与 $6$、$3$、$1$、$2$ 比较，走左-左-右-右，最终得到 $k = 19$，这甚至不是一个有效的数组下标。

这个技巧在于注意到：除非答案是数组的最后一个元素，否则我们会在某个时刻把 $x$ 与它比较；在得知它不小于 $x$ 之后，我们恰好向左走一次，然后一直向右走到达一个叶节点（因为接下来我们只会把 $x$ 与更小的元素比较）。因此，要恢复答案，我们只需"抵消"一定数量的右转，再多抵消一次。

这可以用一种优雅的方式完成：注意到右转记录在 $k$ 的二进制表示中为 1 位，所以我们只需找到二进制表示中末尾 1 的个数，并把 $k$ 右移这么多位再加一位。为此，我们可以对数字取反（`~k`）并调用"find first set"指令：

```c++
int lower_bound(int x) {
    int k = 1;
    while (k <= n)
        k = 2 * k + (t[k] < x);
    k >>= __builtin_ffs(~k);
    return t[k];
}
```

我们运行它，然后……嗯，它看起来并不*那么*好：

![](../img/search-eytzinger.svg)

较小数组上的延迟与无分支的二分查找实现不相上下——这并不奇怪，因为它只是两行代码——但它的曲线上升得早得多。原因是 Eytzinger 二分查找没有得到空间局部性的好处：我们比较的最后 3–4 个元素不再位于同一条缓存行里，我们必须分别取回它们。

如果你再深入想一想，你可能会反驳说，改善的时间局部性应该能补偿这一点。以前，我们只使用缓存行的约 $\frac{1}{16}$ 来存储一个热点元素，而现在我们使用了整条缓存行，所以有效缓存大小扩大了 16 倍，这让我们能多覆盖 $\log_2 16 = 4$ 次首次请求。

但如果你再往深里想，你会明白这不足以补偿。缓存其他 15 个元素并非完全无用，而且硬件预取器可以预取我们请求的相邻缓存行。如果这是我们最后的请求之一，我们接下来要读的其余内容很可能是已被缓存的元素。所以实际上，最后 6–7 次访问很可能被缓存，而不是 3–4 次。

看起来我们切换到这种布局整体上做了一件蠢事，但有一种方法可以让它变得值得。

### 预取

为了隐藏内存延迟，我们可以使用与无分支二分查找类似的软件预取。但与其为左、右子节点发出两条独立的预取指令，我们可以注意到它们在 Eytzinger 数组中相邻：一个下标是 $2 k$，另一个是 $(2k + 1)$，所以它们很可能在同一条缓存行上，我们可以只用一条指令。

这个观察可以扩展到节点 $k$ 的孙辈——它们也是顺序存储的：

```
2 * 2 * k           = 4 * k
2 * 2 * k + 1       = 4 * k + 1
2 * (2 * k + 1)     = 4 * k + 2
2 * (2 * k + 1) + 1 = 4 * k + 3
```

<!--
\begin{aligned}
   2 \cdot 2 \cdot k       &= 4 \cdot k
\\ 2 \cdot 2 \cdot k + 1   &= 4 \cdot k + 1
\\ 2 \cdot (2 \cdot k) + 1 &= 4 \cdot k + 2
\\ 2 \cdot (2 \cdot k + 1) + 1 &= 4 \cdot k + 3
\end{aligned}
-->

它们的缓存行也可以用一条指令取回。有趣……如果我们继续这样，不取直接的子节点，而是尽可能多地预取能塞进一条缓存行的后代呢？那就是 $\frac{64}{4} = 16$ 个元素，即下标从 $16k$ 到 $(16k + 15)$ 的曾曾孙辈。

现在，如果我们只预取这 16 个元素中的一个，我们可能只会得到其中一部分而不是全部，因为它们可能跨越缓存行边界。我们可以预取第一个*和*最后一个元素，但要只用一次内存请求就搞定，我们需要注意到第一个元素的下标 $16k$ 能被 16 整除，所以它的内存地址是数组基地址加上某个能被 $16 \cdot 4 = 64$（缓存行大小）整除的数。如果数组从一条缓存行开始，那么这 $16$ 个曾曾孙辈元素就保证位于同一条缓存行上，这正是我们需要的。

因此，我们只需要[对齐](/hpc/cpu-cache/alignment)数组：

```c++
t = (int*) std::aligned_alloc(64, 4 * (n + 1));
```

然后在每次迭代中预取下标为 $16 k$ 的元素：

```c++
int lower_bound(int x) {
    int k = 1;
    while (k <= n) {
        __builtin_prefetch(t + k * 16);
        k = 2 * k + (t[k] < x);
    }
    k >>= __builtin_ffs(~k);
    return t[k];
}
```

大型数组上的性能比之前的版本提升 3–4 倍，比 `std::lower_bound` 提升约 2 倍。对仅仅多写两行代码来说还不错：

![](../img/search-eytzinger-prefetch.svg)

本质上，我们在这里做的是通过提前四步预取和重叠内存请求来隐藏延迟。理论上，如果计算无关紧要，我们会期望约 4 倍的加速，但现实中我们得到的加速要温和一些。

我们也可以尝试比提前四步更远的预取，而且我们甚至不必为此使用超过一条预取指令：我们可以只请求第一条缓存行，依靠硬件来预取它的邻居。这个技巧可能提升也可能不提升实际性能——取决于硬件：

```c++
__builtin_prefetch(t + k * 32);
```

另外，请注意最后几次预取请求实际上并不需要，而且事实上它们甚至可能超出为程序分配的内存区域。在大多数现代 CPU 上，无效的预取指令会被转换成空操作，所以这不是问题，但在某些平台上这可能导致变慢，所以也许值得把循环的最后约 4 次迭代拆出去，以尝试移除它们。

这种预取技术让我们最多提前读取四个元素，但它并不是免费的——我们实际上是在用多余的内存[带宽](/hpc/cpu-cache/bandwidth)换取更低的[延迟](/hpc/cpu-cache/latency)。如果你在独立的硬件线程上同时运行不止一个实例，或是在后台运行任何其他内存密集型计算，它会显著[影响](/hpc/cpu-cache/sharing)基准测试的性能。

但我们可以做得更好。与其一次取回四条缓存行，我们可以取回少*四倍*的缓存行。在[下一节](../s-tree)中，我们将探讨这种方法。

<!--

但那只是一个小插曲。让我们回到为*大型*数组优化的话题。

[第 2 部分](https://algorithmica.org/en/b-tree)探讨在带宽受限环境中隐式静态 B 树的高效实现。

-->

### 去除最后一个分支

只差最后一点修饰：你注意到 Eytzinger 搜索的起伏不平了吗？这不是随机噪声——让我们放大看看：

![](../img/search-eytzinger-small.svg)

形如 $1.5 \cdot 2^k$ 的数组大小，延迟要高出约 10 纳秒。这些是循环本身造成的预测失误分支——准确地说，是最后一个分支。当数组大小远离 2 的幂时，很难预测循环会迭代 $\lfloor \log_2 n \rfloor$ 次还是 $\lfloor \log_2 n \rfloor + 1$ 次，所以有 50% 的几率遭受恰好一次分支预测失误。

解决这个问题的一种方法是用无穷大把数组填充到最近的 2 的幂，但这浪费内存。相反，我们通过总是执行一个恒定的最少迭代次数来去除最后一个分支，然后用谓词化有选择地对某个哑元元素做最后一次比较——它保证小于 $x$，因此这次比较会被取消：

```c++
t[0] = -1; // an element that is less than x
iters = std::__lg(n + 1);

int lower_bound(int x) {
    int k = 1;

    for (int i = 0; i < iters; i++)
        k = 2 * k + (t[k] < x);

    int *loc = (k <= n ? t + k : t);
    k = 2 * k + (*loc < x);

    k >>= __builtin_ffs(~k);

    return t[k];
}
```

曲线现在平滑了，在小型数组上只比无分支的二分查找慢几个周期：

![](../img/search-eytzinger-branchless.svg)

有趣的是，现在 GCC 没能把分支替换成 `cmov`，但 Clang 可以。1–1 平局。

### 附录：随机二分查找

顺便说一句，算出随机二分查找的确切期望比较次数本身就是个相当有趣的数学问题。先试着自己解决它吧！

*算法上*计算它的方法是动态规划。如果把 $f_n$ 记为在大小为 $n$ 的搜索区间上找到随机 lower bound 的期望比较次数，它可以由之前的 $f_n$ 通过考虑所有 $(n - 1)$ 种可能的分裂来计算：

$$
f_n = \sum_{l = 1}^{n - 1} \frac{1}{n-1} \cdot \left( f_l \cdot \frac{l}{n} + f_{n - l} \cdot \frac{n - l}{n} \right) + 1
$$

直接应用这个公式给出一个 $O(n^2)$ 算法，但我们可以通过像这样重排求和来优化它：

$$
\begin{aligned}
f_n &= \sum_{i = 1}^{n - 1} \frac{ f_i \cdot i + f_{n - i} \cdot (n - i) }{ n \cdot (n - 1) } + 1
\\  &= \frac{2}{n \cdot (n - 1)} \cdot \sum_{i = 1}^{n - 1} f_i \cdot i + 1
\end{aligned}
$$

要更新 $f_n$，我们只需要计算所有 $i < n$ 的 $f_i \cdot i$ 之和。为此，让我们引入两个新变量：

$$
g_n = f_n \cdot n,
\;\;
s_n = \sum_{i=1}^{n} g_n
$$

现在它们可以这样顺序计算：

$$
\begin{aligned}
g_n &= f_n \cdot n
     = \frac{2}{n-1} \cdot \sum_{i = 1}^{n - 1} g_i + n
     = \frac{2}{n - 1} \cdot s_{n - 1} + n
\\ s_n &= s_{n - 1} + g_n
\end{aligned}
$$

这样我们得到一个 $O(n)$ 算法，但我们还能做得更好。让我们把 $g_n$ 代进 $s_n$ 的更新公式：

$$
\begin{aligned}
s_n &= s_{n - 1} + \frac{2}{n - 1} \cdot s_{n - 1} + n
\\  &= (1 + \frac{2}{n - 1}) \cdot s_{n - 1} + n
\\  &= \frac{n + 1}{n - 1} \cdot s_{n - 1} + n
\end{aligned}
$$

<!-- todo: 我们能不能简化证明并去掉 r？ -->

下一个技巧更复杂。我们这样定义 $r_n$：

$$
\begin{aligned}
r_n &= \frac{s_n}{n}
\\  &= \frac{1}{n} \cdot \left(\frac{n + 1}{n - 1} \cdot s_{n - 1} + n\right)
\\  &= \frac{n + 1}{n} \cdot \frac{s_{n - 1}}{n - 1} + 1
\\  &= \left(1 + \frac{1}{n}\right) \cdot r_{n - 1} + 1
\end{aligned}
$$

我们可以把它代入之前得到的 $g_n$ 公式：

$$
g_n = \frac{2}{n - 1} \cdot s_{n - 1} + n = 2 \cdot r_{n - 1} + n
$$

回忆 $g_n = f_n \cdot n$，我们可以用 $f_n$ 表示 $r_{n - 1}$：

$$
f_n \cdot n = 2 \cdot r_{n - 1} + n
\implies
r_{n - 1} = \frac{(f_n - 1) \cdot n}{2}
$$

最后一步。我们刚刚用 $r_{n - 1}$ 表示了 $r_n$，并用 $f_n$ 表示了 $r_{n - 1}$。这让我们能用 $f_n$ 表示 $f_{n + 1}$：

$$
\begin{aligned}
&&\quad r_n &= \left(1 + \frac{1}{n}\right) \cdot r_{n - 1} + 1
\\ &\Rightarrow & \frac{(f_{n + 1} - 1) \cdot (n + 1)}{2} &= \left(1 + \frac{1}{n}\right) \cdot \frac{(f_n - 1) \cdot n}{2} + 1
\\ &&&= \frac{n + 1}{2} \cdot (f_n - 1) + 1
\\ &\Rightarrow & (f_{n + 1} - 1) &= (f_{n} - 1) + \frac{2}{n + 1}
\\ &\Rightarrow &f_{n + 1} &= f_{n} + \frac{2}{n + 1}
\\ &\Rightarrow &f_{n} &= f_{n - 1} + \frac{2}{n}
\\ &\Rightarrow &f_{n} &= \sum_{k = 2}^{n} \frac{2}{k}
\end{aligned}
$$

最后一个表达式是[调和级数](https://en.wikipedia.org/wiki/Harmonic_series_(mathematics))的两倍，众所周知它在 $n \to \infty$ 时近似 $\ln n$。因此，随机二分查找会比普通的二分查找多做 $\frac{2 \ln n}{\log_2 n} = 2 \ln 2 \approx 1.386$ 次比较。

### 致谢

本文大致基于 Paul-Virak Khuong 和 Pat Morin 的"[Array Layouts for Comparison-Based Searching](https://arxiv.org/pdf/1509.05053.pdf)"。它长达 46 页，更详细地讨论了这些方法和许多其他（不太成功的）方法。我强烈推荐你也看看——这是我最喜欢的性能工程论文之一。

感谢 Marshall Lochbaum [提供了](https://github.com/algorithmica-org/algorithmica/issues/57)随机二分查找的证明。我自己绝对做不到。

我还很久以前从某个博客偷来了这些可爱的布局可视化图，但我不记得博客的名字和它们是什么许可证，反向图片搜索也找不到它们了。如果你不起诉我，谢谢你，无论你是谁！