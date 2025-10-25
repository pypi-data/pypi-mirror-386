""" Controller class to organize the preparation and sampling """
from typing import List, Dict, Tuple, Any
import os
import numpy as np
from inmotifin.utils.paramsdata.basicparams import BasicParams
from inmotifin.utils.paramsdata.motifparams import MotifParams
from inmotifin.utils.paramsdata.multimerparams import MultimerParams
from inmotifin.utils.paramsdata.groupparams import GroupParams
from inmotifin.utils.paramsdata.freqparams import FreqParams
from inmotifin.utils.paramsdata.backgroundparams import BackgroundParams
from inmotifin.utils.paramsdata.samplingparams import SamplingParams
from inmotifin.utils.paramsdata.positionparams import PositionParams
from inmotifin.utils.fileops.reader import Reader
from inmotifin.utils.fileops.writer import Writer
from inmotifin.modules.prepare.setupper import Setupper
from inmotifin.modules.prepare.multimerer import Multimerer
from inmotifin.modules.prepare.motifer import Motifer
from inmotifin.modules.prepare.backgrounder import Backgrounder
from inmotifin.modules.sample.sampler import Sampler
from inmotifin.modules.sample.inserter import Inserter
from inmotifin.modules.data.motif import Motifs
from inmotifin.modules.sample.motifinstancer import MotifInstancer
from inmotifin.modules.sample.inminscheme import InMOTIFinScheme
from inmotifin.organizer.summarizer import Summarizer


