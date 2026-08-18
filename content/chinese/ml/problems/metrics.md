---
title: 分类的评估指标
---

分类错误分为**假阳性（False Positive**）和**假阴性（False Negative**）。在统计学中，前一种错误称为第一类错误，后一种称为第二类错误。

![](../img/errors.png)

## Accuracy

$$\text { accuracy }=\frac{T P+T N}{T P+T N+F P+F N}$$

**Accuracy（准确率**）是算法给出正确答案的比例。在类别不平衡的问题中，这个指标没有用处。

## Precision

$$\text { precision }=\frac{T P}{T P+F P}$$

**Precision（精确率**）是指被分类器判为正类的对象中确实为正类的比例。

## Recall

$$\text { recall }=\frac{T P}{T P+F N}$$

**Recall（召回率**）是指所有正类对象中被正确找出的正类对象所占的比例。

*Recall* 体现算法发现某个类的能力，而 *precision* 体现把该类与其他类区分开的能力。

## F 值

$$F_{\beta}=\left(1+\beta^{2}\right) \cdot \frac{\text { precision } \cdot \text { recall }}{\left(\beta^{2} \cdot \text { precision }\right)+\text { recall }}$$

**F 值**（一般形式为 $F_{\beta}$）是 *precision* 和 *recall* 的调和平均。

这里的 $\beta$ 决定该指标中精确率的权重；当 $\beta=1$ 时它就是调和平均（乘上因子 2，是为了在 *precision* = 1 且 *recall* = 1 时得到 $F_{1}=1$）。

**F 值**在召回率和精确率都等于 1 时达到最大值；当其中一个参数接近 0 时，它也会接近 0（与算术平均不同，调和平均在至少一个值趋近于 0 时趋近于 0）。

## ROC-AUC

**ROC AUC** 是错误分类曲线（受试者工作特征曲线 Receiver Operating Characteristic curve）下的面积（Area Under Curve）。该曲线是坐标轴为 *True Positive Rate (TPR)* 和 *False Positive Rate (FPR)* 的平面中从 (0,0) 到 (1,1) 的一条线：

$$\begin{aligned}
T P R &=\frac{T P}{T P+F N} \\
F P R &=\frac{F P}{F P+T N}
\end{aligned}$$

::: center
![图片](tickets/pictures/curve.png)
:::

## LogLoss

$$\text { logloss }=-\frac{1}{l} \cdot \sum_{i=1}^{l}\left(y_{i} \cdot \log \left(\hat{y}_{i}\right)+\left(1-y_{i}\right) \cdot \log \left(1-\hat{y}_{i}\right)\right)$$

这里 $\hat{y}$ 是算法在第 $i$ 个样本上的输出，$y$ 是第 $i$ 个样本的真实类别标签，$l$ 是数据集大小。

可以把最小化 *logloss* 理解为：通过对错误预测施加惩罚来实现 *accuracy* 的最大化。不过*，logloss* 会对分类器在错误答案上的高置信度施加极其严厉的惩罚。

## 多分类问题

把多分类问题转化为二分类问题的主要方法：**one-vs-all**（为每个类训练一个二分类器，把它与其余所有类区分开）和 **all-vs-all**（为每对不同的类训练 $C_{K}^{2}$ 个分类器，结果为得票最多的类）。

把质量评估归结为分类指标时，有两种做法：**微平均**和**宏平均**。

设数据集由 $K$ 个类组成。考虑 $K$ 个二分类问题，每个问题都把其中一个类与其余类分开。对它们可以计算
$\mathrm{TP}_{k}, \mathrm{FP}_{k}, \mathrm{FN}_{k}, \mathrm{TN}_{k} .$

## 微平均 {#微平均 .unnumbered}

在*微平均*中，先对所有类求这些指标的平均值，然后计算最终的二分类指标——例如*精确率*、*召回率*或*F 值*。例如*，精确率*按公式
$$\operatorname{precision}(a, X)=\frac{\overline{\mathrm{TP}}}{\overline{\mathrm{TP}}+\overline{\mathrm{FP}}}$$
计算，其中例如 $\overline{\mathrm{TP}}$ 按公式
$$\overline{\mathrm{TP}}=\frac{1}{K} \sum_{k=1}^{K} \mathrm{TP}_{k}$$
计算

## 宏平均 {#宏平均 .unnumbered}

在*宏平均*中，先为每个类计算最终指标，然后把结果对所有类取平均。例如*，精确率*计算为
$$\operatorname{precision}(a, X)=\frac{1}{K} \sum_{k=1}^{K} \operatorname{precision}_{k}(a, X) ; \quad \text { precision }_{k}(a, X)=\frac{\mathrm{TP}_{k}}{\mathrm{TP}_{k}+\mathrm{FP}_{k}}$$