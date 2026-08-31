from __future__ import annotations
from itertools import combinations
import numpy as np

def _product(subset, probs):
    out = 1.0
    for i in subset:
        out *= float(probs[i])
    return out

def find_top_k_product_sets(candidate_indices, probs, subset_size, k):
    all_subsets = list(combinations(candidate_indices, subset_size))
    vals = [_product(s, probs) for s in all_subsets]
    if not vals:
        return [], []
    idx = np.argsort(vals)[-k:][::-1]
    return [all_subsets[i] for i in idx], [vals[i] for i in idx]

def calculate_topk_accuracy(y_true, y_pred, k_values=(1, 3, 5, 10, 20), use_pred_threshold=False):
    hits = {k: 0 for k in k_values}
    valid = 0
    for i in range(y_true.shape[0]):
        true_idx = np.where(y_true[i] == 1)[0]
        if len(true_idx) == 0:
            continue
        valid += 1
        true_set = set(true_idx)
        if use_pred_threshold:
            pred = np.where(y_pred[i] > 0.5)[0]
            if len(pred) != len(true_set):
                continue
            n = len(pred)
        else:
            n = len(true_set)
        order = np.argsort(-y_pred[i])
        for k in k_values:
            if true_set.issubset(set(order[:max(k, n)])):
                hits[k] += 1
    return {f"top_{k}_acc": hits[k] / max(valid, 1) for k in k_values}

def calculate_combination_accuracy(y_true, y_pred, k_values=(1, 3, 5, 10, 20), top_candidates=20, use_pred_threshold=False):
    max_k = max(k_values)
    hits = {k: 0 for k in k_values}
    valid = 0
    for i in range(y_true.shape[0]):
        true_idx = np.where(y_true[i] == 1)[0]
        if len(true_idx) == 0:
            continue
        valid += 1
        if use_pred_threshold:
            pred = np.where(y_pred[i] > 0.5)[0]
            if len(pred) != len(true_idx):
                continue
            size = len(pred)
        else:
            size = len(true_idx)
        cands = np.argsort(-y_pred[i])[:min(top_candidates, y_pred.shape[1])]
        sets, _ = find_top_k_product_sets(cands, y_pred[i], size, max_k)
        sets = [tuple(sorted(s)) for s in sets]
        true = tuple(sorted(true_idx))
        try:
            pos = sets.index(true)
        except ValueError:
            continue
        for k in k_values:
            if pos < k:
                hits[k] += 1
    return {f"top_{k}_combo_acc": hits[k] / max(valid, 1) for k in k_values}
