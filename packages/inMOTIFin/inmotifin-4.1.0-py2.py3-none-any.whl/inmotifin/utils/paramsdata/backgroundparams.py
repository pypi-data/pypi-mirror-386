""" Data storage for background parameters """
from typing import List
from dataclasses import dataclass
import numpy as np


@dataclass
class BackgroundParams:
    """ Class for keeping track of parameters for background

    Class parameters
    ----------------
    b_alphabet: str
        Background alphabet, default is "ACGT"
    background_files: List[str]
        List of background files to use, default is empty
    b_alphabet_prior: np.ndarray
        Background alphabet prior probabilities, default is uniform
    number_of_backgrounds: int
        Number of backgrounds to generate, default is 100
    length_of_backgrounds_min: int
        Minimum length of background sequences, default is 50
    length_of_backgrounds_max: int
        Maximum length of background sequences, default is None, \
        if not set all background sequences will have the same \
        length as length_of_backgrounds_min
    background_type: str
        Options: \
        1) fasta_iid (fasta files are used as is - default when \
        background_files is not None) \
        2) random_nucl_shuffled_only (fasta files are used, nucleotides in \
        sequences are shuffled and only shuffled ones are used) \
        3) random_nucl_shuffled_addon (fasta files are used, nucleotides in \
        sequences are shuffled and both shuffled and original ones are used)
        4) iid (fasta files are ignored if provided, b_alphabet_prior \
        specifies nucelotide probabilities - default when \
        background_files is None) \
        5) markov_fit (fasta files are used to fit hidden Markov model with \
        order specified with markov_order. Original sequences are kept) \
        6) markov_sim (fasta files are used to fit hidden Markov model with \
        order specified with markov_order. New sequences are sampled)
    number_of_shuffle: int
        Number of times to shuffle the backgrounds
    markov_order: int
        Order of Markov model to learn from sequences (when provided) \
        and to simulate sequences. Defaults to 0 corresponding to \
        learning independent nucleotide frequencies.
    markov_n_iter: int
        Number of iterations of Markov model to learn from sequences, \
        default is 100
    markov_algorithm: str
        Algorithm of Markov model to learn from sequences. Options: 'viterbi' \
        or 'map'. See hmmlearn 0.3.3 documentation. default is 'viterbi'."
    markov_seed: int
        Seed for reproducibility for HMM
    """
    b_alphabet: List[str] = None
    b_alphabet_prior: np.ndarray = None
    number_of_backgrounds: int = None
    length_of_backgrounds_min: int = None
    length_of_backgrounds_max: int = None
    background_files: List[str] = None
    background_type: str = None
    number_of_shuffle: int = None
    markov_order: int = None
    markov_n_iter: int = None
    markov_algorithm: str = None
    markov_seed: int = None

    def __post_init__(self):
        """ Set default values for parameters if not provided and \
        validate them
        """
        if self.b_alphabet is None:
            self.b_alphabet = "ACGT"
        if self.b_alphabet_prior is None:
            self.b_alphabet_prior = [0.25] * len(self.b_alphabet)
        assert len(self.b_alphabet_prior) == len(self.b_alphabet), \
            "b_alphabet_prior should have the same length as b_alphabet"
        self.b_alphabet_prior = np.array(self.b_alphabet_prior)
        if self.number_of_backgrounds is None:
            self.number_of_backgrounds = 100
        if self.length_of_backgrounds_min is None:
            self.length_of_backgrounds_min = 50
        if self.length_of_backgrounds_max is None:
            self.length_of_backgrounds_max = self.length_of_backgrounds_min
        if self.markov_order is None:
            self.markov_order = 0
        if self.markov_n_iter is None:
            self.markov_n_iter = 100
        if self.markov_algorithm is None:
            self.markov_algorithm = 'viterbi'
        if self.background_type is None:
            if self.background_files is None:
                self.background_type = "iid"
            else:
                self.background_type = "fasta_iid"
