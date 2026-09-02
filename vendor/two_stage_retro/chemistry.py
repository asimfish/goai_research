from __future__ import annotations

import logging
import math
from collections import Counter
from typing import List
import numpy as np
from pymatgen.core import Composition
from .env import VOLATILE_ELEMENTS, IGNORABLE_ELEMENTS

logger = logging.getLogger(__name__)

NUM_ELEMENTS = 118


# ==================== 细粒度特征提取 ====================

def extract_detailed_features(
    pids: List[int],
    probs: np.ndarray,
    target_features: np.ndarray,
    pke: List[Set[int]],
    pm: List[Set[int]],
) -> dict:
    """
    提取 ChemRank 的所有中间变量 (用于可微分公式)

    Returns:
        dict with:
          base: float, 概率几何均值
          kc: float, 关键元素覆盖率
          mc: float, 金属覆盖率
          n_unwanted: int, 不需要的金属数
          is_perfect: bool
          set_size: int
          covered_elems: set, 已覆盖的目标元素
          uncovered_elems: set, 未覆盖的目标元素
          unwanted_metals: set, 引入的不需要金属
          elem_coverage: np.ndarray [118], 每个元素是否被覆盖 (0/1)
          elem_is_target: np.ndarray [118], 每个元素是否是目标元素 (0/1)
          elem_is_unwanted: np.ndarray [118], 每个元素是否是不需要的金属 (0/1)
    """
    te = set(np.where(target_features > 0)[0].tolist()) - IGNORABLE_ELEMENTS
    tm = set(np.where(target_features > 0)[0].tolist()) - VOLATILE_ELEMENTS

    if not pids:
        return {
            'base': 0.0, 'kc': 0.0, 'mc': 0.0, 'n_unwanted': 0,
            'is_perfect': False, 'set_size': 0,
            'covered_elems': set(), 'uncovered_elems': te,
            'unwanted_metals': set(),
            'elem_coverage': np.zeros(NUM_ELEMENTS, dtype=np.float32),
            'elem_is_target': np.zeros(NUM_ELEMENTS, dtype=np.float32),
            'elem_is_unwanted': np.zeros(NUM_ELEMENTS, dtype=np.float32),
            'log_probs': np.zeros(1, dtype=np.float32),
        }

    ps = np.array([max(probs[p], 1e-10) for p in pids])
    base = float(np.exp(np.mean(np.log(ps))))

    ck, cm, um = set(), set(), set()
    for p in pids:
        ck |= pke[p]
        cm |= (pm[p] & tm)
        um |= (pm[p] - tm)

    covered = ck & te
    uncovered = te - ck
    kc = len(covered) / max(len(te), 1)
    mc = len(cm) / max(len(tm), 1)
    n_unwanted = len(um)
    is_perfect = (kc == 1.0 and n_unwanted == 0)

    # 元素级特征
    elem_coverage = np.zeros(NUM_ELEMENTS, dtype=np.float32)
    for e in covered:
        if e < NUM_ELEMENTS:
            elem_coverage[e] = 1.0

    elem_is_target = np.zeros(NUM_ELEMENTS, dtype=np.float32)
    for e in te:
        if e < NUM_ELEMENTS:
            elem_is_target[e] = 1.0

    elem_is_unwanted = np.zeros(NUM_ELEMENTS, dtype=np.float32)
    for e in um:
        if e < NUM_ELEMENTS:
            elem_is_unwanted[e] = 1.0

    return {
        'base': base,
        'kc': kc,
        'mc': mc,
        'n_unwanted': n_unwanted,
        'is_perfect': is_perfect,
        'set_size': len(pids),
        'covered_elems': covered,
        'uncovered_elems': uncovered,
        'unwanted_metals': um,
        'elem_coverage': elem_coverage,
        'elem_is_target': elem_is_target,
        'elem_is_unwanted': elem_is_unwanted,
        'log_probs': np.log(ps),
        'max_prob': float(ps.max()),
        'min_prob': float(ps.min()),
    }


