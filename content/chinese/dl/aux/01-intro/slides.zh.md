# 深度学习（Deep Learning）

第 1 讲

Sergey Slotin\
2021 年 2 月 12 日

---

## 建模

* 我们试图找到特征（$X$）与目标变量（$y$）之间的函数
* 我们借助关于理想解应该是什么样子的假设。例如：「$y = f_k(x) = kx + \epsilon$，其中 $k$ 是某个常数」
* 然后我们引入某种**损失函数**（例如 $l(y') = (y'-y)^2$），并挑选使它的期望值最小的模型参数。

---

![](https://sqream.com/wp-content/uploads/2017/03/cpu_vs_gpu-11.png)

---

![](https://ml4a.github.io/images/figures/non_convex_function.png)