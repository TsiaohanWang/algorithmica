---
title: 向量化
draft: true
---

考虑下面这个算一维整数数组和的程序：

```c++
#pragma GCC optimize("O3")
// ^ 开启最"激进"的优化级别
// 等价于命令行编译时加 "-O3" 标志

#include <iostream>
using namespace std;

const int n = 1e5;
int a[n], s = 0;

int main() {
    for (int t = 0; t < 100000; t++)
        for (int i = 0; i < n; i++)
            s += a[i];

    return 0;
}
```

若在 GCC 下不做额外设置编译并运行，耗时 2.43 秒。

现在在程序最开头加这条魔法指令：

```c++
#pragma GCC target("avx2")
// ...其余与之前完全一样
```

同样条件下编译运行，程序 1.24 秒完成。几乎快一倍，而代码和优化级别都没改。

为理解发生了什么，需要先说明现代计算机的一些工作特点。（懂汇编的读者可快进到约 ⅓ 处。）

## Complex Instruction Set Computing

从前，当计算机叫 ЭВМ、占整整一间房时，性能提升主要靠提高时钟频率。时钟频率近似等于处理器单位时间执行的指令数。（现代处理器[并非如此](http://ithare.com/infographics-operation-costs-in-cpu-clock-cycles/)——不同指令耗时不同，且还可能依赖不同情形。）

除了[光速](https://ru.wikipedia.org/wiki/%D0%A1%D0%BA%D0%BE%D1%80%D0%BE%D1%81%D1%82%D1%8C_%D1%81%D0%B2%D0%B5%D1%82%D0%B0)对最大时钟频率的硬[物理限制](https://ru.wikipedia.org/wiki/%D0%A1%D0%BA%D0%BE%D1%80%D0%BE%D1%81%D1%82%D1%8C_%D1%81%D0%B2%D0%B5%D1%82%D0%B0)，这种思路某刻也不再有经济价值：直接提频导致超线性功耗增长，进而发热，而热还得排出去。

因此厂商为追求更便宜的每美元[flops](https://en.wikipedia.org/wiki/FLOPS)，走了另一条路：加入更复杂、一次做很多有用事情的指令。缺点：加入新指令使芯片严重复杂化，在许多其他应用里可能致命。于是所有架构分成两类：

* [RISC](https://en.wikipedia.org/wiki/Reduced_instruction_set_computer)（英文 **reduced** instruction set computer），其中指令自身的码长（标识符）受限，因此指令数也受限。最早的计算机属此类，甚至可能没有乘除指令。这类处理器需要更少晶体管，因而更小、更便宜、更省电。最流行的架构族叫 [arm](https://en.wikipedia.org/wiki/ARM_architecture)，几乎所有现代移动设备都用。

* [CISC](https://en.wikipedia.org/wiki/Complex_instruction_set_computer)（英文 **complex** instruction set computer），指一切非 RISC——指令长度不固定，可支持几乎任意指令数。最流行架构族叫 [x86](https://en.wikipedia.org/wiki/X86)，几乎所有现代台式机和服务器都用。

![](https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Mips32_addi.svg/370px-Mips32_addi.svg.png)

新指令逐渐加入，且按应用领域各异。

* 普通 CPU 很快加入一条指令：接收数 $(x, y)$，按地址 $a \cdot x + y$ 把数据装入寄存器。这在数组索引时有用——不必单独算下标。

* 图形协处理器出现独立指令「saxpy」（`s += a * x + y` 的缩写），例如在矩阵乘法时有用。

* Nvidia 最新 GPU 加了「tensor core」——单独电路一次乘两个 $4 \times 4$ 矩阵并加到第三个，相当于一次做 $4 \times 4 \times 4 = 64$ 次乘法与 $4 \times 4 = 16$ 次加法，极大加速[分块矩阵乘法](https://en.wikipedia.org/wiki/Strassen_algorithm)。

本文聚焦一种特殊指令：能一次对某段数据执行同一个操作。这概念叫 [SIMD](https://en.wikipedia.org/wiki/SIMD) 并行（英文 *single instruction, multiple data*）。

## Streaming SIMD Extensions

SSE 是 x86 所有 SIMD 指令的统称。

它们这样工作：除普通寄存器（离处理器最近、它直接操作的内存单元）外，还有额外寄存器，容纳的不是 64 而是 128、256 甚至 512 位——取决于支持的 SSE 版本。往这些寄存器载入内存连续块，对其做一串操作，结果写回内存。操作本身通常逻辑上把这个布尔序列按例如 32 位分成块，再同时处理。

![](https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/SIMD.svg/1200px-SIMD.svg.png)

这样容易优化对向量（数组）做彼此独立操作的简单循环——因此这方法叫*向量化*。

例如，两个 int 数组相加能优化 $\frac{512}{32} = 16$ 倍（若处理器支持 AVX512）；[bitset](bitset) 操作 512 倍（STL 实现[看来](https://github.com/gcc-mirror/gcc/blob/master/libstdc%2B%2B-v3/include/std/bitset#L77)不用 SSE，所以连 `c = a | b` 也比遍历 int 数组的 `for` 慢约三倍）。

SSE 常用来处理实数，此时出现计算精度与速度的直接权衡：例如可用 float 代替 double，同一寄存器能放两倍多的数。因此近来各种[量化](https://en.wikipedia.org/wiki/Quantization)方法兴起：把输入数据在某过程（如[矩阵乘法](https://github.com/google/gemmlowp)）入口转成更离散的格式，出口再恢复原格式。

具体指令集与寄存器大小取决于厂商和架构代次。截至现在（2019 夏）[多数](https://www.cpubenchmark.net/market_share.html)x86 处理器由 Intel 生产，因此聚焦他们的指令集。

![](https://i0.wp.com/www.urtech.ca/wp-content/uploads/2017/11/Intel-mmx-sse-sse2-avx-AVX-512.png)

SIMD 指令支持逐渐加入、保持向后兼容。1999 年第三代奔腾能处理 128 位寄存器，最新 i7 有 512 位寄存器。作者不是微处理器设计专家，但猜测超过 64 字节（512 位）的寄存器不会很快出现，因为已超过[缓存行](https://en.wikipedia.org/wiki/CPU_cache)大小。

为让开发者不必为每种架构提供单独优化二进制，处理器指令集支持信息编进汇编指令 `cpuid`，可在运行时调用全部获知：[例如这样](https://gist.github.com/hi2p-perim/7855506)。

GCC 有内建函数 `__builtin_cpu_supports`，接受指令集名字符串（"sse"、"avx2"、"avx512f" 等）返回整数——零或某个 2 的幂。它这样工作：输入字符串在编译期转成相应 2 的幂，运行时与 cpuid 的掩码 AND 并返回——全为效率。

```c++
#include <iostream>
using namespace std;

int main() {
    cout << __builtin_cpu_supports("sse") << endl;
    cout << __builtin_cpu_supports("sse2") << endl;
    cout << __builtin_cpu_supports("avx") << endl;
    cout << __builtin_cpu_supports("avx2") << endl;
    cout << __builtin_cpu_supports("avx512f") << endl;

    return 0;
}
```

省读者时间：CodeForces 服务器与多数在线评测在写本文时支持 AVX2，即能完整处理 256 位寄存器。

## C++ intrinsics

SSE 是纯汇编指令。任何更高[抽象层](https://en.wikipedia.org/wiki/Java_virtual_machine)的语言都无法直接操作。但不必写纯汇编来用它们——编译器开发者已替你做，做出内建包装函数，叫*内建函数*（英文 *intrinsic*——「内部的」）。

要使用，需 `include` 相应头文件，并告诉编译器想用某个或某几个指令集。文章开头例子正是这么做的：写 `target("avx2")`——编译器获得更宽寄存器与相应高级指令，能把程序优化约两倍（默认启用 128 位 `sse` 和 `sse2`，所以是 2 而非 $\frac{256}{32} = 8$）。

类比 `<bits/stdc++.h>`，GCC 有类似头文件 `<x86intrin.h>`，一次包含全部 SSE intrinsics。喜欢污染命名空间、编译极慢的人可用：

```c++
#pragma GCC target("avx2")
#pragma GCC optimize("O3")

#include <x86intrin.h>
#include <bits/stdc++.h>

using namespace std;
```

**例子。** 把两个 64 位实数组相加的简单循环，用 SSE intrinsics 写：

```c++
double a[100], b[100], c[100];

for (int i = 0; i < 100; i += 4) {
    // 把两个 256 位段装入各自寄存器
    __m256d x = _mm256_loadu_pd(&a[i]);
    __m256d y = _mm256_loadu_pd(&b[i]);
    // - 256 表示寄存器大小
    // - d 表示 "double"
    // - pd 表示 "packed double"

    // 求和并把结果放另一寄存器：
    __m256d z = _mm256_add_pd(x, y);
    // 把寄存器内容写进内存：
    _mm256_storeu_pd(&c[i], z);
}
```

若数组大小不是寄存器大小的倍数，程序可能不正确。此时二选一：

1. 在数组末尾加「中性」元素，补到方便长度。

2. 用 SSE 处理能处理的数量，剩余单独处理。

例如这样算任意大小数组的和：

```c++
int sum(int a[], int n) {
    int res = 0;

    // 建存 8 个当前和的寄存器
    __m256i x = _mm256_setzero_si256();
    for (int i = 0; i + 8 < n; i += 8) {
        __m256i y = _mm256_loadu_si256((__m256i*) &a[i]);
        x = _mm256_add_epi32(x, y);
    }

    // 把寄存器中 8 个数加成一个
    int *b = (int*) &x;
    for (int i = 0; i < 8; i++)
        res += b[i];

    // 加数组剩余部分
    for (int i = (n / 8) * 8; i < n; i++)
        res += a[i];

    return res;
}
```

**命令名。** 多数命令编码为 `_mm<维度>_<动作>_<类型>`。

另几个例子：

* `_mm_add_epi16`——加两组 16 位 *extended packed integer*，即 $\frac{128}{16} = 8$ 个 `short`（未标寄存器大小的指令，其大小为 128）。

* `_mm256_acos_pd`——接收一个含 4 个 `double` 的寄存器，返回它们的反余弦。

* `_mm256_broadcast_sd`——把内存中的 `double` 广播（复制）到寄存器四个槽。

* `_mm256_ceil_pd`——把 `double` 向上取整到最近 `int`。

* `_mm256_cmpeq_epi32`——比较打包 `int`，返回掩码向量，完全匹配的元素处有 32 个 1。

* `_mm256_blendv_ps`——按给定掩码取第一或第二数组的值。常用于替代 `if`。

组合起来函数极多。完整文档——[Intel Intrinsics Guide](https://software.intel.com/sites/landingpage/IntrinsicsGuide/)——在每位有自尊的性能工程师浏览器书签里。

**对齐。** 单独提一点：读写操作各有两版——`load` / `loadu` 与 `store` / `storeu`。字母「u」表示「unaligned」（英文 *未对齐*）。前者只在整个读取块落进一条缓存行时才正确（否则运行时触发 segfault），而 unaligned 版总是工作。

有时尤其当操作「轻」时，这个区别影响很大——若无法「对齐」内存，性能可能骤降（至少因为要加载两条缓存行而非一条）。

例如，这样加两个数组：

```c++
void aplusb_unaligned() {
    for (int i = 3; i + 7 < n; i += 8) {
        __m256i x = _mm256_loadu_si256((__m256i*) &a[i]);
        __m256i y = _mm256_loadu_si256((__m256i*) &b[i]);
        __m256i z = _mm256_add_epi32(x, y);
        _mm256_storeu_si256((__m256i*) &c[i], z);
    }
}
```

...会比这样慢 30%：

```c++
void aplusb_aligned() {
    for (int i = 0; i < n; i += 8) {
        __m256i x = _mm256_load_si256((__m256i*) &a[i]);
        __m256i y = _mm256_load_si256((__m256i*) &b[i]);
        __m256i z = _mm256_add_epi32(x, y);
        _mm256_store_si256((__m256i*) &c[i], z);
    }
}
```

若假设第一版数组起点与缓存行起点重合、缓存行 64 字节，那么约一半 `loadu` 与 `storeu` 是「坏的」。

手工把数组内存「对齐」以便用 `load` 顺序读取，可这样做：

```c++
alignas(32) float a[n];

for (int i = 0; i < n; i += 8) {
    __m256 x = _mm256_load_ps(&a[i]);
    // ...
}
```

数组起点指针现在是 32 字节的倍数，即 sse 块大小。于是任何读写保证在缓存行内。

**类型化。** 其实用 intrinsics 加载、保存数据乃至用 `__m` 类型都不是必须——都能用普通 reinterpret_cast 完成。所有数据格式相同，不同类型只是为类型检查、避免相关错误。

对每种寄存器维度有 3 种类型。以 AVX 为例：`__m256` 用于 `float`、`__m256d` 用于 `double`、`__m256i` 用于各种 `int`。

有些操作只对某一类型存在（例如 `_mm256_blendv_ps` 没有 32 位 `int` 对应），但用其他类型完全一样。因此要让编译器满意，需对其做类型转换，这不会在运行时花额外指令。它们都是这种格式：`_mm<维度>_cast<来源>_<去向>`。

**Loop unrolling。** 加 `unroll-loops` 标志（或 pragma：`#pragma GCC optimize("unroll-loops")`）让编译器做循环[「展开」](https://en.wikipedia.org/wiki/Loop_unrolling)，即把形如

```c++
for (int i = 1; i < n; i++)
    a[i] = (i % b[i]);
```

...变成这样：

```c++
int i;
for (i = 1; i < n - 3; i += 4) {
    a[i] = (i % b[i]);
    a[i + 1] = ((i + 1) % b[i + 1]);
    a[i + 2] = ((i + 2) % b[i + 2]);
    a[i + 3] = ((i + 3) % b[i + 3]);
}

for (; i < n; i++)
    a[i] = (i % b[i]);
```

这种技术能大幅加速重算指示器与循环体时间相当、但指令数增加多的轻循环。它不总有用：二进制会更大，且若指令缓存容量不够，循环效率甚至可能显著下降。

## 非平凡例子

假设需要把 $10^8$ 个数取某些次幂。

比较两个解：普通与向量化。用如下代码测试：

```c++
#pragma GCC optimize("O3")
#pragma GCC target("avx2")

#include <x86intrin.h>
#include <bits/stdc++.h>

using namespace std;

typedef unsigned long long ull;
typedef __m256i reg;

const int n = 1e8;
alignas(32) unsigned bases[n], results[n], powers[n];

void timeit(void (*f)()) {
    // 运行另一函数并测其执行时间
    clock_t start = clock();
    f();
    cout << double(clock() - start) / CLOCKS_PER_SEC << endl;

    for (int i = 0; i < 10; i++)
        cout << results[i] << " ";
    cout << endl;
}

int main() {
    for (int i = 0; i < n; i++) {
        bases[i] = rand();
        powers[i] = rand();
    }

    // timeit(binpow_simple);
    // timeit(binpow_sse);

    return 0;
}
```

SSE 里除 `int` 很麻烦（见下方注），因此都按模 $2^{32}$ 算，即自然让 `unsigned int` 溢出。

写标准迭代快速幂：

```c++
void binpow_simple() {
    for (int i = 0; i < n; i++) {
        unsigned a = bases[i], p = powers[i];

        unsigned res = 1;
        while (p > 0) {
            if (p & 1)
                res = (res * a);
            a = (a * a);
            p >>= 1;
        }

        results[i] = res;
    }
}
```

这代码 9.47 秒。

现在试向量化版本：

```c++
void binpow_sse() {
    const reg ones = _mm256_set_epi32(1, 1, 1, 1, 1, 1, 1, 1);
    for (int i = 0; i < n; i += 8) {
        reg a = _mm256_load_si256((__m256i*) &bases[i]);
        reg p = _mm256_load_si256((__m256i*) &powers[i]);
        reg res = ones;

        // 其实这里不会有循环
        // -- 编译器会把它展开成 32 个独立操作块
        for (int i = 0; i < 32; i++) {
            // 为不写 if，为每个元素算它的因子：
            // 视 p 最低位的值，因子是 1 或 a
            // 需要乘 a 的元素的掩码：
            reg mask = _mm256_cmpeq_epi32(_mm256_and_si256(p, ones), ones);
            // 按掩码混合两个向量：
            reg mul = _mm256_blendv_epi8(ones, a, mask);
            // res *= mul:
            res = _mm256_mullo_epi32(res, mul);
            // a *= a:
            a = _mm256_mullo_epi32(a, a);
            // p >>= 1:
            p = _mm256_srli_epi32(p, 1);
        }

        _mm256_store_si256((__m256i*) &results[i], res);
    }
}
```

这个实现 0.7 秒——快 13.5 倍。而且还有可优化的地方。

## 自动向量化的困难

文章开头给出一个只加目标编译头就得到优化二进制的例子。那程序员为何还要做别的？

因为有时——非常罕见——程序员确实比编译器聪明，因为他略多知道任务。

看这个例子，去掉多余部分：

```c++
void sum(int a[], int b[], int c[], int n) {
    for (int i = 0; i < n; i++)
        c[i] = a[i] + b[i];
}
```

为何不能自动把它换成向量化版本？

第一，因为这不总正确。假设 `a[]` 与 `c[]` 相交，且数组起点指针相差 1–2 个位置。也许我们正想用这种精巧卷积算斐波那契序列。那么 simd 块中数据会相交，观察到行为会完全不是我们想要的。

第二，我们对数组对齐一无所知，可能在此损失性能（对大循环无所谓——编译器把两个「边缘」用单独循环处理）。

其实，当编译器怀疑函数会用于大循环时，在高优化级别它会自己插入这些情形的运行时检查、生成两个版本：SSE 版与「安全」版。

但不想在运行时做这些检查，因此可告诉编译器我们确信不会坏：

```c++
#pragma GCC ivdep
for (int i = 0; i < n; i++)
    // ...
```

这里「ivdep」指 **i**gnore **v**ector **dep**endencies——循环内数据互不依赖。

还有[很多其他方式](https://software.intel.com/sites/default/files/m/4/8/8/2/a/31848-CompilerAutovectorizationGuide.pdf)暗示编译器我们的意图，但复杂情形——循环里有 `if` 或调用外部函数——降到 intrinsics 层自己写更简单。

## Gather 和 scatter

长期以来优化的一大障碍是：要对数据用 SIMD 指令，得先把它们集中到一个寄存器里，这在某些情形比向量化收益还贵——例如稀疏矩阵乘法。

为加速，AVX2 加了新的一类操作：gather 与 scatter。前者接受内存位置指针、按正确顺序把内容载入所需寄存器；后者相反——接受寄存器值、写入指定内存位置。

![](https://gainperformance.files.wordpress.com/2017/06/indexed_gather_scatter3.png)

这些操作带来显著加速，但注意它们不是 8 倍、甚至不是常数倍快，因为它们不只受处理器还受内存限制。

我们竞赛选手对稀疏线性代数兴趣不大，因此看另一个非连续内存的启发例子：优化[树状数组](fenwick)。这次不写 intrinsics，完全靠自动向量化。

```cpp
#pragma GCC optimize("03")
#pragma GCC target("avx2")

#include <bits/stdc++.h>
using namespace std;

const int logn = 20;
const int n = (1<<logn), m = 1e5;
int t[n], q[m], res[m], rs[m];
//  ^ 树状数组、查询、结果

int sum(int r) {
    int res = 0;
    for (; r > 0; r -= r & -r)
        res += t[r];
    return res;
}

void simple_fenwick() {
    for (int i = 0; i < m; i++)
        res[i] = sum(q[i]);
}

void vectorized_fenwick() {
    memcpy(rs, q, sizeof q);
    
    // 同样的树状数组循环，只是沿查询走；
    // 不用条件停止，循环执行 logn 次，
    // 其中最后若干次迭代什么都不改
    for (int l = 0; l < logn; l++) {
        for (int i = 0; i < m; i++) {
            int x = rs[i];  // 会被换成 gather
            res[i] += t[x]; // 会被换成 add
            x -= (x & -x);  // 会被换成另外 3 个操作
            rs[i] = x;      // 会被换成 storeu
        }
    }
    // 因 (x & -x) 等于末位、t[0] 为 0，算法正确，
    // 虽然平均一半操作白做
}

void timeit(void (*f)()) {
    clock_t start = clock();
    for (int i = 0; i < 1000; i++)
        f();
    cout << double(clock() - start) / CLOCKS_PER_SEC << endl;
}

int main() {
    for (int i = 0; i < m; i++)
        q[i] = rand() % n;

    timeit(simple_fenwick);
    timeit(vectorized_fenwick);

    return 0;
}
```

内存实验用不同结构大小总有趣：

* $n \approx 10^4$ 时向量化版本快约 4 倍。

* $n \approx 10^5$ 时向量化版本快约 3 倍。

* $n \approx 10^6$ 时向量化版本快约 2 倍。

* $n \approx 10^7$ 时向量化版本**慢**约 3 倍。

这些结果可解释为：$n$ 增大时结构开始装不进不同层缓存，更多取决于内存访问次数而非寄存器操作——向量化实现在此吃亏，因为平均做两倍于所需的访问。

$n \approx 10^7$ 时树状数组连 L3 都装不进，程序几乎每次访问 RAM——正因如此那里跳变如此显著。

## 杂项

**C++ 到汇编。** 这样查看生成指令：

```powershell
g++ -S program.cpp -o program.s
```

这能理解编译器是否已经向量化代码（向量指令名以字母 v 开头）。许多 IDE 有方便插件，能对特定函数查明这一点。

若指定标志 `-fopt-info-vec-optimized`，编译器会直接指出它成功向量化的操作：

```powershell
g++ -fopt-info-vec-optimized program.cpp -o run
```

可把 `optimized` 换成 `missed` 或 `all`，查看其他操作没能向量化的原因。

**打印向量。** 调试时这段代码有帮助：

```c++
template<typename T>
void print(T var) {
    unsigned *val = (unsigned*) &var;
    for (int i = 0; i < 4; i++)
        cout << bitset<32>(val[i]) << " ";
    cout << endl;
}
```

此处它输出 128 位向量中 4 组各 32 位。