class Controller:
    """
    Organizer of preparation and sampling

    Class parameters
    ----------------
    reader: Reader
        File reader class to read in motifs if necessary
    writer: Writer
        instance of the writer class
    data_for_simulation: Dict[str, Any]
        Dictionary of simulated data passed for sampling
    summary: Dict[str, Dict[str, int]]
        Dictionary of summary information about the sampling
    rng: np.random.Generator
        Random generator for length (uniform from integeres) \
        and motif (Dirichlet) sampling
    """

    def __init__(self, basic_params: BasicParams) -> None:
        """
        Constructor

        Parameters
        ----------
        basic_params: BasicParams
            Dataclass storing title, workdir, and seed
        """
        self.writer = Writer(
            workdir=basic_params.workdir,
            title=basic_params.title)
        self.reader = Reader()
        self.data_for_simulation = {}
        self.rng = np.random.default_rng(basic_params.seed)
        self.summary = {}

    def create_multimers(self, multimer_params: MultimerParams) -> None:
        """
        Option of creating multimers given input motifs and rules

        Parameters
        ----------
        multimer_params: MultimerParams
            Dataclass storing motif_files, jaspar_db_version and \
            multimerisation_rule_path
        """
        my_multimerer = Multimerer(
            params=multimer_params,
            reader=self.reader,
            writer=self.writer,
            rng=self.rng)
        my_multimerer.main()

    def create_motifs(self, motif_params: MotifParams) -> None:
        """
        Option of creating motifs given input parameters

        Parameters
        ----------
        motif_params: MotifParams
            Dataclass storing dirichlet_alpha, number_of_motifs, \
            length_of_motifs_min, length_of_motifs_max, alphabet \
            and motif_files
        """
        motifer = Motifer(
            params=motif_params,
            rng=self.rng,
            reader=self.reader,
            writer=self.writer)
        motifer.create_motifs()

    def create_backgrounds(self, background_params: BackgroundParams) -> None:
        """
        Option of creating backgrounds given input parameters

        Parameters
        ----------
        background_params: BackgroundParams
            Dataclass storing alphabet, sequence length, sequence number, \
            b_alphabet_prior, background_files, background_type, \
            number_of_shuffle, and markov_order
        """
        backgrounder = Backgrounder(
            params=background_params,
            reader=self.reader,
            writer=self.writer,
            rng=self.rng)
        backgrounder.create_backgrounds()

    def simulate_backgrounds(
            self,
            background_params: BackgroundParams,
            b_lengths: List[int] = None
            ) -> Tuple[Dict[str, str], Dict[str, np.ndarray]]:
        """
        Simulate backgrounds with background parameters, \
            but can also create multiple different lengths

        Parameters
        ----------
        background_params: BackgroundParams
            Dataclass storing alphabet, sequence length, sequence number, \
            b_alphabet_prior, background_files, background_type, \
            number_of_shuffle, and markov_order
        b_lengths: List[int]
            List of lenght of simulated backgrounds. Order should \
            match with b_numbers.

        Return
        ------
        backgrounds: Dict[str, str]
            Dictionary of background sequences
        backgrounds_prob: Dict[str, np.ndarray]
            Dictionary of background sequence probabilities of letters \
            in each position
        """
        backgrounder = Backgrounder(
            params=background_params,
            reader=self.reader,
            writer=self.writer,
            rng=self.rng)
        backgrounds, background_probs = backgrounder.simulate_iid_backgrounds(
            b_lengths=b_lengths)
        return backgrounds, background_probs

    def create_motif_in_seq(
            self,
            background_ids: List[str],
            background_dict: Dict[str, str],
            b_alphabets: Dict[str, str],
            sequence_probs: Dict[str, np.ndarray],
            positions: List[Tuple[int]],
            motif_ids: List[str],
            motifs: Motifs,
            orientations: List[List[int]],
            to_replace: bool = True
            ) -> Tuple[Dict[str, str], Dict[str, np.ndarray]]:
        """
        Add motif instances to specific positions into specific backgrounds

        Parameters
        ----------
        background_ids: List[str]
            List of background IDs in order of insertion
        background_dict: Dict[str, str]
            Dictionary of backgound IDs and sequences
        b_alphabets: Dict[str, str]
            Dictionary of background alphabet
        sequence_probs: Dict[str, np.ndarray]
            Dictionary of background alphabet prior probabilities
        positions: List[List[Tuple[int]]]
            List of list of position tuples in order of insertion per \
            sequence and per motif in the inner list
        motif_ids: List[List[str]]
            List of list of motif IDs in order of insertion per sequence \
            and per position in the inner list.
        motifs: Motifs
            Data class for motifs with names (key), PPM, alphabet and \
            alphabet pairs
        orientations: List[List[int]]
            List of list of motif instance orientations per sequence \
            and per motif in the inner list.
        to_replace: bool
            Whether to replace backgorund bases with motif instance. \
            Alternative is to insert between existing bases. Default: True

        Return
        ------
        motif_in_sequences: Dict[str, str]
            Dictionary of sequence ids (with background, motif, position, \
            and orientation) and corresponding sequences with motifs in
        probabilistic_motif_in_sequences: Dict[str, np.ndarray]
            Dictionary of sequence ids (with background, motif, position, \
            and orientation) and corresponding probabilities of letters in \
            sequences with motifs in
        """
        comp0 = len(positions) != len(motif_ids)
        comp1 = len(positions) != len(background_ids)
        comp2 = len(positions) != len(orientations)
        if comp0 or comp1 or comp2:
            message = "Positions, motif ids and backgrounds ids should be "
            message += "of the same length. They are positions: "
            message += f"{len(positions)}, motif_ids: {len(motif_ids)}, "
            message += f"background_ids: {len(background_ids)}, "
            message += f"orientations: {len(orientations)}"
            print(message)
            raise AssertionError

        inserter = Inserter(to_replace=to_replace)
        instancer = MotifInstancer(
            motifs=motifs,
            rng=self.rng)

        full_zip = zip(
            background_ids,
            motif_ids,
            positions,
            orientations)
        motif_in_sequences = {}
        probabilistic_motif_in_sequences = {}
        for bck, mot_list, pos_list, orient_list in full_zip:
            seq_name = bck + "_" + "_".join(mot_list) + "_"
            seq_name += "_".join(
                [str(p[0]) + ":" + str(p[1]) for p in pos_list])
            seq_name += "_" + "_".join([str(ori) for ori in orient_list])
            motif_instances = instancer.sample_instances(
                motif_idx_list=mot_list,
                orientations=orient_list)
            motif_in_seq = inserter.generate_motif_in_sequence(
                sequence=background_dict[bck],
                motif_instances=motif_instances,
                positions=pos_list)
            motif_in_sequences[seq_name] = motif_in_seq
            prob_motif_in_seq = \
                inserter.generate_probabilistic_motif_in_sequence(
                    b_alphabet=b_alphabets[bck],
                    sequence_prob=sequence_probs[bck],
                    motifs=motifs,
                    motif_ids=mot_list,
                    orientation_list=orient_list,
                    positions=pos_list)
            probabilistic_motif_in_sequences[seq_name] = prob_motif_in_seq

        return motif_in_sequences, probabilistic_motif_in_sequences

    def mask_motif_in_seq(
            self,
            seq_with_motif: Dict[str, str],
            positions: Dict[str, List[Tuple[int]]],
            mask_alphabet: str,
            mask_alphabet_prior: np.ndarray,
            seq_with_motif_prob: Dict[str, np.ndarray] = None
            ) -> Tuple[Dict[str, str], Dict[str, np.ndarray]]:
        """
        Mask motif instances with background-like sequences

        Parameters
        ----------
        seq_with_motif: Dict[str, str]
            Dictionary of sequences with motifs corresponding to positions \
            of masking
        positions: Dict[str, List[Tuple[int]]]
            Dictionary of list of position tuples corresponding to masking \
            per sequence and per motif in the inner list
        mask_alphabet: str
            Alphabet of masking
        mask_alphabet_prior: np.array
            Array of probabilties of each letter in the alphabet of masking
        seq_with_motif_prob: Dict[str, np.ndarray]
            Dictionary of sequence with motifs probabilities corresponding to \
            positions of masking. Optional. If not provided, no probabilistic \
            output is returned (i.e., masked_probs is None)

        Return
        ------
        masked_sequences: Dict[str, str]
            Dictionary of sequences after motifs are masked out
        masked_probs: Dict[str, np.ndarray]
            Dictionary of sequence probabilities after the motifs are masked
        """
        bckg_params = BackgroundParams(
            b_alphabet=mask_alphabet,
            b_alphabet_prior=mask_alphabet_prior,
            number_of_backgrounds=1,
            length_of_backgrounds_min=1,
            length_of_backgrounds_max=1,
            markov_order=0,
            background_files=None,
            background_type="iid",
            number_of_shuffle=None)
        inserter = Inserter(to_replace=True)
        masked_sequences = {}
        masked_probs = {}
        for seqid, seq_w_m in seq_with_motif.items():
            new_id = seqid + "_masked"
            b_lengths = [pos[1]-pos[0]+1 for pos in positions[seqid]]
            seq_masks, mask_prob = self.simulate_backgrounds(
                background_params=bckg_params,
                b_lengths=b_lengths)
            seq_mask = [sm for _, sm in seq_masks.items()]
            idx_mask = [si for si, _ in seq_masks.items()]
            masked_seq = inserter.generate_motif_in_sequence(
                sequence=seq_w_m,
                motif_instances=seq_mask,
                positions=positions[seqid])
            masked_sequences[new_id] = masked_seq
            if seq_with_motif_prob is not None:
                # we define revcomp pairs as identity because these will not be
                # oriented other way (see hardcoded orientation_list)
                masking_motif = Motifs(
                    motifs=mask_prob,
                    alphabet=mask_alphabet,
                    alphabet_revcomp_pairs={ml: ml for ml in mask_alphabet})
                msk_prob = inserter.generate_probabilistic_motif_in_sequence(
                    b_alphabet=mask_alphabet,
                    sequence_prob=seq_with_motif_prob[seqid],
                    motifs=masking_motif,
                    motif_ids=idx_mask,
                    orientation_list=[1]*len(idx_mask),
                    positions=positions[seqid])
                masked_probs[new_id] = msk_prob
            else:
                masked_probs = None
        return masked_sequences, masked_probs

    def setup_simulation(
            self,
            motif_params: MotifParams,
            background_params: BackgroundParams,
            group_params: GroupParams,
            freq_params: FreqParams) -> None:
        """
        Create data for sampling

        Parameters
        ----------
        motif_params: MotifParams
            Dataclass storing dirichlet_alpha, number_of_motifs, \
            length_of_motifs_min, length_of_motifs_max, alphabet \
            and motif_files
        background_params: BackgroundParams
            Dataclass storing alphabet, sequence length, sequence number, \
            b_alphabet_prior, background_files, background_type, \
            number_of_shuffle, and markov_order
        group_params: groupParams
            Dataclass storing number_of_groups, max_group_size, \
            group_size_binom_p and group_motif_assignment_file
        freq_params: FreqParams
            Dataclass storing group_frequency_type, group_frequency_range, \
            motif_frequency_type, motif_frequency_range, group_freq_file and \
            motif_freq_file
        """
        setupper = Setupper(
            reader=self.reader,
            writer=self.writer,
            motif_params=motif_params,
            background_params=background_params,
            group_params=group_params,
            frequency_params=freq_params,
            rng=self.rng)
        self.data_for_simulation["motifs"] = setupper.create_motifs()
        self.data_for_simulation["backgrounds"] = setupper.create_backgrounds()
        self.data_for_simulation["groups"] = setupper.create_groups()
        self.data_for_simulation["frequencies"] = setupper.create_frequencies()

    def run_sampling(
            self,
            sampling_params: SamplingParams,
            positions_params: PositionParams) -> Tuple[Any]:
        """
        Run main simulation module

        Parameters
        ----------
        sampling_params: SamplingParams
            Data class with sampling parameters
        positions_params: PositionParams
            Data class with positioning parameters

        Return
        ------
        sampled_data: Tuple[Any]
            Tuple containing dagsim_graph, data, and no_motif_seq
        """
        dag_name = self.writer.get_outfolder()
        sampler = Sampler(
            sampling_params=sampling_params,
            position_params=positions_params,
            data_for_simulation=self.data_for_simulation,
            reader=self.reader,
            rng=self.rng)
        my_sim = InMOTIFinScheme(
            dag_name=os.path.join(
                dag_name,
                self.writer.title + "_dagsim_table"),
            sampler=sampler,
            number_of_motif_in_seq=sampling_params.number_of_motif_in_seq)
        dagsim_graph, data = my_sim.run_sampling()
        no_motif_seq, no_motif_prob = sampler.get_backgrounds(
            num_backgrounds=sampling_params.number_of_no_motif_in_seq)
        return dagsim_graph, data, no_motif_seq, no_motif_prob

    def save_outputs(
            self,
            dagsim_graph,
            data,
            no_motif_seq: List[str],
            no_motif_prob: List[np.ndarray],
            to_draw: bool) -> None:
        """
        Save outputs of simulation into files

        Parameters
        ----------
        dagsim_graph
            Graph output from DagSim
        data: Dict[]
            Dictionary of sampled data
        no_motif_seq: List[str]
            List of sequences without motifs
        to_draw: bool
            Whether to draw dagsim_graph or not
        """
        if to_draw:
            dagsim_graph.draw()
        self.writer.save_dagsim_data(
            dagsim_data=data,
            nomotif_in_seq=no_motif_seq,
            nomotif_prob=no_motif_prob)
        summarizer = Summarizer(
            dagsim_data=data,
            no_motif_seq=no_motif_seq,
            writer=self.writer)
        self.summary = summarizer.summarize()

    def run_inmotifin(
            self,
            motif_params: MotifParams,
            background_params: BackgroundParams,
            group_params: GroupParams,
            freq_params: FreqParams,
            sampling_params: SamplingParams,
            positions_params: PositionParams) -> None:
        """
        Prepare and sample

        Parameters
        ----------
        motif_params: MotifParams
            Dataclass storing dirichlet_alpha, number_of_motifs, \
            length_of_motifs_min, length_of_motifs_max, alphabet \
            and motif_files
        background_params: BackgroundParams
            Dataclass storing alphabet, sequence length, sequence number, \
            b_alphabet_prior, background_files, background_type, \
            number_of_shuffle, and markov_order
        group_params: groupParams
            Dataclass storing number_of_groups, max_group_size, \
            group_size_binom_p and group_motif_assignment_file
        freq_params: FreqParams
            Dataclass storing group_frequency_type, group_frequency_range, \
            motif_frequency_type, motif_frequency_range, group_freq_file and \
            motif_freq_file
        sampling_params: SamplingParams
            Data class with sampling parameters
        positions_params: PositionParams
            Data class with positioning parameters
        """
        self.setup_simulation(
            motif_params=motif_params,
            background_params=background_params,
            group_params=group_params,
            freq_params=freq_params)
        dagsim_graph, data, no_motif_seq, no_motif_prob = self.run_sampling(
            sampling_params=sampling_params,
            positions_params=positions_params)
        self.save_outputs(
            dagsim_graph=dagsim_graph,
            data=data,
            no_motif_seq=no_motif_seq,
            no_motif_prob=no_motif_prob,
            to_draw=sampling_params.to_draw)
