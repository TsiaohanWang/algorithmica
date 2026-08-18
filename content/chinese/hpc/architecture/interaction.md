---
title: 中断与系统调用
weight: 9
draft: true
---

```asm
global _start

section .text

_start:
  mov rax, 1        ; write(
  mov rdi, 1        ;   STDOUT_FILENO,
  mov rsi, msg      ;   "Hello, world!\n",
  mov rdx, msglen   ;   sizeof("Hello, world!\n")
  syscall           ; );

  mov rax, 60       ; exit(
  mov rdi, 0        ;   EXIT_SUCCESS
  syscall           ; );

section .rodata
  msg: db "Hello, world!", 10
  msglen: equ $ - msg
```

中断的代价高昂。它们本不该出现在正常执行路径上。异常（Exceptions）。

执行系统调用会带来一些开销，所以通常会尽量避免。例如，所有 I/O 通常都会被缓冲，这样你只需向操作系统发送一块（比如说 4KB）数据。