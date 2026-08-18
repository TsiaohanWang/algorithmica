---
title: 搜索树
weight: 3
---

在[上一篇文章](../s-tree)中，我们设计并实现了*静态* B 树，以加速有序数组中的二分查找。在它的[最后一节](../s-tree/#as-a-dynamic-tree)中，我们简要讨论了如何再次让它们变得*动态*，同时保留从 [SIMD](/hpc/simd) 获得的性能收益，并通过在 S+ 树的内部节点中添加和跟随显式指针来验证我们的预测。

在本文中，我们延续这一方案，为整数键设计一棵功能最小化的搜索树，[实现](#evaluation)了相对于 `std::set` 高达 18 倍/8 倍、相对于 [`absl::btree`](https://abseil.io/blog/20190812-btree) 高达 7 倍/2 倍的 `lower_bound` 与 `insert` 查询加速——而且仍有充足的改进空间。

该结构对 32 位整数的内存开销约为 30%，最终实现[不到 150 行 C++](https://github.com/sslotin/amh-code/blob/main/b-tree/btree-final.cc)。它可以轻松推广到其他算术类型，以及哈希值、国家代码、股票代码等小型/定长字符串。

<!--

对 `std::set` 有 7–18 倍/3–8 倍、对 `absl::btree` 有 3–7 倍/1.5–2 倍的加速

我们称之为 *B− 树*

-->

## B− 树

与其他案例研究中我们通常所做的一点一点的小改进不同，本文中我们将只实现一种数据结构，我们称之为 *B− 树*，它基于 [B+ 树](../s-tree/#b-tree-layout-1)，只有几个小的不同：

- B− 树的节点不存储指针，除指向内部节点子节点的指针外也不存储任何元数据（而 B+ 树的叶节点存储指向下一个叶节点的指针）。这使我们能够把叶节点中的键完美地放置到缓存行上。
- 我们把键 $i$ 定义为子节点 $i$ 子树中的*最大*键，而不是子节点 $(i + 1)$ 子树中的*最小*键。这使我们到达叶节点后不必再取回其他任何节点（在 B+ 树中，叶节点中的所有键都可能小于搜索键，所以我们需要去下一个叶节点取它的第一个元素）。

我们还使用了 $B=32$ 的节点大小，这比典型值要小。之所以不是 $16$——那个对 [S+ 树最优](../s-tree/#modifications-and-further-optimizations)的值——是因为我们还有与取回指针相关的额外开销，而把树高降低约 20% 的收益超过了每节点处理两倍元素的代价；同时它还能改善 `insert` 查询的运行时间，该查询平均每 $\frac{B}{2}$ 次插入就要执行一次代价高昂的节点分裂。

<!--

我们稍后会讨论其他节点大小。

为了让 SIMD 高效运行，这是必要的（我们稍后会讨论其他节点大小）。

这里有一些开销，所以使用超过一条缓存行是有意义的。

与 B+ 树类似，

-->

### 内存布局

虽然从软件工程的角度来看这也许不是最佳做法，但我们干脆把整棵树存储在一个预先分配的大数组中，不区分叶节点和内部节点：

```c++
const int R = 1e8;
alignas(64) int tree[R];
```

我们还用无穷大预填充这个数组以简化实现：

```c++
for (int i = 0; i < R; i++)
    tree[i] = INT_MAX;
```

（总的来说，与 `std::set` 或其他内部使用 `new` 的结构作比较在技术上有作弊之嫌，但内存分配和初始化在这里并不是瓶颈，所以这不大会显著影响评估结果。）

两种节点类型都把键按排序顺序顺序存储，并通过其第一个键在数组中的下标来标识：

- 一个叶节点最多有 $(B - 1)$ 个键，但会用无穷大填充到 $B$ 个元素。
- 一个内部节点最多有 $(B - 2)$ 个键并填充到 $B$ 个元素，以及最多 $(B - 1)$ 个子节点下标，同样填充到 $B$ 个元素。

这些设计决策并非随意为之：

- 填充确保叶节点恰好占据 2 条缓存行，内部节点恰好占据 4 条缓存行。
- 我们特意使用[下标而不是指针](/hpc/cpu-cache/pointers/)来节省缓存空间，并使它们更便于用 SIMD 移动。  
  （从现在起，我们将交替使用"指针"和"下标"这两个词。）
- 我们紧随键之后存储下标，尽管它们存储在不同的缓存行中，因为[我们有理由这么做](/hpc/cpu-cache/aos-soa/)。
- 我们故意在叶节点中"浪费"一个数组单元，在内部节点中浪费 $2+1=3$ 个单元，因为分裂节点时我们需要这些单元来存储临时结果。

最初，我们只有一个空的叶节点作为根：

```c++
const int B = 32;

int root = 0;   // where the keys of the root start
int n_tree = B; // number of allocated array cells
int H = 1;      // current tree height
```

要"分配"一个新节点，我们只需在叶节点时把 `n_tree` 增加 $B$，或在内部节点时增加 $2 B$。

由于新节点只能通过分裂满节点来创建，除根之外的每个节点都至少会半满。这意味着每个整型元素需要 4 到 8 字节（内部节点大约只贡献其中的 $\frac{1}{16}$），前者对应插入为顺序插入的情况，后者对应输入为对抗性（adversarial）输入的情况。当查询均匀分布时，节点平均约 75% 满，折算下来每个元素约 5.2 字节。

与基于指针的二叉树相比，B 树非常节省内存。例如，`std::set` 至少需要三个指针（左孩子、右孩子和父节点），仅此一项就要花掉 $3 \times 8 = 24$ 字节，再加上由于[结构体对齐](/hpc/cpu-cache/alignment/)而至少还需要 $8$ 字节来存储键和元信息。

### 搜索

超过 90% 的操作是查找（lookup）是非常常见的场景，即便不是如此，其他每一种树操作通常也以定位一个键开始，所以我们就从实现和优化搜索入手。

当我们实现 [S 树](../s-tree/#optimization)时，由于 blending/packs 指令的种种微妙之处，我们最终以置换后的顺序存储键。对于*动态树*问题，以置换顺序存储键会使插入难得多，所以我们将改变方法。

思考如何在有序数组中找出元素 `x` 的应有位置，另一种方式不是"第一个不小于 `x` 的元素的下标"，而是"小于 `x` 的元素个数"。这一观察引出了如下想法：把键与 `x` 比较，把向量掩码聚合成一个 32 位掩码（其中每一位可以对应任意元素，只要映射是双射的），然后对它调用 `popcnt`，返回小于 `x` 的元素个数。

这个技巧让我们无需任何重排就能高效地完成局部搜索：

```c++
typedef __m256i reg;

reg cmp(reg x, int *node) {
    reg y = _mm256_load_si256((reg*) node);
    return _mm256_cmpgt_epi32(x, y);
}

// returns how many keys are less than x
unsigned rank32(reg x, int *node) {
    reg m1 = cmp(x, node);
    reg m2 = cmp(x, node + 8);
    reg m3 = cmp(x, node + 16);
    reg m4 = cmp(x, node + 24);

    // take lower 16 bits from m1/m3 and higher 16 bits from m2/m4
    m1 = _mm256_blend_epi16(m1, m2, 0b01010101);
    m3 = _mm256_blend_epi16(m3, m4, 0b01010101);
    m1 = _mm256_packs_epi16(m1, m3); // can also use blendv here, but packs is simpler

    unsigned mask = _mm256_movemask_epi8(m1);
    return __builtin_popcount(mask);    
}
```

注意，由于这个过程，我们必须用无穷大填充"键区域"，这使我们无法在空出的单元中存储元数据（除非我们愿意在加载 SIMD 通道时花几个周期把它掩蔽掉）。

现在，要实现 `lower_bound`，我们可以像在 S+ 树中那样沿树下降，但在算出子节点编号之后再取指针：

```c++
int lower_bound(int _x) {
    unsigned k = root;
    reg x = _mm256_set1_epi32(_x);
    
    for (int h = 0; h < H - 1; h++) {
        unsigned i = rank32(x, &tree[k]);
        k = tree[k + B + i];
    }

    unsigned i = rank32(x, &tree[k]);

    return tree[k + i];
}
```

实现搜索很容易，而且不会引入太多开销。困难的部分是实现插入。

### 插入

一方面，正确实现插入需要大量代码，但另一方面，这些代码中的大部分执行得极为稀少，所以我们不必太在意它的性能。大多数时候，我们需要做的只是到达叶节点（我们已经知道怎么做了），然后把新键插入其中，把键的某个后缀右移一个位置。偶尔，我们还需要分裂节点和/或更新一些祖先，但这种情况相对罕见，所以我们先关注最常见的执行路径。

要把一个键插入一个有 $(B - 1)$ 个有序元素的数组，我们可以把它们加载到向量寄存器中，然后用一个[预计算](/hpc/compilation/precalc/)的掩码[掩蔽存储](/hpc/simd/masking)到右侧一个位置，该掩码告诉我们对于给定的 `i` 哪些元素需要被写入：

```c++
struct Precalc {
    alignas(64) int mask[B][B];

    constexpr Precalc() : mask{} {
        for (int i = 0; i < B; i++)
            for (int j = i; j < B - 1; j++)
                // everything from i to B - 2 inclusive needs to be moved
                mask[i][j] = -1;
    }
};

constexpr Precalc P;

void insert(int *node, int i, int x) {
    // need to iterate right-to-left to not overwrite the first element of the next lane
    for (int j = B - 8; j >= 0; j -= 8) {
        // load the keys
        reg t = _mm256_load_si256((reg*) &node[j]);
        // load the corresponding mask
        reg mask = _mm256_load_si256((reg*) &P.mask[i][j]);
        // mask-write them one position to the right
        _mm256_maskstore_epi32(&node[j + 1], mask, t);
    }
    node[i] = x; // finally, write the element itself
}
```

这个 [constexpr 魔法](/hpc/compilation/precalc/)是我们使用的唯一一个 C++ 特性。

还有其他方法可以做到这一点，有些可能更高效，但我们暂时就此打住。

当我们分裂一个节点时，需要把一半的键移到另一个节点，所以让我们再写一个完成这件事的原语：

```c++
// move the second half of a node and fill it with infinities
void move(int *from, int *to) {
    const reg infs = _mm256_set1_epi32(INT_MAX);
    for (int i = 0; i < B / 2; i += 8) {
        reg t = _mm256_load_si256((reg*) &from[B / 2 + i]);
        _mm256_store_si256((reg*) &to[i], t);
        _mm256_store_si256((reg*) &from[B / 2 + i], infs);
    }
}
```

有了这两个向量函数，我们现在可以非常仔细地实现插入了：

```c++
void insert(int _x) {
    // the beginning of the procedure is the same as in lower_bound,
    // except that we save the path in case we need to update some of our ancestors
    unsigned sk[10], si[10]; // k and i on each iteration
    //           ^------^ We assume that the tree height does not exceed 10
    //                    (which would require at least 16^10 elements)
    
    unsigned k = root;
    reg x = _mm256_set1_epi32(_x);

    for (int h = 0; h < H - 1; h++) {
        unsigned i = rank32(x, &tree[k]);

        // optionally update the key i right away
        tree[k + i] = (_x > tree[k + i] ? _x : tree[k + i]);
        sk[h] = k, si[h] = i; // and save the path
        
        k = tree[k + B + i];
    }

    unsigned i = rank32(x, &tree[k]);

    // we can start computing the is-full check before insertion completes
    bool filled  = (tree[k + B - 2] != INT_MAX);

    insert(tree + k, i, _x);

    if (filled) {
        // the node needs to be split, so we create a new leaf node
        move(tree + k, tree + n_tree);
        
        int v = tree[k + B / 2 - 1]; // new key to be inserted
        int p = n_tree;              // pointer to the newly created node
        
        n_tree += B;

        for (int h = H - 2; h >= 0; h--) {
            // ascend and repeat until we reach the root or find a the node is not split
            k = sk[h], i = si[h];

            filled = (tree[k + B - 3] != INT_MAX);

            // the node already has a correct key (the right one)
            //                  and a correct pointer (the left one)
            insert(tree + k,     i,     v);
            insert(tree + k + B, i + 1, p);
            
            if (!filled)
                return; // we're done

            // create a new internal node
            move(tree + k,     tree + n_tree);     // move keys
            move(tree + k + B, tree + n_tree + B); // move pointers

            v = tree[k + B / 2 - 1];
            tree[k + B / 2 - 1] = INT_MAX;

            p = n_tree;
            n_tree += 2 * B;
        }

        // if reach here, this means we've reached the root,
        // and it was split into two, so we need a new root
        tree[n_tree] = v;

        tree[n_tree + B] = root;
        tree[n_tree + B + 1] = p;

        root = n_tree;
        n_tree += 2 * B;
        H++;
    }
}
```

这里有很多低效之处，但幸运的是，`if (filled)` 的函数体执行得极为稀少——大约每 $\frac{B}{2}$ 次插入一次——而且插入性能并不是我们的首要任务，所以我们就把它放在那里。

## 评估

我们只实现了 `insert` 和 `lower_bound`，所以这就是我们要测量的。

我们希望评估在一个合理的时间内完成，所以我们的基准测试是一个在两个步骤之间交替的循环：

- 用逐个 `insert` 把结构规模从 $1.17^k$ 增加到 $1.17^{k+1}$，并测量所花的时间。
- 执行 $10^6$ 次随机 `lower_bound` 查询并测量所花的时间。

我们从规模 $10^4$ 开始，到 $10^7$ 结束，总共约 $50$ 个数据点。我们为两种查询类型在 $[0, 2^{30})$ 范围内均匀生成数据，且各阶段之间相互独立。由于数据生成过程允许重复键，我们与 `std::multiset` 和 `absl::btree_multiset`[^absl] 进行比较，尽管为了方便我们仍然称它们为 `std::set` 和 `absl::btree`。我们还为三轮运行在系统层面启用了[大页（hugepages）](/hpc/cpu-cache/paging)。

[^absl]: 如果你也认为只和 Abseil 的 B 树比较不够有说服力，[欢迎](https://github.com/sslotin/amh-code/tree/main/b-tree)把任何你喜欢的搜索树加入基准测试。

<!--

键是均匀分布的，但我们不应依赖这一事实（例如使用插值搜索）。

超过 90% 的操作是查找是很常见的。优化搜索很重要，因为其他每个操作都以定位一个键开始。

我向其他所有人道歉，但没使用公开的基准测试多少是你们的错。

-->

B− 树的性能与我们最初预测的一致——至少在查找方面是这样：

![](../img/btree-absolute.svg)

相对加速比随结构规模变化——对 STL 为 7–18 倍/3–8 倍，对 Abseil 为 3–7 倍/1.5–2 倍：

![](../img/btree-relative.svg)

插入只比 `absl::btree` 快 1.5–2 倍，后者用标量代码完成所有工作。我对插入为什么*那么*慢的最佳猜测是数据依赖：由于树节点可能会变化，CPU 在前一个查询完成之前无法开始处理下一个查询（两种查询的[真实延迟](../s-tree/#comparison-with-stdlower_bound)大致相等，约为 `lower_bound` 倒数吞吐量的 3 倍）。

![](../img/btree-absl.svg)

当结构规模较小时，`lower_bound` 的[倒数吞吐量](../s-tree/#comparison-with-stdlower_bound)呈阶梯状增长：当只有根需要访问时从 3.5 纳秒开始，然后增长到 6.5 纳秒（两个节点），再到 12 纳秒（三个节点），之后触及 L2 缓存（图上未显示）并开始更平滑地增长，但当树高增加时仍会出现明显的尖峰。

有趣的是，即使只存储一个键，B− 树也胜过 `absl::btree`：它需要约 5 纳秒在[分支预测失误](/hpc/pipelining/branching/)上停滞，而 B− 树（的搜索）完全无分支。

### 可能的优化

在我们之前的数据结构优化工作中，尽可能多地把变量变成编译期常量帮助很大：编译器可以把这些常量硬编码进机器码、简化算术、展开所有循环，并为我们做许多其他好事。

如果我们的树高度恒定，这根本不是问题，但它不是。不过它在*很大程度上*是恒定的：高度很少变化，事实上，在基准测试的约束下，最大高度只有 6。

我们能做的是为几个不同的编译期常量高度预编译 `insert` 和 `lower_bound` 函数，并在树增长时在它们之间切换。惯用的 C++ 做法是使用虚函数，但我更愿意显式地使用原始函数指针，像这样：

```c++
void (*insert_ptr)(int);
int (*lower_bound_ptr)(int);

void insert(int x) {
    insert_ptr(x);
}

int lower_bound(int x) {
    return lower_bound_ptr(x);
}
```

我们现在定义以树高为参数的模板函数，并在 `insert` 函数内树增长的代码块中，随着树的增长更换指针：

```c++
template <int H>
void insert_impl(int _x) {
    // ...
}

template <int H>
void insert_impl(int _x) {
    // ...
    if (/* tree grows */) {
        // ...
        insert_ptr = &insert_impl<H + 1>;
        lower_bound_ptr = &lower_bound_impl<H + 1>;
    }
}

template <>
void insert_impl<10>(int x) {
    std::cerr << "This depth was not supposed to be reached" << std::endl;
    exit(1);
}
```

<!--
insert_ptr = &insert_impl<1>;
lower_bound_ptr = &lower_bound_impl<1>;
-->

我尝试过，但没能从中获得任何性能提升，不过我仍然对这个方法抱有很高的期望，因为编译器（理论上）可以移除 `sk` 和 `si`，完全消除任何临时存储，只读取和计算一次所有内容，从而大幅优化 `insert` 过程。

插入也可能通过使用更大的块大小来优化，因为节点分裂会变得罕见，但这以更慢的查找为代价。我们还可以为不同的层尝试不同的节点大小：叶节点可能应该比内部节点更大。

**另一个想法**是在插入时把多余的键移到兄弟节点，尽可能推迟节点分裂。

其中一个特定的修改被称为 B* 树。当当前节点已满时，它把最后一个键移到下一个节点；当两个节点都满时，它联合分裂这两个节点，产生三个 ⅔ 满的节点。这降低了内存开销（节点平均将达到 ⅚ 满）并提高了扇出系数，从而降低了树高，这对所有操作都有帮助。

这种技术甚至可以扩展到比如三到四的分裂，尽管进一步推广会以更慢的 `insert` 为代价。

**还有一个想法**是去掉（部分）指针。例如，对于大规模树，我们大概可以负担得起一个约 $16 \cdot 17$ 个元素的小型 [S+ 树](../s-tree) 作为根，在它发生变化的罕见时刻从头重建。遗憾的是，你不能把它扩展到整棵树：我确信某篇论文说过，不付出每次查询 $\Omega(\sqrt n)$ 次操作的代价，就无法让一个动态结构完全隐式化。

我们还可以尝试一些非树数据结构，比如[跳表（skip list）](https://en.wikipedia.org/wiki/Skip_list)。甚至已经有人[成功尝试过将其向量化](https://doublequan.github.io/)——虽然加速并不那么惊人。我尤其对跳表能被改进不抱太大希望，尽管在并发环境下它可能达到更高的总吞吐量。

### 其他操作

要*删除*一个键，我们可以用同样的掩蔽存储技巧定位并从节点中移除它。之后，如果节点至少半满，我们就完成了。否则，我们尝试从下一个兄弟节点借一个键。如果兄弟节点有多于 $\frac{B}{2}$ 个键，我们就追加它的第一个键，并把它的其余键左移一位。否则，当前节点和下一个节点的键都少于 $\frac{B}{2}$ 个，所以我们可以合并它们，然后前往父节点并迭代地在其中删除一个键。

我们可能还想实现的另一件事是*迭代*。批量加载从 `l` 到 `r` 的每个键是一种非常常见的模式——例如数据库中的 `SELECT abc ORDER BY xyz` 类型查询——而 B+ 树通常在数据层存储指向下一个节点的指针以支持这种快速迭代。在 B− 树中，由于我们使用的节点大小小得多，如果这样做我们可能会遇到[指针追逐](/hpc/cpu-cache/latency/)问题。前往父节点并读取它的全部 $B$ 个指针可能更快，因为它抵消了这个问题。因此，一个祖先栈（我们在 `insert` 中使用的 `sk` 和 `si` 数组）可以作为迭代器，甚至可能比在节点中单独存储指针更好。

我们可以轻松实现 `std::set` 几乎所有的功能，但 B− 树和其他任何 B 树一样，由于指针稳定性的要求，极不可能成为 `std::set` 的直接替代品：指向元素的指针在元素被删除之前应保持有效，而当我们不断分裂和合并节点时这很难做到。这不仅对搜索树，对大多数数据结构而言都是一个主要问题：同时拥有指针稳定性和高性能几乎是不可能的。

<!--
也许 C++ 标准会加入类似 `std::set_with_unstable_pointers` 的东西

我们不能在键中存储垃圾数据。
-->

## 致谢

感谢 Google 的 [Danila Kutenin](https://danlark.org/) 就 B 树在 Abseil 中的适用性和使用进行了有意义的讨论。

<!-- 一个有趣的用例是 *rope*，也叫 *cord*（绳），它用于把字符串包裹在一棵树中以支持批量操作。例如，编辑一个非常大的文本文件。这正是本文的主题。 -->