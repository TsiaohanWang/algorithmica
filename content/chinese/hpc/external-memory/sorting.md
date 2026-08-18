---
title: 外部排序
weight: 4
published: true
---

现在，让我们尝试为新的[外部存储模型](../model)设计一些真正有用的算法。本节的目标是由浅入深，逐步构建更复杂的东西，最终讲到*外部排序*及其有趣的应用。

这个算法将基于标准的归并排序算法，因此我们首先需要推导出它的主要原语。

### 归并

**问题**。给定两个已排序的数组 $a$ 和 $b$，长度分别为 $N$ 和 $M$，请生成一个长度为 $N + M$、包含它们全部元素的有序数组 $c$。

归并有序数组的标准双指针技术是这样的：

```cpp
void merge(int *a, int *b, int *c, int n, int m) {
    int i = 0, j = 0;
    for (int k = 0; k < n + m; k++) {
        if (i < n && (j == m || a[i] < b[j]))
            c[k] = a[i++];
        else
            c[k] = b[j++];
    }
}
```

从内存操作的角度看，我们只是线性读取 $a$ 和 $b$ 的所有元素，并线性写入 $c$ 的所有元素。由于这些读写操作都可以缓冲，它只需要 $SCAN(N+M)$ 次 I/O 操作。

到目前为止，这些例子都很简单，它们的分析与 RAM 模型差别不大，只是把最终答案除以块大小 $B$。但这里有一个并非如此的情形。

**$k$ 路归并**。考虑这个算法的变体：我们需要归并的不止两个数组，而是总数大小为 $N$ 的 $k$ 个数组——做法同样是察看 $k$ 个值，选出其中的最小值写入 $c$，并递增其中一个迭代器。

在标准 RAM 模型中，渐近复杂度要乘以 $k$，因为每填充下一个元素都需要 $O(k)$ 次比较。但在外部存储模型中，我们在内存中所做的一切都不花钱，因此只要内存中能放下 $(k+1)$ 个完整的块——即 $k = O(\frac{M}{B})$——它的渐近复杂度就不会改变。

还记得我们引入计算模型时的 $M \gg B$ 假设吗？如果对某个 $\epsilon > 0$ 有 $M \geq B^{1+ε}$，那么内存中就能放下任意亚多项式数量的块，当然包括 $O(\frac{M}{B})$ 个。这个条件称为*高缓存假设（tall cache assumption*），许多其他外部存储算法通常也需要它。

### 归并排序

标准归并排序算法的「常规」复杂度是 $O(N \log_2 N)$：在它的 $O(\log_2 N)$ 个「层」中，每一层都需要遍历全部 $N$ 个元素，并以线性时间将它们归并。

在外部存储模型中，当我们读取一个大小为 $M$ 的块时，可以「免费」对其元素排序，因为它们已经在内存中了。这样，我们可以把数组分成 $O(\frac{N}{M})$ 个包含连续元素的块，先把它们分别排好序作为基本步骤，然后再合并它们。

![](../img/k-way.png)

这实际上意味着，就 I/O 操作而言，归并排序前 $O(\log M)$ 层是免费的，只有 $O(\log_2 \frac{N}{M})$ 层有非零成本，每一层总共可以在 $O(\frac{N}{B})$ 次 IOPS 内完成归并。这使得总的 I/O 复杂度为

$$
O\left(\frac{N}{B} \log_2 \frac{N}{M}\right)
$$

这相当快。如果我们有 1GB 内存和 10GB 数据，这实际上意味着排序所需的工作量仅仅比读取数据多出一点点（大约 3 倍多一点）。有意思的是，我们还能做得更好。

### $k$ 路归并排序

半页之前我们学到，在外部存储模型中，归并 $k$ 个数组和归并两个数组一样容易——代价只是读取它们。我们为什么不在这里应用这个事实呢？

让我们像之前一样在内存中排序每个大小为 $M$ 的块，但在每个归并阶段，我们不只把已排序的块两两配对归并，而是在一次 $k$ 路归并中尽量多拿几个能装进内存的块。这样归并树的高度会大大降低，而每一层仍然可以在 $O(\frac{N}{B})$ 次 IOPS 内完成。

一次能归并多少个有序数组？恰好是 $k = \frac{M}{B}$，因为每个数组都需要一个块的内存。由于总层数将减少到 $\log_{\frac{M}{B}} \frac{N}{M}$，总复杂度将降低为

$$
SORT(N) \stackrel{\text{定义}}{=} O\left(\frac{N}{B} \log_{\frac{M}{B}} \frac{N}{M} \right)
$$

注意，在我们的例子中，有 10GB 数据、1GB 内存，HDD 的块大小约为 1MB。这使得 $\frac{M}{B} = 1000$、$\frac{N}{M} = 10$，于是对数小于 1（即 $\log_{1000} 10 = \frac{1}{3}$）。当然，我们不可能比读取数组更快地完成排序，因此这种分析适用于数据集非常大、内存很小和/或块很大的情况，而如今这在现实中很少发生。

### 实际实现

在更现实的约束下，我们可以不用 $\log_{\frac{M}{B}} \frac{N}{M}$ 层，而只用两层：一层用于对大小为 $M$ 的元素块内的数据进行排序，另一层用于一次性归并所有块。这样，从 I/O 操作的角度看，我们只是把数据集循环了两遍。而且，在 1GB RAM、1MB 块大小的情况下，这种方法可以排序高达 1TB 的数组。

