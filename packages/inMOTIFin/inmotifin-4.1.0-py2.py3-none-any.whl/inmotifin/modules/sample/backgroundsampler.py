""" Sampling from backgrounds """
from typing import List, Tuple
import numpy as np
from inmotifin.modules.data.background import Backgrounds


class BackgroundSampler:
    """ Class to support sampling functions

    Class parameters
    ----------------
    backgrounds: Backgrounds
        Data class for backgrounds
    rng: np.random.Generator
        Random generator for selecting a background
    """

    def __init__(
            self,
            backgrounds: Backgrounds,
            rng: np.random.Generator) -> None:
        """ Constructor

        Parameters
        -----------
        backgrounds: Backgrounds
            Data class for backgrounds
        rng: np.random.Generator
            Random generator for selecting a background
        """
        self.backgrounds = backgrounds
        self.rng = rng

    def get_background_ids(self, num_sample: int) -> List[str]:
        """ Get a list of selected background sequence IDs

        Parameters
        -----------
        num_sample: int
            Number of samples to select

        Return
        ------
        selected_ids: List[str]
            List of sequence IDs
        """
        selected_ids_array = self.rng.choice(
            a=self.backgrounds.background_ids,
            size=num_sample)
        selected_ids = [str(seqid) for seqid in selected_ids_array]
        return selected_ids

    def get_single_background(
            self,
            selected_id: str) -> Tuple[str, np.ndarray]:
        """ Get a selected background sequence

        Parameters
        ----------
        selected_id: str
            The name of the selected sequence

        Return
        ------
        bckg_seq: str
            A sequence given the selected_id
        bckg_prob: np.ndarray
            A corresponding matrix of probabilities per \
            position per letter
        """
        bckg_seq = self.backgrounds.backgrounds[selected_id]
        bckg_prob = self.backgrounds.sequence_probs[selected_id]
        return bckg_seq, bckg_prob

    def get_b_alphabet(self) -> str:
        """ Get background alphabet
        """
        return self.backgrounds.b_alphabet

    def get_b_alphabet_prior(self) -> np.ndarray:
        """ Get background alphabet prior
        """
        return self.backgrounds.b_alphabet_prior

    def get_backgrounds(
            self,
            num_backgrounds: int
            ) -> Tuple[List[str], List[np.ndarray]]:
        """ Get a list of backgrounds and their probabilties \
        may contain duplicated entries

        Parameters
        ----------
        num_backgrounds: int
            Number of requested backgrounds

        Return
        ------
        selected_backgrounds: List[str]
            List of non-unique comma separated background IDs and sequences
        selected_b_probs: List[np.ndarray]
            List of corresponding sequence probabilities
        """
        selected_backgrounds = []
        selected_b_probs = []
        background_ids = self.get_background_ids(
            num_sample=num_backgrounds)
        for bid in background_ids:
            background_seq, background_prob = self.get_single_background(
                selected_id=bid
            )
            selected_backgrounds.append(f"{bid},{background_seq}")
            selected_b_probs.append(background_prob)

        return selected_backgrounds, selected_b_probs
