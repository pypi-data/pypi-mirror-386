---
comments: true
---

# PaddleX Time Series Anomaly Detection Task Module Data Annotation Tutorial

Time series anomaly detection is an unsupervised learning task, thus there is no need to annotate training data. The collected training samples should ideally consist solely of normal data, i.e., no anomalies (represented by 0 for no anomaly). In the training set, the label column indicating anomalies can be set to 0 or omitted entirely. For the validation set, to evaluate model accuracy, annotations are required. For points that are anomalous at a specific time, set the label for that time point to 1, and the labels for other normal time points to 0.
