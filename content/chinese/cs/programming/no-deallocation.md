---
title: 不释放内存的分配器
draft: true
---

C 程序可以用两种方式为对象分配内存：在栈上（stack allocation）和在堆上（heap allocation）。

第一种情况下维护一个指向内存末尾的指针，创建对象时它增加所需的字节数，删除对象时则减少。就像栈一样。这种方式用于例如在函数或循环体内创建临时变量时——当变量离开作用域，编译器会自动生成指令来删除它们。

第二种方式下，程序礼貌地请求操作系统按自己方便的方式分配若干字节内存并返回指向它们的指针，同时保证其他进程无法访问这块内存（尽管计算机是很复杂的东西，这点[并不总能做到](https://meltdownattack.com/)）。这种情况下，程序员必须自己负责在对象不再需要时删除它们。要用这种方式创建对象，需要调用 `new` 运算符，删除时调用 `delete` 运算符。

底层内存操作或许是人们对 C 和 C++ 爱恨交加的主要原因。如果不删除堆上分配的对象，就会发生*内存泄漏*，但在竞赛中这无关紧要——在几秒的运行时间内，很难分配超过可用容量的内存。

舍弃「正确」地释放内存，可以显著加快使用 `delete` 的数据结构的运行速度——有时能快 1.5 到 2 倍（尤其是大多数 STL 容器）。

为此可以全局重定义 `new` 和 `delete`：

```
const int max_memory = 1e8;

int pos_memory = 0;
char memory[max_memory];

void* operator new(size_t n) {
    char *res = memory + pos_memory;
    pos_memory += n;
    assert(pos_memory <= max_memory);
    return (void*) res;
}
void operator delete(void *){}
```

`new` 运算符接受需要分配的字节数并返回指向已分配内存的指针——在我们的实现里，它返回并推进「栈」的末尾。

`delete` 运算符接受指向内存起始位置的指针并释放内存。在我们的实现里，它什么都不做。