""" Class to create multimer motifs given input """
from typing import List, Tuple
import numpy as np
from inmotifin.utils.mathutils import normalize_2d_array
from inmotifin.modules.data.motif import Motifs
from inmotifin.utils.fileops.reader import Reader
from inmotifin.utils.fileops.writer import Writer
from inmotifin.utils.paramsdata.multimerparams import MultimerParams


class Multimerer:
    """ Prepare multimers given two motifs and a distance

    Class parameters
    ----------------
    params: MultimerParams
        Dataclass storing motif_files, jaspar_db_version and \
        multimerisation_rule_path
    multimer_rules: Dict[str, Tuple[List[str], List[int]]]
        Dictionary of IDs and tuple of motif ID and pairwise distances
    motifs: Motifs
        Data class for motifs with names (key) and PPM, alphabet and ids
    multimers: Motifs
        Data class for multimer motifs with names (key) and PPM, \
        alphabet and ids
    reader: Reader
        File reader class to read in motifs and distances
    writer: Writer
        instance of the writer class
    rng: np.random.Generator
        Random generator for adding epsilon to the equal \
        probability of empty positions
    """

    def __init__(
            self,
            params: MultimerParams,
            reader: Reader,
            writer: Writer,
            rng: np.random.Generator) -> None:
        """Initialize simulator

        Parameters
        ----------
        params: MultimerParams
            Dataclass storing motif_files, jaspar_db_version and \
            multimerisation_rule_path
        reader: Reader
            File reader class to read in motifs and distances
        writer: Writer
            instance of the writer class
        rng: np.random.Generator
            Random generator for adding epsilon to the equal \
            probability of empty positions
        """
        self.reader = reader
        self.writer = writer
        self.params = params
        self.rng = rng
        self.motifs = None
        self.multimer_rules = None
        self.multimers = None

    def set_motifs(self, motifs: Motifs) -> None:
        """ Setter for motifs when run from within python

        Parameters
        ----------
        motifs: Motifs
            Instance of the Motifs dataclass
        """
        self.motifs = motifs

    def get_multimers(self) -> Motifs:
        """ Getter for multimers

        Return
        ------
        multimers: Motifs
            Data class for multimer motifs with names (key) and PPM, alphabet \
            and ids
        """
        if self.multimers is None:
            raise ValueError(
                "Missing multimers. Please run create_a_multimer() first.")

    def read_motifs(self) -> None:
        """ Read  motifs from files in csv, jaspar or meme format
        """
        motifs, alphabet = self.reader.read_in_motifs(
            motif_files=self.params.motif_files,
            jaspar_db_version=self.params.jaspar_db_version)
        self.motifs = Motifs(
            motifs=motifs,
            alphabet=alphabet,
            alphabet_revcomp_pairs=None)

    def read_multimer_rules(
            self
            ) -> Tuple[str, Tuple[List[str], List[int], List[float]]]:
        """ Read tsv of multimerisation rules """
        multimer_rules = self.reader.read_multimerisation_tsv(
            multimerisation_rule_path=self.params.multimerisation_rule_path)
        return multimer_rules

    def create_a_multimer(
            self,
            motifs: List[np.ndarray],
            distances: List[int],
            weights: List[float] = None,
            random_variance: float = 0.01) -> np.ndarray:
        """  Based on motifs and a rule create a multimer

        Parameters
        ----------
        multimer_parts: Tuple[List[str], List[int], List[float]]
            Tuple of motifs, corresponding distances between, and weights
        random_variance: float
            Magnitude of gaussian variance at the in-between positions

        Return
        ------
        multimer: np.ndarray
            Multimer motif in numpy array format
        """
        # guard against missing weights
        if weights is None:
            weights = [1.0] * (len(motifs))
        # initialize multimer with first motif
        multimer = motifs[0]
        for idx, motif_ppm in enumerate(motifs[1:]):
            # get next motif and weight by contribution
            component = motif_ppm
            # fetch distances for between current motif and previous motif
            if idx < len(distances):
                # if not yet at the end, add filling or
                # adjust multimer end and motif beginning
                if distances[idx] > 0:
                    # positive distance: fill in with non-informative positions
                    inbetween = np.full(
                        (distances[idx], len(self.motifs.alphabet)),
                        1/len(self.motifs.alphabet))
                    inbetween += self.rng.normal(
                            0, random_variance,
                            size=inbetween.shape)
                    inbetween_norm = normalize_2d_array(inbetween)
                    component = np.concatenate(
                        [inbetween_norm, component],
                        axis=0)
                elif distances[idx] < 0:
                    # negative distance: take average of before / after
                    to_trim = distances[idx]
                    # get overlapping region
                    comp_overlap = component[:-to_trim]
                    multimer_overlap = multimer[to_trim:]
                    # remove beginning from motif
                    component = component[-to_trim:]
                    # remove end from multimer
                    multimer = multimer[:to_trim]
                    inbetween = np.average(np.array(
                        [comp_overlap, multimer_overlap]),
                        weights=[weights[idx+1], weights[idx]],
                        axis=0)
                    component = np.concatenate([inbetween, component], axis=0)
                # if no distance in between, just add component
                multimer = normalize_2d_array(
                    np.concatenate([multimer, component], axis=0))
        return multimer

    def save_multimers(self) -> None:
        """ Save multimers in meme format """
        self.writer.motif_to_meme(
            motifs=self.multimers.motifs,
            alphabet=self.multimers.alphabet,
            file_prefix="multimer_motifs")

    def create_multimers(
            self,
            multimer_rules: Tuple[
                str, Tuple[List[str], List[int], List[float]]],
            random_variance: float = 0.01
            ) -> None:
        """ Fnction to assemble multimers """
        multimers_dict = {}
        for multimer_id, multimer_parts in multimer_rules.items():
            motifs = [self.motifs.motifs[mid] for mid in multimer_parts[0]]
            distances = multimer_parts[1]
            if len(multimer_parts) < 3 or multimer_parts[2] is None:
                weights = [1.0] * (len(motifs))
            else:
                weights = multimer_parts[2]
            multimer = self.create_a_multimer(
                motifs=motifs,
                distances=distances,
                weights=weights,
                random_variance=random_variance)
            multimers_dict[multimer_id] = multimer
        self.multimers = Motifs(
            motifs=multimers_dict,
            alphabet=self.motifs.alphabet,
            alphabet_revcomp_pairs=self.motifs.alphabet_revcomp_pairs)

    def main(self) -> None:
        """ Main function to read, assemble and save multimers"""
        self.read_motifs()
        multimer_rules = self.read_multimer_rules()
        self.create_multimers(multimer_rules=multimer_rules)
        self.save_multimers()