def feats_to_tensor(feat_dict: dict) -> np.ndarray:
    """将 detailed features 转为固定长度向量 [8 + 118*3 = 362]"""
    scalar = np.array([
        feat_dict['base'],
        feat_dict['kc'],
        feat_dict['mc'],
        float(feat_dict['n_unwanted']),
        float(feat_dict['is_perfect']),
        float(feat_dict['set_size']) / 8.0,
        feat_dict['max_prob'],
        feat_dict['min_prob'],
    ], dtype=np.float32)
    return np.concatenate([
        scalar,                          # [8]
        feat_dict['elem_coverage'],      # [118]
        feat_dict['elem_is_target'],     # [118]
        feat_dict['elem_is_unwanted'],   # [118]
    ])  # total: 362


FEAT_DIM = 8 + 118 * 3  # 362



NUM_CHEM_FEATS = 12


# ==================== Anion Leavability ====================

# Higher = easier to decompose/leave as gas
ANION_LEAVABILITY = {
    'carbonate': 0.9,   # CO3 -> CO2 ↑
    'oxalate': 0.9,     # C2O4 -> CO2 ↑
    'nitrate': 0.85,    # NO3 -> NOx ↑
    'hydroxide': 0.8,   # OH -> H2O ↑
    'acetate': 0.75,    # CH3COO -> CO2 + organics ↑
    'oxide': 0.7,       # already oxide, no leaving group needed
    'fluoride': 0.3,    # F hard to remove
    'chloride': 0.5,    # Cl -> HCl ↑ (moderate)
    'bromide': 0.4,     # Br harder
    'iodide': 0.35,     # I harder
    'sulfide': 0.3,     # S hard to remove cleanly
    'sulfate': 0.2,     # SO4 very hard to decompose
    'elemental': 0.6,   # pure element, no anion
    'hydride': 0.7,     # H -> H2 ↑
    'nitride': 0.5,     # N -> N2 ↑ (needs high T)
    'other': 0.4,
}


def classify_precursor_type(name: str) -> str:
    """Classify precursor by anion type."""
    if 'C2O4' in name:
        return 'oxalate'
    if 'CO3' in name:
        return 'carbonate'
    if 'CH3COO' in name or 'OAc' in name or 'Ac' in name:
        return 'acetate'
    if 'NO3' in name:
        return 'nitrate'
    if 'SO4' in name:
        return 'sulfate'
    if 'OH' in name:
        return 'hydroxide'
    # Check for hydrides
    if name.endswith('H2') or name.endswith('H3') or name.endswith('H4') or 'H2' in name:
        # Could be hydride, but also could be part of formula
        pass
    if 'Cl' in name and 'O' not in name:
        return 'chloride'
    if 'Br' in name and 'O' not in name:
        return 'bromide'
    if 'I' in name and 'O' not in name and name != 'I':
        return 'iodide'
    if 'F' in name and 'O' not in name:
        return 'fluoride'
    if 'S' in name and 'O' not in name:
        return 'sulfide'
    if 'N' in name and 'O' not in name and name not in ('Na', 'Nb', 'Nd', 'Ni', 'Np'):
        return 'nitride'
    if 'O' in name:
        return 'oxide'
    # Pure element or hydride
    try:
        from pymatgen.core import Composition
        comp = Composition(name)
        if len(comp.elements) == 1:
            return 'elemental'
        if 'H' in [str(e) for e in comp.elements]:
            return 'hydride'
    except Exception:
        pass
    return 'other'


# ==================== Chemistry Prior Features ====================

