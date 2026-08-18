---
title: GPU 编程
weight: 5
---

这是一个以 HTML 渲染的 Jupyter notebook。如果你想就在这里完成练习，在 [Colab]() 中打开它或[下载]()并在本地编辑。前一种情况下，你需要完成一点小小的任务并安装 CUDA 以及它的 Python 绑定 PyCuda。在基于 Debian 的机器上，下面这些大概就够了：
* `apt-get install nvidia-cuda-dev nvidia-cuda-toolkit`
* `pip install pycuda`

前置要求：Python 和 C 的基础知识、基础算法，以及计算机的基本工作原理。

## 摩尔定律的微妙之处

下面这张图大致反映了 CPU 界正在发生的事情：

<img width='600px' src='https://www.karlrupp.net/wp-content/uploads/2015/06/35years.png'>

**摩尔定律**是观察到的一个现象：微处理器中的晶体管数量大约每两年翻一番。这大致意味着性能也翻一番。

你可以看到，大约在 2005 年，设计上出现了一个转变。

这些核或多或少是相互独立的。

现代 GPU 出现在 2000 年代初。它们利用了它们所运行的特定领域。

核的速度存在物理极限。

一个确凿的极限：光速。你至少需要电磁波（光也是电磁波）从主板的一侧传到另一侧的时间。

其中一些拥有……

Google Colab 上默认的免费 GPU [相当强大](https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/tesla-t4/t4-tensor-core-datasheet-951643.pdf)。作者不知道为什么 Google 要这么做，但这太棒了。

## 为什么要多处理？

时钟频率——例如，Intel Core i7 可以达到……。这给出了一个上限

有两种类型……

## 通用 GPU

曾经有一段时间，对冲基金从游戏公司挖计算机图形工程师，因为他们会计算。

有几种……

这就像 Windows 和 Linux 的关系。

我们将坚持使用 CUDA，因为它更普及，尤其是在没人关心的领域，比如深度学习。

## 异构计算

CUDA 编程涉及在两个不同的平台上并发运行代码：一个带有一个或多个 CPU 的主机系统，以及一个或多个 GPU。

## 与 CPU 的差异

### 线程

CPU 上的线程通常是重量级的实体。操作系统必须在 CPU 执行通道上换入换出线程以提供多线程能力。因此上下文切换缓慢且代价高昂。

相比之下，GPU 上的线程极其轻量。在典型系统中，数千个线程排队等待工作——每 32 个线程组成一个 warp。如果 GPU 必须等待某个 warp 的线程，它会直接开始执行另一个 warp 的工作。由于所有活动线程都分配了独立的寄存器，在 GPU 线程之间切换时无需交换寄存器或其他状态。资源会一直分配给每个线程，直到它执行完毕。

简而言之，CPU 核的设计目标是将一次一到两个线程的延迟最小化，而 GPU 的设计目标是处理大量并发轻量线程以最大化吞吐量。

### 内存

主机系统和设备各自拥有彼此独立、各自附着的物理内存。由于主机内存与设备内存被 PCI Express（PCIe）总线隔开，主机内存中的内容必须不时地通过总线传输到设备内存，反之亦然，正如《What Runs on a CUDA-Enabled Device?》中描述的那样。

如果你这样想的话，你很容易丢掉 98% 的性能。

## 安装 PyCUDA

CUDA 支持许多语言。

不错的文档可以在这里找到：https://documen.tician.de/pycuda/index.html

如果你在 Colab 上，前往 Runtime -> Change runtime type -> Hardware accelerator 并设置为「GPU」。


```python
# you may want to clear the output of this cell after installation
from IPython.display import clear_output
 
# this might take a while
!pip install pycuda

clear_output()
```


```python
import numpy as np

from pycuda.compiler import SourceModule
import pycuda.driver as drv
import pycuda.autoinit
```

## 基础

让我们从一个简单的例子开始，然后再深入。

## 内核（Kernel）

就像 C 或 C++ 一样，只不过你使用一些自定义的内置函数和限定符。

CUDA 与普通 C 非常相似，只不过你可以指定某些函数以……方式运行。根据实现，工作流程如下：

你需要把你的计算机想象成一台异构机器：有主机数据和设备数据。

