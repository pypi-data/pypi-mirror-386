---
comments: true
---

# PaddleX时序预测任务模块数据标注教程

时序预测任务的数据是无需标注的，只要收集真实数据，将所有数据按照时间的顺序排列在csv文件中即可。训练时会将数据自动切分为多个时间片段，组合训练样本，如下图所示，历史的时间序列数据和未来的序列分别表示训练模型输入数据和其对应的预测目标。为了保证数据的质量和完整性，可以基于专家经验或统计方法进行缺失值填充。

<img src="https://raw.githubusercontent.com/cuicheng01/PaddleX_doc_images/main/images/data_prepare/time_series/01.png">
