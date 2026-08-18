---
title: 矩阵乘法
weight: 20
---

<!--
baseline 13.58622 0.5209607970428861
hugepages 16.749895 0.42256312651512146
transposed 12.377302 0.5718441708863531
autovec 3.117215 2.2705806304666187
vectorized 3.075742 2.301196914435606
kernel 2.24264 3.1560517960974566
blocked 0.461477 15.33746643928083
noalloc 0.408031 17.346446716058338
nomove 0.303826 23.295860130469414
blas 0.27489790320396423 25.747333528217077
-->

在本案例研究中，我们将设计并实现几种矩阵乘法算法。

我们从朴素的「for-for-for」算法出发，逐步改进，最终得到一个快 50 倍、性能与 BLAS 库相当、而代码不足 40 行 C 的版本。

所有实现都用 GCC 13 编译，并在主频 2GHz 的 [Zen 2](https://en.wikichip.org/wiki/amd/microarchitectures/zen_2) CPU 上运行。

## 基线

一个 $l \times n$ 矩阵 $A$ 乘以 $n \times m$ 矩阵 $B$ 的结果定义为 $l \times m$ 矩阵 $C$，满足：

$$
C_{ij} = \sum_{k=1}^{n} A_{ik} \cdot B_{kj}
$$

为了简单起见，我们只考虑*方阵*，即 $l = m = n$。

要实现矩阵乘法，我们只需把这一定义翻译成代码；但为了显式地体现指针运算，我们不用二维数组（即矩阵），而是用一维数组：

```c++
void matmul(const float *a, const float *b, float *c, int n) {
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++)
                c[i * n + j] += a[i * n + k] * b[k * n + j];
}
```

出于稍后会说明的原因，我们在基准测试中只使用 $48$ 的倍数作为矩阵大小，但实现对于其他大小同样正确。我们还特意使用 [32 位浮点数](/hpc/arithmetic/ieee-754)，尽管所有实现都可以很容易地[推广](#generalizations)到其他数据类型和运算。

用 `g++ -O3 -march=native -ffast-math -funroll-loops` 编译后，朴素方法将两个大小为 $n = 1920 = 48 \times 40$ 的矩阵相乘约需 16.7 秒。换个角度看，这大约是 $\frac{1920^3}{16.7 \times 10^9} \approx 0.42$ 次有效运算每纳秒（GFLOPS），也就是每次乘法约 5 个 CPU 周期，看起来还不怎么样。

## 转置

一般来说，在优化处理大量数据的算法时——而 $1920^2 \times 3 \times 4 \approx 42$ MB 显然算大量数据，因为它放不进任何[CPU 缓存](/hpc/cpu-cache)——应该总是先考虑内存再优化运算，因为内存更可能是瓶颈。

元素 $C_{ij}$ 可以看作是矩阵 $A$ 的第 $i$ 行与矩阵 $B$ 的第 $j$ 列的点积。在上面的内层循环中递增 `k` 时，我们顺序读取矩阵 `a`，但在遍历 `b` 的一列时，每次都要跳过 $n$ 个元素，而这[不如](/hpc/cpu-cache/aos-soa)顺序遍历快。

一个[众所周知的](/hpc/external-memory/oblivious/#matrix-multiplication)解决这个问题的优化是：把矩阵 $B$ 按*列主序*存储——或者等价地，在矩阵乘法之前把它*转置*。这需要 $O(n^2)$ 次额外操作，但能保证最内层循环中的顺序读取：

<!--

![](../img/column-major.jpg)

-->

```c++
void matmul(const float *a, const float *_b, float *c, int n) {
    float *b = new float[n * n];

    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            b[i * n + j] = _b[j * n + i];
    
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++)
                c[i * n + j] += a[i * n + k] * b[j * n + k]; // <- note the indices
}
```

这段代码运行约 12.4s，快了约 30%。

稍后我们会看到，转置带来的好处远不止顺序内存读取。

## 向量化

现在我们所做的一切不过就是顺序读取 `a` 和 `b` 的元素、相乘并把结果加到一个累加变量上，因此我们可以用 [SIMD](/hpc/simd/) 指令来加速这一切。使用 [GCC 向量类型](/hpc/simd/intrinsics/#gcc-vector-extensions) 实现起来相当直接——我们可以让矩阵行[内存对齐](/hpc/cpu-cache/alignment/)、用零填充，然后像计算任何其他[归约](/hpc/simd/reduction/)那样计算乘加：

```c++
// a vector of 256 / 32 = 8 floats
typedef float vec __attribute__ (( vector_size(32) ));

// a helper function that allocates n vectors and initializes them with zeros
vec* alloc(int n) {
    vec* ptr = (vec*) std::aligned_alloc(32, 32 * n);
    memset(ptr, 0, 32 * n);
    return ptr;
}

void matmul(const float *_a, const float *_b, float *c, int n) {
    int nB = (n + 7) / 8; // number of 8-element vectors in a row (rounded up)

    vec *a = alloc(n * nB);
    vec *b = alloc(n * nB);

    // move both matrices to the aligned region
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            a[i * nB + j / 8][j % 8] = _a[i * n + j];
            b[i * nB + j / 8][j % 8] = _b[j * n + i]; // <- b is still transposed
        }
    }

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            vec s{}; // initialize the accumulator with zeros

            // vertical summation
            for (int k = 0; k < nB; k++)
                s += a[i * nB + k] * b[j * nB + k];
            
            // horizontal summation
            for (int k = 0; k < 8; k++)
                c[i * n + j] += s[k];
        }
    }

    std::free(a);
    std::free(b);
}
```

当 $n = 1920$ 时，性能现在约为 2.3 GFLOPS——比转置但未向量化的版本又高了约 4 倍。

![](../img/mm-vectorized-barplot.svg)

这个优化看起来既不复杂，也并非矩阵乘法所独有。为什么编译器不能自己[自动向量化](/hpc/simd/auto-vectorization/)内层循环呢？

它其实可以；唯一阻碍它的是 `c` 可能与 `a` 或 `b` 重叠的可能性。要排除这一点，你可以通过给 `c` 加上 `__restrict__` 关键字来告知编译器你保证 `c` 不与任何东西[别名](/hpc/compilation/contracts/#memory-aliasing)：

<!-- （编译器已经知道按任意顺序读取 `a` 和 `b` 都是安全的，因为它们被标记为 `const`）：-->

```c++
void matmul(const float *a, const float *_b, float * __restrict__ c, int n) {
    // ...
}
```

手动向量化和自动向量化的实现性能大致相当。

<!--

性能瓶颈在于使用了一个单一变量。我们可以像其他归约那样使用多个变量，不过无论如何我们稍后都会解决它。

-->

## 内存效率

有意思的是，实现效率取决于问题的规模。

起初，性能（定义为每秒的有效运算数）随着循环管理和水平归约的开销减小而上升。然后，在大约 $n=256$ 处，它开始平滑下降，因为矩阵放不进[缓存](/hpc/cpu-cache/)了（$2 \times 256^2 \times 4 = 512$ KB 是 L2 缓存的大小），性能转而受限于[内存带宽](/hpc/cpu-cache/bandwidth/)。

![](../img/mm-vectorized-plot.svg)

同样有趣的是，朴素实现与未向量化的转置版本大致持平——甚至略好一点，因为它不需要做转置。

有人可能会认为，顺序读取会有某种普适的性能收益，因为我们取到的缓存行更少，但事实并非如此：取 `b` 的第一列确实更耗时，但接下来的 15 次列读取都落在与第一次相同的缓存行里，所以它们无论如何都会被缓存——除非矩阵大到连 `n * cache_line_size` 字节都放不进缓存，而这在任何实际规模的矩阵上都不会发生。

相反，性能只会在少数特定矩阵大小上恶化，这是[缓存组相联](/hpc/cpu-cache/associativity/)效应所致：当 $n$ 是某个大的 2 的幂的倍数时，我们从 `b` 中取出的地址很可能都映射到相同的缓存行组，从而减小了有效缓存大小。这解释了 $n = 1920 = 2^7 \times 3 \times 5$ 时 30% 的性能下滑，你还能看到 $1536 = 2^9 \times 3$ 处更明显的下滑：它比 $n=1535$ 时慢了约 3 倍。

所以，与直觉相反，转置矩阵并不能改善缓存——而且在朴素的标量实现中，我们本来就不真正受限于内存带宽。但我们的向量化实现确实受限于此，所以让我们着手提高它的 I/O 效率。

## 寄存器复用

用类似 Python 的记号表示子矩阵：要计算单元 $C[x][y]$，我们需要计算 $A[x][:]$ 与 $B[:][y]$ 的点积，这需要读取 $2n$ 个元素，即使我们把 $B$ 按列主序存储。

<!-- A 和 B 的任意两个单元都用于更新 C 的某个单元。 -->

要计算 $C[x:x+2][y:y+2]$（$C$ 的一个 $2 \times 2$ 子矩阵），我们需要 $A$ 的两行和 $B$ 的两列，即 $A[x:x+2][:]$ 和 $B[:][y:y+2]$，共含 $4n$ 个元素，却用来更新*四个*元素而不是*一个*——就 I/O 效率而言，这是 $\frac{2n / 1}{4n / 4} = 2$ 倍的优势。

<!--

为了真正避免读取更多数据，我们需要并行读取这 $2+2$ 行和列，并用所有可能的乘积组合一次性更新全部 $2 \times 2$ 个单元。

-->

为了避免重复读取数据，我们需要并行遍历这些行和列，一次性用所有 $2 \times 2$ 种乘积组合来更新。下面是一个概念验证：

```c++
void kernel_2x2(int x, int y) {
    int c00 = 0, c01 = 0, c10 = 0, c11 = 0;

    for (int k = 0; k < n; k++) {
        // read rows
        int a0 = a[x][k];
        int a1 = a[x + 1][k];

        // read columns
        int b0 = b[k][y];
        int b1 = b[k][y + 1];

        // update all combinations
        c00 += a0 * b0;
        c01 += a0 * b1;
        c10 += a1 * b0;
        c11 += a1 * b1;
    }

    // write the results to C
    c[x][y]         = c00;
    c[x][y + 1]     = c01;
    c[x + 1][y]     = c10;
    c[x + 1][y + 1] = c11;
}
```

我们现在可以直接在 $C$ 的所有 2x2 子矩阵上调用这个内核，但不必费心评测它：尽管这个算法在 I/O 操作上更优，它仍然打不过我们基于 SIMD 的实现。相反，我们将推广这一思路，直接开发一个类似的*向量化*内核。

<!-- 它还能提升指令级并行（我们不必在每次迭代之间等待更新循环状态），并省去执行读取指令的周期。

当然，尽管在 I/O 上更优，这种 $2 \times 2$ 的更新仍然打不过我们的向量化实现，所以我们不会特别尝试这个版本，而是会立刻把这套思路放大。

-->

## 设计内核

我们不设计一个从零计算 $C$ 的 $h \times w$ 子矩阵的内核，而是声明一个*更新*它的函数：用 $A$ 的第 $l$ 到 $r$ 列以及 $B$ 的第 $l$ 到 $r$ 行。目前这看起来像是过度泛化，但这个函数接口稍后会证明很有用。

<!--

我们遵循这一思路，设计一个通用内核：用 $A$ 的第 $l$ 到 $r$ 列和 $B$ 的第 $l$ 到 $r$ 行更新 C 的 $h \times w$ 子矩阵（即不是完整计算，而只是部分更新——稍后会明白为什么）。

-->

为了确定 $h$ 和 $w$，我们有几点性能上的考量：

- 一般而言，计算一个 $h \times w$ 子矩阵需要读取 $2 \cdot n \cdot (h + w)$ 个元素。为了优化 I/O 效率，我们希望 $\frac{h \cdot w}{h + w}$ 这个比值尽量高，这可以通过大的、接近方形的子矩阵来实现。
- 我们希望使用所有现代 x86 架构都提供的 [FMA](https://en.wikipedia.org/wiki/FMA_instruction_set)（「融合乘加」）指令。正如你从名字能猜到的，它一步就能在 8 元素向量上执行 `c += a * b` 运算——这正是点积的核心——省去了分别执行向量乘法和加法。<!-- saxpy：单精度 A·X 加 Y（Single-Precision A·X Plus Y） -->
- 为了更好利用这条指令，我们希望发挥[指令级并行](/hpc/pipelining/)的作用。在 Zen 2 上，`fma` 指令的延迟为 5、吞吐量为 2，意味着需要并发执行至少 $5 \times 2 = 10$ 条才能打满它的执行端口。
- 我们希望避免寄存器溢出（不必要地在寄存器和内存之间搬移数据），而我们只有 $16$ 个逻辑向量寄存器可以用作累加器（减去用于存放临时值的那些）。

基于这些原因，我们选定 $6 \times 16$ 的内核。这样我们一次处理 $96$ 个元素，存放在 $6 \times 2 = 12$ 个向量寄存器中。为了高效地更新它们，我们采用下面的流程：

<!--

我们[广播](/hpc/simd/moving/#broadcast) A 的一个元素，然后用它更新第一行（$8 + 8$ 个元素）。接着加载它下面的元素，依此类推。当更新完最后一行后，我们向右移动到接下来的 $6$ 个元素。

最终实现比听起来更简单：

-->

```c++
// update 6x16 submatrix C[x:x+6][y:y+16]
// using A[x:x+6][l:r] and B[l:r][y:y+16]
void kernel(float *a, vec *b, vec *c, int x, int y, int l, int r, int n) {
    vec t[6][2]{}; // will be zero-filled and stored in ymm registers

    for (int k = l; k < r; k++) {
        for (int i = 0; i < 6; i++) {
            // broadcast a[x + i][k] into a register
            vec alpha = vec{} + a[(x + i) * n + k]; // converts to a broadcast
            // multiply b[k][y:y+16] by it and update t[i][0] and t[i][1]
            for (int j = 0; j < 2; j++)
                t[i][j] += alpha * b[(k * n + y) / 8 + j]; // converts to an fma
        }
    }

    // write the results back to C
    for (int i = 0; i < 6; i++)
        for (int j = 0; j < 2; j++)
            c[((x + i) * n + y) / 8 + j] += t[i][j];
}
```

我们需要 `t` 来让编译器把这些元素存放在向量寄存器中。我们本可以直接更新它们在 `c` 中的最终位置，但遗憾的是，编译器会把它们重新写回内存，造成性能下降（给所有东西包上 `__restrict__` 关键字也无济于事）。

在展开这些循环并把 `b` 从 `i` 循环中提升出来（`b[(k * n + y) / 8 + j]` 不依赖 `i`，可以只加载一次并在全部 6 次迭代中复用）之后，编译器生成了与下面更相似的东西：

<!-- /hpc/simd/intrinsics/#simd-intrinsics -->

```c++
for (int k = l; k < r; k++) {
    __m256 b0 = _mm256_load_ps((__m256*) &b[k * n + y];
    __m256 b1 = _mm256_load_ps((__m256*) &b[k * n + y + 8];
    
    __m256 a0 = _mm256_broadcast_ps((__m128*) &a[x * n + k]);
    t00 = _mm256_fmadd_ps(a0, b0, t00);
    t01 = _mm256_fmadd_ps(a0, b1, t01);

    __m256 a1 = _mm256_broadcast_ps((__m128*) &a[(x + 1) * n + k]);
    t10 = _mm256_fmadd_ps(a1, b0, t10);
    t11 = _mm256_fmadd_ps(a1, b1, t11);

    // ...
}
```

我们使用 $12+3=15$ 个向量寄存器和总共 $6 \times 3 + 2 = 20$ 条指令来完成 $16 \times 6 = 96$ 次更新。假设没有其他瓶颈，我们就应该能打满 `_mm256_fmadd_ps` 的吞吐量。

注意，这个内核是架构相关的。如果没有 `fma`，或者它的吞吐量/延迟不同，或者 SIMD 宽度是 128 或 512 位，我们都会做出不同的设计选择。跨平台的 BLAS 实现[自带许多内核](https://github.com/xianyi/OpenBLAS/tree/develop/kernel)，每个都用手写汇编编写，并为特定架构做过优化。

实现的其余部分很直接。与之前的向量化实现类似，我们只需把矩阵搬到内存对齐的数组里，然后用内核替换最内层循环：

```c++
void matmul(const float *_a, const float *_b, float *_c, int n) {
    // to simplify the implementation, we pad the height and width
    // so that they are divisible by 6 and 16 respectively
    int nx = (n + 5) / 6 * 6;
    int ny = (n + 15) / 16 * 16;
    
    float *a = alloc(nx * ny);
    float *b = alloc(nx * ny);
    float *c = alloc(nx * ny);

    for (int i = 0; i < n; i++) {
        memcpy(&a[i * ny], &_a[i * n], 4 * n);
        memcpy(&b[i * ny], &_b[i * n], 4 * n); // we don't need to transpose b this time
    }

    for (int x = 0; x < nx; x += 6)
        for (int y = 0; y < ny; y += 16)
            kernel(a, (vec*) b, (vec*) c, x, y, 0, n, ny);

    for (int i = 0; i < n; i++)
        memcpy(&_c[i * n], &c[i * ny], 4 * n);
    
    std::free(a);
    std::free(b);
    std::free(c);
}
```

这改善了基准测试的性能，但只提升约 40%：

![](../img/mm-kernel-barplot.svg)

在较小的数组上加速比要高得多（2–3 倍），说明仍然存在内存带宽问题：

![](../img/mm-kernel-plot.svg)

如果你读过[缓存无关算法](/hpc/external-memory/oblivious/)那节，就会知道这类问题的一个通用解决方案是把所有矩阵分成四块、执行八次递归的块矩阵乘法、再小心地把结果组合起来。这个方案在实践中尚可，但递归有一些[开销](/hpc/architecture/functions/)，而且也不允许我们精细地调优算法，所以我们将采用一种不同的、更简单的方案。

## 分块

分治技巧的*缓存感知*替代方案是*缓存分块*（cache blocking）：把数据切分为能放进缓存的块，再逐块处理。如果有多层缓存，我们还可以做层次化分块：先选一块能放进 L3 缓存的数据，再把它切分成能放进 L2 缓存的块，依此类推。这种方法需要事先知道缓存大小，但通常更容易实现，实践上也更快。

对矩阵做缓存分块比对数组更难一些，但总体思路如下：

- 选取一块能放进 L3 缓存的 $B$ 的子矩阵（比如，它的一部分列）。
- 选取一块能放进 L2 缓存的 $A$ 的子矩阵（比如，它的一部分行）。
- 从先前选取的 $B$ 的子矩阵中再选取一块能放进 L1 缓存的子矩阵（它的一部分行）。
- 用内核更新 $C$ 的相应子矩阵。

这里有一个 Jukka Suomela 制作的很好的[可视化演示](https://jukkasuomela.fi/cache-blocking-demo/)（里面展示了多种不同方法；你感兴趣的是最后一种）。

注意，选择从矩阵 $B$ 开始并不是随意的。在内核执行期间，我们读取 $A$ 元素的速度比 $B$ 元素慢得多：我们每次只取 $A$ 的一个元素并广播它，然后乘以 $B$ 的 $16$ 个元素。因此，我们希望 $B$ 在 L1 缓存中，而 $A$ 可以待在 L2 缓存里，而不是反过来。

它听起来很复杂，但我们只需再增加三个外层 `for` 循环就能实现，它们合称*宏内核*（macro-kernel）（而那个高度优化的、更新 6x16 子矩阵的底层函数称为*微内核*（micro-kernel））：

```c++
const int s3 = 64;  // how many columns of B to select
const int s2 = 120; // how many rows of A to select 
const int s1 = 240; // how many rows of B to select

for (int i3 = 0; i3 < ny; i3 += s3)
    // now we are working with b[:][i3:i3+s3]
    for (int i2 = 0; i2 < nx; i2 += s2)
        // now we are working with a[i2:i2+s2][:]
        for (int i1 = 0; i1 < ny; i1 += s1)
            // now we are working with b[i1:i1+s1][i3:i3+s3]
            // and we need to update c[i2:i2+s2][i3:i3+s3] with [l:r] = [i1:i1+s1]
            for (int x = i2; x < std::min(i2 + s2, nx); x += 6)
                for (int y = i3; y < std::min(i3 + s3, ny); y += 16)
                    kernel(a, (vec*) b, (vec*) c, x, y, i1, std::min(i1 + s1, n), ny);
```

缓存分块彻底消除了内存瓶颈：

![](../img/mm-blocked-barplot.svg)

性能不再（显著）受问题规模影响：

![](../img/mm-blocked-plot.svg)

注意 $1536$ 处的凹坑仍在：缓存组相联依然影响性能。为了缓解它，我们可以调整步长常量或在布局中打孔，但眼下我们不打算折腾这些。

## 优化

要更接近性能极限，我们还需要几项优化：

- 去掉内存分配，直接在传入函数的数组上操作。注意我们不需要对 `a` 做任何事，因为我们一次只读一个元素；对 `c` 我们可以使用[非对齐](/hpc/simd/moving/#aligned-loads-and-stores)的 `store`，因为我们很少用到它，所以唯一的顾虑是读取 `b`。
- 去掉 `std::min`，使大小参数（基本）保持常量，能被编译器嵌入机器码（这也让它能更高效地[展开](/hpc/architecture/loops/)微内核循环，并省去运行时检查）。
- 用手写 12 个向量变量的方式重写微内核（编译器似乎难以让它们保持待在寄存器里，会先把它们写到一个临时内存位置，再写回 $C$）。

这些优化直截了当但相当繁琐，所以我们不把[代码](https://github.com/sslotin/amh-code/blob/main/matmul/v5-unrolled.cc)列在这篇文章里。它还需要做更多工作才能有效支持「怪异」的矩阵大小，这也就是为什么我们只对 $48 = \frac{6 \cdot 16}{\gcd(6, 16)}$ 的倍数大小跑基准。

<!--

有效支持怪异的大小需要更多工作，这也是我们为什么只在能被 $48 = \frac{6 \cdot 16}{\gcd(6, 16)}$ 整除的数组大小上跑基准的原因。我们不列代码，因为改动很大且繁琐，还需要稍微修改基准测试代码本身。这很直截了当，但我们只实现了这一特定大小的版本，没有任何安全检查。在基准测试上作弊。

但避免搬动任何东西是值得的。

-->

这些单个的小改进叠加起来，又带来了 50% 的提升：

![](../img/mm-noalloc.svg)

其实我们离理论性能极限并不远——它可以用 SIMD 宽度乘以 `fma` 指令吞吐量再乘以时钟频率来计算：

$$
\underbrace{8}_{SIMD} \cdot \underbrace{2}_{thr.} \cdot \underbrace{2 \cdot 10^9}_{cycles/sec} = 32 \; GFLOPS \;\; (3.2 \cdot 10^{10})
$$

更有代表性的做法是和某个实用库比较，比如 [OpenBLAS](https://www.openblas.net/)。最省事的办法就是直接从 [NumPy 调用矩阵乘法](/hpc/complexity/languages/#blas)。中间可能会有一点 Python 带来的开销，但最终它达到了理论极限的 80%，这看起来是合理的（20% 的开销可以接受：CPU 又不是只用来做矩阵乘法）。

![](../img/mm-blas.svg)

我们达到了 BLAS 性能的约 93% 和理论性能极限的约 75%，对于本质上只有 40 行 C 的代码来说已经很棒了。

有趣的是，整个东西可以卷进一个高度嵌套的 `for` 循环中，并获得 BLAS 级别的性能（假设我们身处 2050 年、使用终于不再搞砸寄存器溢出的 GCC 35）：

```c++
for (int i3 = 0; i3 < n; i3 += s3)
    for (int i2 = 0; i2 < n; i2 += s2)
        for (int i1 = 0; i1 < n; i1 += s1)
            for (int x = i2; x < i2 + s2; x += 6)
                for (int y = i3; y < i3 + s3; y += 16)
                    for (int k = i1; k < i1 + s1; k++)
                        for (int i = 0; i < 6; i++)
                            for (int j = 0; j < 2; j++)
                                c[x * n / 8 + i * n / 8 + y / 8 + j]
                                += (vec{} + a[x * n + i * n + k])
                                   * b[n / 8 * k + y / 8 + j];
```

还有一种渐近上做更少算术运算的方法——[Strassen 算法](/hpc/external-memory/oblivious/#strassen-algorithm)——但它的常数因子很大，只对[非常大的矩阵](https://arxiv.org/pdf/1605.01078.pdf)（$n > 4000$）才高效，而那时我们通常本来就不得不用多进程或某种近似的降维方法。

## 推广

FMA 也支持 64 位浮点数，但不支持整数：你得分开执行加法和乘法，这会导致性能下降。如果你能保证所有中间结果都能精确表示为 32 位或 64 位浮点数（这[常常是成立的](/hpc/arithmetic/errors/)），那么把它们转换成浮点数再转回来可能反而更快。

这种方法也能应用到一些看起来相似的运算上。一个例子是「min-plus 矩阵乘法」，定义为：

$$
(A \circ B)_{ij} = \min_{1 \le k \le n} (A_{ik} + B_{kj})
$$

它也被称为「距离乘积」，源于它的图解释：把它自己与自己做 $(D \circ D)$，结果就是由边权矩阵 $D$ 指定的全连通带权图中所有顶点对之间长度为二的路径矩阵。

关于距离乘积的一个酷地方是，如果我们迭代这个过程并计算

$$
D_2 = D \circ D \\
D_4 = D_2 \circ D_2 \\
D_8 = D_4 \circ D_4 \\
\ldots
$$

……就能在 $O(\log n)$ 步内找到所有点对的最短路径：

```c++
for (int l = 0; l < logn; l++)
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++)
                d[i][j] = min(d[i][j], d[i][k] + d[k][j]);
```

这需要 $O(n^3 \log n)$ 次运算。如果按特定的顺序做这些两段松弛，我们只需一遍就能完成，这就是著名的 [Floyd–Warshall 算法](https://en.wikipedia.org/wiki/Floyd%E2%80%93Warshall_algorithm)：

```c++
for (int k = 0; k < n; k++)
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            d[i][j] = min(d[i][j], d[i][k] + d[k][j]);
```

有意思的是，类似地向量化距离乘积并执行 $O(\log n)$ 次（[或可能更少](https://arxiv.org/pdf/1904.01210.pdf)），总共 $O(n^3 \log n)$ 次运算，反而比朴素地执行 $O(n^3)$ 次运算的 Floyd–Warshall 算法更快，尽管快得不多。

作为练习，试着加速这个「for-for-for」计算。它比矩阵乘法的情况更难，因为现在迭代之间存在逻辑依赖，你需要按特定顺序执行更新；但仍然可以设计[一个类似的内核和块迭代顺序](https://github.com/sslotin/amh-code/blob/main/floyd/blocked.cc)，获得总计 30–50 倍的加速。

## 致谢

最终算法最初由 Kazushige Goto 设计，它是 GotoBLAS 和 OpenBLAS 的基础。作者本人在《[Anatomy of High-Performance Matrix Multiplication](https://www.cs.utexas.edu/~flame/pubs/GotoTOMS_revision.pdf)》中更详细地描述了它。

讲解风格受 Jukka Suomela 的「[Programming Parallel Computers](http://ppc.cs.aalto.fi/)」课程启发，该课程有一个[类似的加速距离乘积的案例研究](http://ppc.cs.aalto.fi/ch2/)。
