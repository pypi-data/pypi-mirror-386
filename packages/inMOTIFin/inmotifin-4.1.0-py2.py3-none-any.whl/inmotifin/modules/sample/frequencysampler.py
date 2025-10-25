""" Sample from group and motif frequencies """
from typing import List
import numpy as np
from inmotifin.utils.baseutils import choice_from_dict
from inmotifin.modules.data.frequencies import Frequencies


class FrequencySampler:
    """ Class to select motif based on its background frequencies

    Class parameters
    ----------------
    frequencies: Frequencies
        Frequencies data class including probabilities of \
        groups and motifs within them
    num_groups_per_seq: int
        Number of groups to select in total
    rng: np.random.Generator
        Random generator for sampling
    """

    def __init__(
            self,
            frequencies: Frequencies,
            num_groups_per_seq: int,
            rng: np.random.Generator):
        """ Constructor

        Parameters
        ----------
        frequencies: Frequencies
            Frequencies data class including probabilities of \
            groups and motifs within them
        num_groups_per_seq: int
            Number of groups to select in total
        rng: np.random.Generator
            Random generator for sampling
        """
        self.frequencies = frequencies
        self.num_groups_per_seq = num_groups_per_seq
        self.rng = rng

    def select_groups(self) -> List[str]:
        """ Select groups based on their frequency and transition \
            probability in a Markov chain fashion: the selection of the next \
            group depends on the previous selected one given the \
            group_group_transition_prob matrix. The first group is selected \
            from the base group frequency list

        Return
        ------
        selected_ids: List[str]
            List of selected group ids
        """
        selected_groups = []
        # Start by selecting the first group given group frequencies
        selected_group = str(choice_from_dict(
            indict=self.frequencies.group_freq,
            size=1,
            rng=self.rng)[0])
        selected_groups.append(selected_group)
        for _ in range(self.num_groups_per_seq - 1):
            group_probs = self.frequencies.group_group_transition_prob.loc[
                selected_group,]
            selected_group = str(choice_from_dict(
                indict=group_probs,
                size=1,
                rng=self.rng)[0])
            selected_groups.append(selected_group)

        return selected_groups

    def select_motifs_from_groups(
            self,
            group_ids: List[str],
            num_instances_per_seq: int,
            w_replacement: bool = True) -> List[str]:
        """ Select motifs from given groups. Equal number of motifs \
            from each group. If cannot equally assign, loops through \
            groups and picks one each until no more motifs

        Parameters
        ----------
        group_ids: List[str]
            List of selected group ids
        num_instances_per_seq: int
            Number of motifs to select (per sequence)
        w_replacement: bool
            Whether to select motifs from groups with replacement. \
            Note, if more motifs are requested than available in a group, \
            replacement will be used regardless of this parameter.

        Return
        ------
        selected_motifs: List[str]
            List of selected motif IDs
        """
        # assign equal number of motifs per group
        num_motif_per_group = int(np.floor(
            num_instances_per_seq / self.num_groups_per_seq))
        all_selected_motifs = []
        for group in group_ids:
            prob_series = self.frequencies.motif_freq_per_group[group]
            more_avail_motifs = num_motif_per_group < sum(prob_series > 0)
            if (not w_replacement) and (not more_avail_motifs):
                # check number of available motifs
                # if equal (here for speed) or not enough, take all motifs
                selected_motifs = list(
                    prob_series.index[np.where(prob_series > 0)])
            else:
                selected_motifs = self.rng.choice(
                    a=prob_series.index,
                    size=num_motif_per_group,
                    replace=w_replacement,
                    p=prob_series.tolist())
            all_selected_motifs += list(selected_motifs)
        # if total number of motifs is not divisible by number of groups,
        # pick one group, then pick one motif from that group in a loop
        # until enough motifs
        while len(all_selected_motifs) < num_instances_per_seq:
            # pick one more motif from one group
            one_more_group_idx = self.rng.choice(
                a=group_ids,
                size=1)[0]
            motif_probs = self.frequencies.motif_freq_per_group[
                one_more_group_idx]
            one_more_motif = self.rng.choice(
                a=motif_probs.index,
                size=1,
                p=motif_probs.tolist())
            all_selected_motifs.append(one_more_motif[0])
        return all_selected_motifs
