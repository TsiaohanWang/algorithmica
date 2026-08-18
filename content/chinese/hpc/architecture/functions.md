---
title: 函数与递归
weight: 3
published: true
---

在汇编中「调用函数」，你需要[跳转](../loops)到它的开头，然后再跳回来。但这样一来就产生了两个重要的问题：

1. 如果调用方把数据存在与被调用方相同的寄存器里怎么办？
2. 「回去」是回到哪里？

这两个问题都可以通过设置一个专门的内存位置来解决：在调用函数之前，我们先把返回所需的所有信息写到那里。这个位置称为*栈*（stack）。

### 栈

硬件栈的工作方式与软件栈相同，实现上也就是两个指针：

- *基址指针*（base pointer）标记栈的起始位置，按惯例存放在 `rbp` 中。
- *栈指针*（stack pointer）标记栈的最后一个元素，按惯例存放在 `rsp` 中。

当你需要调用函数时，先把所有局部变量压入栈中（其他情况下也可以这么做，例如寄存器不够用的时候），然后把当前指令指针压栈，最后跳转到函数的开头。从函数退出时，查看栈顶存放的指针，跳转到那里，然后把栈上保存的所有变量小心地读回寄存器。

<!--

函数参数和局部变量分别通过给 `ebp` 加上或减去一个常量偏移来访问。

ebp 本身实际指向上一帧的基址指针，这使得调试器中的栈回溯（stack walking）和查看其他帧的局部变量成为可能。挺有意思的，比如让程序停下来，看看哪些函数被哪些函数调用。

push ebp      ; Preserve current frame pointer
mov ebp, esp  ; Create new frame pointer pointing to current stack top
sub esp, 20   ; allocate 20 bytes worth of locals on stack.

你可以启用的帧指针省略（frame pointer omission）优化实际上会消除这一点，把 ebp 当作另一个寄存器使用，并直接从 esp 访问局部变量，但这会让调试变得稍微困难一些，因为调试器再也无法直接访问更早函数调用的栈帧了。

当函数开始时，它会执行*函数序言*（function prologue）：把上一个基址指针保存在栈上，并设置 `rbp = rsp`。

-->

这些操作你都可以用普通的内存操作和跳转来实现，但由于它们太常用了，有 4 条专门的指令来做这件事：

- `push` 把数据写到栈指针处并递减它。
- `pop` 从栈指针处读取数据并递增它。
- `call` 把下一条指令的地址压到栈顶并跳转到一个标签。
- `ret` 从栈顶读取返回地址并跳转到那里。

要不是它们真的是硬件指令，你简直想称之为「语法糖」——它们其实就是下面这些两条指令片段的融合等价形式：

```nasm
; "push rax"
sub rsp, 8
mov QWORD PTR[rsp], rax

; "pop rax"
mov rax, QWORD PTR[rsp]
add rsp, 8

; "call func"
push rip ; <- instruction pointer (although accessing it like that is probably illegal)
jmp func

; "ret"
pop  rcx ; <- choose any unused register
jmp rcx
```

`rbp` 与 `rsp` 之间的内存区域称为*栈帧*（stack frame），函数的局部变量通常存放在这里。它在程序启动时预先分配好；如果你向栈中压入的数据超过其容量（Linux 上默认 8MB），就会遇到*栈溢出*错误。由于现代操作系统并不会真正把内存页分配给你，直到你读写它们的地址空间为止，因此你可以随意指定一个非常大的栈大小，这更像是对可用栈内存量的一种限制，而不是每个程序都必须占用的固定数量。

<!--

在函数开头保存帧指针 `rbp` 并用 `rsp` 替换它是一个好主意——这样离开函数时，只需恢复 `rbp` 就能忘掉它所有的局部变量。这一序列被称为*函数序言*，通常看起来大致是这样（编译器常常会把它优化掉）：

```nasm
push rbp     ; preserve the current frame pointer
mov rbp, rsp ; create a new frame pointer pointing to the current top of the stack
sub rsp, 20  ; allocate 20 bytes worth of locals on stack
```

-->

<!--
专用于栈内存的内存区域（称为*栈帧*）与其他任何内存区域并无不同。它在程序启动时分配。你还可以做一些巧妙的事情，例如

函数会执行一个*序言*，通常看起来大致是这样：

```nasm
push rbp     ; preserve the current frame pointer
mov rbp, rsp ; create a new frame pointer pointing to the current top of the stack
sub rsp, 20  ; allocate 20 bytes worth of locals on stack
```

注意栈中的数据是自上而下写入的。这只是一个约定：也可以反着来。当你需要「离开」一个函数或一个可见性作用域（比如 `if` 或 `for` 的循环体）时，只需增大栈指针即可。

-->

### 调用约定

