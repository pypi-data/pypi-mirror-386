---
comments: true
---

# PaddleX时序分类任务模块数据标注教程

标注时序分类数据时，基于收集的真实数据，明确时序数据的分类目标，并定义相应的分类标签。在`csv`文件中设置表示样本的`groud_id`列，同一个 `group_id`就表示属于同一个样本。例如，在股票价格预测中，标签可能是“上涨”（0）、“持平”（1）或“下跌”（2）。对于在一段时间是“上涨”的时间序列，可以作为一个样本（group），即这段时间序列每个时间点都具有共同的 `group_id`, 标签列我们都设置为 0 ；对于在一段时间是“下跌”的时间序列，可以作为一个样本（group），即这段时间序列每个时间点都具有共同的 `group_id`, 标签列我们都设置为2。如下图，绿色框是一个样本(groud_id=0)，类别(label)是1，红色框是另一个时序分类样本(groud_id=1)，类别(label)是0，如果有n个样本可以设置groud_id=0,...n-1；每个样本长度(time=0,...,9)都是10，特征维度（dim_0, dim_1）是2。

<img src="https://raw.githubusercontent.com/cuicheng01/PaddleX_doc_images/main/images/data_prepare/time_series/02.png">
