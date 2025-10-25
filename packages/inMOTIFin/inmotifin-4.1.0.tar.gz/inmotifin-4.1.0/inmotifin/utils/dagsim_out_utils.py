""" Utility functions related to dagsim output conversions """
from typing import Any, Dict, List
import numpy as np
import pandas as pd


def dagsim_data_to_dict_of_dict(
        dagsim_data: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    """ Takes the dictionary generate by dagsim and transforms it

    Parameters
    ----------
    dagsim_data:
        dictionary from the Dagsim output

    Return
    ------
    transformed_data_dict: Dict[int, Dict[str, Any]]
        Dictionary of dictionary, where the outer key  are unique \
        identifiers to each simulated sequence and each dictionary \
        contains all the information to that sequence.
    """
    data_pd = pd.DataFrame(dagsim_data)
    transformed_data_dict = data_pd.to_dict(orient='index')

    return transformed_data_dict


def label_fasta_seq(
        dagsim_data: Dict[str, Any],
        no_motif_seq: List[str],
        no_motif_prob: List[np.ndarray]) -> Dict[str, str]:
    """ Harmonize background names between motif-in-seq and empty seq

    Parameters
    ----------
    dagsim_data: Dict[str, Any]
        dictionary from the Dagsim output
    no_motif_seq: List[str]
        List of non-unique comma separated background IDs and sequences
    no_motif_prob: List[np.ndarray]
        List of corresponding sequence probabilties

    Return
    ------
    unique_id_seq_dict: Dict[str, str]
        Dictionary of sequences with unique IDs (both with and wo motif in)
    unique_id_prob_dict: Dict[str, np.ndarray]
        Dictionary of sequence IDs and letter probabilities per position
    """
    unique_id_seq_dict = {}
    unique_id_prob_dict = {}
    transformed_data_dict = dagsim_data_to_dict_of_dict(
        dagsim_data=dagsim_data)
    unique_id = -1
    for unique_id, info_dict in transformed_data_dict.items():
        identifier = str(unique_id) + "_" + info_dict["backgrounds"]
        motif_in_seq = info_dict["motif_in_seq"]
        unique_id_seq_dict[identifier] = motif_in_seq
        unique_id_prob_dict[identifier] = info_dict["prob_motif_in_seq"]
    for empty_sequence, empty_prob in zip(no_motif_seq, no_motif_prob):
        unique_id += 1
        identifier = str(unique_id) + "_" + empty_sequence.split(',')[0]
        unique_id_seq_dict[identifier] = empty_sequence.split(',')[1]
        unique_id_prob_dict[identifier] = empty_prob
    return unique_id_seq_dict, unique_id_prob_dict


def extract_info_for_bed(
        dagsim_data: Dict[str, Any]) -> List[str]:
    """ Extract information from dagsim output for creating bed files

    Parameters
    ----------
    dagsim_data: Dict[str, Any]
        dictionary from the Dagsim output

    Return
    ------
    line_list: List[str]
        List of lines in bed file
    """
    line_list = []
    transformed_data_dict = dagsim_data_to_dict_of_dict(
        dagsim_data=dagsim_data)

    for unique_id, info_dict in transformed_data_dict.items():
        num_instances = info_dict["num_instances"]
        if num_instances == 0:
            continue
        instances = info_dict["instances"]
        positions = info_dict["positions"]
        # check if start and end positions are identical
        # this indicates that the motif is inserted without replacing existing
        # bases, in which case, the positions should be adjusted
        if positions[0][0] == positions[0][1]:
            # make sure the positions are in reverse order
            if len(positions) > 1:
                assert positions[0][0] >= positions[1][0]

            corrected_positions_len = 0
            corrected_positons = []
            for pos, inst in zip(reversed(positions), reversed(instances)):
                # go from smallest to largest position
                instance_len = len(inst)
                start_pos = pos[0] + corrected_positions_len
                end_pos = start_pos + instance_len - 1
                corrected_positions_len += instance_len
                corrected_positons.append((start_pos, end_pos))
                corrected_positons.sort(reverse=True)
            positions = corrected_positons
        orientations = info_dict["orientations"]
        names = info_dict["selected_motifs"]
        identifier = str(unique_id) + "_" + info_dict["backgrounds"]

        for instances_index in range(num_instances):
            orientation = \
                '+' if orientations[instances_index] == 1 else '-'
            line_list.append(
                f"{identifier}" +
                f"\t{positions[instances_index][0]}" +
                f"\t{positions[instances_index][1]}\t" +
                f"{names[instances_index]}_" +
                f"{instances[instances_index]}" +
                "\t." +
                f"\t{orientation}"
            )
    return line_list
