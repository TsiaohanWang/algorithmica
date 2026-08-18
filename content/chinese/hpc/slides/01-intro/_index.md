---
title: 为什么超越大 O？
outputs: [Reveal]
---

# 性能工程

Sergey Slotin

$x + y$

2022 年 5 月 7 日

---

### 关于我

- 前[算法竞赛选手](https://codeforces.com/profile/sslotin)
- 创办了 [Algorithmica.org](https://ru.algorithmica.org/cs)，并「共同创办」了 [Tinkoff Generation](https://algocode.ru/)
- 撰写了《[Algorithms for Modern Hardware](https://en.algorithmica.org/hpc/)》，本讲座即以它为基础
- Twitter: [@sergey_slotin](https://twitter.com/sergey_slotin)；Telegram: [@bydlokoder](https://t.me/bydlokoder)；其他地方：@sslotin

----

### 关于本迷你课程

- 底层算法优化
- 两天、六讲
- **第一天：** CPU 体系结构与汇编、流水线、SIMD 编程
- **第二天：** CPU 缓存与内存、二分查找、树形数据结构
- 前置知识：CS 102、C/C++
- 没有作业，但鼓励大家复现案例研究：https://github.com/sslotin/amh-code

---

## 第 0 讲：为什么超越大 O

*（《AMH》第 1 章）*

---

## RAM 计算模型

- 有一组*基本操作*（读、写、加、乘、除）
- 每个操作顺序执行，并具有某个恒定的*代价*
- 运行时间 ≈ 所有基本操作按其代价加权之和

----

![](https://en.algorithmica.org/hpc/complexity/img/cpu.png =400x)

- CPU 的「基本操作」称为*指令*
- 它们的「代价」称为*延迟*（以周期计）
- 指令会修改 CPU 状态，后者存储在一组*寄存器*中
- 要换算成真实时间，就把所有已执行指令的延迟相加，再除以*时钟频率*（某块 CPU 每秒完成的周期数） <!-- .element: class="fragment" data-fragment-index="1" -->
- 时钟频率是变化的，因此数周期对分析更有用 <!-- .element: class="fragment" data-fragment-index="1" -->

----

![](https://external-preview.redd.it/6PIp0RLbdWFGFUOT6tFuufpMlplgWdnXWOmjuqkpMMU.jpg?auto=webp&s=9bed495f3dbb994d7cdda33cc114aba1cebd30e2 =400x)

http://ithare.com/infographics-operation-costs-in-cpu-clock-cycles/

----

### 渐近复杂度

![](https://en.algorithmica.org/hpc/complexity/img/complexity.jpg =400x)

对足够大的 $n$，我们只关心渐近复杂度：$O(n) = O(1000 \cdot n)$

$\implies$ 基本操作的代价无关紧要，因为它们不影响复杂度 <!-- .element: class="fragment" data-fragment-index="1" -->

但我们能处理「足够大的」$n$ 吗？ <!-- .element: class="fragment" data-fragment-index="2" -->

---

当复杂度理论诞生时，计算机还是另一番模样

![](https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Eniac.jpg/640px-Eniac.jpg =500x)

笨重、昂贵，而且本质上很慢（受限于光速）

----

![](https://researchresearch-news-wordpress-media-live.s3.eu-west-1.amazonaws.com/2022/02/microchip_fingertip-738x443.jpg =500x)

微尺度的电路让信号传播得更快

----

<style>
.randomname{
    display: flex;
    flex: 1em 5em;
}
</style>

<div class="randomname">

<div style="flex: 1; margin-top: -30px">

![](https://en.algorithmica.org/hpc/complexity/img/lithography.png =450x)    

</div>

<div style="flex: 2">

微芯片是通过一种叫[光刻](https://en.wikipedia.org/wiki/Photolithography)的工艺「印制」在一片硅晶圆上的：

1. 生长并切片出[非常纯的硅晶体](https://en.wikipedia.org/wiki/Wafer_(electronics))
2. 在上面覆盖一层[光刻胶](https://en.wikipedia.org/wiki/Photoresist)
3. 用光子按设定图案照射它
4. 化学[刻蚀](https://en.wikipedia.org/wiki/Etching_(microfabrication))暴露的部分
5. 去除剩余的光刻胶

（…再加上其余 40–50 道工序，经过数月才能完成 CPU 的其余部分）
    
</div>

</div>

----

微芯片与光刻的发展带来了：

- 更高的时钟频率
- 扩大生产规模的能力
- **大幅**降低的材料与功耗（= 更低的成本）

----

![](https://upload.wikimedia.org/wikipedia/commons/4/49/MOS_6502AD_4585_top.jpg =500x)

MOS Technology 6502（1975）、Atari 2600（1977）、Apple II（1977）、Commodore 64（1982）

----

还有一条清晰的改进路径：把镜头做得更强、把芯片做得更小

**摩尔定律：** 晶体管数量每两年翻一番。 <!-- .element: class="fragment" data-fragment-index="1" -->

----

**Dennard 缩放：** 把芯片尺寸缩小 30%

- 使晶体管密度翻倍（$0.7^2 \approx 0.5$）
- 使时钟频率提高 40%（$\frac{1}{0.7} \approx 1.4$）
- 保持总体*功率密度*不变
  （我们对能散掉多少热存在机械上的上限）

$\implies$ 每一「代」新芯片的总成本大致相同，但时钟提升 40%、晶体管数量翻倍

（这些晶体管可以用于，比如，增加新指令或增大字长） <!-- .element: class="fragment" data-fragment-index="1" -->

----

大约从 2005 年起，Dennard 缩放停滞了——原因在于*漏电*问题：

- 晶体管变得非常小
- $\implies$ 它们的磁场开始干扰相邻电路
- $\implies$ 产生不必要的发热，偶尔还会翻转比特
- $\implies$ 不得不提高电压来修复
- $\implies$ 不得不降低时钟频率以平衡功耗

----

![](https://en.algorithmica.org/hpc/complexity/img/dennard.ppm =600x)

时钟频率的上限

---

时钟频率已趋于平稳，但我们仍有余裕使用更多晶体管：

- **流水线：** 重叠执行顺序指令，让 CPU 的不同部分保持忙碌
- **乱序执行：** 不必等待之前的指令完成
- **超标量处理：** 添加重复的执行单元
- **缓存：** 在芯片上增加多级更快的内存，以加速对 RAM 的访问
- **SIMD：** 增加能一次处理 128、256 或 512 位数据块的指令
- **并行计算：** 在芯片上放置多个相同核心
- **分布式计算：** 主板上的多块芯片或成多台计算机
- **FPGA** 和 **ASIC：** 用定制硬件解决特定问题

----

![](https://en.algorithmica.org/hpc/complexity/img/die-shot.jpg =500x)

对现代计算机而言，「把所有操作都数一遍」来预测算法性能的方法会相差好几个数量级

---

### 矩阵乘法

```python
n = 1024

a = [[random.random()
      for row in range(n)]
      for col in range(n)]

b = [[random.random()
      for row in range(n)]
      for col in range(n)]

c = [[0
      for row in range(n)]
      for col in range(n)]

for i in range(n):
    for j in range(n):
        for k in range(n):
            c[i][j] += a[i][k] * b[k][j]
```

用纯 Python 把两个 $1024 \times 1024$ 的矩阵相乘需要 630 秒，即 10.5 分钟

每次乘法约 880 个周期

----

```java
public class Matmul {
    static int n = 1024;
    static double[][] a = new double[n][n];
    static double[][] b = new double[n][n];
    static double[][] c = new double[n][n];

    public static void main(String[] args) {
        Random rand = new Random();

        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                a[i][j] = rand.nextDouble();
                b[i][j] = rand.nextDouble();
                c[i][j] = 0;
            }
        }

        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                for (int k = 0; k < n; k++)
                    c[i][j] += a[i][k] * b[k][j];
    }
}
```

Java 需要 10 秒，快了 63 倍

每次乘法约 13 个周期

----

```c
#define n 1024
double a[n][n], b[n][n], c[n][n];

int main() {
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            a[i][j] = (double) rand() / RAND_MAX;
            b[i][j] = (double) rand() / RAND_MAX;
        }
    }

    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++)
                c[i][j] += a[i][k] * b[k][j];
    
    return 0;
}
```

`GCC -O3` 需要 9 秒，但如果加上 `-march=native` 和 `-ffast-math`，编译器会对代码做向量化，耗时降到 0.6 秒。

----

```python
import time
import numpy as np

n = 1024

a = np.random.rand(n, n)
b = np.random.rand(n, n)

start = time.time()

c = np.dot(a, b)

duration = time.time() - start
print(duration)
```

BLAS 大约需要 0.12 秒
（比自动向量化的 C 快约 5 倍，比纯 Python 快约 5250 倍）
