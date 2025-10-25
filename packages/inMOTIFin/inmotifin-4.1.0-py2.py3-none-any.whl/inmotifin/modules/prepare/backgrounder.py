""" Creating or importing backgrounds """
from typing import Dict, Tuple, List
import numpy as np
from inmotifin.utils.paramsdata.backgroundparams import BackgroundParams
from inmotifin.modules.data.background import Backgrounds
from inmotifin.modules.prepare.markover import Markover
from inmotifin.modules.prepare.shuffler import Shuffler
from inmotifin.utils.fileops.reader import Reader
from inmotifin.utils.fileops.writer import Writer
from inmotifin.utils.mathutils import sample_lengths


class Backgrounder:
    """ Class to generate or read background sequences

    Class parameters
    ----------------
    title: str
        Title of the analysis
    params: BackgroundParams
        Dataclass storing alphabet, sequence length, sequence number, \
        b_alphabet_prior, order, background_files, background_type, \
        number_of_shuffle, and markov_order
    backgrounds: Backgrounds
        Data class for backgrounds
    shuffler: Shuffler
        Class for shuffling background sequence
    reader: Reader
        File reader class to read in sequences if necessary
    writer: Writer
        instance of the writer class
    rng: np.random.Generator
        Random generator for sampling letters
    """

    def __init__(
            self,
            params: BackgroundParams,
            reader: Reader,
            writer: Writer,
            rng: np.random.Generator) -> None:
        """ Constructor

        Parameters
        ----------
        params: BackgroundParams
            Dataclass storing alphabet, sequence length, sequence number, \
            b_alphabet_prior, background_files, background_type \
            number_of_shuffle, and markov_order
        reader: Reader
            File reader class to read in sequences if necessary
        writer: Writer
            instance of the writer class
        rng: np.random.Generator
            Random generator for sampling letters
        """
        self.params = params
        self.reader = reader
        self.writer = writer
        self.rng = rng
        self.title = writer.get_title()
        self.backgrounds = None

    def get_backgrounds(self) -> Backgrounds:
        """ Getter for simulated backgrounds

        Return
        -------
        backgrounds: Backgrounds
            Backgrounds dataclass with sequence and metadata
        """
        return self.backgrounds

    def get_backgrounds_seq(self) -> Dict[str, str]:
        """ Getter for simulated backgrounds

        Return
        -------
        backgrounds_seq: Dict[str, str]
            Dictionary with the background IDs and sequences
        """
        return self.backgrounds.backgrounds

    def assign_iid_probs(
            self,
            backgrounds: Dict[str, str]) -> Dict[str, np.ndarray]:
        """
        Assign position probabilities to sequences based on alphabet priors

        Parameters
        ----------
        backgrounds: Dict[str, str]
            Dictionary with the background IDs and sequences

        Return
        ------
        backgrounds_prob: Dict[str, np.ndarray]
            Dictionary of background sequence probabilities of letters \
            in each position
        """
        background_probs = {}
        for bid, bseq in backgrounds.items():
            background_probs[bid] = np.tile(
                self.params.b_alphabet_prior,
                (len(bseq), 1))
        return background_probs

    def shuffle_backgrounds(
            self) -> Tuple[Dict[str, str], Dict[str, np.ndarray]]:
        """
        Shuffle available backgrounds thus generate new ones

        Parameters
        ----------
        backgrounds: Dict[str, str]
            Dictionary with the background IDs and sequences

        Return
        -------
        backgrounds_seq: Dict[str, str]
            Dictionary with the shuffled background IDs and sequences
        backgrounds_prob: Dict[str, np.ndarray]
            Dictionary of background sequence probabilities of letters \
            in each position
        """
        backgrounds = self.reader.read_fasta(
            fasta_files=self.params.background_files)
        shuffler = Shuffler(
            number_of_shuffle=self.params.number_of_shuffle,
            rng=self.rng)
        if self.params.background_type == "random_nucl_shuffled_addon":
            shuffled = shuffler.shuffle_seq_random_nucleotide(
                backgrounds=backgrounds)
            backgrounds.update(shuffled)
        elif self.params.background_type == "random_nucl_shuffled_only":
            backgrounds = shuffler.shuffle_seq_random_nucleotide(
                backgrounds=backgrounds)
        else:
            msg = "Choose 'random_nucl_shuffled_addon'"
            msg += "or 'random_nucl_shuffled_only'"
            raise ValueError(msg)
        backgrounds_prob = self.assign_iid_probs(backgrounds=backgrounds)
        return backgrounds, backgrounds_prob

    def fit_markov(
            self,
            sequences: Dict[str, str]) -> Dict[str, np.ndarray]:
        """Fit hidden Markov model on sequences to get position \
            specific letter probabilities

        Parameters
        ----------
        sequences: Dict[str, str]
            Dict of input sequences

        Return
        ------
        backgrounds: Dict[str, str]
            Dictionary of background sequences
        backgrounds_prob: Dict[str, np.ndarray]
            Dictionary of background sequence probabilities of letters \
            in each position
        """
        markover = Markover(
            alphabet=self.params.b_alphabet,
            order=self.params.markov_order,
            n_iter=self.params.markov_n_iter,
            algorithm=self.params.markov_algorithm,
            rng=self.rng,
            seed=self.params.markov_seed)
        backgrounds_prob = markover.get_probabilities(
            sequences=sequences)
        return backgrounds_prob

    def simulate_markov(
            self,
            sequences: Dict[str, str]
            ) -> Tuple[Dict[str, str], Dict[str, np.ndarray]]:
        """Simulate background using Markov model

        Parameters
        ----------
        sequences: Dict[str, str]
            Dict of input sequences

        Return
        ------
        backgrounds: Dict[str, str]
            Dictionary of background sequences
        backgrounds_prob: Dict[str, np.ndarray]
            Dictionary of background sequence probabilities of letters \
            in each position
        """
        backgrounds = {}
        backgrounds_prob = {}
        markover = Markover(
            alphabet=self.params.b_alphabet,
            order=self.params.markov_order,
            n_iter=self.params.markov_n_iter,
            algorithm=self.params.markov_algorithm,
            rng=self.rng,
            seed=self.params.markov_seed)
        markover.fit_model(sequences=list(sequences.values()))
        seq_str, seq_probs = markover.sample_str_and_prob(
            len_seq_min=self.params.length_of_backgrounds_min,
            len_seq_max=self.params.length_of_backgrounds_max,
            num_seq=self.params.number_of_backgrounds)
        for idx, b_str in enumerate(seq_str):
            seq_id = self.title + "_seq_" + str(idx)
            backgrounds[seq_id] = b_str
            backgrounds_prob[seq_id] = seq_probs[idx]

        return backgrounds, backgrounds_prob

    def simulate_iid_backgrounds(
            self,
            b_lengths: List[int] = None
            ) -> Tuple[Dict[str, str], Dict[str, np.ndarray]]:
        """Generates a dictionary of random sequences \
        within which each position is iid, and assignes IDs for each sequence

        Parameters
        ----------
        b_lengths: List[int]
            List of lenght of simulated backgrounds. If None, sampled \
            with b_length_min and b_length_max fetched from params data

        Return
        ------
        backgrounds: Dict[str, str]
            Dictionary of background sequences
        backgrounds_prob: Dict[str, np.ndarray]
            Dictionary of background sequence probabilities of letters \
            in each position
        """
        if b_lengths is None:
            b_lengths = sample_lengths(
                len_min=self.params.length_of_backgrounds_min,
                len_max=self.params.length_of_backgrounds_max,
                num_len=self.params.number_of_backgrounds,
                rng=self.rng)
        backgrounds = {}
        backgrounds_prob = {}
        for idx, b_length in enumerate(b_lengths):
            seq_id = self.title + "_seq_" + str(idx)
            alphabet_to_list = list(self.params.b_alphabet)
            random_list = [
                self.rng.choice(
                    alphabet_to_list,
                    p=self.params.b_alphabet_prior,
                    replace=True)[0]
                for _ in range(b_length)
                ]
            backgrounds_prob[seq_id] = np.tile(
                self.params.b_alphabet_prior,
                (b_length, 1))
            random_sequence = "".join(random_list)
            backgrounds[seq_id] = random_sequence

        return backgrounds, backgrounds_prob

    def markov_backgrounds(
            self
            ) -> Tuple[Dict[str, str], Dict[str, np.ndarray]]:
        """ Generates a dictionary of sequences with ids

        Return
        ------
        backgrounds: Dict[str, str]
            Dictionary of background sequences and IDs
        background_probs: Dict[str, np.ndarray]
            Dictionary of background sequence probabilities of letters \
            in each position
        """
        backgrounds = self.reader.read_fasta(
            fasta_files=self.params.background_files)
        if self.params.background_type == "markov_fit":
            # fit a Markov model
            background_probs = self.fit_markov(
                sequences=backgrounds)
        elif self.params.background_type == "markov_sim":
            # fit and sample from Markov model
            backgrounds, background_probs = self.simulate_markov(
                sequences=backgrounds)
        else:
            msg = "Choose 'markov_fit' or markov_sim"
            raise ValueError(msg)

        return backgrounds, background_probs

    def read_backgrounds(self) -> Tuple[Dict[str, str], Dict[str, np.ndarray]]:
        """
        Reads sequences into a dictionary of sequences with ids and \
        dictionary of sequence probabilities (iid)

        Return
        ------
        backgrounds: Dict[str, str]
            Dictionary of background sequences and IDs
        background_probs: Dict[str, np.ndarray]
            Dictionary of background sequence probabilities of letters \
            in each position
        """
        if self.params.background_files is None:
            msg = "background_files cannot be None when background_type "
            msg += "is fasta_iid"
            raise ValueError(msg)
        backgrounds = self.reader.read_fasta(
            fasta_files=self.params.background_files)
        background_probs = self.assign_iid_probs(backgrounds=backgrounds)
        return backgrounds, background_probs

    def create_backgrounds(self) -> None:
        """ Controller function to read backgrounds or simulate if \
            no file available """
        markov_model = ["markov_fit", "markov_sim"]
        shuffling = ["random_nucl_shuffled_only", "random_nucl_shuffled_addon"]
        if self.params.background_type == "iid":
            backgrounds, background_probs = self.simulate_iid_backgrounds()
        elif self.params.background_type == "fasta_iid":
            backgrounds, background_probs = self.read_backgrounds()
        elif self.params.background_type in markov_model:
            backgrounds, background_probs = self.markov_backgrounds()
        elif self.params.background_type in shuffling:
            backgrounds, background_probs = self.shuffle_backgrounds()
        else:
            msg = "Unsupported background_type: "
            msg += f"{self.params.background_type}. The check is "
            msg += "case sensitive. Only iid, markov_fit, "
            msg += "markov_sim, random_nucl_shuffled_only, and "
            msg += "random_nucl_shuffled_addon are supported."
            raise ValueError(msg)

        self.writer.dict_to_fasta(
            seq_dict=backgrounds,
            filename="backgrounds")
        self.writer.save_dictionary_with_numpy_to_npz(
            numpy_dict=background_probs,
            filename=self.title + "_background_probabilities")
        self.backgrounds = Backgrounds(
            backgrounds=backgrounds,
            b_alphabet=self.params.b_alphabet,
            sequence_probs=background_probs)
