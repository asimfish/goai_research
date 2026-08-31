from __future__ import annotations

import ast
import hashlib
import json
import logging
import pickle
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from pymatgen.core import Element
from pymatgen.core.composition import Composition

PACKAGE_ROOT = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_ROOT / "data"
logger = logging.getLogger(__name__)
SUPPORTED_DATASETS = {"retro", "ceder"}


def parse_precursor_ids(value):
    if isinstance(value, list):
        return [int(x) for x in value]
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    text = str(value).strip()
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (list, tuple, set)):
            return [int(x) for x in parsed]
        return [int(parsed)]
    except Exception:
        return [int(x) for x in text.replace(";", ",").split(",") if x.strip()]


def dataset_file(dataset_type: str, suffix: str) -> Path:
    if dataset_type not in SUPPORTED_DATASETS:
        raise ValueError(f"Unsupported dataset_type={dataset_type!r}; expected one of {sorted(SUPPORTED_DATASETS)}")
    return DATA_DIR / f"{dataset_type}_{suffix}"


def default_charge_path(dataset_type: str) -> Path:
    deepseek_path = dataset_file(dataset_type, "deepseek_charge.csv")
    if deepseek_path.exists():
        return deepseek_path
    return dataset_file(dataset_type, "charge.csv")


def infer_dataset_type(csv_path: Path | None, dataset_type: str) -> str:
    if dataset_type != "auto":
        return dataset_type
    if csv_path is None:
        return "retro"
    name = csv_path.name
    for candidate in SUPPORTED_DATASETS:
        if name.startswith(f"{candidate}_"):
            return candidate
    raise ValueError(f"Cannot infer dataset type from {csv_path}; pass --dataset explicitly.")


def load_dataset(log=None, csv_path=None, dataset_type="retro"):
    log = log or logger
    csv_path = Path(csv_path) if csv_path else None
    dataset_type = infer_dataset_type(csv_path, dataset_type)
    if dataset_type not in SUPPORTED_DATASETS:
        raise ValueError(f"Unsupported dataset_type={dataset_type!r}; expected one of {sorted(SUPPORTED_DATASETS)}")
    csv_path = csv_path or dataset_file(dataset_type, "split.csv")
    precursor_id_path = csv_path.parent / f"{dataset_type}_precursor_id.json"
    precursor_charge_path = default_charge_path(dataset_type)
    log.info("Reading dataset: %s", csv_path)
    log.info("Reading precursor ids: %s", precursor_id_path)
    log.info("Reading precursor charges: %s", precursor_charge_path)
    df = pd.read_csv(csv_path)
    charge_df = pd.read_csv(precursor_charge_path)
    charge_df["elements"] = charge_df["elements"].apply(ast.literal_eval)
    charge_df["charges"] = charge_df["charges"].apply(ast.literal_eval)
    precursor_species_id = charge_df.apply(
        lambda row: [(el, int(charge)) for el, charge in zip(row["elements"], row["charges"])], axis=1
    )
    df["precursor_id_list"] = df["precursor_ids"].apply(parse_precursor_ids)
    with open(precursor_id_path, "r", encoding="utf-8") as f:
        precursor_id_mapping = json.load(f)
    max_precursor_id = max(int(idx) for idx in precursor_id_mapping.keys())
    return df, precursor_id_mapping, precursor_species_id, max_precursor_id, str(csv_path)


def split_data(df, X, max_precursor_id, log=None):
    y_binary = np.zeros((len(df), max_precursor_id + 1), dtype=np.float32)
    for i, ids in enumerate(df["precursor_id_list"]):
        for pid in ids:
            if 0 <= int(pid) <= max_precursor_id:
                y_binary[i, int(pid)] = 1.0
    train_mask = df["type"].values == "train"
    val_mask = df["type"].values == "val"
    test_mask = df["type"].values == "test"
    X_train, y_train = X[train_mask], y_binary[train_mask]
    X_val, y_val = X[val_mask], y_binary[val_mask]
    X_test, y_test = X[test_mask], y_binary[test_mask]
    if log:
        log.info("Split sizes: train=%d val=%d test=%d", len(X_train), len(X_val), len(X_test))
    return X_train, y_train, X_val, y_val, X_test, y_test, X.shape[1], max_precursor_id + 1


def extract_element_composition_features(formulas, cache_file=None):
    if cache_file and Path(cache_file).exists():
        with open(cache_file, "rb") as f:
            return pickle.load(f)["X"]
    elems = list(Element)
    rows = []
    for formula in formulas:
        try:
            comp = Composition(str(formula))
            total = sum(comp.values())
            rows.append(np.array([comp.get(e, 0) / total if total > 0 else 0 for e in elems], dtype=np.float32))
        except Exception:
            rows.append(np.zeros(118, dtype=np.float32))
    X = np.asarray(rows, dtype=np.float32)
    if cache_file:
        Path(cache_file).parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "wb") as f:
            pickle.dump({"X": X}, f)
    return X


def prepare_data(args, device="cpu"):
    cache_dir = Path(getattr(args, "cache_dir", PACKAGE_ROOT / "artifacts/cache"))
    dataset = getattr(args, "dataset", "retro")
    data_path = getattr(args, "data_path", None)
    df, precursor_id_mapping, precursor_species_id, max_precursor_id, csv_path = load_dataset(logger, data_path, dataset)
    cache_dir.mkdir(parents=True, exist_ok=True)
    csv_hash = hashlib.md5(Path(csv_path).read_bytes()).hexdigest()[:10]
    X = extract_element_composition_features(df["target"].tolist(), cache_dir / f"features_mpc_{dataset}_{csv_hash}.pkl")
    precursor_formulas = [v[0] for _, v in sorted(precursor_id_mapping.items(), key=lambda kv: int(kv[0]))]
    precursor_X = extract_element_composition_features(
        precursor_formulas, cache_dir / f"features_mpc_precursor_{dataset}_{csv_hash}.pkl"
    )
    X_train, y_train, X_val, y_val, X_test, y_test, input_dim, num_classes = split_data(df, X, max_precursor_id, logger)
    return {
        "X_train": X_train, "y_train": y_train,
        "X_val": X_val, "y_val": y_val,
        "X_test": X_test, "y_test": y_test,
        "precursor_X": precursor_X,
        "precursor_id_mapping": precursor_id_mapping,
        "precursor_species_id": precursor_species_id,
        "num_classes": num_classes,
        "input_dim": input_dim,
    }


def make_data_args(cache_dir=None, data_path=None, dataset="retro"):
    return SimpleNamespace(
        dataset=dataset,
        data_path=data_path,
        cache_dir=str(cache_dir or PACKAGE_ROOT / "artifacts/cache"),
    )
