---
title: 梯度下降
---


```
# 第二部分：深度学习

首先回顾机器学习的基本概念。

什么是建模？建模就是试图以某种方式刻画特征（$X$）与目标变量（$y$）之间的依赖关系（函数）。

* 为此，我们会借助关于理想解形态的某种假设。例如，我们可以说「对某个 $k$，$y = f_k(x) = kx + \epsilon$」，也就是假设变量 $x$ 与 $y$ 之间存在某种线性关系，但比例系数未知——此时 $k$ 就称为模型的**参数**。
* 接着，我们引入某个**损失函数**（例如 $l(y') = (y'-y)^2$），并挑选使损失函数期望值最小的模型参数。

如何挑选这些参数？在类似线性回归的简单情形下，参数可以解析求出：求导、令其为零、然后解方程组。但有时候这些函数要复杂得多。此时该如何优化它们？
```

## 欢迎来到可微函数的世界

作者从「寻找最小值的难易程度」出发，定义了下面这种「好函数」的层级：

* 可解析求解——它们的全局最小值可以用某个简单的公式表示。例子：线性回归。
* 凸函数。它们的解有保证，且唯一，可以用各种方法快速求出，尤其是梯度下降（不过通常还有更快的办法）。例子：逻辑回归。
* 可微函数。可以对它们应用梯度下降，而且它收敛到的可能不是局部最小值，而是全局最小值*。*<-- 你现在在这里**
* 离散函数。这里通常没什么好办法，但至少我们能很快求出函数值。
* 不可计算函数。有时我们需要估计一些完全无法用数学形式化的东西——比如翻译质量，或者用户行为。研究不可计算函数的是强化学习（Reinforcement Learning）。

在本课程中，你们将用各种方法构建模型，这些模型只由关于参数*可微*的变换组成，从而可以寻找（有时成功，有时不成功）使损失函数期望达到最小的参数集合。

## 梯度下降

**梯度**是一个向量（一组数），其每个分量是函数对相应自变量的偏导数值（在其余变量固定的前提下）。

**好，它有什么用**？ 假设有一个我们想最小化的函数，并且我们推测它的形状像一个光滑的「坑」。那么可以这样操作：从某个点出发，朝函数下降最快的方向走很多非常小的步子，直到到达局部最小值。

