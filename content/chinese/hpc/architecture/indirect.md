---
title: 间接跳转
weight: 4
---

在汇编阶段，所有标签都会被转换成地址（绝对地址或相对地址），然后编码进跳转指令。

你也可以通过寄存器中存储的非恒定值进行跳转，这被称为*计算跳转*（computed jump）：

```nasm
jmp rax
```

这在动态语言和实现更复杂的控制流方面有一些有趣的用途。

### 多路分支

如果你已经忘了 `switch` 语句是干什么的，这里有一个在美式评分体系中计算 GPA 的小子程序：

```cpp
switch (grade) {
    case 'A':
        return 4.0;
        break;
    case 'B':
        return 3.0;
        break;
    case 'C':
        return 2.0;
        break;
    case 'D':
        return 1.0;
        break;
    case 'E':
    case 'F':
        return 0.0;
        break;
    default:
        return NAN;
}
```

我个人已经不记得上一次在非教学场景下使用 switch 是什么时候了。一般来说，switch 语句等价于一串「if、else if、else if、else if……」这样的判断，正因如此许多语言甚至根本没有 switch。不过，这类控制流结构对实现解析器、解释器和其他状态机很重要，它们通常由一个 `while (true)` 循环加上里面的 `switch (state)` 语句构成。

当我们能控制变量取值范围时，可以利用计算跳转玩一个技巧：不必构造 $n$ 个条件分支，而是创建一张包含各个可能跳转位置的指针/偏移量的*跳转表*（branch table），然后用取值在 $[0, n)$ 范围内的 `state` 变量直接索引它。

当各取值在数值上紧密排列时（不一定要严格连续，但值得为表中留空白字段付出代价），编译器就会使用这种技术。也可以用*计算 goto*（computed goto）显式实现：

```cpp
void weather_in_russia(int season) {
    static const void* table[] = {&&winter, &&spring, &&summer, &&fall};
    goto *table[season];

    winter:
        printf("Freezing\n");
        return;
    spring:
        printf("Dirty\n");
        return;
    summer:
        printf("Dry\n");
        return;
    fall:
        printf("Windy\n");
        return;
}
```

基于 switch 的代码对编译器来说并不总是容易优化，因此在状态机的语境下，常常直接使用 `goto` 语句。`glibc` 中与 I/O 相关的部分就有大量这样的例子。

### 动态分派

间接跳转在实现运行时多态方面也至关重要。

考虑一个老掉牙的例子：一个抽象类 `Animal`，带有一个虚方法 `.speak()`，以及两个具体实现——汪汪叫的 `Dog` 和喵喵叫的 `Cat`：

```cpp
struct Animal {
    virtual void speak() { printf("<abstract animal sound>\n");}
};

struct Dog {
    void speak() override { printf("Bark\n"); }
};

struct Cat {
    void speak() override { printf("Meow\n"); }
};
```

我们想创建一个动物，并且在不预先知道其类型的情况下调用它的 `.speak()` 方法，它应该以某种方式调用正确的实现：

```c++
Dog sparkles;
Cat mittens;

Animal *catdog = (rand() & 1) ? &sparkles : &mittens;
catdog->speak();
```

实现这种行为的方法有很多种，C++ 采用的是*虚方法表*（virtual method table）。

对于 `Animal` 的所有具体实现，编译器会给它们的所有方法（也就是它们的指令序列）填充（padding，在 `ret` 后面插入一些[填充指令](../layout)），使所有类的方法长度完全相同，然后把它们按顺序写到指令内存的某处。接着它给结构体（也就是它的所有实例）添加一个*运行时类型信息*（run-time type information）字段，它本质上就是在内存区域中指向该类虚方法正确实现的偏移量。

进行虚方法调用时，从结构体的实例中取出这个偏移量字段，据此进行一次普通的函数调用，这利用了每个派生类的所有方法和其他字段具有完全相同偏移量这一事实。

当然，这会带来一些开销：

- 由于与[分支预测错误](/hpc/pipelining)相同的流水线冲刷原因，你可能还需要多花大约 15 个周期。
- 编译器很可能无法内联这次的函数调用。
- 类的大小会增加几个字节左右（这取决于具体实现）。
- 二进制文件本身也会变大一点点。

出于这些原因，运行时多态在性能关键的应用程序中通常会被避免。