class ChemistryPriorV2:
    """Enhanced chemistry knowledge from training data."""

    def __init__(self, env, precursor_id_map, X_train=None, y_train=None):
        self.env = env
        self.pke = env.precursor_key_elements
        self.pm = env.precursor_metals

        # Precursor pair co-occurrence
        self.pair_freq = Counter()
        self.precursor_freq = Counter()  # individual precursor frequency
        if X_train is not None and y_train is not None:
            for i in range(len(y_train)):
                pids = sorted(np.where(y_train[i] > 0)[0].tolist())
                for pid in pids:
                    self.precursor_freq[pid] += 1
                for a in range(len(pids)):
                    for b in range(a + 1, len(pids)):
                        self.pair_freq[(pids[a], pids[b])] += 1
            logger.info(
                f"ChemistryPriorV2: {len(self.pair_freq)} pairs, "
                f"{len(self.precursor_freq)} precursors from {len(y_train)} samples"
            )

        # Precursor type + leavability
        self.precursor_type = {}
        self.precursor_leavability = {}
        for pid_str, v in precursor_id_map.items():
            pid = int(pid_str)
            name = v[0]
            ptype = classify_precursor_type(name)
            self.precursor_type[pid] = ptype
            self.precursor_leavability[pid] = ANION_LEAVABILITY.get(ptype, 0.4)

        # Precursor metal atom counts (for stoichiometry)
        self.precursor_metal_counts = {}  # pid -> {metal_Z: count}
        for pid_str, v in precursor_id_map.items():
            pid = int(pid_str)
            name = v[0]
            try:
                from pymatgen.core import Composition, Element as PymatElement
                comp = Composition(name)
                metal_counts = {}
                for elem, amt in comp.items():
                    z = elem.Z - 1
                    if z not in VOLATILE_ELEMENTS:
                        metal_counts[z] = float(amt)
                self.precursor_metal_counts[pid] = metal_counts
            except Exception:
                self.precursor_metal_counts[pid] = {}

    def extract_chem_features(self, pids: List[int], target_features: np.ndarray,
                               probs: np.ndarray = None) -> np.ndarray:
        """Extract 12 chemistry prior features for a precursor set."""
        te = set(np.where(target_features > 0)[0].tolist()) - IGNORABLE_ELEMENTS
        tm = te - VOLATILE_ELEMENTS  # target metals

        if not pids or not tm:
            return np.zeros(NUM_CHEM_FEATS, dtype=np.float32)

        # Metal-to-precursor mapping
        metal_to_precs = {}  # metal -> list of precursors providing it
        prec_to_metals = {}  # precursor -> set of target metals it provides
        for p in pids:
            metals_p = self.pm[p] & tm
            prec_to_metals[p] = metals_p
            for m in metals_p:
                if m not in metal_to_precs:
                    metal_to_precs[m] = []
                metal_to_precs[m].append(p)

        # 1. metal_mapping_entropy: entropy of the mapping distribution
        # For each metal, how many precursors provide it? Higher entropy = more complex mapping
        if metal_to_precs:
            counts = [len(precs) for precs in metal_to_precs.values()]
            total_c = sum(counts)
            if total_c > 0:
                ps_dist = [c / total_c for c in counts]
                entropy = -sum(p * math.log(p + 1e-10) for p in ps_dist)
                max_entropy = math.log(max(len(counts), 1) + 1e-10)
                metal_mapping_entropy = entropy / (max_entropy + 1e-10)
            else:
                metal_mapping_entropy = 0.0
        else:
            metal_mapping_entropy = 0.0

        # 2. multi_source_frac: fraction of metals with >1 precursor source
        n_multi = sum(1 for precs in metal_to_precs.values() if len(precs) > 1)
        multi_source_frac = n_multi / max(len(tm), 1)

        # 3. stoich_cosine: cosine similarity of metal ratios
        # Target metal ratios
        target_metal_vec = {}
        for m in tm:
            target_metal_vec[m] = target_features[m]

        # Precursor combined metal ratios
        prec_metal_vec = {}
        for p in pids:
            mc = self.precursor_metal_counts.get(p, {})
            for m, cnt in mc.items():
                if m in tm:
                    prec_metal_vec[m] = prec_metal_vec.get(m, 0.0) + cnt

        # Compute cosine similarity
        all_metals = sorted(set(target_metal_vec.keys()) | set(prec_metal_vec.keys()))
        if all_metals:
            t_vec = np.array([target_metal_vec.get(m, 0.0) for m in all_metals])
            p_vec = np.array([prec_metal_vec.get(m, 0.0) for m in all_metals])
            t_norm = np.linalg.norm(t_vec)
            p_norm = np.linalg.norm(p_vec)
            if t_norm > 0 and p_norm > 0:
                stoich_cosine = float(np.dot(t_vec, p_vec) / (t_norm * p_norm))
            else:
                stoich_cosine = 0.0
        else:
            stoich_cosine = 0.0

        # 4. cooccurrence: avg log-frequency of precursor pairs
        if len(pids) >= 2:
            pair_scores = []
            for i in range(len(pids)):
                for j in range(i + 1, len(pids)):
                    a, b = min(pids[i], pids[j]), max(pids[i], pids[j])
                    freq = self.pair_freq.get((a, b), 0)
                    pair_scores.append(np.log1p(freq))
            cooccurrence = np.mean(pair_scores) if pair_scores else 0.0
        else:
            cooccurrence = 0.0
        cooccurrence = min(cooccurrence / 5.0, 1.0)

        # 5. type_consistency: fraction with easily-decomposable anions
        easy_types = {'carbonate', 'oxalate', 'nitrate', 'hydroxide', 'oxide', 'acetate'}
        n_easy = sum(1 for p in pids if self.precursor_type.get(p, 'other') in easy_types)
        type_consistency = n_easy / max(len(pids), 1)

        # 6. anion_leavability: average leavability score
        leavabilities = [self.precursor_leavability.get(p, 0.4) for p in pids]
        anion_leavability = np.mean(leavabilities) if leavabilities else 0.4

        # 7. uncovered_frac
        covered_metals = set()
        for metals_p in prec_to_metals.values():
            covered_metals |= metals_p
        n_uncovered = len(tm - covered_metals)
        uncovered_frac = n_uncovered / max(len(tm), 1)

        # 8. size_match
        size_diff = abs(len(pids) - len(tm))
        size_match = 1.0 / (1.0 + size_diff)

        # 9. precursor_freq: avg log-frequency of individual precursors
        freqs = [self.precursor_freq.get(p, 0) for p in pids]
        precursor_freq = np.mean([np.log1p(f) for f in freqs]) if freqs else 0.0
        precursor_freq = min(precursor_freq / 7.0, 1.0)  # normalize

        # 10. metal_overlap: avg pairwise metal overlap between precursors
        if len(pids) >= 2:
            overlaps = []
            for i in range(len(pids)):
                for j in range(i + 1, len(pids)):
                    mi = prec_to_metals.get(pids[i], set())
                    mj = prec_to_metals.get(pids[j], set())
                    if mi or mj:
                        overlap = len(mi & mj) / max(len(mi | mj), 1)
                        overlaps.append(overlap)
                    else:
                        overlaps.append(0.0)
            metal_overlap = np.mean(overlaps) if overlaps else 0.0
        else:
            metal_overlap = 0.0

        # 11. prob_gap: max_prob - min_prob in the set
        if probs is not None and len(pids) > 0:
            set_probs = [max(probs[p], 1e-10) for p in pids]
            prob_gap = max(set_probs) - min(set_probs)
        else:
            prob_gap = 0.0

        # 12. prob_entropy: entropy of probability distribution within the set
        if probs is not None and len(pids) > 0:
            set_probs = np.array([max(probs[p], 1e-10) for p in pids])
            set_probs = set_probs / set_probs.sum()
            prob_entropy = float(-np.sum(set_probs * np.log(set_probs + 1e-10)))
            max_ent = math.log(len(pids) + 1e-10)
            prob_entropy = prob_entropy / (max_ent + 1e-10) if max_ent > 0 else 0.0
        else:
            prob_entropy = 0.0

        return np.array([
            metal_mapping_entropy,
            multi_source_frac,
            stoich_cosine,
            cooccurrence,
            type_consistency,
            anion_leavability,
            uncovered_frac,
            size_match,
            precursor_freq,
            metal_overlap,
            prob_gap,
            prob_entropy,
        ], dtype=np.float32)


# ==================== Extended Feature Extraction ====================

TOTAL_FEAT_DIM = FEAT_DIM + NUM_CHEM_FEATS  # 362 + 12 = 374


def extract_full_features(pids, probs, tf, pke, pm, chem_prior):
    """Extract base features (362) + chemistry features (12) = 374 dims."""
    base_d = extract_detailed_features(pids, probs, tf, pke, pm)
    base_feat = feats_to_tensor(base_d)
    chem_feat = chem_prior.extract_chem_features(pids, tf, probs)
    return np.concatenate([base_feat, chem_feat])
