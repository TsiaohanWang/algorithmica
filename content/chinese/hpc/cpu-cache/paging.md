---
title: 内存分页
weight: 12
---

[再次](../associativity)考虑跨步递增循环：

```cpp
const int N = (1 << 13);
int a[D * N];

for (int i = 0; i < D * N; i += D)
    a[i] += 1;
```

我们改变步长 $D$，并按比例增大数组大小，使总迭代次数 $N$ 保持不变。由于总内存访问次数也保持不变，对于所有 $D \geq 16$，我们应该恰好取回 $N$ 条缓存行——准确地说，是 $64 \cdot N = 2^6 \cdot 2^{13} = 2^{19}$ 字节。这与步长无关，恰好能装进 L2 缓存，吞吐量曲线应该是平坦的。

这一次，我们考虑更大的 $D$ 值范围，最大到 1024。从大约 256 开始，曲线显然不再平坦：

![](../img/strides.svg)

这个异常同样源于缓存系统，虽然标准的 L1-L3 数据缓存与它毫无关系。罪魁祸首是[虚拟内存](/hpc/external-memory/virtual)，特别是*快表*（translation lookaside buffer，TLB），它是负责检索虚拟内存页物理地址的缓存。

在[我的 CPU](https://en.wikichip.org/wiki/amd/microarchitectures/zen_2) 上有两级 TLB：

- L1 TLB 有 64 个条目，如果页大小为 4K，那么它可以处理 $64 \times 4K = 512K$ 的活动内存而无需访问 L2 TLB。
- L2 TLB 有 2048 个条目，它可以处理 $2048 \times 4K = 8M$ 的内存而无需访问页表。

当 $D$ 等于 256 时分配了多少内存？你猜对了：$8K \times 256 \times 4B = 8M$，恰好是 L2 TLB 所能处理的极限。当 $D$ 超过这个值时，一些请求开始被重定向到主页表，而主页表具有很大的延迟和非常有限的吞吐量，这使整个计算陷入瓶颈。

### 更改页大小

那 8MB 的无减速内存看起来是个非常严格的限制。虽然我们无法改变硬件特性来解除它，但*可以*增大页大小，这反过来会减轻 TLB 容量的压力。

现代操作系统允许我们全局地或针对单个分配设置页大小。CPU 只支持一组特定大小的页——例如我的 CPU 可以用 4K 或 2M 的页。另一个典型的页大小是 1G——它通常只与拥有数百 GB 内存的服务器级硬件相关。任何超过默认 4K 的页在 Linux 上称为*大页*（huge pages），在 Windows 上称为*大页面*（large pages）。

在 Linux 上，有一个特殊的系统文件管理大页的分配。下面是让内核在每次分配时都给你大页的方法：

```bash
$ echo always > /sys/kernel/mm/transparent_hugepage/enabled
```

像这样全局启用大页并不总是一个好主意，因为它降低了内存粒度并提高了进程消耗的最小内存——而某些环境中的进程数比空闲内存的兆字节数还多。因此，除了 `always` 和 `never`，该文件中还有第三个选项：

```bash
$ cat /sys/kernel/mm/transparent_hugepage/enabled
always [madvise] never
```

`madvise` 是一个特殊的系统调用，它让程序向内核建议是否使用大页，可用于按需分配大页。如果它被启用，你可以在 C++ 中这样使用：

```c++
#include <sys/mman.h>

void *ptr = std::aligned_alloc(page_size, array_size);
madvise(ptr, array_size, MADV_HUGEPAGE);
```

只有当内存区域具有相应的对齐时，你才能请求用大页来分配它。

Windows 有类似的功能。它的内存 API 把这两个函数合并为一个：

```c++
#include "memoryapi.h"

void *ptr = VirtualAlloc(NULL, array_size,
                         MEM_RESERVE | MEM_COMMIT | MEM_LARGE_PAGES, PAGE_READWRITE);
```

在两种情况下，`array_size` 都应该是 `page_size` 的倍数。

### 大页的影响

分配大页的两种方式都立即让曲线变得平坦：

![](../img/strides-hugepages.svg)

启用大页还能将装不进 L2 缓存的数组的[延迟](../latency)最多改善 10-15%：

![](../img/permutation-hugepages.svg)

总的来说，当你进行任何形式的稀疏读取时，启用大页是个好主意，因为它们通常会略微改善性能，而且（几乎）[从不](../aos-soa)会损害性能。

话虽如此，如果可以的话，你不应该依赖大页，因为由于硬件或计算环境的限制，它们并不总是可用的。出于[很多](../cache-lines)[其他](../prefetching)[原因](../aos-soa)，在空间上对数据访问进行分组是有益的，这会自动解决分页问题。

<!--


虚拟定位，物理标记

实际上，TLB 未命中可能因为同样的原因使内存读取停滞。TLB 缓存被称为「后备」（lookaside）是因为其查找可以与普通数据缓存查找独立进行。而 L1 和 L2 缓存是核心私有的，因此它们可以存储虚拟地址并与 TLB 并发查询——取回一条缓存行后，用其标签恢复物理地址，再与并发取回的 TLB 条目比对。然而，这种技巧不适用于共享内存，因为其带宽有限，无缘无故向它派发读查询通常不是个好主意。因此，当页装不进 L1 TLB 和 L2 TLB 时，我们可以分别在 L3 和内存读取中观察到类似的效果。

对于稀疏读取，增大页大小通常是有意义的，这能改善延迟。

页的典型大小是 4KB，但对于大型数据库可以大到 1G 左右，不过默认启用它并不是个好主意，因为拥有 256M 内存的 VPS 却有超过 256 个进程的场景并不罕见。

典型的页大小是 4K、2M 和 1G（例如，分别允许 256K、128M、64G 的内存区域存储在 64 个条目的 L1 TLB 中）。


- CPU 内部还有其他类型的缓存，用于数据以外的用途。对我们来说最重要的是*指令缓存*（I-cache），它用于加速从内存取机器码，以及*快表*（TLB），它用于存储虚拟内存页的物理位置，对虚拟内存的效率至关重要。

你可以用 `cpuid` 命令获取你的架构的这些信息。

-->

