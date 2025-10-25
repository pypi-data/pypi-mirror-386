"""Main module."""
import click

from inmotifin.utils.config_args import (
    read_config,
    assign_background_params,
    assign_basic_params,
    assign_motif_params,
    assign_group_freq_params,
    assign_position_sampling_params)
from inmotifin.utils.paramsdata.multimerparams import MultimerParams
from inmotifin.organizer.controller import Controller


@click.group()
def cli():
    """ You are running inMOTIFin """
    click.echo('You are running inMOTIFin')


@cli.command()
@click.option(
    "--title", default="sim", type=str,
    help="Title of the simulation. Default: sim")
@click.option(
    "--workdir", default=".", type=click.Path(),
    help="Folder of the simulation outputs. \
Defaults to current work directory.")
@click.option(
    '--config', default=None, type=click.Path(),
    help="Config file for the simulation with the parameters for \
creating motifs")
@click.option(
    "--dirichlet_alpha",
    help="Alpha values for the Dirichlet distribution \
from which motifs are sampled. Default: 0.5,0.5,0.5,0.5")
@click.option(
    "--num_motifs", type=int,
    help="Number of motifs to create. Default: 10")
@click.option(
    "--m_length_min", type=int,
    help="Length of the motif. If --len_motifs_max is also \
specified, this is the lower boundary of length. Default: 5")
@click.option(
    "--m_length_max", type=int,
    help="Maximum allowed length of the motif. The actual \
length is sampled from a uniform distribution.(Optional)")
@click.option(
    "--m_alphabet", type=str,
    help="String of letters in the motif alphabet, Default: ACGT")
@click.option(
    '--seed', type=int,
    default=None,
    help="Seed value for reproducibility. Recommended (Optional)")
@click.pass_context
def motifs(
        ctx,
        title,
        workdir,
        config,
        dirichlet_alpha,
        num_motifs,
        m_length_min,
        m_length_max,
        m_alphabet,
        seed):
    """ Creating motifs given information content, length, and alphabet """
    click.echo(
        'Creating motifs given information content, length, and alphabet')
    ctx = read_config(ctx=ctx, config=config)
    ctx, basic_params = assign_basic_params(
        ctx=ctx, title=title, workdir=workdir, seed=seed)
    ctx.default_map['m_alphabet_pairs'] = None
    ctx.default_map['motif_files'] = None
    ctx.default_map['jaspar_db_version'] = None

    ctx, motif_params = assign_motif_params(
        ctx=ctx,
        dirichlet_alpha=dirichlet_alpha,
        num_motifs=num_motifs,
        m_length_min=m_length_min,
        m_length_max=m_length_max,
        m_alphabet=m_alphabet,
        m_alphabet_pairs=None,
        motif_files=None,
        jaspar_db_version=None)
    controller = Controller(basic_params=basic_params)
    controller.create_motifs(motif_params=motif_params)


@cli.command()
@click.option(
    "--title", default="sim", type=str,
    help="Title of the simulation. Default: sim")
@click.option(
    "--workdir", default=".", type=click.Path(),
    help="Folder of the simulation outputs.\
Defaults to current work directory.")
@click.option(
    '--config', default=None, type=click.Path(),
    help="Config file for the simulation with the parameters for \
creating multimers")
@click.option(
    '--motif_files', type=click.Path(),
    help="List of path(s) to the motif file(s). Supported formats \
are jaspar, meme, csv with JASPAR motif ids")
@click.option(
    "--jaspar_db_version", type=str,
    help="Version of JASPAR database to use when fetching \
JASPAR motif IDs.")
@click.option(
    "--multimerisation_rules", type=click.Path(),
    help="Path to the multimerisation rule tsv files. \
It should have two tab separated columns: \
list of motif IDs separated by comma, and \
list of distances between them spearated by comma.")
@click.option(
    '--seed', type=int, default=None,
    help="Seed value for reproducibility. Recommended (Optional)")
