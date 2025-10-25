""" Training Markov model from sequences """
from typing import List, Tuple, Dict
import numpy as np
from hmmlearn import hmm
from inmotifin.utils.mathutils import sample_lengths


class Markover:
    """ Class to learn Markov model from input sequences

    Class parameters
    ----------------
    algorithm: str
        Name of the algorithm to be used in HMM: \
        map (default) or viterbi
    alphabet_idx_map: Dict[str, int]
        Map alphabet characters to integers
    idx_alphabet_map: Dict[int, str]
        Map integers to alphabet characters
    model: hmm.CategoricalHMM
        HMM model to fit and sample from
    rng: np.random.Generator
        Random generator for length (uniform from integers)
    """

    def __init__(
            self,
            alphabet: str,
            order: int,
            n_iter: int,
            rng: np.random.Generator,
            algorithm: str = "map",
            seed: int = 123) -> None:
        """ Constructor

        Parameters
        ----------
        alphabet: str
            Alphabet of the possible characters in the sequences \
            the model will be trained on
        order: int
            This corresponds to the kmer length that is considered \
            for learning. Number of Markov model hidden states are defined as \
            len(alphabet) ** order. Note: Use carefully \
            anything above 1. 2nd order already requires 303 free \
            parameters to learn.
        n_iter: int
            Number of iterations for HMM fitting
        algorithm: str
            Name of the algorithm to be used in HMM: \
            map (default) or viterbi
        seed: int
            Seed used for random state in HMM
        rng: np.random.Generator
            Random generator for length (uniform from integers)
        """
        if algorithm not in ["map", "viterbi"]:
            msg = "algorithm should be either map or viterbi"
            raise ValueError(msg)
        self.algorithm = algorithm
        # map alphabet chars to integers
        self.alphabet_idx_map = {ch: i for i, ch in enumerate(alphabet)}
        # and integers to char
        self.idx_alphabet_map = dict(enumerate(alphabet))
        self.model = hmm.CategoricalHMM(
            n_components=len(alphabet) ** order,
            n_features=len(alphabet),
            n_iter=n_iter,
            algorithm=self.algorithm,
            random_state=seed)
        self.rng = rng

    def fit_model(self, sequences: List[str]) -> None:
        """ Function to fit model on sequences

        Parameters
        ----------
        sequences: List[str]
            List of sequences to fit model on
        """
        # encode sequences into arrays of ints
        try:
            encoded_sequences = [
                np.array([self.alphabet_idx_map[ch] for ch in seq], dtype=int)
                for seq in sequences
            ]
        except KeyError as exc:
            msg = "Unexpected character in sequence. Make sure that your "
            msg += "alphabet includes everything that is expected. "
            msg += f"Current alphabet: {list(self.alphabet_idx_map.keys())}"
            raise ValueError(msg) from exc
        # flatten into one observation sequence
        xseq_vector = np.concatenate(encoded_sequences).reshape(-1, 1)
        # lengths tell HMM how to split back into sequences
        xseq_lengths = [len(seq) for seq in encoded_sequences]
        self.model.fit(
            X=xseq_vector,
            lengths=xseq_lengths)

    def sample_from_model(
            self,
            len_sample: int) -> Tuple[List[int], List[List[int]]]:
        """ Sample sequence from fitted model

        Parameters
        ----------
        len_sample: int
            Length of the sequence to be sampled

        Return
        -------
        sampled_seq: List[int]
            List of sampled sequences
        sampled_states: List[List[int]]
            List of sampled stated per position
        """
        sampled_seq, sampled_states = self.model.sample(n_samples=len_sample)
        return sampled_seq, sampled_states

    def calc_position_probabilities(
            self,
            sampled_states: List[int]) -> np.ndarray:
        """ Given a sequence and a trained model, calculate \
            emission probabilities for each position

        Parameters
        ----------
        sampled_states: List[int]
            List of sampled states (in a single sequence)

        Return
        -------
        _ : np.ndarray
            Numpy array of probabilities of each letter per each position
        """
        prob_list = []
        # emissionprob_ (array, shape (n_components, n_features))
        # Probability of emitting a given symbol when in each state.
        for hmm_state in sampled_states:
            prob_list.append(self.model.emissionprob_[hmm_state,])
        return np.array(prob_list)

    def get_str_sequence(self, sampled_seq: np.ndarray) -> str:
        """ Convert sampled sequence to string

        Parameters
        ----------
        sampled_seq: np.ndarray
            A list of sampled integers as characters per position

        Return
        -------
        sampled_str: str
            Character string representation of the sampled sequence
        """
        sampled_str = ""
        for ch_i in sampled_seq.flatten().tolist():
            sampled_str += self.idx_alphabet_map[ch_i]
        return sampled_str

    def sample_str_and_prob(
            self,
            len_seq_min: int,
            len_seq_max: int,
            num_seq: int
            ) -> Tuple[List[str], List[List[np.ndarray]]]:
        """Sample a sequence and its positional probabilities

        Parameters
        ----------
        len_seq_min: int
            Minimum length of the sequence to be sampled
        len_seq_max: int
            Maximum length of the sequence to be sampled. \
            If None, it is set equal to len_seq_min. Defaults to None
        num_seq: int
            Number of sequences to generate

        Return
        ------
        seq_str: List[str]
            List of sampled sequences
        seq_probs: List[List[np.ndarray]]
            List of position-specific letter probabilities
        """
        seq_probs = []
        seq_str = []
        if len_seq_max is None:
            seq_lengths = [len_seq_min]*num_seq
        else:
            seq_lengths = sample_lengths(
                len_min=len_seq_min,
                len_max=len_seq_max,
                num_len=num_seq,
                rng=self.rng)
        for len_seq in seq_lengths:
            sampled_seq, sampled_states = self.sample_from_model(
                len_sample=len_seq)
            seq_probs.append(self.calc_position_probabilities(
                sampled_states=sampled_states))
            seq_str.append(self.get_str_sequence(
                sampled_seq=sampled_seq))
        return seq_str, seq_probs

    def get_probabilities(
            self,
            sequences: Dict[str, str]) -> Dict[str, np.ndarray]:
        """Assign position specific probabilities for the input \
            sequences based on fitted model

        Parameters
        ----------
        sequences: Dict[str, str]
            Dictionary of background sequences

        Return
        ------
        backgrounds_prob: Dict[str, np.ndarray]
            Dictionary of background sequence probabilities of letters \
            in each position
        """
        backgrounds_prob = {}
        seq_str_list = list(sequences.values())
        self.fit_model(sequences=seq_str_list)
        for seq_id, seq_str in sequences.items():
            encoded_seq = np.array(
                [self.alphabet_idx_map[ch] for ch in seq_str], dtype=int)
            encoded_vector = encoded_seq.reshape(-1, 1)
            _, state_seq = self.model.decode(
                X=encoded_vector,
                lengths=len(seq_str),
                algorithm=self.algorithm)
            backgrounds_prob[seq_id] = self.calc_position_probabilities(
                sampled_states=state_seq)
        return backgrounds_prob
