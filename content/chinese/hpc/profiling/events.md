---
title: 统计剖析
weight: 2
---

[插桩](../instrumentation)是一种相当繁琐的剖析方式，尤其是当你关心程序中的多个小片段时。即使工具能部分自动化它，由于其固有的开销，它仍然无法帮你收集细粒度的统计数据。

另一种侵入性更小的剖析方法是：在随机的间隔中断程序的执行，看看指令指针停在哪里。指针停在每个函数代码块中的次数，大致正比于执行这些函数所花的总时间。你还可以用这种方式获得一些其他有用信息，比如通过检查[调用栈](/hpc/architecture/functions)找出哪些函数被哪些函数调用。

原则上，这可以简单地用 `gdb` 运行程序并在随机间隔按 `ctrl+c` 来实现，但现代 CPU 和操作系统为此类剖析提供了专门的工具。

### 硬件事件

硬件*性能计数器（performance counter）*是内置于微处理器中的特殊寄存器，可以保存某些与硬件相关的活动的计数。在微芯片上添加它们的成本很低，因为它们基本上就是带有激活引线的二进制计数器。

每个性能计数器都连接到一大片电路子集，可以配置为在某个特定的硬件事件（如分支预测失败或缓存未命中）发生时递增。你可以在程序开始时重置计数器、运行它、在结束时输出其中保存的值，它就等于整个执行过程中某个事件被触发的精确次数。

你还可以通过在多个事件之间进行多路复用（multiplexing）来同时跟踪多个事件，也就是按固定间隔暂停程序并重新配置计数器。这种情况下结果并不精确，而是统计近似。这里有一个微妙之处：不能简单地通过提高采样频率来提高精度，因为那样会过多地影响性能，从而扭曲分布；所以为了收集多项统计量，你需要把程序运行更长时间。

总的来说，事件驱动的统计剖析通常是诊断性能问题最有效、最简便的方式。

### 用 perf 进行剖析