@click.pass_context
def multimers(
        ctx,
        title,
        workdir,
        config,
        motif_files,
        jaspar_db_version,
        multimerisation_rules,
        seed):
    """ Multimerizing motifs given motifs and distances"""
    click.echo('Multimerizing motifs given motifs and distances')
    ctx = read_config(ctx=ctx, config=config)
    ctx, basic_params = assign_basic_params(
        ctx=ctx, title=title, workdir=workdir, seed=seed)
    if motif_files is not None:
        mfiles = [fname.strip() for fname in motif_files.split(',')]
        ctx.default_map['motif_files'] = mfiles
    if ctx.default_map['motif_files'] is None:
        raise ValueError("Motif files should be provided.")
    if jaspar_db_version is not None:
        ctx.default_map['jaspar_db_version'] = jaspar_db_version
    if jaspar_db_version not in ctx.default_map:
        ctx.default_map['jaspar_db_version'] = None
    if multimerisation_rules is not None:
        ctx.default_map['multimerisation_rules'] = multimerisation_rules
    if ctx.default_map['multimerisation_rules'] is None:
        raise ValueError("Multimerisation rules should be provided.")
    multimer_params = MultimerParams(
        motif_files=ctx.default_map["motif_files"],
        jaspar_db_version=ctx.default_map["jaspar_db_version"],
        multimerisation_rule_path=ctx.default_map["multimerisation_rules"])
    controller = Controller(basic_params=basic_params)
    controller.create_multimers(multimer_params=multimer_params)


@cli.command()
@click.option(
    "--title", type=str, default="sim",
    help="Title of the simulation. Default: sim")
@click.option(
    "--workdir", default=".", type=click.Path(),
    help="Folder of the simulation outputs.\
Defaults to current work directory.")
@click.option(
    '--config', default=None, type=click.Path(),
    help="Config file for the simulation with the parameters for \
creating random sequences")
@click.option(
    "--num_backgrounds", type=int,
    help="Number of background sequences to simulate. Default: 100")
@click.option(
    "--b_length_min", type=int,
    help="Length of background sequences to simulate. If b_length_max \
is also specified, this is the lower  boundary of length. Default: 50")
@click.option(
    "--b_length_max", type=int,
    help="Maximum allowed length of the background sequences. The actual \
length is sampled from a uniform distribution. Default: None")
@click.option(
    "--b_alphabet", type=str,
    help="String of letters in the background alphabet, Default: ACGT")
@click.option(
    "--b_alphabet_prior", type=str,
    help="Comma separated probability of the letters in the background \
alphabet. Default: 0.25,0.25,0.25,0.25")
@click.option(
    "--background_files", type=click.Path(),
    help="Path(s) to the background file(s) in fasta format.")
@click.option(
    "--background_type", type=str,
    help="Parameter defining how the background sequences are used. \
Supported types are: iid, fasta_iid, markov_fit, markov_sim, \
random_nucl_shuffled_only, random_nucl_shuffled_addon. \
iid: Fasta files are ignored if provided, b_alphabet_prior specifies \
nucelotide probabilities. Default when background_files is None. \
fasta_iid: Fasta files are used as is, position probabilities are \
assigned based on b_alphabet_prior. Default when background_files \
is not None. markov_fit: Fasta files are used as is, position \
probabilities are calculated from a fitted hidden Markov model. \
Order specified with markov_order. markov_sim: Fasta files are used \
to fit and sample from hidden Markov model, so this is a type of \
simulation. Order specified with markov_order. random_nucl_shuffled_only: \
Fasta files are used, nucleotides in sequences are shuffled and only \
shuffled ones are returned. Position probabilities are \
assigned based on b_alphabet_prior. random_nucl_shuffled_addon: Fasta \
files are used, nucleotides in sequences are shuffled and both the \
original and the shuffled sequences are returned. Position \
probabilities are assigned based on b_alphabet_prior.")
@click.option(
    "--num_shuffle", type=int,
    help="Number of shuffle of the backgrounds. Used when shuffle is \
set not none.")
@click.option(
    "--markov_order", type=int,
    help="Order of Markov model to learn from sequences background_type \
is set to markov_fit or markov_sim. Defaults to 0 corresponding to \
learning independent nucleotide frequencies.")
@click.option(
    "--markov_n_iter", type=int,
    help="Number of iterations of Markov model to learn from sequences. \
Defaults to 100")
@click.option(
    "--markov_algorithm", type=int,
    help="Algorithm of Markov model to learn from sequences. \
Options: 'viterbi' or 'map'. See hmmlearn 0.3.3 documentation. \
Defaults to 'viterbi'.")
@click.option(
    '--seed', type=int, default=None,
    help="Seed value for reproducibility. Recommended (Optional)")
