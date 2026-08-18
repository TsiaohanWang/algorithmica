---
title: 基准测试
weight: 6
---

大多数好的软件工程实践都在以这样或那样的方式解决同一个问题：让*开发周期*更快——你想更快地编译软件（构建系统）、尽快地发现 bug（静态分析、持续集成）、在新版本就绪后尽快发布（持续部署），以及毫不拖延地响应用户反馈（敏捷开发）。

性能工程也不例外。如果你做得正确，它也应该像一个循环：

1. 运行程序并收集指标。
2. 找出瓶颈在哪里。
3. 消除瓶颈，然后回到第 1 步。

本节我们将讨论基准测试，并介绍一些能让这个循环更短、帮助你更快迭代的实用技巧。大部分建议都来自编写本书的过程，因此你可以在本书的[代码仓库](https://github.com/sslotin/ahm-code)中找到许多所述方案的真实示例。

### 在 C++ 内部做基准测试

编写基准测试代码有好几种方法。也许最流行的一种是：把你想比较的几个同语言实现放进同一个文件，在 `main` 函数中分别调用它们，并在同一个源文件中计算你想要的所有指标。

这种方法的缺点是，你需要写大量样板代码，并且要为每个实现重复一遍，但元编程可以部分抵消这一点。例如，当你为多个 [gcd](/hpc/algorithms/gcd) 实现做基准测试时，借助下面这个高阶函数可以大幅精简测试代码：

```c++
const int N = 1e6, T = 1e9 / N;
int a[N], b[N];

void timeit(int (*f)(int, int)) {
    clock_t start = clock();

    int checksum = 0;

    for (int t = 0; t < T; t++)
        for (int i = 0; i < n; i++)
            checksum ^= f(a[i], b[i]);
    
    float seconds = float(clock() - start) / CLOCKS_PER_SEC;

    printf("checksum: %d\n", checksum);
    printf("%.2f ns per call\n", 1e9 * seconds / N / T);
}

int main() {
    for (int i = 0; i < N; i++)
        a[i] = rand(), b[i] = rand();
    
    timeit(std::gcd);
    timeit(my_gcd);
    timeit(my_another_gcd);
    // ...

    return 0;
}
```

这是一种开销非常低的方法，能让你运行更多实验，并从中[获得更准确的结果](../noise)。你仍然要做一些重复性操作，但这些大多可以用框架自动化，[Google benchmark 库](https://github.com/google/benchmark)是 C++ 中最流行的选择。有些编程语言还内置了方便的基准测试工具：这里要特别提一下 [Python 的 timeit 函数](https://docs.python.org/3/library/timeit.html)和 [Julia 的 @benchmark 宏](https://github.com/JuliaCI/BenchmarkTools.jl)。

尽管在运行速度上*高效*，但 C 和 C++ 并不是*生产力*最高的语言，尤其是在数据分析方面。当你的算法依赖于输入规模等参数、并且你需要从每个实现中收集的不止一个数据点时，你确实想把基准测试代码与外部环境集成起来，用别的工具分析结果。

### 拆分实现

提高模块化和可复用性的一种方法是：把所有测试和分析代码与算法的实际实现分开，并让不同版本实现在各自独立的文件中，但拥有相同的接口。

在 C/C++ 中，你可以创建一个头文件（例如 `gcd.hh`）来声明函数接口，并把所有基准测试代码放在 `main` 里：

```c++
int gcd(int a, int b); // to be implemented

// for data structures, you also need to create a setup function
// (unless the same preprocessing step for all versions would suffice)

int main() {
    const int N = 1e6, T = 1e9 / N;
    int a[N], b[N];
    // careful: local arrays are allocated on the stack and may cause stack overflow
    // for large arrays, allocate with "new" or create a global array

    for (int i = 0; i < N; i++)
        a[i] = rand(), b[i] = rand();

    int checksum = 0;

    clock_t start = clock();

    for (int t = 0; t < T; t++)
        for (int i = 0; i < n; i++)
            checksum += gcd(a[i], b[i]);
    
    float seconds = float(clock() - start) / CLOCKS_PER_SEC;

    printf("%d\n", checksum);
    printf("%.2f ns per call\n", 1e9 * seconds / N / T);
    
    return 0;
}
```

然后你为每个算法版本创建许多实现文件（例如 `v1.cc`、`v2.cc` 等等，或者起一些有意义的名字），它们都包含同一个头文件：

```c++
#include "gcd.hh"

int gcd(int a, int b) {
    if (b == 0)
        return a;
    else
        return gcd(b, a % b);
}
```

这样做的全部目的，就是能在命令行里对某个特定的算法版本做基准测试，而无需改动任何源代码文件。为此，你可能还想把算法可能拥有的参数暴露出来——例如，从命令行参数中解析它们：

```c++
int main(int argc, char* argv[]) {
    int N = (argc > 1 ? atoi(argv[1]) : 1e6);
    const int T = 1e9 / N;

    // ...
}
```

另一种做法是使用 C 风格的全局宏定义，然后在编译时通过 `-D N=...` 标志传入：

```c++
#ifndef N
#define N 1000000
#endif

const int T = 1e9 / N;
```

这样你就可以利用编译期常量，这对某些算法的性能可能非常有利；代价是每次想修改参数都必须重新构建程序，这会显著增加跨参数范围收集指标所需的时间。

### Makefile

<!-- TODO -->

拆分源文件后，你可以借助 [Make](https://en.wikipedia.org/wiki/Make_(software)) 这样的缓存构建系统来加速编译。

我通常在各个项目之间随身携带这样一个版本的 Makefile：

```c++
compile = g++ -std=c++17 -O3 -march=native -Wall

%: %.cc gcd.hh
	$(compile) $< -o $@ 

%.s: %.cc gcd.hh
	$(compile) -S -fverbose-asm $< -o $@

%.run: %
	@./$<

.PHONY: %.run
```

现在你可以用 `make example` 编译 `example.cc`，并用 `make example.run` 自动运行它。

你还可以在 Makefile 中添加用于计算统计量的脚本，或者把 `perf stat` 调用整合进去，让剖析自动化。

### Jupyter Notebook

为了加快高层数据分析，你可以创建一个 Jupyter notebook，把所有脚本放进去，并绘制所有图表。

为某个实现添加一个基准测试包装函数会很方便，它只需返回一个标量结果：

```python
def bench(source, n=2**20):
    !make -s {source}
    if _exit_code != 0:
        raise Exception("Compilation failed")
    res = !./{source} {n} {q}
    duration = float(res[0].split()[0])
    return duration
```

然后你就可以用它来写干净的分析代码：

```python
ns = list(int(1.17**k) for k in range(30, 60))
baseline = [bench('std_lower_bound', n=n) for n in ns]
results = [bench('my_binary_search', n=n) for n in ns]

# plotting relative speedup for different array sizes
import matplotlib.pyplot as plt

plt.plot(ns, [x / y for x, y in zip(baseline, results)])
plt.show()
```

一旦建立起来，这套工作流就能让你迭代快得多，并专注于优化算法本身。