* 你把输入数据移到设备内存。
* 你在设备上运行一些计算。
* 你把数据取回。

事实上，内核运行是并发的——你的程序不会阻塞到内核运行完成。更新的设备甚至可以用这种方式并发运行多个内核，并等待它们的结果。

## 著名的 $A + B$ 问题

为了测试以及与主机协调，我们将使用 **NumPy** 包。如果你没有它，请安装：`pip install numpy`。

NumPy 是 Python 中用于线性代数和数组操作的包。它用 C 编写，非常高效，但只在 CPU 上运行，所以我们将以它为基准。


```python
# lets generate our test data: two float arrays filled with something random
a = numpy.random.randn(100).astype('float32')
b = numpy.random.randn(100).astype('float32')
# the type needs to be specified in this case, because randn's default type is float64, but CUDA knows nothing about it

# we need to create space where kernel should write its answers to
dest = numpy.zeros_like(a)

# this is the kernel itself
mod = SourceModule("""
    __global__ void add(float *dest, float *a, float *b) {
        const int i = threadIdx.x;
        dest[i] = a[i] + b[i];
    }
""")

# you need to specify the source code, and PyCUDA will compile it
add_kernel = mod.get_function("add")

add_kernel(
    drv.Out(dest),  # specifies that this memory should be accessible for writing
    drv.In(a),  # specifies this should be accessible for reading
    drv.In(b),
    block=(100,1,1)  # we'll talk about it in a minute
)

assert np.allclose(dest, a + b), 'WA'  # checks that these are equal
print('OK')
```


      File "<ipython-input-27-afc857479fe4>", line 19
        %%time
        ^
    SyntaxError: invalid syntax



### 内存管理

在 CUDA C API 中，你需要显式地分配内存。所以这实际上真的很好。

还有一个 `drv.InOut` 函数，它使内存既可读也可写，但本教程中我们不会使用它，因为我们也需要测试我们的代码。

这里的大多数操作都是内存操作，所以测量性能没有意义。别担心，我们很快就会讲到更复杂的例子。

GPU 有非常特殊的操作。不过，对于 NVIDIA GPU，管理起来相当简单：显卡具有*计算能力*（compute capability）等级（1.0、1.1、1.2、1.3、2.0 等），在等级 $x$ 上新增的所有特性在更高版本中也可用。这些可以在运行时或编译时检查。

你可以在这篇 Wikipedia 文章中查看差异：https://en.wikipedia.org/wiki/CUDA#Version_features_and_specifications

## 同步

**归约（reduction）**是任何逐数组（array-wise）的操作。

假设以下问题：


## 动态规划

考虑下面的递推式：


```python
## Problem: dynamic programming
```

## 工作 vs. 延迟

我们现在同时考虑工作复杂度和步复杂度。

有些任务，尤其是密码学中的任务，无法并行化。但有些可以。

## 在 $O(\log n)$ 时间内求和

假设我们要对一个 $n$ 元素的数组执行某种结合（即 $A*(B*C) = (A*B)*C$）操作。比如说，求和。

通常，我们会用一个简单的循环来做：

```c++
float s = 0;
for (int i = 0; i < n; i++) {
     s += a[i]; 
}
```

它的计算图长这样：

<img width='400px' src='https://www.elemarjr.com/wp-content/uploads/2018/03/sequential_sum.png'>

这在工作复杂度上是最优的，但在步复杂度上不是：它是 $O(n)$。我们可能想要一种在工作复杂度上稍差一点、但可以并行化的方案。

让我们试试这种分治方法：

<img width='400px' src='https://www.elemarjr.com/wp-content/uploads/2018/03/parallel_sum.png'>

现在它仍然是 $O(n)$ 的工作复杂度（实际上你确实需要相同次数的加法），但这是 $O(\log n)$ 的步复杂度。

当你把递归从上到下展开时，你会看到，为了得到每个所需的值，

<img width='400px' src='http://i.stack.imgur.com/Uehc3.png'>

## 归约小数组


