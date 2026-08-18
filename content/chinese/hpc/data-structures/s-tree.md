---
title: 静态 B 树
weight: 2
---

本节是[上一节](../binary-search)的续篇，在那里我们通过去除分支和改善内存布局优化了二分查找。在这里，我们同样在有序数组中搜索，但这一次我们不再局限于一次只取回和比较一个元素。

在本节中，我们把为二分查找开发的技术推广到*静态 B 树*，并用 [SIMD 指令](/hpc/simd)进一步加速它们。具体来说，我们开发两种新的隐式数据结构：

- [第一种](#b-tree-layout)基于 B 树的内存布局，根据数组大小的不同，它比 `std::lower_bound` 快最多 8 倍，同时使用与数组相同的空间，只需置换其元素。
- [第二种](#b-tree-layout-1)基于 B+ 树的内存布局，它比 `std::lower_bound` 快最多 15 倍，同时只多用 6–7% 的内存——如果我们能保留原始有序数组，则只使用其内存的 6–7%。

为了把它们与 B 树（带指针、每节点成百上千个键、内部有空位的结构）区分开，我们将分别用 *S 树*和 *S+ 树*这两个名字来指代这两种特定的内存布局[^name]。

[^name]: [与 B 树类似](https://en.wikipedia.org/wiki/B-tree#Origin)，"你对 S 树中 S 的含义想得越多，你就越理解 S 树。"

<!--

类似于 B 树中的 B 代表很多东西，我们甚至比 Bayer 对 B 树更有资格这么说：它是 succinct（简洁）、static（静态）、simd（SIMD），是我的名，是我的姓。

- *S 树*：一种基于隐式（无指针）B 布局、用 SIMD 操作加速的方法，以更少的内存带宽高效地执行搜索，在小数组上约快 8 倍，在大数组上约快 5 倍。
- *S+ 树*：一种类似地基于 B+ 布局的方法，在小数组上最多快 15 倍，在大数组上约快 7 倍。只使用数组内存的 6–7%。

计算机视觉中有一个冷门的数据结构。

最后两种方法使用 SIMD，这严格来说使它们不再是二分查找。这严格来说也不是直接替代品，因为它需要一些预处理，但我想不出多少场景是你拿到有序数组却负担不起线性时间预处理。

-->

据我所知，这是对现有[方法](http://kaldewey.com/pubs/FAST__SIGMOD10.pdf)的重大改进。和以前一样，我们使用面向 Zen 2 CPU 的 Clang 10，但性能提升大致可以移植到大多数其他平台，包括基于 Arm 的芯片。如果你想在自己机器上测试，请使用最终实现的[这个单文件基准测试](https://github.com/sslotin/amh-code/blob/main/binsearch/standalone.cc)。

这是一篇长文章，由于它也充当[教科书](/hpc/)案例研究，为教学目的我们将逐步改进算法。如果你已经是专家，觉得在几乎没有上下文的情况下阅读大量 [intrinsic](/hpc/simd/intrinsics) 代码毫无压力，你可以直接跳到[最终实现](#implicit-b-tree-1)。

## B 树布局

B 树推广了二叉搜索树的概念，允许节点有多于两个的子节点。一棵阶为 $k$ 的 B 树节点不像单个键那样，而是可以包含最多 $B = (k - 1)$ 个按排序顺序存储的键和最多 $k$ 个指向子节点的指针。每个子节点 $i$ 满足这样的性质：其子树中的所有键都位于父节点的键 $(i - 1)$ 和 $i$ 之间（如果它们存在的话）。

![一棵 4 阶 B 树](../img/b-tree.jpg)

这种方法的主要优点是它把树高降低了 $\frac{\log_2 n}{\log_k n} = \frac{\log k}{\log 2} = \log_2 k$ 倍，而取回每个节点仍然花大致相同的时间——只要它适合单个[内存块](/hpc/external-memory/hierarchy/)。

B 树最初主要是为管理磁盘数据库而开发的，在磁盘上随机取回一个字节的延迟与顺序读取接下来 1MB 数据的时间相当。对于我们的用例，我们将使用 $B = 16$ 个元素的块大小——即 $64$ 字节，缓存行的大小——这使得每次查询的树高和缓存行取回总数比二分查找小 $\log_2 17 \approx 4$ 倍。

### 隐式 B 树

在 B 树节点中存储和取回指针会浪费宝贵的缓存空间并降低性能，但它们对于在插入和删除时改变树结构是必不可少的。但当没有更新、树的结构*静态*时，我们可以去掉指针，使结构*隐式*。

实现这一点的方法之一是把 [Eytzinger 编号](../binary-search#eytzinger-layout)推广到 $(B + 1)$ 叉树：

- 根节点编号为 $0$。
- 节点 $k$ 有 $(B + 1)$ 个子节点，编号为 $\\{k \cdot (B + 1) + i + 1\\}$，其中 $i \in [0, B]$。

这样，我们只需分配一个大的二维键数组，并依靠下标算术在树中定位子节点，就能只用 $O(1)$ 的额外内存：

```c++
const int B = 16;

int nblocks = (n + B - 1) / B;
int btree[nblocks][B];

int go(int k, int i) { return k * (B + 1) + i + 1; }
```

<!-- todo: 精确高度 -->

这种编号自动使 B 树完全或几乎完全，高度为 $\Theta(\log_{B + 1} n)$。如果初始数组的长度不是 $B$ 的倍数，最后一个块用其数据类型的最大值填充。

### 构造

我们可以像构造 Eytzinger 数组那样构造 B 树——通过遍历搜索树：

```c++
void build(int k = 0) {
    static int t = 0;
    if (k < nblocks) {
        for (int i = 0; i < B; i++) {
            build(go(k, i));
            btree[k][i] = (t < n ? a[t++] : INT_MAX);
        }
        build(go(k, B));
    }
}
```

它是正确的，因为初始数组的每个值都会被复制到结果数组的一个唯一位置，而且树高是 $\Theta(\log_{B+1} n)$，因为每次下降到子节点时 $k$ 都会乘以 $(B + 1)$。

注意，这种编号会略微造成不平衡：更靠左的子节点可能有更大的子树，尽管这仅对 $O(\log_{B+1} n)$ 个父节点成立。

### 搜索

要找 lower bound，我们需要取回一个节点中的 $B$ 个键，找到第一个不小于 $x$ 的键 $a_i$，下降到第 $i$ 个子节点——然后继续，直到到达一个叶节点。如何找到这第一个键有一些变体。例如，我们可以做一个小型内部二分查找，进行 $O(\log B)$ 次迭代，或者只是按顺序逐个比较每个键，用 $O(B)$ 时间直到找到局部 lower bound，希望能提前一点退出循环。

但我们不打算这么做——因为我们可以用 [SIMD](/hpc/simd)。它对分支不友好，所以本质上我们想做的是一视同仁地与所有 $B$ 个元素比较，从这些比较中计算出一个位掩码，然后用 `ffs` 指令找到第一个不小于 $x$ 的元素对应的位：

```cpp
int mask = (1 << B);

for (int i = 0; i < B; i++)
    mask |= (btree[k][i] >= x) << i;

int i = __builtin_ffs(mask) - 1;
// now i is the number of the correct child node
```

不幸的是，编译器还不够聪明，还不能[自动向量化](/hpc/simd/auto-vectorization/)这段代码，所以我们必须手动优化它。在 AVX2 中，我们可以加载 8 个元素，与搜索键比较，产生一个[向量掩码](/hpc/simd/masking/)，然后用 `movemask` 从中提取标量掩码。下面是一个最小化的图示示例，说明我们想做什么：

```center
       y = 4        17       65       103     
       x = 42       42       42       42      
   y ≥ x = 00000000 00000000 11111111 11111111
           ├┬┬┬─────┴────────┴────────┘       
movemask = 0011                               
           ┌─┘                                
     ffs = 3                                  
```

由于我们一次只能处理 8 个元素（我们块/缓存行大小的一半），我们必须把元素分成两组，然后合并两个 8 位掩码。为此，把条件换成 `x > y` 并计算取反后的掩码会稍微容易一些：

```c++
typedef __m256i reg;

int cmp(reg x_vec, int* y_ptr) {
    reg y_vec = _mm256_load_si256((reg*) y_ptr); // load 8 sorted elements
    reg mask = _mm256_cmpgt_epi32(x_vec, y_vec); // compare against the key
    return _mm256_movemask_ps((__m256) mask);    // extract the 8-bit mask
}
```

现在，要处理整个块，我们需要调用它两次并合并掩码：

```c++
int mask = ~(
    cmp(x, &btree[k][0]) +
    (cmp(x, &btree[k][8]) << 8)
);
```

要沿树下降，我们对这个掩码使用 `ffs` 得到正确的子节点编号，然后调用我们之前定义的 `go` 函数：

```c++
int i = __builtin_ffs(mask) - 1;
k = go(k, i);
```

为了最后真正返回结果，我们希望在访问的最后一个节点中直接取 `btree[k][i]`，但问题是有时局部 lower bound 不存在（$i \ge B$），因为 $x$ 恰好大于节点中的所有键。理论上，我们可以像对 [Eytzinger 二分查找](../binary-search/#search-implementation)那样，在算出最后一个下标*之后*再恢复正确的元素，但这次我们没有一个漂亮的位技巧，必须做一大堆[除以 17](/hpc/arithmetic/division)来计算它，这会很慢，而且几乎肯定不值。

相反，我们可以记住并返回在下降树时遇到的最后一个局部 lower bound：

```c++
int lower_bound(int _x) {
    int k = 0, res = INT_MAX;
    reg x = _mm256_set1_epi32(_x);
    while (k < nblocks) {
        int mask = ~(
            cmp(x, &btree[k][0]) +
            (cmp(x, &btree[k][8]) << 8)
        );
        int i = __builtin_ffs(mask) - 1;
        if (i < B)
            res = btree[k][i];
        k = go(k, i);
    }
    return res;
}
```

这个实现以巨大优势超越了之前所有的二分查找实现：

![](../img/search-btree.svg)

这已经非常好了——但我们还能进一步优化。

### 优化

首先，让我们把数组内存分配在[大页](/hpc/cpu-cache/paging)上：

```c++
const int P = 1 << 21;                        // page size in bytes (2MB)
const int T = (64 * nblocks + P - 1) / P * P; // can only allocate whole number of pages
btree = (int(*)[16]) std::aligned_alloc(P, T);
madvise(btree, T, MADV_HUGEPAGE);
```

这略微改善了较大数组规模上的性能：

![](../img/search-btree-hugepages.svg)

理想情况下，我们还需要为所有[之前的实现](../binary-search)启用大页，以使比较公平，但这关系不大，因为它们都有某种形式的预取来缓解这个问题。

定了这件事，让我们开始真正的优化。首先，我们想尽可能多地使用编译期常量而不是变量，因为这能让编译器把它们嵌入机器码、展开循环、优化算术，并为我们免费做各种其他好事。具体来说，我们想提前知道树高：

<!-- todo: 也许这个可以算得更简单？ -->

```c++
constexpr int height(int n) {
    // grow the tree until its size exceeds n elements
    int s = 0, // total size so far
        l = B, // size of the next layer
        h = 0; // height so far
    while (s + l - B < n) {
        s += l;
        l *= (B + 1);
        h++;
    }
    return h;
}

const int H = height(N);
```

<!--

```c++
constexpr std::pair<int, int> precalc(int n) {
    int s = 0, // total size
        l = B, // size of next layer
        h = 0; // height so far
    while (s + l - B < n) {
        s += l;
        l *= (B + 1);
        h++;
    }
    int r = (n - s + B - 1) / B; // remaining blocks on the last layer
    return {h, s / B + (r + B) / (B + 1) * (B + 1)};
}

const int [height, nblocks] = precalc(N);
```

-->

接下来，我们可以更快地在节点中找到局部 lower bound。与其分别为两个 8 元素块计算并合并两个 8 位掩码，我们可以用 [packs](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html#ig_expand=3037,4870,6715,4845,3853,90,7307,5993,2692,6946,6949,5456,6938,5456,1021,3007,514,518,7253,7183,3892,5135,5260,3915,4027,3873,7401,4376,4229,151,2324,2310,2324,4075,6130,4875,6385,5259,6385,6250,1395,7253,6452,7492,4669,4669,7253,1039,1029,4669,4707,7253,7242,848,879,848,7251,4275,879,874,849,833,6046,7250,4870,4872,4875,849,849,5144,4875,4787,4787,4787,5227,7359,7335,7392,4787,5259,5230,5223,6438,488,483,6165,6570,6554,289,6792,6554,5230,6385,5260,5259,289,288,3037,3009,590,604,5230,5259,6554,6554,5259,6547,6554,3841,5214,5229,5260,5259,7335,5259,519,1029,515,3009,3009,3011,515,6527,652,6527,6554,288,3841,5230,5259,5230,5259,305,5259,591,633,633,5259,5230,5259,5259,3017,3018,3037,3018,3017,3016,3013,5144&text=_mm256_packs_epi32&techs=AVX,AVX2)指令合并向量掩码，并只用一次 `movemask` 轻松提取：

```c++
unsigned rank(reg x, int* y) {
    reg a = _mm256_load_si256((reg*) y);
    reg b = _mm256_load_si256((reg*) (y + 8));

    reg ca = _mm256_cmpgt_epi32(a, x);
    reg cb = _mm256_cmpgt_epi32(b, x);

    reg c = _mm256_packs_epi32(ca, cb);
    int mask = _mm256_movemask_epi8(c);

    // we need to divide the result by two because we call movemask_epi8 on 16-bit masks:
    return __tzcnt_u32(mask) >> 1;
}
```

这条指令把存储在两个寄存器中的 32 位整数转换成存储在一个寄存器中的 16 位整数——在我们的情况下，实际上是合并两个向量掩码。注意我们交换了比较顺序——这让我们最后不用取反掩码，但我们必须在一开始从搜索键中减去[^float]一，以使其正确（否则它工作起来就像 `upper_bound`）。

[^float]: 如果你需要处理[浮点](/hpc/arithmetic/float)键，请考虑 `upper_bound` 是否够用——因为如果你特别需要 `lower_bound`，那么从搜索键中减去一或机器 epsilon 是行不通的：你需要[得到前一个可表示的数](https://stackoverflow.com/questions/10160079/how-to-find-nearest-next-previous-double-value-numeric-limitsepsilon-for-give)来代替。除了少数边界情况外，这本质上意味着把它的位重新解释为整数、减一、再重新解释回浮点数（由于 [IEEE-754 浮点数](/hpc/arithmetic/ieee-754)在内存中的存储方式，这神奇地有效）。

问题是，它做了这种诡异的交错，结果以 `a1 b1 a2 b2` 的顺序写入，而不是我们想要的 `a1 a2 b1 b2`——许多 AVX2 指令都倾向于这样做。要纠正这一点，我们需要[置换](/hpc/simd/shuffling)结果向量，但与其在查询时做，我们可以在预处理时置换每个节点：

```c++
void permute(int *node) {
    const reg perm = _mm256_setr_epi32(4, 5, 6, 7, 0, 1, 2, 3);
    reg* middle = (reg*) (node + 4);
    reg x = _mm256_loadu_si256(middle);
    x = _mm256_permutevar8x32_epi32(x, perm);
    _mm256_storeu_si256(middle, x);
}
```

现在我们只需在构建完节点后立即调用 `permute(&btree[k])`。或许有更快的方法交换中间元素，但我们先把它留在这里，因为预处理时间目前没那么重要。

这个新的 SIMD 例程明显更快，因为额外的 `movemask` 很慢，而且混合两个掩码也需要不少指令。不幸的是，我们现在不能再做 `res = btree[k][i]` 更新了，因为元素被置换了。我们可以在 `i` 上用一些位级技巧解决这个问题，但事实证明索引一个小查找表更快，而且也不需要新的分支：

```c++
const int translate[17] = {
    0, 1, 2, 3,
    8, 9, 10, 11,
    4, 5, 6, 7,
    12, 13, 14, 15,
    0
};

void update(int &res, int* node, unsigned i) {
    int val = node[translate[i]];
    res = (i < B ? val : res);
}
```

这个 `update` 过程需要一些时间，但它不在迭代之间的关键路径上，所以对实际性能影响不大。

把所有这些拼在一起（并省略一些其他小的优化）：

```c++
int lower_bound(int _x) {
    int k = 0, res = INT_MAX;
    reg x = _mm256_set1_epi32(_x - 1);
    for (int h = 0; h < H - 1; h++) {
        unsigned i = rank(x, &btree[k]);
        update(res, &btree[k], i);
        k = go(k, i);
    }
    // the last branch:
    if (k < nblocks) {
        unsigned i = rank(x, btree[k]);
        update(res, &btree[k], i);
    }
    return res;
}
```

所有这些工作为我们节省了 15–20% 左右：

![](../img/search-btree-optimized.svg)

到目前为止，它给人的感觉并不那么令人满意，但我们稍后会复用这些优化思路。

当前实现有两个主要问题：

- `update` 过程相当昂贵，尤其是考虑到它很可能是没用的：17 次中有 16 次，我们可以直接从最后一个块取结果。
- 我们执行非常数次的迭代，造成与 [Eytzinger 二分查找](../binary-search/#removing-the-last-branch)类似的分支预测问题；这次你在图上也能看到，但延迟突起的周期是 $2^4$。

要解决这些问题，我们需要稍微改变布局。

## B+ 树布局

大多数时候，人们谈到 B 树时，他们真正的意思是 *B+ 树*，这种变体区分两类节点：

- *内部节点*存储最多 $B$ 个键和 $(B + 1)$ 个指向子节点的指针。键 $i$ 总是等于第 $(i + 1)$ 个子节点子树中的最小键。
- *数据节点*或*叶节点*存储最多 $B$ 个键、指向下一个叶节点的指针，以及（可选地）与每个键关联的值——如果该结构用作键值映射的话。

这种方法的好处包括更快的搜索时间（因为内部节点只存储键）和快速迭代一段范围内的条目（通过跟随下一个叶节点指针），但代价是一些内存开销：我们必须在内部节点中存储键的副本。

![一棵 4 阶 B+ 树](../img/bplus.png)

回到我们的用例，这种布局可以帮助我们解决两个问题：

- 我们要么在最后下降进入的节点里找到局部 lower bound，要么它就是下一个叶节点的第一个键，所以我们不需要在每次迭代时调用 `update`。
- 所有叶节点的深度恒定，因为 B+ 树在根处生长而不是在叶处生长，这消除了对分支的需要。 <!-- todo: 详细说明这一点 -->

缺点是这个布局不是*简洁*的（succinct）：我们需要一些额外的内存来存储内部节点——准确地说，大约是原始数组大小的 $\frac{1}{16}$——但性能提升将完全值得。

### 隐式 B+ 树

为了在指针算术上更明确，我们将整棵树存储在一个一维数组中。为了在运行期间最小化下标计算，我们将每层顺序存储在这个数组中，并使用编译期计算的偏移量来寻址它们：第 `h` 层上编号为 `k` 的节点的键从 `btree[offset(h) + k * B]` 开始，它的第 `i` 个子节点位于 `btree[offset(h - 1) + (k * (B + 1) + i) * B]`。

要实现所有这些，我们需要稍微多一些 `constexpr` 函数：

```c++
// number of B-element blocks in a layer with n keys
constexpr int blocks(int n) {
    return (n + B - 1) / B;
}

// number of keys on the layer previous to one with n keys
constexpr int prev_keys(int n) {
    return (blocks(n) + B) / (B + 1) * B;
}

// height of a balanced n-key B+ tree
constexpr int height(int n) {
    return (n <= B ? 1 : height(prev_keys(n)) + 1);
}

// where the layer h starts (layer 0 is the largest)
constexpr int offset(int h) {
    int k = 0, n = N;
    while (h--) {
        k += blocks(n) * B;
        n = prev_keys(n);
    }
    return k;
}

const int H = height(N);
const int S = offset(H); // the tree size is the offset of the (non-existent) layer H

int *btree; // the tree itself is stored in a single hugepage-aligned array of size S
```

注意，我们按逆序存储各层，但每层内的节点及其中的数据仍然是左到右的，而且各层是自底向上编号的：叶节点构成第 0 层，根是第 `H - 1` 层。这些只是任意的决定——只是这样在代码中实现稍微容易一点。

### 构造

要从有序数组 `a` 构造树，我们首先需要把它复制到第 0 层，并用无穷大填充：

```c++
memcpy(btree, a, 4 * N);

for (int i = N; i < S; i++)
    btree[i] = INT_MAX;
```

现在我们逐层构建内部节点。对于每个键，我们需要在它的右侧下降，始终向左走，直到到达一个叶节点，然后取它的第一个键——它将是子树中最小的：

```c++
for (int h = 1; h < H; h++) {
    for (int i = 0; i < offset(h + 1) - offset(h); i++) {
        // i = k * B + j
        int k = i / B,
            j = i - k * B;
        k = k * (B + 1) + j + 1; // compare to the right of the key
        // and then always to the left
        for (int l = 0; l < h - 1; l++)
            k *= (B + 1);
        // pad the rest with infinities if the key doesn't exist 
        btree[offset(h) + i] = (k * B < N ? btree[k * B] : INT_MAX);
    }
}
```

然后只是点睛之笔——我们需要置换内部节点中的键以更快地搜索：

```c++
for (int i = offset(1); i < S; i += B)
    permute(btree + i);
```

我们从 `offset(1)` 开始，特意不置换叶节点，让数组保持原始排序顺序。动机是如果键被置换了，我们就需要做 `update` 中那种复杂的下标翻译，而当这是最后一次操作时，它处于关键路径上。所以，仅对这一层，我们换回原始的掩码混合局部 lower bound 过程。

### 搜索

搜索过程变得比 B 树布局更简单：我们不需要做 `update`，只执行固定次数的迭代——尽管最后一次有一些特殊处理：

```c++
int lower_bound(int _x) {
    unsigned k = 0; // we assume k already multiplied by B to optimize pointer arithmetic
    reg x = _mm256_set1_epi32(_x - 1);
    for (int h = H - 1; h > 0; h--) {
        unsigned i = permuted_rank(x, btree + offset(h) + k);
        k = k * (B + 1) + i * B;
    }
    unsigned i = direct_rank(x, btree + k);
    return btree[k + i];
}
```

切换到 B+ 布局完全值得：与优化的 S 树相比，S+ 树快 1.5–3 倍：

![](../img/search-bplus.svg)

图高端的尖峰是由于 L1 TLB 不够大：它有 64 个条目，所以最多可以处理 64 × 2 = 128MB 的数据，而这正是存储 `2^25` 个整数所需的。S+ 树因为约 7% 的内存开销而略微更早触及这个限制。

### 与 `std::lower_bound` 比较

我们从二分查找一路走了很远：

![](../img/search-all.svg)

在这些尺度上，看相对加速比更有意义：

![](../img/search-relative.svg)

图开头处的断崖是因为 `std::lower_bound` 的运行时间随数组大小平滑增长，而 S+ 树是局部平坦的，在需要添加新层时呈阶梯式增加。

我们还没有讨论的一个重要注记是，我们测量的不是真实延迟，而是*倒数吞吐量*——执行大量查询的总时间除以查询数量：

```c++
clock_t start = clock();

for (int i = 0; i < m; i++)
    checksum ^= lower_bound(q[i]);

float seconds = float(clock() - start) / CLOCKS_PER_SEC;
printf("%.2f ns per query\n", 1e9 * seconds / m);
```

要测量*真实*延迟，我们需要在循环迭代之间引入依赖，使下一个查询在前一个完成之前无法开始：

```c++
int last = 0;

for (int i = 0; i < m; i++) {
    last = lower_bound(q[i] ^ last);
    checksum ^= last;
}
```

就真实延迟而言，加速没那么令人印象深刻：

![](../img/search-relative-latency.svg)

S+ 树性能提升的很大一部分来自去除分支和最小化内存请求，这允许重叠执行更多相邻查询——显然平均约三个。

<!-- 显式地把请求分组在一起？ -->

虽然除了高频交易（HFT）从业者之外，可能没人真正在乎真实延迟，而且每个人实际上都在测吞吐量，哪怕嘴上说的是"延迟"，但在预测用户应用中的可能加速时，这个细微差别仍然值得考虑。

### 改进与进一步优化

<!--

臃肿版：

```c++
void permute32(int *node) {
    // a b c d 1 2 3 4 -> (a c) (b d) (1 3) (2 4) -> (a c) (1 3) (b d) (2 4)
    reg x = _mm256_load_si256((reg*) (node + 8));
    reg y = _mm256_load_si256((reg*) (node + 16));
    _mm256_storeu_si256((reg*) (node + 8), y);
    _mm256_storeu_si256((reg*) (node + 16), x);
    permute16(node);
    permute16(node + 16);
}

unsigned permuted_rank32(reg x, int *node) {
    reg a = _mm256_load_si256((reg*) node);
    reg b = _mm256_load_si256((reg*) (node + 8));
    reg c = _mm256_load_si256((reg*) (node + 16));
    reg d = _mm256_load_si256((reg*) (node + 24));

    reg ca = _mm256_cmpgt_epi32(a, x);
    reg cb = _mm256_cmpgt_epi32(b, x);
    reg cc = _mm256_cmpgt_epi32(c, x);
    reg cd = _mm256_cmpgt_epi32(d, x);

    reg cab = _mm256_packs_epi32(ca, cb);
    reg ccd = _mm256_packs_epi32(cc, cd);
    reg cabcd = _mm256_packs_epi16(cab, ccd);
    unsigned mask = _mm256_movemask_epi8(cabcd);

    return __tzcnt_u32(mask);
}
```

```c++
unsigned rank32(reg x, int *node) {
    unsigned mask = cmp(x, node)
                  | (cmp(x, node + 8) << 8)
                  | (cmp(x, node + 16) << 16)
                  | (cmp(x, node + 24) << 24);
```

就这样。这个实现应该能超越高性能数据库中使用的甚至是最先进的索引，尽管这主要是由于真实数据库中的数据结构必须支持快速更新，而我们不需要。

问题有更多维度。

-->

为了在查询期间最小化内存访问次数，我们可以增大块大小。要在 32 元素节点（跨越两条缓存行和四个 AVX2 寄存器）中找到局部 lower bound，我们可以使用一个[类似的技巧](https://github.com/sslotin/amh-code/blob/a74495a2c19dddc697f94221629c38fee09fa5ee/binsearch/bplus32.cc#L94)，用两次 `packs_epi32` 和一次 `packs_epi16` 来合并掩码。

我们还可以尝试通过控制每层树在缓存层级中的存储位置来更高效地使用缓存。我们可以通过把节点预取到[特定层级](/hpc/cpu-cache/prefetching/#software-prefetching)，并在查询中使用[非临时读取](/hpc/cpu-cache/bandwidth/#bypassing-the-cache)来实现。

我实现了这些优化的两个版本：一个是块大小为 32，另一个是最后一次读取为非临时读取。它们没有提升吞吐量：

![](../img/search-bplus-other.svg)

……但它们确实降低了延迟：

![](../img/search-latency-bplus.svg)

我还没能实现但我认为很有前景的想法有：

- 使块大小不统一。动机是拥有一个 32 元素层的减速小于拥有两个独立层。而且根通常不满，所以也许有时它应该只有 8 个键，甚至只有一个键。为给定的数组大小挑选最优的层配置应该能消除相对加速图上的尖峰，使它看起来更像它的上包络。

  我知道如何用代码生成来做这件事，但我选择了通用方案，尝试用现代 C++ 的能力[实现](https://github.com/sslotin/amh-code/blob/main/binsearch/bplus-adaptive.cc)它，但编译器无法以这种方式生成最优代码。
- 把节点与其一两代后代（约 300 个节点/约 5k 个键）分组，使它们在内存中彼此靠近——这正是 [FAST](http://kaldewey.com/pubs/FAST__SIGMOD10.pdf) 所称的分层阻塞（hierarchical blocking）的精神。这降低了 TLB 未命中的严重程度，也可能改善延迟，因为内存控制器可能会选择保持 [RAM 行缓冲区](/hpc/cpu-cache/aos-soa/#ram-specific-timings)打开，预判到局部读取。
- 可选地在某些特定层上使用预取。除了 $\frac{1}{17}$ 的概率恰好预取到我们需要的节点外，如果数据总线不忙，硬件预取器还可能为我们取到它的一些邻居。它还与阻塞有相同的 TLB 和行缓冲效应。

其他可能的小优化包括：

- 也置换最后一层的节点——如果我们只需要下标而不需要值。
- 反转各层的存储顺序为左到右，使前几层位于同一页上。
- 用汇编重写整个东西，因为编译器似乎在指针算术上很吃力。
- 用[混合（blending）](/hpc/simd/masking)代替 `packs`：你可以奇偶混洗节点键（`[1 3 5 7] [2 4 6 8]`），与搜索键比较，然后把第一个寄存器掩码的低 16 位与第二个的高 16 位混合。混合在许多架构上稍微快一点，而且它可能有助于在打包和混合之间交替，因为它们使用不同的端口子集。（感谢 HackerNews 的 Const-me [提出](https://news.ycombinator.com/item?id=30381912)这一点。）
- 用 [popcount](/hpc/simd/shuffling/#shuffles-and-popcount) 代替 `tzcnt`：下标 `i` 等于小于 `x` 的键的个数，所以我们可以把 `x` 与所有键比较，以任何方式合并向量掩码，调用 `maskmov`，然后用 `popcnt` 计算置位数。这消除了按特定顺序存储键的需要，让我们跳过置换步骤，也可以对最后一层使用这个过程。
- 把键 $i$ 定义为子节点 $i$ 子树中的*最大*键，而不是子节点 $(i + 1)$ 子树中的*最小*键。正确性不变，但这保证了结果存储在我们访问的最后一个节点里（而不是下一个邻居节点的第一个元素），这让我们能少取几条缓存行。

注意，当前实现特定于 AVX2，适配其他平台可能需要一些不平凡的改动。把它移植到带 AVX-512 的 Intel CPU 和带 128 位 NEON 的 Arm CPU 会很有趣，这可能需要的[一些技巧](https://github.com/WebAssembly/simd/issues/131)。

<!--

移动端和一些旧 CPU 只有 128 位宽的寄存器，一些高端 CPU 有 512 位寄存器，有些计算机甚至有不同大小的缓存行。NEON 需要一些[技巧](https://github.com/WebAssembly/simd/issues/131)

-->

有了这些优化，我不会惊讶于在某些平台上看到再提升 10–30%，以及在大数组上对 `std::lower_bound` 超过 10 倍的加速。

### 作为动态树

与 `std::set` 和其他基于指针的树的比较甚至更有利。在我们的基准测试中，我们添加相同的元素（不测量添加它们的时间）并使用相同的 lower bound 查询，而 S+ 树快最多 30 倍：

![](../img/search-set-relative.svg)

这表明我们也许可以用这种方法大幅改进*动态*搜索树。

为了验证这个假设，我为每个节点添加了一个包含 17 个下标、指向它们子节点位置的数组，并用这个数组下降树，而不是通常的隐式编号。这个数组与树分离、未对齐，甚至不在大页上——我们做的唯一优化是预取一个节点的第一个和最后一个指针。

我还把 [Abseil 的 B 树](https://abseil.io/blog/20190812-btree)加入了比较，它是我知道的唯一被广泛使用的 B 树实现。它的表现只比 `std::lower_bound` 略好，而带指针的 S+ 树在大数组上快约 15 倍：

<!--

我的下一个优先事项是把它适配到线段树（我知道怎么做）和 B 树（我不太确定怎么做）。但与 `std::set` 的比较暗示可能有高达 30 倍的提升：

`absl::btree_set`，我认识的唯一被广泛使用的 B 树实现，只比二分查找快一点点。

-->

![](../img/search-set-relative-all.svg)

当然，这个比较并不公平，因为实现一棵动态搜索树是一个更高维度的问题。

我们还需要实现更新操作，它不会那么高效，而且我们得为此牺牲扇出系数。但实现一个快 10–20 倍的 `std::set` 和一个快 3–5 倍的 `absl::btree_set` 似乎仍然是可能的，取决于你如何定义"更快"——这是我们[接下来要尝试做](../b-tree)的事情之一。


<!--

约 15 倍的提升绝对值得——而且内存开销不大，因为我们只需要为内部节点存储指针（实际上是下标）。它可能更高，因为我们需要取回两个独立的内存块，或者更低，因为我们需要以某种方式处理更新。无论如何，这将是一个有趣的优化问题。

尽管这主要是由于真实数据库中的数据结构必须支持快速更新，而我们不需要。

问题有更多维度。

-->

### 致谢

Cory Nelson 的这篇 [StackOverflow 回答](https://stackoverflow.com/questions/20616605/using-simd-avx-sse-for-tree-traversal)是我拿来置换的 16 元素搜索技巧的地方。

<!--

我从博客上偷了一些图片，找不到原图了。

-->