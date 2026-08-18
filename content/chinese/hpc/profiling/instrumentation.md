---
title: 插桩
weight: 1
published: true
---

<!-- Linux 中的 pv、管道 -->

*插桩（instrumentation）*是一个听起来很复杂的术语，意思是在程序中插入计时器和其他跟踪代码。最简单的例子就是在类 Unix 系统中使用 `time` 工具来测量整个程序的执行时长。

更一般地，我们想知道程序的*哪些部分*需要优化。编译器和 IDE 自带一些工具，可以自动为指定函数计时，但更稳妥的做法是手动完成：使用语言提供的任何与时间交互的方法。

```cpp
clock_t start = clock();
do_something();
float seconds = float(clock() - start) / CLOCKS_PER_SEC;
printf("do_something() took %.4f", seconds);
```

这里有一个微妙之处：你无法用这种方式测量特别快的函数的执行时间，因为 `clock` 函数以微秒（$10^{-6}$ 秒）为单位返回当前时间戳，而且它本身执行完就要花费最多几百纳秒。所有其他与时间相关的工具同样至少具有微秒级的分辨率，而在底层优化的世界里，这简直是一段永恒。

为了获得更高的精度，你可以在循环中反复调用该函数，只计时一次整个过程，然后把总时间除以迭代次数：

```cpp
#include <stdio.h>
#include <time.h>

const int N = 1e6;

int main() {
    clock_t start = clock();

    for (int i = 0; i < N; i++)
        clock(); // benchmarking the clock function itself

    float duration = float(clock() - start) / CLOCKS_PER_SEC;
    printf("%.2fns per iteration\n", 1e9 * duration / N);

    return 0;
}
```

你还需要确保没有任何东西被缓存、被编译器优化掉，或受到类似的副作用影响。这是一个独立且非常复杂的话题，我们将在[本章末尾](../benchmarking)更详细地讨论。

### 事件采样

插桩还可以用来收集其他类型的信息，为特定算法的性能提供有用的洞见。例如：

- 对于哈希函数，我们关心其输入的平均长度；
- 对于二叉树，我们关心它的大小和高度；
- 对于排序算法，我们想知道它做了多少次比较。

类似地，我们可以在代码中插入计数器来计算这些算法特有的统计量。

添加计数器有引入开销的缺点，不过你可以只对一小部分调用随机地执行统计，几乎完全消除这个缺点：

```c++
void query() {
    if (rand() % 100 == 0) {
        // update statistics
    }
    // main logic
}
```

如果采样率足够小，每次调用剩下的唯一开销就是随机数生成和一次条件检查。有趣的是，我们可以借助一点统计学的魔法进一步优化它。

从数学上看，我们在这里做的是反复从[伯努利分布](https://en.wikipedia.org/wiki/Bernoulli_distribution)中采样（$p$ 等于采样率），直到抽中一次成功。还有另一种分布，它告诉我们需要多少次伯努利采样才能等到第一次成功，称为[几何分布](https://en.wikipedia.org/wiki/Geometric_distribution)。我们可以改为从它采样，并把得到的值用作递减计数器：

```c++
void query() {
    static next_sample = geometric_distribution(sample_rate);
    if (next_sample--) {
        next_sample = geometric_distribution(sample_rate);
        // ...
    }
    // ...
}
```

这样我们就不必在每次调用时都采样一个新的随机数，只在选择计算统计量时才重置计数器。

类似的技术经常被大型项目中的库算法开发者用来收集剖析数据，而不会过多影响最终程序的性能。