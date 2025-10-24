import re
import numpy as np
from numba import njit
from itertools import chain
from joblib import Parallel, delayed
from typing import Literal

class LabelMatrix:
    def __init__(self):
        self.labels_ = None
    
    def fit_transform(self, labels, control_label=None, sep_pattern=r'[,;_\s]', speedup: Literal['none','vectorize','parallel']='none'):
        if speedup=='none':
            mat, self.labels_ = label_to_matrix(labels=labels, sep_pattern=sep_pattern)
        elif speedup=='vectorize':
            mat, self.labels_ = vectorized_label_to_matrix(labels=labels, sep_pattern=sep_pattern)
        elif speedup=='parallel':
            mat, self.labels_ = parallel_label_to_matrix(labels=labels, sep_pattern=sep_pattern)
            
        self.labels_ = np.array(self.labels_)
        
        if control_label is not None:
            idx = np.where(self.labels_==control_label)[0]
            mat = np.delete(mat, idx, axis=1)
            self.labels_ = np.delete(self.labels_, idx)
            
        return mat
            
    def inverse_transform(self, matrix):
        return matrix_to_labels(matrix=matrix, unique_labels=self.labels_)

class DoseMatrix:
    def __init__(self):
        self.labels_ = None 
        
    def fit_transform(self, labels, label_dose, control_label=None):
        mat, self.labels_ = dose_to_matrix(labels, label_dose)
        
        if control_label is not None:
            idx = np.where(self.labels_==control_label)[0]
            mat = np.delete(mat, idx, axis=1)
            self.labels_ = np.delete(self.labels_, idx)
            
        return mat 
        
def label_to_matrix(labels, sep_pattern=r'[;_\-\s]'):
    """
    将混合分隔符的多标签数据转换为 0-1 矩阵
    
    Args:
        labels: 原始标签列表，如 ["cat", "dog", "cat;dog", "bird_dog"]
        sep_pattern: 多标签分隔符的正则模式（默认匹配 ; _ - 和空格）
    
    Returns:
        one_hot_matrix: 0-1 矩阵
        unique_labels: 唯一标签列表
    """
    # 统一分隔符
    labels_unified = [re.sub(sep_pattern, ';', label) for label in labels]
    
    # 获取所有唯一标签
    all_unique_labels = sorted(set(chain(*[label.split(';') for label in labels_unified])))
    
    # 生成 0-1 矩阵
    matrix = np.zeros((len(labels), len(all_unique_labels)), dtype=int)
    label_to_idx = {label: i for i, label in enumerate(all_unique_labels)}
    
    for i, label in enumerate(labels_unified):
        for sub_label in label.split(';'):
            if sub_label in label_to_idx:
                matrix[i, label_to_idx[sub_label]] = 1
    
    return matrix, all_unique_labels


def vectorized_label_to_matrix(labels, sep_pattern=r'[;_\-\s]'):
    labels_unified = [re.sub(sep_pattern, ';', label) for label in labels]
    unique_labels = sorted(set(chain(*[label.split(';') for label in labels_unified])))
    
    # 向量化操作
    label_matrix = np.array([label.split(';') for label in labels_unified], dtype=object)
    matrix = np.zeros((len(labels), len(unique_labels)), dtype=int)
    
    for i, label in enumerate(unique_labels):
        matrix[:, i] = np.array([label in lst for lst in label_matrix], dtype=int)
    
    return matrix, unique_labels



def parallel_label_to_matrix(labels, sep_pattern=r'[;_\-\s]', n_jobs=4):
    labels_unified = [re.sub(sep_pattern, ';', label) for label in labels]
    unique_labels = sorted(set(chain(*[label.split(';') for label in labels_unified])))
    
    def process_row(row_labels, unique_labels):
        return [1 if label in row_labels else 0 for label in unique_labels]
    
    label_lists = [label.split(';') for label in labels_unified]
    matrix = Parallel(n_jobs=n_jobs)(
        delayed(process_row)(row, unique_labels) for row in label_lists
    )
    
    return np.array(matrix, dtype=int), unique_labels


def matrix_to_labels(matrix, unique_labels):
    return [';'.join([unique_labels[i] for i in np.where(row)[0]]) 
            for row in matrix]







@njit(parallel=True)
def _numba_fill_matrix(dose_matrix, label_indices, label_doses):
    """Numba 加速的矩阵填充函数"""
    for i in range(len(label_indices)):
        dose_matrix[i, label_indices[i]] = label_doses[i]

def dose_to_matrix(labels, label_dose, all_labels=None):
    """
    使用 Numba 的终极加速版本（需预先安装 numba）
    """
    if all_labels is None:
        all_labels = sorted(set().union(labels))
    
    label_to_idx = {label: idx for idx, label in enumerate(all_labels)}
    n_samples = len(labels)
    n_labels = len(all_labels)
    dose_matrix = np.zeros((n_samples, n_labels), dtype=np.float64)
    
    # 预处理为 Numba 兼容格式
    label_indices = []
    label_doses = []
    for i, label in enumerate(labels):
        label_indices.append(label_to_idx[label])
        label_doses.append(label_dose[i])
    
    # 调用 Numba 加速函数
    _numba_fill_matrix(dose_matrix, label_indices, label_doses)
    return dose_matrix,np.array(all_labels)