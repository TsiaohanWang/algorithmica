---
title: 进程
weight: 1
---

当你需要时，它工作得很好。

fork 系统调用用于创建新进程，这个新进程被称为子进程（child process），它与发起 fork() 调用的进程（父进程）并发运行。创建新的子进程之后，两个进程都会执行 fork() 系统调用之后的下一条指令。子进程使用与父进程相同的 PC（程序计数器）、相同的 CPU 寄存器、相同的已打开文件。

它不带参数，返回一个整数值。下面是 fork() 返回的不同值。

```cpp
#include <stdio.h> 
#include <sys/types.h> 
#include <unistd.h> 
int main() { 
    // make two process which run same 
    // program after this instruction 
    fork(); 
  
    printf("Hello world!\n"); 
    return 0; 
} 
```

主要缺点是额外的开销。它由操作系统管理。当你需要这种粒度时，会使用独立的进程。

fork 出来的进程既不能看到也不能修改彼此的内存空间。