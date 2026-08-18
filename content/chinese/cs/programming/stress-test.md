---
title: 压力测试
authors:
- Сергей Слотин
- Константин Амеличев
weight: 3
created: 2019
date: 2021-08-25
---

压力测试（对拍）是在解法中找错误的方法：生成随机测试，比较两个解的结果：

1. 正确但慢。
2. 快但不正确。

它在 IOI 赛制尤其有用——当时间充裕和/或已经给小子组写了能拿分的解时。

更详细：

0. 有解 `smart`——快，但其中有个想找的 bug。
1. 写解 `stupid`——慢，但确定正确。
2. 写生成器 `gen`——随机生成某个合法测试并输出。
3. 全部喂给脚本 `checker`，它 $n$ 次生成测试、给 `stupid` 和 `smart` 当输入、比较输出，在输出不同时停下。

有些情况下总体流程因题型略有不同——文末再谈。

## 具体例子

**题目**。给数组 $1 \le a_1 ... a_n \le 10^9$。求最小元素值。

给出用作参照的 `stupid` 解：

```c++
int a[maxn];

void stupid() {
    int n;
    cin >> n;
    for (int i = 0; i < n; i++)
        cin >> a[i];
    int ans = 1e9;
    for (int i = 0; i < n; i++)
        ans = min(ans, a[i]);
    cout << ans;
}
```

假设 `smart` 解里循环边界有错：

```c++
int a[maxn];

void smart() {
    int n;
    cin >> n;
    for (int i = 0; i < n; i++)
        cin >> a[i];
    int ans = 1e9;
    for (int i = 1; i < n; i++)
        ans = min(ans, a[i]);
    cout << ans;
}
```

即便这种例子，若手工挑随机测试并核对答案，也可能要很久才找到错误，所以我们想找出两个解给出不同答案的测试，从而在 `smart` 里定位 bug。

### 内联测试

*注。* 作者不建议这么做，但很多人觉得这样更好懂。

最简单的方法是把对拍逻辑全写在一个源文件里：把生成器和两个解放进单独函数，在 `main` 里循环多次调用。

生成器要把一个随机测试写到某处。最简单选项：

- 放进返回值；
- 放进按引用传入的变量；
- 放进全局变量。

然后把这个测试依次传给解函数，它们类似地传出结果，比较；若答案不同，就输出测试并退出。

``` c++
int a[maxn];
int n;

int stupid() {
    int n;
    cin >> n;
    int ans = 1e9;
    for (int i = 0; i < n; i++)
        ans = min(ans, a[i]);
    return ans;
}

int smart() {
    int n;
    cin >> n;
    int ans = 1e9;
    for (int i = 1; i < n; i++)
        ans = min(ans, a[i]);
    return ans;
}

void gen() {
    n = rand() % 10 + 1;
    for (int i = 0; i < n; i++)
        a[i] = rand();
}

int main() {
    for (int i = 0; i < 100; i++) {
        gen();
        if (smart() != stupid()) {
            cout << "WA" << endl;
            cout << n << endl;
            for (int j = 0; j < n; j++)
                cout << a[j] << ' ';
            break;
        }
        cout << "OK" << endl;
    }
    return 0;
}
```

这个方法通用，但有很多缺点：

- 测试不同题目要复制大量代码。
- 不能在其他语言里写生成器或参照解（脚本语言如 Python 常更简单更快）。
- 源码膨胀，难定位。
- 用全局变量要小心。
- 需要在「压力测试」与普通「从控制台输入」模式间切换。

可以把全部逻辑抽到另一个程序，解本身不动。

### 用外部脚本测试

要点如下：

- 所有解和生成器放进单独文件——它们不必在同一个环境运行。
- 通过 I/O 流重定向传测试。程序读取输入的方式与在评测系统中自然读取一样。
- 运行外部脚本，$n$ 次运行生成器、把输出写进文件，再把文件喂给两个解、逐行比较输出。

文件 `stupid.cpp`、`smart.cpp` 和 `gen.py` 里是我们已懂代码。`checker.py` 脚本大致如下：

```python
import os, sys

_, f1, f2, gen, iters = sys.argv
# 第一个参数是程序名 "checker.py"，
# 所以用 "_" "忘掉" 它

for i in range(int(iters)):
    print('Test', i + 1)
    os.system(f'python3 {gen} > test.txt')
    v1 = os.popen(f'./{f1} < test.txt').read()
    v2 = os.popen(f'./{f2} < test.txt').read()
    if v1 != v2:
        print("Failed test:")
        print(open("test.txt").read())
        print(f'Output of {f1}:')
        print(v1)
        print(f'Output of {f2}:')
        print(v2)
        break
```

作者通常先编译 `stupid` 和 `smart` 到与 `checker.py` 同一目录，再运行 `python3 checker.py stupid smart gen.py 100`。也可在脚本里写编译。

脚本面向 Linux / Mac。Windows 需去掉外部命令里的 `./`，并把 `python3` 换成 `python`。

别忘了，如果至少一个程序不在文件末尾输出换行，checker 会认为输出不同。

### 变体

有时甚至写不出 `stupid`——例如几何题——但可以写几个不同解互相对拍，希望它们的 bug 集合交集不大。若输出不同，就保证至少一个不正确。也可以拿别人的、也得 WA 的解当 `stupid`，这样至少有一个能发现 bug。

如果题目输出不唯一（例如输出最小值下标——可能多个），就不该用 `stupid` 解和 `v1 != v2`，而应写一个外部 checker 脚本：读测试和解的输出、验证它、输出 `yes` / `no`。

交互题可以写一个交互器来测试：把它的输出重定向到解、把解的输出重定向回来。Linux 下这样做：

```bash
mkfifo fifo
./solution < fifo | ./interactor > fifo
```

但这样不能立刻拿到交互协议——为此交互器需把所有有用信息写进某个单独文件。

---

还有很多可能有用：

- 完整支持交互题，
- 多线程测试，
- 内存与时间限制支持，
- 自动跑手工测试，
- 检测源码变化并自动重测，
- 从评测系统解析测试，
- 彩色 `diff` 输出及 checker 的其他自定义输出。

作者一段时间前写过一个[更高级的测试程序](https://github.com/sslotin/jay)，里面都有，但搁置了。谁想继续开发或自己写，请告知。
