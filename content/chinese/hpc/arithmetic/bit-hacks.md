---
title: 位运算
weight: 7
draft: true
---

本文很大程度上基于 Sean Eron Anderson 的 [Bit Twiddling Hacks](https://graphics.stanford.edu/~seander/bithacks.html)。我们补充了一些方法，也删除了一些已经被硬件解决的问题。其中大部分技巧编译器已经能够自动优化。

在支持 `cmov` 的架构上，其中很多已经过时。

这里也充当一份练习题。

## 基本操作

`>>`

注意，算术移位对负数移入 `1`，对正数移入 `0`（不过它可能是由实现定义的？）。

在 C/C++ 中，对负数进行左移或右移属于未定义行为。

`<<`

`rol` 指令，即“循环左移”。

`__builtin_popcount` `popcnt` 返回 x 中 1 位的个数。

`__builtin_parity` 返回 x 的*奇偶性*（即 x 中 1 位的个数模 2）。

这大概是为了[错误检测](https://en.wikipedia.org/wiki/Parity_bit)。

`__builtin_clrsb` 返回 x 中前导冗余符号位的个数，即最高有效位之后与它相同的位数。对 0 或其他值没有特殊处理。

`__builtin_ffs` 返回 x 中最低位 1 的下标加 1；若 x 为零，则返回 0。

`__builtin_clz` 返回 x 中从最高有效位开始的前导 0 的个数。若 x 为 0，则结果未定义。

`__builtin_ctz` 返回 x 中从最低有效位开始的末尾 0 的个数。若 x 为 0，则结果未定义。

`ctz`、`clz` -> `__lg`

## 实用技巧

### 整数的符号

`(x < 0)` 或 `x >> 31`

### 判断两个整数是否同号

`x ^ z < 0`

### 整数的绝对值

提取符号位：`int mask = x >> 31`。负数时为 `1`，正数时为 `0`。

将其与初始值异或：`x ^ mask`（这相当于根据符号加 1 或减 1）。

再从第 2 步的结果中减去 mask：`(x ^ mask) - mask`。

或者，你也可以用 `(v + mask) ^ mask`，效果相同，只是顺序相反。

### 取出最后一个 1 位

`x & -x`

### 去掉整数的最后一个 1 位

`x & (x - 1)`

### 判断是否为 2 的幂

`(x & (x - 1)) == 0`

注意，0 也会被视为 2 的幂。

### 反转位

Clang 提供 `__builtin_bitreverse{8,16,32,64}`

```c++
int reverseBits(int x)
{
	unsigned int s = sizeof(x) * 8;
	T mask = ~T(0);
	while ((s >>= 1) > 0)
	{
		mask ^= mask << s;
		x = ((x >> s) & mask) | ((x << s) & ~mask);
	}
	return x;
}
```

### 用异或交换两个数

你可能听说过这个。

```c++
a ^= b;
b ^= a;
a ^= b;
```

这不是它底层的实现方式。处理器有一条单独的 xchng 指令。

### 模 2 的幂

如果 `m = (1 << k)`，那么 `x % m` 与 `x & (m - 1)` 相同。

## 掩码

掩码操作。

### 暴力枚举

你可以用递归（显然很慢），也可以选择无分支的做法。

背包问题有一个 $O(2^n)$ 的暴力解法。

```c++
int ans = 0;
for (int mask = 0; mask < (1 << n); mask++) {
    int s = 0;
    for (int i = 0; i < n; i++)
        if (mask >> i & 1)
            s += a[i];
    if (s <= C)
        ans = max(ans, s);
}
```

### 子集的子集

```c++
for (int submask = mask; submask != 0; submask = (submask - 1) & mask) {
    // ...
}
```

事实证明，总数会是 $3^n$。每次迭代中，每个位可以处于三种状态之一：不在 $m$ 中、尚未加入 $s$、同时属于 $s$ 和 $m$。由于总共有 $n$ 个位，因此至多有 $3^n$ 种不同的组合。