* 「下降最快的方向」是什么意思？意思是「沿梯度的反方向」。
* 什么是「小步子」？就是 $-\lambda \cdot (f'_1, f'_2, \ldots, f'_n)$。通常 $\lambda$ 取 $10^{-3}$ 之类的值。这个参数称为学习率（learning rate）。
* 「直到到达局部最小值」是什么意思？意思是「直到梯度变为零」。实践中我们会检查梯度的范数（即向量长度）是否大于某个非常小的 $\epsilon$。

![grad_descent](images/gradient_descent.png)

只要学习率足够小，我们一定能到达至少一个局部最小值。这个方法称为**梯度下降**，它常被用于优化那些处处都能快速算出梯度的函数。科学目前还无法保证找到任意函数的全局最小值（而且大概率永远都做不到）。

### 随机梯度下降

梯度下降可能需要很多次迭代才能收敛。而且，单次迭代的耗时可能非常长，仅仅因为每次都要遍历整个数据集。因此，梯度下降的每一步我们不使用精确梯度，而使用它的估计：选取几十个样本——这样的集合称为一个批次（batch）——计算它们上的梯度并取平均。这样我们得到的是带噪声但可以接受的梯度估计。这种梯度下降称为随机梯度下降（SGD — stochastic gradient descent）。

为什么不干脆只取一个样本？从理论角度讲，其实可以。但实践中不应该把批次大小设得太小，因为要考虑并行性：在计算这些梯度的设备上，按组而不是逐个处理数据时，每个样本的耗时更少（在 Google Colab 中启用 GPU 并执行下面的单元格试试）。

[可以证明](https://openreview.net/pdf?id=B1Yy1BxCZ)，为了弥补批次大小的减小，需要将学习率按同样的倍数调小。换句话说，噪声更大的梯度估计可以用更小、更谨慎的步子来补偿。

<img width='500px' src='https://sqream.com/wp-content/uploads/2017/03/cpu_vs_gpu-11.png'>

如果你在本地工作，请访问 https://pytorch.org/get-started/locally/ 并安装 PyTorch。


```
import torch
import numpy
```


```
A = numpy.random.randn(1000, 5000)
B = numpy.random.randn(5000, 2000)

%time C = numpy.matmul(A, B)
```


```
A = torch.randn(1000, 5000)
B = torch.randn(5000, 2000)

%time C = torch.matmul(A, B)
```


```
# 如果你通过 Google Colab 打开本笔记本，请启用 GPU
# （左上角 Runtime -> Change runtime type... -> GPU）

A = torch.randn(1000, 5000).cuda()
B = torch.randn(5000, 2000).cuda()

%time C = torch.matmul(A, B)
```

### 启发式方法

在复杂模型——比如神经网络——中，被优化函数的曲面通常看起来非常可怕：

<img width='250px' src='https://ml4a.github.io/images/figures/non_convex_function.png'>

优化过程中的「坏」点实际上有两种类型：梯度为零的点和梯度为无穷的点。

**动量（Momentum**）。如果我们落入了梯度几乎为零的点该怎么办？每次不再沿当前点的梯度方向迈步，而是沿之前所有迭代中梯度*指数加权平均*的方向迈步（最近几次迭代的梯度权重更大）。为此引入一个超参数 $0 < \gamma < 1$，并为每个参数保存其梯度的加权平均，按如下公式更新：

$$ \hat{g}_i = \hat{g}_{i-1} \cdot \gamma + g_i $$

<img width='250px' src='https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Saddle_point.svg/300px-Saddle_point.svg.png'>

**RMSProp**。如果我们身处「悬崖」边上该怎么办？用同样的方式维护梯度*平方*的平均，并在更新参数时对梯度做归一化：除以这个估计值的平方根。这样优化器就能适应「湍流」区域，在其中减小步长，避免参数因为悬崖而飞出去。

<img width='250px' src='https://3.bp.blogspot.com/-fJQ8OM1dHl4/WV363VZZVqI/AAAAAAAAFSk/0e0EuS3WZ9gv5jW93cuF-XjU2FAN42VMQCLcBGAs/s1600/gradient_clipping.png'>

将这两种启发式方法结合起来的算法叫 **Adam**。它是深度学习中最常用的优化器之一。

更多关于梯度下降启发式方法的内容可以在这里阅读：http://ruder.io/optimizing-gradient-descent/

----

## 实践部分：框架

要用梯度下降关于参数优化损失函数，首先至少要能算出这个梯度。你们在第 3 节课上会体会到，手工做这件事非常痛苦。为此出现了各种框架，它们可以替我们自动计算导数。除了其主要功能（支持高效的自动微分与优化器），它们还提供机器学习中各种有用的抽象。

框架有很多，而且越来越多。我们将使用 **PyTorch**。你会觉得它非常像 numpy——本质上 numpy 能做的它都能做，只是它还能计算关于参数的梯度。

PyTorch 可以当作 numpy 的替代品：


```
x = torch.tensor([1., 2., 3.])
y = torch.tensor([4., 5., 6.])
z = x + y

print(z)
```


```
# 创建变量时可以加上 requires_grad 标志
x = torch.tensor([1., 2., 3], requires_grad=True)

# 有了这个标志，我们可以做和以前一样的操作
y = torch.tensor([4., 5., 6], requires_grad=True)
z = torch.dot(x, y)
print(z)
```

...但现在 z 对自己有所了解：


```
print(z.grad_fn)
```

`z` 是标量，我们可以求出整个计算图关于它的导数：


```
z.backward()
```

现在，所有带 requires_grad=True、并且在计算 z 的过程中以任何方式使用过的变量旁边，都会出现它们的梯度。


```
print(x.grad)
print(y.grad)
```

之后我们可以利用这些梯度，在梯度下降中恰当地移动参数。

## MNIST

以上内容都比较抽象。来看一个更具体的例子。

MNIST 数据集包含 70000 张 0 到 9 的黑白数字图片，每张 28×28 像素。任务是给定一张图片，预测它所对应的最可能的数字。

<img width='400px' src='https://camo.githubusercontent.com/24545a9ca1aa3b5d1036bd3deaed3ed7ec6cfdc4/68747470733a2f2f692e696d6775722e636f6d2f4954726d3978342e706e67'>

**神经网络**只不过是对输入数据的一连串可微操作。通常这些作用在向量上的批量操作称为**层**。最简单的例子是矩阵乘法，后面跟着一个 `softmax` 操作：

$$ \sigma(x)_k = \frac{e^{x_k}}{\sum_i e^{x_i}} $$

它返回一个概率分布：不难验证每个元素都非负，且所有 $\sigma_i$ 之和为 1。如果还记得的话——我们刚刚描述的就是逻辑回归，它在某种意义上也是一种非常简单的神经网络。

我们来训练一个神经网络，它接受大小为 $784 = 28^2$ 的向量并返回概率分布。**重要**：出于计算方面的原因，我们几乎总是按批次处理数据，因此输入和中间数据的形状总是形如 (batch_size x dim)。


```
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import datasets, transforms

import matplotlib.pyplot as plt
%matplotlib inline
```


```
def get_loader(train, batch_size):
    '''会下载 MNIST 并保存在旁边某处。'''

    # PyTorch 中的 Dataset 是某种对象，它包装原始数据并对数据做一些预处理
    dataset = datasets.MNIST('mnist', train=train, download=True,
        transform=transforms.ToTensor())

    # DataLoader 把数据集变成生成器，按批次分组返回数据
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

    return loader

train = get_loader(True, 64)
val = get_loader(False, 64)
```

第一节课不需要详细了解 Dataset 和 DataLoader 的内部构造，但将来阅读 pytorch.org 上的这个教程会很有用：https://pytorch.org/tutorials/beginner/data_loading_tutorial.html

我们选择交叉熵作为损失函数——和逻辑回归一样。PyTorch 中有个函数接受概率的对数和正确答案，返回交叉熵——`nn.NLLLoss`（negative log likelihood loss）。出于计算原因（主要是精度问题），我们几乎总是使用概率的对数而不是概率本身。要让网络输出对数概率，需要把 `nn.LogSoftmax` 层加为最后一层。

### 如何创建简单的模型

构建神经网络的基本结构是 nn.Sequential，它接受一组层作为参数，数据将依次经过这些层。层有两种类型：一种需要知道张量的维度，另一种不需要。重要的是理解：因为数据是按顺序通过各层的，张量的尺寸可能会逐层变化。

列出初期必需的层：


* nn.Linear —— 执行线性变换的层。实际上，在简单模型中我们训练的就是它——挑选所需的变换系数。使用 nn.Linear 需要指明输入张量的维度和期望的输出维度。例如，nn.Linear(784, 10) 把形状为 (batch_size, 784) 的张量变换为形状为 (batch_size, 10) 的张量。
* nn.ReLU —— 应用 ReLU 函数的层，该函数具有非线性性质。为什么要非线性，稍后解释。
* nn.Sigmoid —— 应用 Sigmoid 函数的层，该函数有两个性质：第一，非线性；第二，其值落在 [0, 1] 区间内。如果只需要非线性，最好用 ReLU（因为存在梯度消失问题）。
* nn.Softmax —— 上面已经讲过。这个层根据数据输出概率分布，主要用于分类任务。




### 为什么需要非线性

非线性函数也叫激活函数。包含这些函数的层通常不含训练时需要优化的参数，它们的作用是防止线性函数相互复合。毕竟线性函数的复合仍然是线性函数。如果允许复合，那么对于层 B 与 C 的复合，总存在一个参数相同、但训练资源消耗更少的层 A。


```
model = nn.Sequential(
    # 若干个 nn.Linear 和非线性层
    # ...
    nn.LogSoftmax(dim=1)
)
```

交叉熵不太直观——它是以某种「鹦鹉」为单位度量的，而不是易懂的单位。我们更关心分类的绝对准确率：


```
def accuracy(model, val):
    total = 0
    correct = 0
    for X, y in val:
        X = X.view(-1, 784)
        res = model(X)
        res = res.argmax(dim=1)
        total += res.shape[0]
        correct += (res == y).sum().item()
    return correct / total
```

## 训练

下面这些代码块非常重要，因为我们会一直用到它们。这里发生了什么：


1.   optimizer——负责梯度下降和更新模型参数的对象。
2.   criterion——我们要最小化的那个损失函数。
3.   epoch——轮次。我们想把整个训练数据集处理若干次（例如 10 次），并在其上训练。
4.   zero_grad——把优化器之前保存的所有梯度数据清零。
5.   output——得到模型的输出结果。
6.   loss——计算损失函数。
7.   backward——得到优化器在这一步更新模型参数时要用到的梯度（见 [backpropagation](https://colab.research.google.com/drive/1U2rElWU-0QVjSy421fsTrRMPUK2p9v9F#scrollTo=JpKNvmHR1I_e&line=12&uniqifier=1)）。
8.   step——优化器更新整个模型。




```
optimizer = torch.optim.Adam(model.parameters(), lr=1e-2)
criterion = nn.NLLLoss()
# ^ 如果你还不信交叉熵，试试别的损失函数并比较一下
```


```
train_losses = []
for epoch in range(10):
    for X, y in train:
        X = X.view(-1, 784)  # 把图片展平成向量

        optimizer.zero_grad()

        output = model(X)
        loss = criterion(output, y)
        loss.backward()

        train_losses.append(loss.item())
        # 想一想，为什么需要 .item()？
        # 提示：loss 保存了自己的历史信息
        # 试着去掉 .item()，观察内存消耗

        optimizer.step()

    print(accuracy(model, train), accuracy(model, val))

plt.plot(train_losses)
plt.show()
```

### 正则化

你可能会注意到，从某个时刻起 `val` 上的损失函数不再下降（随后甚至开始上升），而 `train` 上的损失稳定下降。这与过拟合有关。如果网络足够大，神经元就能通过自我调整在单个样本上取得更小的损失，但这无法很好地泛化到模型没见过的数据上。例如，网络可能学会「如果这个像素取某个值，那它就是 6」这样的规则，在网络结构中表现为神经元之间极强的连接。为此，神经网络中使用对网络权重或训练过程的正则化方法。

目前最流行的是 Dropout（PyTorch 中是 `nn.Dropout`）。它是一个单独的层，训练时以概率 $p$ 独立地将每个元素置零。这能阻止神经元过度适应。

<img width='600px' src='https://cdn-images-1.medium.com/max/1200/1*iWQzxhVlvadk6VAJjsgXgg.png'>

## 自编码器

**自编码器**是学习重建自己输入数据的网络。这种训练方式有时称为自监督（self-supervised）。


<img width='400px' src='https://habrastorage.org/web/cf6/228/613/cf6228613fdc4f8fb819cbd41bb677eb.png'>

看起来学习 $f(x) = x$ 这样的函数非常容易，但自编码器的结构决定了：其内部所有信息在某个时刻都要经过一个维度很小的隐藏层，因此自编码器根本无法把输入完美复制到输出。

所以网络不得不在这个隐藏层中学出非常紧凑且富含信息的数据表示，之后可以用它做各种有趣的事情。

例如用于可视化：可以把隐藏层大小设为 2，然后把数据画到平面上。

<img width='800px' src='https://i.stack.imgur.com/2gSs1.png'>

处处可见的 PCA 实际上是自编码器的一个特例：其中只允许使用线性变换。

我们还可以用隐藏状态做变形（morphing）——对象之间的平滑过渡。

<img width='250px' src='https://camo.githubusercontent.com/fa61cfca07320919eb6430a2a06f98d3e68e29c1/68747470733a2f2f692e696d6775722e636f6d2f4f72554a7339562e676966'>

把已在数据上训练好的编码器记为函数 $e$，解码器记为函数 $g$。那么图像 $A$ 与 $B$ 之间的变形可以这样做：先把图像 A 和 B 转换到隐藏状态 $a = e(A)$ 与 $b = e(B)$，然后每一帧按如下方式生成

$$ C = d((1-t) \cdot a + t \cdot b) $$

其中 $t$ 在 0 到 1 之间均匀变化。换句话说，我们取线段 ab 上的所有点并依次解码。

这就是你们要实现的。


```
class Autoencoder(nn.Module):
    def __init__(self):
        super().__init__()

        self.encode = nn.Sequential(
            # 我们想把图片转换到某个 X 维空间
        )

        self.decode = nn.Sequential(
            # 现在反过来——从 X 维空间回到图片
            nn.Sigmoid()
            # 图片是取值在 0 到 1 之间的张量
            # 输出这个区间之外的值没什么意义
        )

    def forward(self, x):
        return self.decode(self.encode(x))

model = Autoencoder()
criterion = torch.nn.MSELoss()
#                    ^ 也可以试试别的差异度量（比如绝对误差）
optimizer = torch.optim.Adam(model.parameters())
```


```
for epoch in range(10):
    train_loss = 0
    for data, _ in train:
        #     ^ 我们不需要标签
        data = data.view(-1, 784)

        optimizer.zero_grad()

        reconstructed = model(data)
        loss = criterion(data, reconstructed)

        loss.backward()

        train_loss += loss.item()
        optimizer.step()

    print('epoch %d, loss %.4f' % (epoch, train_loss / len(train)))
```

现在试着像上面那样做个 GIF 动画。

`matplotlib` 的动画很折磨人，不必费力去理解下面的代码。你可能需要完成一个支线任务：安装 `ffmpeg`（在大多数情况下，`apt install ffmpeg`、`pip install ffmpeg` 并重启笔记本就够了）。


```
from matplotlib import animation
from matplotlib.animation import FuncAnimation
from IPython.display import HTML, display
```


```
def get(x):
    return train.dataset[x][0].view(1, 784)

def imshow(img):
    pic = img.numpy().astype('float')
    plt.axis('off')
    return plt.imshow(pic, cmap='Greys', animated=True)

def morph(inputs, steps, delay):
    # 把输入的所有图片转换到潜在空间
    latent = [model.encode(get(k)).data for k in inputs]
    fig = plt.figure()
    images = []
    for a, b in zip(latent, latent[1:] + [latent[0]]):
        for t in numpy.linspace(0, 1, steps):
            # 得到插值点
            c = a*(1-t)+b*t
            # ...并把它解码成图像
            morphed = model.decode(c).data
            morphed = morphed.view(28, 28)
            images.append([imshow(morphed)])

    ani = animation.ArtistAnimation(fig, images, interval=delay)

    display(HTML(ani.to_html5_video()))
```


```
morph(numpy.random.randint(0, len(train.dataset), 30), 20, 30)
```

# 家庭作业

* 在 MNIST 验证集上取得 97% 的准确率。
* 用自编码器实现变形（得到漂亮的 GIF 动画）。
* 用自编码器可视化 MNIST（训练一个潜在空间维度为 2 的自编码器，用 scatter 画出不同颜色的点即可）。

### *卷积

如果还有时间，你可以用卷积来改进结果。

卷积网络的细节将在下一节课讲，目前你可以把 `nn.Conv2d`、`nn.MaxPool2d` 和 `nn.ConvTranspose2d` 当作分类器和自编码器中更高级的层来使用，不必太理解它们的内部原理。

「神经工程师」的主要任务是：设想这个问题的解在「带未知参数的程序」层面应该长什么样，并挑选相应的架构。[关于 Dropout 的实验](https://arxiv.org/pdf/1701.05369.pdf)表明，Linear 中大约 99% 的权重实际上可以丢掉。合理的架构中不应该有无用的权重——多余的参数总是导致过拟合。对于图片，解决办法是利用像素之间的相对位置信息，构造一个关注更相关特征的层。动机大致如此，细节下周再讲。

<img width='250px' src='https://cdn-images-1.medium.com/max/1600/0*iqNdZWyNeCr5tCkc.'>