@click.pass_context
def random_sequences(
        ctx,
        title,
        workdir,
        config,
        num_backgrounds,
        b_length_min,
        b_length_max,
        b_alphabet,
        b_alphabet_prior,
        background_files,
        background_type,
        num_shuffle,
        markov_order,
        markov_n_iter,
        markov_algorithm,
        seed):
    """
    Creating random sequences given length and alphabet, \
    or input files to learn HMM from """
    click.echo(
        'Creating random sequences given length and alphabet, \
    or input files to learn HMM from')
    ctx = read_config(ctx=ctx, config=config)
    ctx, basic_params = assign_basic_params(
        ctx=ctx, title=title, workdir=workdir, seed=seed)
    ctx, background_params = assign_background_params(
        ctx=ctx,
        num_backgrounds=num_backgrounds,
        b_alphabet=b_alphabet,
        b_alphabet_prior=b_alphabet_prior,
        b_length_min=b_length_min,
        b_length_max=b_length_max,
        background_files=background_files,
        background_type=background_type,
        num_shuffle=num_shuffle,
        markov_order=markov_order,
        markov_n_iter=markov_n_iter,
        markov_algorithm=markov_algorithm,
        markov_seed=seed)
    controller = Controller(basic_params=basic_params)
    controller.create_backgrounds(background_params=background_params)


@cli.command()
@click.option(
    "--title", default="sim", type=str,
    help="Title of the simulation. Default: sim")
@click.option(
    "--workdir", default=".", type=click.Path(),
    help="Folder of the simulation outputs.\
Defaults to current work directory.")
@click.option(
    '--config', default=None, type=click.Path(),
    help="Config file for the simulation with the parameters for \
creating motived sequences")
@click.option(
    "--dirichlet_alpha",
    help="Alpha values for the Dirichlet distribution \
from which motifs are sampled. Default: 0.5,0.5,0.5,0.5")
@click.option(
    "--num_motifs", type=int,
    help="Number of motifs to create. Default: 10")
@click.option(
    "--m_length_min", type=int,
    help="Length of the motif. If --len_motifs_max is also \
specified, this is the lower boundary of length. Default: 5")
@click.option(
    "--m_length_max", type=int,
    help="Maximum allowed length of the motif. The actual \
length is sampled from a uniform distribution.(Optional)")
@click.option(
    "--m_alphabet", type=str,
    help="String of letters in the motif alphabet, Default: ACGT")
@click.option(
    "--motif_files", type=click.Path(),
    help="List of path(s) to the motif file(s). Supported formats \
are jaspar, meme, csv with JASPAR motif ids")
@click.option(
    "--jaspar_db_version", type=str,
    help="Version of JASPAR database to use when fetching \
with JASPAR motif IDs.")
@click.option(
    "--m_alphabet_pairs", type=str,
    help="Dictionary of letter pairs for reverse complementing the \
motif instance Default: 'A:T,C:G,G:C,T:A'")
@click.option(
    "--num_backgrounds", type=int,
    help="Number of background sequences to simulate. Default: 100")
@click.option(
    "--b_length_min", type=int,
    help="Length of background sequences to simulate. If b_length_max \
is also specified, this is the lower  boundary of length. Default: 50")
@click.option(
    "--b_length_max", type=int,
    help="Maximum allowed length of the background sequences. The actual \
length is sampled from a uniform distribution. Default: None")
@click.option(
    "--b_alphabet", type=str,
    help="String of letters in the background alphabet, Default: ACGT")
@click.option(
    "--b_alphabet_prior", type=str,
    help="Comma separated probability of the letters in the background \
        alphabet. Default: 0.25,0.25,0.25,0.25")
@click.option(
    "--background_files", type=click.Path(),
    help="Path(s) to the background file(s) in fasta format.")
