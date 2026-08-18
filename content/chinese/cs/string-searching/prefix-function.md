---
title: 前缀函数
authors:
- Сергей Слотин
created: 2018
weight: 1
---

**定义**。字符串 $s$ 的前缀函数是数组 $p$，其中 $p_i$ 等于字符串 $s_0 s_1 s_2 \ldots s_i$ 的最大的、同时也是第 $i$ 个前缀（不含整个第 $i$ 个前缀）后缀的前缀长度。

例如，对字符串「aataataa」，既是后缀又是前缀的最大前缀是「aataa」；这个字符串的前缀函数是 $[0, 1, 0, 1, 2, 3, 4, 5]$。

```c++
vector<int> slow_prefix_function(string s) {
    int n = (int) s.size();
    vector<int> p(n, 0);
    for (int i = 1; i < n; i++)
        for (int len = 1; len <= i; len++)
            // 如果长度为 len 的前缀等于长度为 len 的后缀
            if (s.substr(0, len) == s.substr(i - len + 1, len))
                p[i] = len;
    return p;
}
```

这个算法目前运行在 $O(n^3)$，但之后我们会加速它。

### 这如何帮助解决原题？

先让我们相信能在线性时间内算前缀函数，并学会用它查找子串。

把子串 $s$ 和 $t$ 用某个两边都不出现的字符连接起来——就设这个字符为 `#`。看所得字符串 `s#t` 的前缀函数。

```c++
string s = "choose";
string t =
    "choose life. choose a job. choose a career. choose a family. choose a fu...";

cout << s + "#" + t << endl;
cout << slow_prefix_function(s + "#" + t) << endl;
```

```bash
choose#choose life. choose a job. choose a career. choose a family. choose a fu...
0000000123456000000012345600000000123456000100000001234560000000000012345600000000
```

可以看出，所有值等于 6（即 $s$ 的长度）的位置，都是 $s$ 在文本 $t$ 中出现的末尾。

这种算法（算 `s#t` 的前缀函数，看哪些位置等于 $|s|$）称为**Knuth–Morris–Pratt 算法**。

### 如何快速计算

再看几个前缀函数的例子，尝试找规律：

```bash
aaaaa
01234

abcdef
000000

abacabadava
00101230101
```

可以注意到这样的特点：$p_{i+1}$ 至多比 $p_i$ 大 1。

**证明。** 如果存在等于字符串 $s_{:i+1}$ 后缀、长度为 $p_{i+1}$ 的前缀，那么去掉最后一个字符，就能得到字符串 $s_{:i}$ 的合法后缀，其长度恰好少 1。

尝试用动态规划解题：通过前面的值找 $p_i$ 的公式。

注意 $p_{i+1} = p_i + 1$ 当且仅当 $s_{p_i} =s_{i+1}$。这种情况下可以更新 $p_{i+1}$ 继续。

例如，在字符串 $\underbrace{aabaa}t\overbrace{aabaa}$ 中，标出的最大前缀等于后缀：$p_{10} = 5$。如果下一个字符等于 $t$，那么 $p_{11} = p_{10} + 1 = 6$。

但当 $s_{p_i}\neq s_{i+1}$ 时呢？假设同样例子里下一个字符不是 $t$ 而是 $b$。

* $\implies$ 新字符串的「等于后缀的前缀」的长度肯定小于 5。
* $\implies$ 所求的新「后缀前缀」既是「aabaa**b**」的后缀，又是子串「aabaa」的前缀。
* $\implies$ 于是下一个待检查的候选是「aabaa」的前缀函数值，即已算好的 $p_4 = 2$。
* $\implies$ 如果 $s_2 = s_{11}$（即新字符与候选前缀之后的字符相同），则 $p_{11} = p_2 + 1 = 2 + 1 = 3$。

本例确实如此（所需前缀是「aab」）。但一般情形下如果 $p_{i+1} \neq p_{p_i+1}$ 呢？那就做同样的推理，得到更短的候选——$p_{p_{p_i}}$。如果这个也不行，就类似地检查更短的，直到这个下标变成 0。

```c++
vector<int> prefix_function(string s) {
    int n = (int) s.size();
    vector<int> p(n, 0);
    for (int i = 1; i < n; i++) {
        // 前缀函数肯定不会超过这个值 + 1
        int cur = p[i - 1];
        // 不断减小 cur，直到新字符匹配
        while (s[i] != s[cur] && cur > 0)
            cur = p[cur - 1];
        // 此处要么 s[i] == s[cur]，要么 cur == 0
        if (s[i] == s[cur])
            p[i] = cur + 1;
    }
    return p;
}
```

**复杂度。** 最坏情况下这个 `while` 单次迭代可能运行 $O(n)$，但*平均*每个 `while` 运行 $O(1)$。

前缀函数每步至多增加 1，而每轮 `while` 后至少减少 1。因此总操作数至多 $O(n)$。