下面是第一个阶段在 C++ 中的样子。这个程序打开一个包含无序整数的数 GB 二进制文件，以 256MB 的块读取它，在内存中排序，然后写回到名为 `part-000.bin`、`part-001.bin`、`part-002.bin`……的文件中：

```cpp
const int B = (1<<20) / 4; // 1 MB blocks of integers
const int M = (1<<28) / 4; // available memory

FILE *input = fopen("input.bin", "rb");
std::vector<FILE*> parts;

while (true) {
    static int part[M]; // better delete it right after
    int n = fread(part, 4, M, input);

    if (n == 0)
        break;
    
    // sort a block in-memory
    std::sort(part, part + n);
    
    char fpart[sizeof "part-999.bin"];
    sprintf(fpart, "part-%03d.bin", parts.size());

    printf("Writing %d elements into %s...\n", n, fpart);

    FILE *file = fopen(fpart, "wb");
    fwrite(part, 4, n, file);
    fclose(file);
    
    file = fopen(fpart, "rb");
    parts.push_back(file);
}

fclose(input);
```

现在剩下的就是把它们合并在一起。现代 HDD 的带宽可能相当高，而且需要合并的分片可能很多，因此这个阶段的 I/O 效率不是我们唯一关心的问题：我们还需要比用 $O(k)$ 次比较找最小值更快的方法来归并 $k$ 个数组。如果我们为这 $k$ 个元素维护一个最小堆，每个元素就可以在 $O(\log k)$ 时间内完成，方式与堆排序几乎相同。

下面是实现方法。首先，我们需要一个堆（C++ 中的 `priority_queue`）：

```c++
struct Pointer {
    int key, part; // the element itself and the number of its part

    bool operator<(const Pointer& other) const {
        return key > other.key; // std::priority_queue is a max-heap by default
    }
};

std::priority_queue<Pointer> q;
```

然后，我们需要分配并填充缓冲区：

```c++
const int nparts = parts.size();

auto buffers = new int[nparts][B]; // buffers for each part
int *l = new int[nparts],          // # of already processed buffer elements
    *r = new int[nparts];          // buffer size (in case it isn't full)

// now we add fill the buffer for each part and add their elements to the heap
for (int part = 0; part < nparts; part++) {
    l[part] = 1; // if the element is in the heap, we also consider it "processed"
    r[part] = fread(buffers[part], 4, B, parts[part]);
    q.push({buffers[part][0], part});
}
```

现在，我们只需把元素从堆中弹出写入结果文件，直到堆为空，并仔细地成批读写元素：

```cpp
FILE *output = fopen("output.bin", "w");

int outbuffer[B]; // the output buffer
int buffered = 0; // number of elements in it

while (!q.empty()) {
    auto [key, part] = q.top();
    q.pop();

    // write the minimum to the output buffer
    outbuffer[buffered++] = key;
    // check if it needs to be committed to the file
    if (buffered == B) {
        fwrite(outbuffer, 4, B, output);
        buffered = 0;
    }

    // fetch a new block of that part if needed
    if (l[part] == r[part]) {
        r[part] = fread(buffers[part], 4, B, parts[part]);
        l[part] = 0;
    }

    // read a new element from that part unless we've already processed all of it
    if (l[part] < r[part]) {
        q.push({buffers[part][l[part]], part});
        l[part]++;
    }
}

// write what's left of the output buffer
fwrite(outbuffer, 4, buffered, output);

//clean up
delete[] buffers;
for (FILE *file : parts)
    fclose(file);
fclose(output);
```

这个实现并不是特别高效或安全（好吧，这基本上是朴素的 C 代码），但它是学习如何使用底层内存 API 的好教学示例。

### 连接

排序主要不是单独使用，而是作为其他操作的中间步骤。外部排序的一个重要的现实应用是连接（join，即「SQL join」），用于数据库和其他数据处理应用中。

**问题**。给定两个元组列表 $(x_i, a_{x_i})$ 和 $(y_i, b_{y_i})$，输出一个列表 $(k, a_{x_k}, b_{y_k})$，使得 $x_k = y_k$

最优方案是对两个列表排序，然后用标准双指针技术归并它们。这里的 I/O 复杂度与排序相同；如果数组已经有序，则只需 $O(\frac{N}{B})$。这就是为什么大多数数据处理应用（数据库、MapReduce 系统）喜欢让它们的表至少保持部分有序。

**其他方法**。注意，上述分析只适用于外部存储场景——即你没有足够内存读取整个数据集的情况。在现实世界中，其他方法可能更快。

其中最简单的可能莫过于

```python
def join(a, b):
    d = dict(a)
    for x, y in b:
        if x in d:
            yield d[x]
```

在外部存储中，用哈希表连接两个列表是不可行的，因为这需要 $O(M)$ 次块读取，即使每次其实只用到其中一个元素。

另一种方法是使用替代性排序算法，例如基数排序。具体来说，如果有足够的内存为所有可能的键维护缓冲区，基数排序可以在 $O(\frac{N}{B} \cdot w)$ 次块读取内完成；在键较小而数据集较大的情况下，它可能更快。