@click.option(
    "--background_type", type=str,
    help="Parameter defining how the background sequences are used. \
Supported types are: iid, fasta_iid, markov_fit, markov_sim, \
random_nucl_shuffled_only, random_nucl_shuffled_addon. \
iid: Fasta files are ignored if provided, b_alphabet_prior specifies \
nucelotide probabilities. Default when background_files is None. \
fasta_iid: Fasta files are used as is, position probabilities are \
assigned based on b_alphabet_prior. Default when background_files \
is not None. markov_fit: Fasta files are used as is, position \
probabilities are calculated from a fitted hidden Markov model. \
Order specified with markov_order. markov_sim: Fasta files are used \
to fit and sample from hidden Markov model, so this is a type of \
simulation. Order specified with markov_order. random_nucl_shuffled_only: \
Fasta files are used, nucleotides in sequences are shuffled and only \
shuffled ones are returned. Position probabilities are \
assigned based on b_alphabet_prior. random_nucl_shuffled_addon: Fasta \
files are used, nucleotides in sequences are shuffled and both the \
original and the shuffled sequences are returned. Position \
probabilities are assigned based on b_alphabet_prior.")
@click.option(
    "--num_shuffle", type=int,
    help="Number of shuffle of the backgrounds. Used when shuffle is \
set not none.")
@click.option(
    "--markov_order", type=int,
    help="Order of Markov model to learn from sequences background_type \
is set to markov_fit or markov_sim. Defaults to 0 corresponding to \
learning independent nucleotide frequencies.")
@click.option(
    "--markov_n_iter", type=int,
    help="Number of iterations of Markov model to learn from sequences. \
Defaults to 100")
@click.option(
    "--markov_algorithm", type=int,
    help="Algorithm of Markov model to learn from sequences. \
Options: 'viterbi' or 'map'. See hmmlearn 0.3.3 documentation. \
Defaults to 'viterbi'.")
@click.option(
    "--num_groups", type=int,
    help="Number of groups into which motifs are assigned.  If = 1 \
all motifs are assigned to a single group. Default: 1")
@click.option(
    "--max_group_size", type=int,
    help="Maximum size of each group. It cannot be smaller than the \
number of motifs. Each group size is sampled from binomial distribution \
with number of trials = max_group_size and success = group_size_p. \
Default: inf")
@click.option(
    "--group_size_p", type=float,
    help="This parameter controls the expected size of each group. \
Each group size is sampled from binomial distribution with number of \
trials = max_group_size and success = group_size_p. Default: 1")
@click.option(
    "--group_motif_assignment_file", type=click.Path(),
    help="Path to the motif to group asisgnment file in two column \
tsv format. The first column is the group IDs, and the second column \
lists the motfIDs that are assigned to the corresponding group.")
@click.option(
    "--group_freq_type", type=str,
    help="The method of selecting group background frequencies.\
Values: uniform, random. Where uniform means each group has an \
equal chance to be selected. Random means each group is assigned \
a probability of being selected. The difference between a \
frequent and rare group is controlled by the --group_freq_range \
parameter. Default: uniform")
@click.option(
    "--group_freq_range", type=int,
    help="The range of the potential differences between a frequent \
and a rare group.")
@click.option(
    "--motif_freq_type", type=str,
    help="The method of selecting motif background frequencies.\
Values: uniform, random. Where uniform means each motif has an \
equal chance to be selected. Random means each motif is assigned \
a probability of being selected. The difference between a \
frequent and rare motif is controlled by the --motif_freq_range \
parameter. Default: uniform")
@click.option(
    "--motif_freq_range", type=int,
    help="The range of the potential differences between a frequent \
and a rare motif")
@click.option(
    "--concentration_factor", type=float,
    help="The preference of motifs to share the same group when \
selected for insertion. Value between 0 and 1. Default: 1")
@click.option(
    "--group_group_type", type=str,
    help="The method of selecting group-group transition \
probabilities. Values: uniform, random. Where uniform \
means any two groups are equally probable of co-occuring. \
Random means group pairs are assigned a random probability \
of transition. Default: uniform")
@click.option(
    "--group_freq_file", type=click.Path(),
    help="Tsv file including the background frequencies for the \
groups to be selected")
@click.option(
    "--motif_freq_file", type=click.Path(),
    help="Tsv file including the background frequencies for the \
selection of motifs to be inserted")
@click.option(
    "--group_group_file", type=click.Path(),
    help="Tsv file including the group-group transition \
probability matrix")
@click.option(
    "--position_type", type=str,
    help="Type of position simulation. \
Accepted values: central, left_central, right_central, uniform, \
gaussian. Central means the first motif is inserted into the center \
of the background. Left_central means aligning the first base to the center. \
Right_central means aligning the last base to the position one before center. \
Uniform means all position has equal chance. \
Gaussian means following the probabilities of a Gaussian \
distribution centered on the given position of the background \
as per the position_means and position_variances parameters. \
Gaussian insertions are left aligned and the insertion is without \
replacing existing bases. Default: uniform")
@click.option(
    "--position_means", type=str,
    help="Comma separated mean values for the gaussian positioning option.")
@click.option(
    "--position_variances", type=str,
    help="Comma separated variance values for the gaussian positioning \
option.")
@click.option(
    "--num_motif_in_seq", type=int,
    help="Number of sequences with motifs in them to generate. Default: 100")
