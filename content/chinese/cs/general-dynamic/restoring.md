---
title: 答案还原
weight: 5
draft: true
---


### 答案还原

很多题目不仅要求求出某个量的最大值或最小值，还要求说出如何得到它。在蚱蜢问题中，需要还原出蚱蜢依次跳过的点序列。我们介绍两种方法：

<strong>记住答案</strong>

用一个单独的数组记住：跳到当前格子最优的来源格子。在计算动态规划的同时记录。数组 $prev$ 保存最佳前驱。

``` C++ numberLines
vector<int> dp(n, 0);
for (int i = 1; i < n; i++) {
    for (int j = max(0, i - 3): j < i; j++) {
        if (dp[i] < dp[j] + c[i]) {
            prev[i] = j;
            dp[i] = dp[j] + c[i];
        }
    }
}
```

然后沿着构造出的路径从点 $n-1$ 走到 0：

``` C++ numberLines
vector<int> path;
int cur = n - 1;
while (cur >= 0) {
    path.push_back(cur);
    cur = prev[cur];
}
```

<em>给细心的读者的思考题：</em>

现在请想明白：这样的代码可能会陷入死循环。应该如何初始化数组 $prev$ 才能避免这种情况？数组 $path$ 中的点按什么顺序排列？

<strong>再次遍历</strong>

假设我们已经算好了动态规划数组。现在从最后一个点往前走，根据已有的状态值判断我们是从哪里来的。

``` C++ numberLines
vector<int> path;
int cur = n - 1;
while (cur >= 0) {
    path.push_back(cur);
    if (cur >= 1 && dp[cur] == dp[cur - 1] + c[cur]) {
        cur = cur - 1;
    } else if (cur >= 2 && dp[cur] == dp[cur - 2] + c[cur]) {
        cur = cur - 2;
    } else if (cur >= 3 && dp[cur] == dp[cur - 3] + c[cur]) {
        cur = cur - 3;
    }
}
```

这种方法的优点是不必为每个状态额外占用内存来存储前驱。

### 复杂度

这种情况下，动态规划的值只需一趟遍历数组即可算出，答案也可以在另一趟遍历中还原，因此时间和内存开销均为 $O(n)$。

---

现在我们已经会求 DP 题的答案了，但在某些题目中我们还想知道答案是如何得到的，例如在小乌龟问题中我们可能关心它的路径。这类任务称为动态规划中的答案还原。

有两种实现方法。

1\) 在数组 prev 中记录你是从哪个格子来到当前格子的。

当我们在左边和上边的格子中取最大值时，实际上是在决定通向该格子的最优路径的最后一步——来自上方还是左方——然后取那个格子的答案，再加上当前格子的硬币。我们把来源格子的坐标存进数组 prev。或者，在这个具体例子中，可以不存坐标，而只存 1（从左边来）或 0（从上面来）。

``` C++ numberLines
for (int i = 0; i < n; i++) {
    for (int j = 0; j < m; j++) {
        if (i == 0 && j == 0) {
            dp[0][0] = COINS[0][0];
            prev[0][0] = -1;
        }
        else if (i == 0) {
            dp[0][j] = dp[0][j - 1] + COINS[0][j];
            prev[0][j] = 0;
        }
        else if (j == 0) {
            dp[i][0] = dp[i - 1][0] + COINS[i][0];
            prev[i][0] = 1;
        }
        else {
            dp[i][j] = max(dp[i - 1][j], dp[i][j - 1]) + COINS[i][j];
            if (dp[i - 1][j] > dp[i][j - 1]) {
                prev[i][j] = 1;
            }
            else {
                prev[i][j] = 0;
            }
        }
    }
}
```

然后，要还原答案，只需从末尾沿着这些格子走回起点，再把得到的序列反转即可。

``` C++ numberLines
while (i > 0 || j > 0) {
    if (prev[i][j] == 1) {
        i -= 1;
        answer_directions.push_back("DOWN");
    }
    else {
        j -= 1;
        answer_directions.push_back("RIGHT");
    }
    answer.push_back({i, j});
}
reverse(answer.begin(), answer.end());
reverse(answer_directions.begin(), answer_directions.end());
```

2\) 不存储数组 prev，而是根据数组 dp 推断小乌龟是从哪里来到当前格子的。

在这个例子中这相当容易。如果已经算好了整个数组 dp，就可以从末尾开始轻松判断：在最优路线中小乌龟是从上方还是左方到达该格子的——它来自硬币数更多的那个格子。

``` C++ numberLines
while (i > 0 || j > 0) {
    if (i != 0 && (j == 0 || dp[i - 1][j] > dp[i][j - 1])) {
        i -= 1;
        answer_directions.push_back("DOWN");
    }
    else {
        j -= 1;
        answer_directions.push_back("RIGHT");
    }
    answer.push_back({i, j})
}
reverse(answer.begin(), answer.end());
reverse(answer_directions.begin(), answer_directions.end());
```