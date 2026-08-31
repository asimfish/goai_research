from __future__ import annotations

from typing import Dict, List, Set
import numpy as np
from pymatgen.core import Element as PymatElement

VOLATILE_ELEMENTS = {PymatElement(sym).Z - 1 for sym in ["H", "C", "N", "O", "F", "Cl", "S", "Br", "I"]}
IGNORABLE_ELEMENTS = {PymatElement(sym).Z - 1 for sym in ["H", "C", "N"]}

class ExpertEnv:
    """Minimal precursor environment used by two-stage candidate generation."""
    def __init__(self, precursor_features: np.ndarray, max_precursors: int = 8):
        self.precursor_features = precursor_features
        self.num_precursors = precursor_features.shape[0]
        self.max_precursors = max_precursors
        self.precursor_elements: List[Set[int]] = []
        self.precursor_key_elements: List[Set[int]] = []
        self.precursor_metals: List[Set[int]] = []
        self.element_to_precursors: Dict[int, List[int]] = {}
        for i in range(self.num_precursors):
            elems = set(np.where(precursor_features[i] > 0)[0].tolist())
            key = elems - IGNORABLE_ELEMENTS
            metals = elems - VOLATILE_ELEMENTS
            self.precursor_elements.append(elems)
            self.precursor_key_elements.append(key)
            self.precursor_metals.append(metals)
            for e in key:
                self.element_to_precursors.setdefault(e, []).append(i)