开发编译器和操作系统的人们最终制定出了关于如何编写和调用函数的[约定](https://wiki.osdev.org/Calling_Conventions)。这些约定促成了一些重要的[软件工程壮举](/hpc/compilation/stages/)，例如把编译拆分成独立的单元、复用已经编译好的库，甚至用不同的编程语言编写它们。

来看下面这个 C 例子：

```c
int square(int x) {
    return x * x;
}

int distance(int x, int y) {
    return square(x) + square(y);
}
```

<!--

在没有任何优化标志的情况下编译，它会生成下面的汇编：

```nasm
square:
    push    rbp
    mov     rbp, rsp
    mov     DWORD PTR [rbp-4], edi
    mov     eax, DWORD PTR [rbp-4]
    imul    eax, eax
    pop     rbp
    ret
length:
    push    rbp
    mov     rbp, rsp
    push    rbx
    sub     rsp, 8
    mov     DWORD PTR [rbp-12], edi
    mov     DWORD PTR [rbp-16], esi
    mov     eax, DWORD PTR [rbp-12]
    mov     edi, eax
    call    square
    mov     ebx, eax
    mov     eax, DWORD PTR [rbp-16]
    mov     edi, eax
    call    square
    add     eax, ebx
    mov     rbx, QWORD PTR [rbp-8]
    leave
    ret
```
-->

按约定，函数应通过 `rdi`、`rsi`、`rdx`、`rcx`、`r8`、`r9` 接收参数（如果这些不够用，余下的放在栈里），把返回值放入 `rax`，然后返回。因此，`square` 作为一个简单的单参数函数，可以这样实现：

```nasm
square:             ; x = edi, ret = eax
    imul edi, edi
    mov  eax, edi
    ret
```

每次从 `distance` 调用它时，我们只需费点周折保存它的局部变量：

```nasm
distance:           ; x = rdi/edi, y = rsi/esi, ret = rax/eax
    push rdi
    push rsi
    call square     ; eax = square(x)
    pop  rsi
    pop  rdi

    mov  ebx, eax   ; save x^2
    mov  rdi, rsi   ; move new x=y

    push rdi
    push rsi
    call square     ; eax = square(x=y)
    pop  rsi
    pop  rdi

    add  eax, ebx   ; x^2 + y^2
    ret
```

还有很多细节，但我们这里不打算深入，因为本书讲的是性能，而对付函数调用最好的办法其实是干脆不要调用它们。

### 内联

对于这类小函数，把数据搬进搬出栈会产生明显的开销。不得不这样做是因为，一般情况下你无法知道被调用方是否修改了你存放局部变量的寄存器。但当你拥有 `square` 的代码时，就可以把数据藏在你确定不会被修改的寄存器里来解决这个问题。

```nasm
distance:
    call square
    mov  ebx, eax
    mov  edi, esi
    call square
    add  eax, ebx
    ret
```

这样好一些，但我们仍然在隐式地访问栈内存：每次函数调用都要压入和弹出指令指针。在像这样的简单情况下，我们可以*内联*函数调用：把被调用方的代码拼进调用方，并解决寄存器冲突。在我们的例子中：

```nasm
distance:
    imul edi, edi       ; edi = x^2
    imul esi, esi       ; esi = y^2
    add  edi, esi
    mov  eax, edi       ; there is no "add eax, edi, esi", so we need a separate mov
    ret
```

这与优化编译器对该代码片段生成的输出已经相当接近了——只是它们会使用 [lea 技巧](../assembly)来让生成的机器码序列再小几个字节：

```nasm
distance:
    imul edi, edi       ; edi = x^2
    imul esi, esi       ; esi = y^2
    lea  eax, [rdi+rsi] ; eax = x^2 + y^2
    ret
```

在诸如此类的情况下，函数内联显然是有益的，编译器也大多会[自动](/hpc/compilation/situational)进行内联，但也有不适合内联的情况——我们[稍后](../layout)会谈到。

### 尾调用消除

当被调用方不调用其他任何函数，或者至少这些调用不是递归时，内联是直截了当的。我们来看一个更复杂的例子。考虑下面这个递归计算阶乘的函数：

```cpp
int factorial(int n) {
    if (n == 0)
        return 1;
    return factorial(n - 1) * n;
}
```

等价的汇编：

```nasm
; n = edi, ret = eax
factorial:
    test edi, edi   ; test if a value is zero
    jne  nonzero    ; (the machine code of "cmp rax, 0" would be one byte longer)
    mov  eax, 1     ; return 1
    ret
nonzero:
    push edi        ; save n to use later in multiplication
    sub  edi, 1
    call factorial  ; call f(n - 1)
    pop  edi
    imul eax, edi
    ret
```

即使函数是递归的，也常常可以通过重构让它变得「无需调用」。当函数是*尾递归*时就是这样：它在发出递归调用后立即返回。由于调用之后不再需要任何操作，也不必在栈上保存任何东西，递归调用可以安全地替换为跳转到函数开头——实际上就是把函数变成了一个循环。

要让我们的 `factorial` 函数变成尾递归，可以给它传一个「当前乘积」参数：

```cpp
int factorial(int n, int p = 1) {
    if (n == 0)
        return p;
    return factorial(n - 1, p * n);
}
```

于是这个函数就可以轻松折叠成一个循环：

```nasm
; assuming n > 0
factorial:
    mov  eax, 1
loop:
    imul eax, edi
    sub  edi, 1
    jne  loop
    ret
```

递归可能变慢的首要原因是它需要读写栈上的数据，而迭代和尾递归算法不需要。这一概念在函数式编程中非常重要，那里没有循环，你能用的只有函数。如果没有尾调用消除，函数式程序将需要多得多的执行时间和内存。