@click.option(
    "--pc_no_motif", type=int,
    help="Percentage of sequences without motifs. \
Number between 0 and 100 is expected. Default: 0")
@click.option(
    "--to_replace", default=True, is_flag=True,
    help="Whether to replace backgorund bases with motif instance. \
Alternative is to insert between existing bases. Default: True")
@click.option(
    "--orientation_prob", type=float,
    help="Probability of reversing a motif instance in the motived \
sequence. Default: 0.5")
@click.option(
    "--num_groups_per_seq", type=int,
    help="Number of groups to sample per sequence. \
Default: 1")
@click.option(
    "--motif_sampling_replacement/--no-motif_sampling_replacement",
    default=True,
    help="Whether to select motifs from groups with replacement. \
Note, if more motifs are requested than available in a group, \
replacement will be used regardless of this parameter. \
Default: True")
@click.option(
    "--n_instances_per_sequence", type=int,
    help="Number of motif instances to be inserted per sequence.\
Takes precedent over --n_instances_per_sequence_l. Default: 1")
@click.option(
    "--n_instances_per_sequence_l", type=int,
    help="Lambda parameter of Poisson distribution for selecting the \
number of motif instances to be inserted per sequence.")
@click.option(
    '--to_draw', default=False, is_flag=True,
    help="Whether to draw the directed acyclic graph of the simulation steps.\
Default: False")
@click.option(
    '--seed', type=int,
    default=None,
    help="Seed value for reproducibility. Recommended (Optional)")
@click.pass_context
def motif_in_seq(
        ctx,
        title,
        workdir,
        config,
        dirichlet_alpha,
        num_motifs,
        m_length_min,
        m_length_max,
        m_alphabet,
        motif_files,
        jaspar_db_version,
        m_alphabet_pairs,
        num_backgrounds,
        b_length_min,
        b_length_max,
        b_alphabet,
        b_alphabet_prior,
        background_files,
        background_type,
        num_shuffle,
        markov_order,
        markov_n_iter,
        markov_algorithm,
        num_groups,
        max_group_size,
        group_size_p,
        group_motif_assignment_file,
        group_freq_type,
        group_freq_range,
        motif_freq_type,
        motif_freq_range,
        concentration_factor,
        group_group_type,
        group_freq_file,
        motif_freq_file,
        group_group_file,
        position_type,
        position_means,
        position_variances,
        to_replace,
        num_motif_in_seq,
        pc_no_motif,
        orientation_prob,
        num_groups_per_seq,
        motif_sampling_replacement,
        n_instances_per_sequence,
        n_instances_per_sequence_l,
        to_draw,
        seed):
    """ Simulating sequences with inserted motif instances """
    click.echo('Simulating sequences with inserted motif instances')
    ctx = read_config(ctx=ctx, config=config)
    ctx, basic_params = assign_basic_params(
        ctx=ctx, title=title, workdir=workdir, seed=seed)
    ctx, motif_params = assign_motif_params(
        ctx=ctx,
        dirichlet_alpha=dirichlet_alpha,
        num_motifs=num_motifs,
        m_length_min=m_length_min,
        m_length_max=m_length_max,
        m_alphabet=m_alphabet,
        m_alphabet_pairs=m_alphabet_pairs,
        motif_files=motif_files,
        jaspar_db_version=jaspar_db_version)
    ctx, background_params = assign_background_params(
        ctx=ctx,
        num_backgrounds=num_backgrounds,
        b_alphabet=b_alphabet,
        b_alphabet_prior=b_alphabet_prior,
        b_length_min=b_length_min,
        b_length_max=b_length_max,
        background_files=background_files,
        background_type=background_type,
        num_shuffle=num_shuffle,
        markov_order=markov_order,
        markov_n_iter=markov_n_iter,
        markov_algorithm=markov_algorithm,
        markov_seed=seed)
    ctx, group_params, freq_params = assign_group_freq_params(
        ctx=ctx,
        num_groups=num_groups,
        max_group_size=max_group_size,
        group_size_p=group_size_p,
        group_motif_assignment_file=group_motif_assignment_file,
        group_freq_type=group_freq_type,
        group_freq_range=group_freq_range,
        motif_freq_type=motif_freq_type,
        motif_freq_range=motif_freq_range,
        concentration_factor=concentration_factor,
        group_group_type=group_group_type,
        group_freq_file=group_freq_file,
        motif_freq_file=motif_freq_file,
        group_group_file=group_group_file)
    ctx, positions_params, sampling_params = assign_position_sampling_params(
        ctx=ctx,
        position_type=position_type,
        position_means=position_means,
        position_variances=position_variances,
        num_motif_in_seq=num_motif_in_seq,
        pc_no_motif=pc_no_motif,
        to_replace=to_replace,
        orientation_prob=orientation_prob,
        num_groups_per_seq=num_groups_per_seq,
        motif_sampling_replacement=motif_sampling_replacement,
        n_instances_per_sequence=n_instances_per_sequence,
        n_instances_per_sequence_l=n_instances_per_sequence_l,
        to_draw=to_draw)
    controller = Controller(basic_params=basic_params)
    controller.run_inmotifin(
        motif_params=motif_params,
        background_params=background_params,
        group_params=group_params,
        freq_params=freq_params,
        sampling_params=sampling_params,
        positions_params=positions_params)