```python
a = numpy.random.randn(2048).astype('float32')

mod = SourceModule("""
    __global__ void sum(float *dest, float *a, float *b) {
        const int i = threadIdx.x;
        // for l from 0 to logn:
        //   __sync_threads()
        //   if the thread is active
        //     sum two elements into where they belong
        // a[0] should containt the needed sum
    }
""")

sum_kernel = mod.get_function("sum")

add_kernel(
    drv.InOut(a),
    block=(1024,1,1)
)

assert np.allclose(dest, a + b), 'WA'  # checks that these are equal
print('OK')
```

## Warp 与线程块

线程按 32 个一组捆绑。一组中的所有线程必须要么在等待，要么在执行相同的操作。这是由架构上的困难造成的。

<img width='300px' src='https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Block-thread.svg/1920px-Block-thread.svg.png'>

你实际上可以用 2 维和 3 维索引做同样的事情——很奇怪，对吧？

## 原子操作

## 归约大数组

## 归约超大数组

现在，事情变得更难了。是时候讲讲 GPU 并行究竟是如何工作的了。



```python

```

## 稠密矩阵乘法

让我们来看第一个真正用得上 GPU 的例子：矩阵乘法。

## 排序

我们的最后一个（也是最难的）任务是实现排序。

你可能已经注意到，我们大多数时候都在推崇分治方法。

确实如此。它们很有效。但我们还没有一个现成可用的算法。


```python
# we'll use a deep learning library for benchmarking because I'm not familiar with anything else 
import torch

a = torch.randn(10**8)
b = a.cuda()
```


```python
# this should run for ~15 secs
%time c = torch.sort(a)
%time c = torch.sort(b)
```

    CPU times: user 15.2 s, sys: 177 µs, total: 15.2 s
    Wall time: 15.2 s
    CPU times: user 274 ms, sys: 237 ms, total: 511 ms
    Wall time: 511 ms


所以，30 倍加速。所以我们现在知道了要与之竞争的目标。


```python
b.sort()
```




    (tensor([-5.4567, -5.3551, -5.3288,  ...,  5.3529,  5.4484,  5.4486],
            device='cuda:0'),
     tensor([55083205,  8383169, 73705953,  ..., 79814161, 50474932, 27805828],
            device='cuda:0'))



有两种类型的排序算法：数据驱动的。

第二种可以用排序网络来表示和分析。下面就是我们将会使用的那个，它叫双调排序（bitonic sort）。

<img src='https://upload.wikimedia.org/wikipedia/commons/thumb/c/c6/BitonicSort.svg/1686px-BitonicSort.svg.png'>