依赖上述事件采样技术的性能分析工具称为*统计剖析器（statistical profiler）*。这类工具很多，但本书主要使用的是随 Linux 内核发布的 [perf](https://perf.wiki.kernel.org/)，它正是一个统计剖析器。在非 Linux 系统上，你可以使用英特尔的 [VTune](https://software.intel.com/content/www/us/en/develop/tools/oneapi/components/vtune-profiler.html#gs.cuc0ks)，就我们的用途而言，它提供的功能大致相同。它是免费的，不过是专有软件，而且你需要每 90 天续期一次社区许可证；而 perf 则是自由软件意义上的免费。

Perf 是一个命令行应用程序，基于程序的实时执行生成报告。它不需要源代码，可以剖析非常广泛的应用程序，甚至包括涉及多进程、与操作系统交互的程序。

为了便于讲解，我写了一个小程序：它创建一个包含一百万个随机整数的数组，对其排序，然后对它做一百万次二分查找：

```c++
void setup() {
    for (int i = 0; i < n; i++)
        a[i] = rand();
    std::sort(a, a + n);
}

int query() {
    int checksum = 0;
    for (int i = 0; i < n; i++) {
        int idx = std::lower_bound(a, a + n, rand()) - a;
        checksum += idx;
    }
    return checksum;
}
```

编译它（`g++ -O3 -march=native example.cc -o run`）之后，我们可以用 `perf stat ./run` 运行它，它会输出执行期间基本性能事件的计数：

```yaml
 Performance counter stats for './run':

        646.07 msec task-clock:u               # 0.997 CPUs utilized          
             0      context-switches:u         # 0.000 K/sec                  
             0      cpu-migrations:u           # 0.000 K/sec                  
         1,096      page-faults:u              # 0.002 M/sec                  
   852,125,255      cycles:u                   # 1.319 GHz (83.35%)
    28,475,954      stalled-cycles-frontend:u  # 3.34% frontend cycles idle (83.30%)
    10,460,937      stalled-cycles-backend:u   # 1.23% backend cycles idle (83.28%)
   479,175,388      instructions:u             # 0.56  insn per cycle         
                                               # 0.06  stalled cycles per insn (83.28%)
   122,705,572      branches:u                 # 189.925 M/sec (83.32%)
    19,229,451      branch-misses:u            # 15.67% of all branches (83.47%)

   0.647801770 seconds time elapsed
   0.647278000 seconds user
   0.000000000 seconds sys
```

可以看到，执行耗时 0.53 秒，即 852M 个周期，有效时钟频率为 1.32 GHz，期间执行了 479M 条指令。还有 122.7M 次分支，其中 15.7% 预测失败。

你可以用 `perf list` 获取所有支持的事件列表，然后用 `-e` 选项指定你想要的具体事件列表。例如，诊断二分查找时，我们主要关心缓存未命中：

```yaml
> perf stat -e cache-references,cache-misses ./run

91,002,054      cache-references:u                                          
44,991,746      cache-misses:u      # 49.440 % of all cache refs
```

`perf stat` 本身只是为整个程序设置性能计数器。它能告诉你分支预测失败的总次数，但不会告诉你它们发生在*哪里*，更不用说*为什么*会发生。

要尝试我们之前讨论的“暂停世界（stop-the-world）”方法，我们需要使用 `perf record <cmd>`，它会记录剖析数据并转储为 `perf.data` 文件，然后调用 `perf report` 来查看它。我强烈建议你们亲自去试一试，因为后一个命令是交互式且带颜色的，不过对于现在无法尝试的人，我会尽力描述它。

当你调用 `perf report` 时，它首先显示一个类似 `top` 的交互式报告，告诉你哪些函数占用了多少时间：

```
Overhead  Command  Shared Object        Symbol
  63.08%  run      run                  [.] query
  24.98%  run      run                  [.] std::__introsort_loop<...>
   5.02%  run      libc-2.33.so         [.] __random
   3.43%  run      run                  [.] setup
   1.95%  run      libc-2.33.so         [.] __random_r
   0.80%  run      libc-2.33.so         [.] rand
```

注意，对每个函数，列表里只给出它自己的*开销（overhead）*，而不是总运行时间（例如，`setup` 包含 `std::__introsort_loop`，但它只把自己的开销记为 3.43%）。有一些工具可以把 perf 报告构建成[火焰图（flame graph）](https://www.brendangregg.com/flamegraphs.html)使其更直观。你还需要考虑可能的内联，这里的 `std::lower_bound` 显然就是被内联了。Perf 还会跟踪共享库（如 `libc`），以及一般的其他任何衍生进程：如果你愿意，可以用 perf 启动一个浏览器，看看里面发生了什么。

接下来，你可以“放大”这些函数中的任意一个，它会（除了其他功能外）提供显示其反汇编及对应热力图的功能。例如，下面是 `query` 的汇编：

```asm
       │20: → call   rand@plt
       │      mov    %r12,%rsi
       │      mov    %eax,%edi
       │      mov    $0xf4240,%eax
       │      nop    
       │30:   test   %rax,%rax
  4.57 │    ↓ jle    52
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
       │52:   sub    %r12,%rsi
  2.22 │      sar    $0x2,%rsi
  0.33 │      add    %esi,%ebp
  0.20 │      dec    %ebx
       │    ↑ jne    20
```

左列是指令指针停在某一行上的次数占比。可以看到，我们约 65% 的时间花在跳转指令上，因为它前面有一个比较操作，说明控制流在那里等待这个比较得出结果。

由于[流水线](/hpc/pipelining)和乱序执行等复杂机制，“现在”在现代 CPU 中并不是一个定义良好的概念，因此指令指针会稍微向前漂移，数据会有轻微失真。指令级数据仍然有用，但要精确到单个周期，我们得改用[更精确的工具](../simulation)。

<!-- 火焰图 -->