""" Data class for backgrounds """
from typing import Dict, List
from dataclasses import dataclass, field
import numpy as np


@dataclass
class Backgrounds:
    """ Class for keeping track of backgrounds

    Class parameters
    ----------------
    backgrounds: Dict[str, str]
        Dictionary of background IDs and sequences
    b_alphabet: str
        Background alphabet, default is "ACGT"
    sequence_prob: Dict[str, np.ndarray]
        Position specific background probabilities. \
        Defaults to i.i.d
    background_ids: List[str]
        List of background IDs (automatically extracted from \
        background dictionary)
    """
    backgrounds: Dict[str, str]
    b_alphabet: str
    sequence_probs: Dict[str, np.ndarray] = None
    background_ids: List[str] = field(init=False)

    def __post_init__(self):
        """ Define background ids as a list """
        self.background_ids = sorted(self.backgrounds.keys())