它有 $O(\log n)$ 个阶段，总共包含 $1 + 2 + 3 + \ldots + \log n = O(\log^2 n$ 个比较块，这些比较块无法并行化，并且涉及数组中的每个元素。所以，它总共有 $O(n \log^ n)$ 的工作复杂度，但只有 $O(\log^2 n)$ 的步复杂度，相当不错。

它实际上并不难实现。为了讲清楚，这里给出一个慢速的递归 Python 实现：


```python
def bitonic_sort(a, up=False):
    if len(a) <= 1:
        return a
    else: 
        l = bitonic_sort(x[:len(a) // 2], True)
        r = bitonic_sort(x[len(a) // 2:], False)
        return bitonic_merge(first + second, up)

def bitonic_merge(a, up): 
    # assume input a is bitonic, and sorted list is returned 
    if len(a) == 1:
        return a
    else:
        bitonic_compare(a, up)
        l = bitonic_merge(a[:len(a) // 2], up)
        r = bitonic_merge(a[len(a) // 2:], up)
        return l + r

def bitonic_compare(a, up):
    dist = len(a) // 2
    for i in range(dist):  
        if (a[i] > a[i + dist]) == up:
            a[i], a[i + dist] = a[i + dist], x[i]  # this is how swap is done in Python
```


```python
bitonic_sort([57, 179, 42, 17, 300, 111])
```




    [300, 179, 111, 57, 42, 17]




```python
a = np.random.randn(10**8).astype('float32')
```


    ---------------------------------------------------------------------------

    NameError                                 Traceback (most recent call last)

    <ipython-input-27-58a927c14aae> in <module>()
    ----> 1 a = np.random.randn(10**8).astype('float32')
    

    NameError: name 'np' is not defined


## 为什么是 CUDA

其中大部分仍然适用。

再说一次，GPU 编程非常特殊。

SSE 和张量核（tensor core）。

## 内核

就像 C 或 C++ 一样，只不过你使用一些自定义的内置函数和限定符。

CUDA 与普通 C 非常相似，只不过你可以指定某些函数以……方式运行。根据实现，工作流程如下：

你需要把你的计算机想象成一台异构机器：有主机数据和设备数据。

* 你把输入数据移到设备内存。
* 你在设备上运行一些计算。
* 你把数据取回。

事实上，内核运行是并发的——你的程序不会阻塞到内核运行完成。更新的设备甚至可以用这种方式并发运行多个内核，并等待它们的结果。

你需要理解的是，GPU 对其应用领域极度特化。

为此有内建函数（intrinsics）。

现在，很多价值来自加密货币和深度学习。后者依赖两个特定的操作：用于线性层的矩阵乘法和用于计算机视觉中卷积层的卷积。

首先，他们引入了每个 GPU 时钟周期一次的「乘加」（multiply-accumulate）操作（例如 `x += y * z`）。

Google 使用张量处理单元（Tensor Processing Units）。没有人真正知道它们是如何工作的（专有硬件，他们出租而不是出售）。

每个张量核在大小为 4x4 的小矩阵上执行操作。每个张量核每个 GPU 时钟可以执行 1 次矩阵乘加操作。它将两个 fp16 的 4x4 矩阵相乘，然后把乘积（fp32 矩阵，大小为 4x4）加到累加器（也是 fp32 的 4x4 矩阵）上。

这是每个……的大量工作

嗯，无论如何，对于深度学习来说，你并不真的需要比这更精确的东西了。

它被称为混合精度，因为输入矩阵是 fp16 的，但乘法结果和累加器是 fp32 矩阵。

也许更合适的名字应该是「4x4 矩阵核」，然而 NVIDIA 的市场团队决定使用「张量核」。

所以你看，这不是一个完全公平的比较。

<img width='500px' src='https://static.seekingalpha.com/uploads/2018/8/11/275308-15340093003448672_origin.png'>

*<center>你只需要把这幅图稍微延长一点：去年 11 月，在比特币崩盘之后，NVIDIA 的股价下跌了 30%，所以我不会那么乐观</center>*

一直降到 int4（16 个取值，你没听错）

要写出高效的代码，你需要了解很多这类专门的东西。所以从头开始写库是个坏主意。

无论如何，出于教学和娱乐的目的，今天我们将重新发明轮子，做一次矩阵乘法。

## 归约数组

这看起来很简单：你只需要……。

当你执行 `s += x` 时实际发生了什么？这不是一个单一操作。实际上发生了四件事：

1. 把 $x$ 读入寄存器
2. 把 $s$ 读入寄存器
3. 计算 $s + x$
4. 把它写回 $s$ 最初所在的位置

两个线程可能以交错的方式执行它。假设线程 A 已经取到了 $s$，但一纳秒后线程 B 将在这里写入，而线程 A 对此毫不知情，会重新写入未改变的值。



注意：原子操作就是用来做这个的

对于小的数据类型，它们是在硬件层面实现的，比那快得多。

引入 `std::atomic` 是为了在多线程上下文中处理原子操作。在多线程环境中，当两个线程对同一个变量进行操作时，你必须格外小心以避免竞态条件。

## 内存类型

如果各种类型的设备内存来一场赛跑，结果会是这样的：

寄存器大小（= 机器字宽）是 32 位，但它们也包含 64 位能力（否则拥有超过 4GB 的内存是不可能的）。

* 第 1 名：**寄存器内存**
  <br> 这是只有写入它的线程才可见的数据。它只持续到该线程生命周期结束。
* 第 2 名：**共享内存**
  <br> 对线程块内的所有线程共享。只持续到该块的生命周期结束。这种内存允许线程之间进行通信（数据共享）。这就是为什么你应该
* 第 3 名：**常量内存**
  <br> 
* 第 4 名：纹理内存
* 并列最后：本地内存和全局内存

你现在需要关心的是寄存器……

现在，你只需要关心不同……

访问全局内存需要数百个（周期）。

## 问题：稠密矩阵乘法

其中很多实际上是稀疏的。你可以对社交网络图或 Web 图做各种处理。

很酷。但让我们先扫一下兴：