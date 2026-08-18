---
title: 读取十进制整数
weight: 10
draft: true
---

我写了一个新的整数解析算法，比 scanf 快约 35 倍。

（不，这不是愚人节玩笑——尽管听起来确实很离谱。）

Zen 2 @ 2GHz。编译器是 Clang 13。

离谱。

### Iostream

### Scanf

### 同步

### Getchar

### 缓冲

### SIMD

http://0x80.pl/notesen/2014-10-12-parsing-decimal-numbers-part-1-swar.html


### 串行方案

### 基于转置的方法

### 指令级并行


### 改进

ILP 的收益不会那么大。

有一个重要的保留意见。我们得到了这些整数，甚至可以对它们做其他解析算法。

每字节 1.75 个周期。

AVX-512 既得益于更大的 SIMD 通道宽度，也得益于专门的过滤运算。

它大约占总时间的 2%，但可以通过特殊流程来优化。用任意数字填充缓冲区。

### 后续工作

下一次，我们将*写*整数。

你可以通过在 Rabin–Karp 算法中计算哈希来构造一种字符串搜索算法——尽管似乎不可能为此设计出*精确*的算法。

## 致谢

http://0x80.pl/articles/simd-parsing-int-sequences.html

https://stackoverflow.com/questions/25622745/transpose-an-8x8-float-using-avx-avx2/25627536#25627536
