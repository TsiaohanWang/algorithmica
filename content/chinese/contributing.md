---
title: 如何添加和编辑文章
authors:
  - Сергей Слотин
date: 2021-01-23
hideSidebar: true
published: true
---

这是一份尚不完整的指南，会逐步补充。

如果有什么问题（哪怕是愚蠢的问题），[给我写信](https://t.me/bydlokoder)。

## 如何开始

### 如果只是小改动

在网站任意页面右上角点击铅笔按钮。会打开 prose.io 界面，需要用 GitHub 登录，之后就可以编辑该页面的 markdown 源代码了。第一次保存时会自动以你的名义创建分支和 pull request，之后它会持续更新。完成后保持原样即可——会有人来审核通过。

那里没有完整的预览——如果你对复杂公式的修改没有把握，请小心。

有时编辑器会稍微改变文章开头元信息块（见下文）的格式。这没问题——只需检查 `published` / `draft` / `date` 是否为你想要的值。

### 如果是大改动

对于比较严肃的工作，建议检出仓库并在本地搭建网站。可以这样做（假设你熟悉终端操作）：

1. [安装 Hugo](https://gohugo.io/getting-started/installing/)：根据系统不同，多半是 `sudo apt-get install hugo`、`sudo pacman -Syu hugo`、`brew install hugo` 或 `choco install hugo -confirm` 之一。
2. Fork 仓库并执行 `git clone https://github.com/$USERNAME/algorithmica.git`。
3. 在仓库根目录执行 `hugo serve`，然后访问 `localhost:1313` 查看英文版或 `localhost:1314` 查看俄文版（端口可能不同）。
4. 找到或创建需要的文章，进行修改（可以用任意文本编辑器；修改会自动在浏览器中重新渲染），推送更改并向 master 发起 pull request。

如果想编辑标记为 draft（未发布）的文章，需要加上 `-D` 标志。建议在创建 PR 前用拼写检查器（例如 `hunspell`）过一遍。

如果以上任何一步需要帮助，还是那句话，给我写信。

### 如果想写新文章

一篇算得上「完成」的文章应当满足：

- 算法有描述和证明，
- 有实现，
- 实现没有 bug，
- 至少有一个题目示例。

为了减少无用功，建议先问一下（在 telegram 或 GitHub issue 里）：这个主题是否已有文章，是否已经有人开始写，是否有必要写，以及应该放在哪个栏目。

许多文章被标记为 draft——这意味着文章已规划但还在准备中。如果文中没有作者，或者有作者但最后一次修改是很久以前，那么可以放心接手。

## 技术能力

### Markdown

[语法指南](https://www.markdownguide.org/basic-syntax/)。

除基础语法外，还支持表格、代码块、删除线、latex 公式（用一或两个 `$`）和 tikz 图（用两个 `@`）。

### Front matter

每篇文章开头都有一个用 `---` 分隔的元信息块，其中比较重要的有：

- `title`：文章标题
- `authors`：作者列表（支持 markdown：例如可以插入链接）
- `editors`：同样的编辑者列表
- `date`：最后修改时间（按 `2021-08-19` 的格式填写）
- `created`：文章最初发布时间（任意格式）
- `prerequisites`：指向前置文章的链接列表（最好用相对链接）；不要列太多，并避免循环引用（这不是技术限制，而是常识）

[一份填好的元信息示例](https://raw.githubusercontent.com/algorithmica-org/algorithmica/master/content/russian/cs/tree-structures/treap.md)。

## 俄语书写规范

反正评审人也会改，但请记住：

1. 引号：用 « 和 »。
2. [连字符、减号和破折号](https://www.artlebedev.ru/kovodstvo/sections/97/)：-、$a-b$（用 latex）和 —。
3. 带公式的句子读起来应该像正常句子（如果是 display 风格的公式，前面的段落通常不以标点收尾，后面的段落若不是独立的句子则以小写字母开头）。
4. 枚举列表也要读起来要么像独立的句子，要么像同一个句子的一部分。
5. 哈希（хеш）、栈（стек）、双端队列（дек）——全都写成带「е」的形式。

学会不用复制就能打出引号和其他特殊字符会很方便。在 Linux 上可以通过 Compose Key 实现。

另外我们*忽略*多作者算法名称中破折号代替连字符的规则（用「Ахо-Корасик」而不用「Ахо — Корасик」），对标点规则也不是特别严格。

## 常见错误与约定

一些小的技术细节和指南：

- 只使用二级（`##`）和三级（`###`）标题。如果小节非常小，就用一个以 **bold** 单词开头的段落来表示。
- 使用相对链接，或从站点根目录开始的绝对链接：`/cs/tree-structures/treap/`。
- 图片通过 `![描述](../img/picture.png)` 插入，并上传到本地的 `img` 目录。尽可能用 `.svg` 代替 `.png`，用 `.png` 代替 `.jpg`。
- 除非是特殊情况，不要使用 html。
- 给代码块标注编写时所使用的语言标签（`cpp` / `python`），否则语法高亮不会生效。
- 注释可以用，也应该用。通用「todo」性质的注释可以写在 front matter 里（通过 `#`），而上下文注释或草稿段落可以用 html 注释：`<!-- ... -->`。

## 代码风格

除非是 Makefile 或 Go，一律使用空格。

**Python.** 完全遵循 PEP。

**C++**：

1. 尽量使用具体类型，而不是元编程。
2. 绝对不要用 `#define forn`。
3. 如果文章中用了单字母变量，实现里可以也应该使用它。否则变量名应该一目了然。
4. 具体题目的解答应该是一个函数或方法。预处理可以写成单独的函数，也可以写在 `main` 里（不写 `main` 本身）。输入输出没人关心。
5. 注释用俄语写，但变量和函数名用英语。

用例子来描述代码风格更清楚：

```cpp
template <typename T>
void f(T a, T *b, T &c) {
    // ...
}

// однострочные форы предпочтительнее
for (/* ... */)
    // ...

for (/* ... */)
    for (/* ... */)
        for (/* ... */)

// однострочные ифы тоже предпочтительнее
if (cond)
    // ...

// но не так:
if (cond) // ...

// при этом однострочные функции ок
int sum(Node *v) { return v ? v->sum : 0; }

if (cond) {
    // ...
} else if {
    // ...
} else {
    // ...
}

// иногда:
if (cond)
    // ...
else {
    // ...
}

// бесконечный цикл делается так
while (true) {
    // ...
}

sort(a.begin(), a.end(), [](int x, int y){
    return x < y;
});

int a[5] = {1, 2, 3, 4, 5};
int a[n] = {0}; // заполнить нулями
```

如果没有特别说明，所有实现都默认：编译器为 GCC，标准不早于 C++17，且在代码块之前有以下导入：

```cpp
#include <bits/stdc++.h>
using namespace std;
```

如果你的习惯风格不同，建议使用 `clang-format` 或其他格式化工具。