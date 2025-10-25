# README #

inMOTIFin is a lightweight python package for simulating cis-regulatory elements.
It consists of four command line modules and python access to the backend for advanced usage.

Complete documentation is found at [https://inmotifin.readthedocs.io/en/latest/](https://inmotifin.readthedocs.io/en/latest/).

## Simulation of sequences with inserted motif instances ##

This option of the inMOTIFin package is built using [DagSim](https://uio-bmi.github.io/dagsim/index.html) a simulation framework for causal models.

The directed acyclic graph (DAG) shown below describes the nodes and their relationship for the simulation.
Each node describes a value or sampling strategy (depending on user input).
The output of one node is the input to its downstream nodes.

![DAG of the simulation](docs/usage/images/dag.png)

## Simulation of random sequences ##

by controlling their length, alphabet, and base preference

```
{
    'background_sim_seq_0': 'CGCGTACGGGGTCCGACCCTTAAAA',
    'background_sim_seq_1': 'CCGCGAACGTGGCCGTCTGCAGAAC',
    'background_sim_seq_2': 'AGAGCACCGGACGTGACCGCGGAAT',
    'background_sim_seq_3': 'GTTCCACCCGAAACCACAGCGGCTA',
    'background_sim_seq_4': 'ACCGTACAAAGGAGGTAAATCGATG'
}
```

## Simulation of motifs ##

by controlling their length, information content, and alphabet.

Left: simulated motif_1 ; right: simulated motif_2

<img src="docs/usage/images/motif_1.png" alt="motif1" width="185"/>
<img src="docs/usage/images/motif_2.png" alt="motif2" width="350"/>


## Multimerisation of motifs ##

by providing distances between the motif components.

Motif_1 and motif_2 multimerised by setting a positive distance.

![dim1](docs/usage/images/multimer_pos_example.png)

...or a negative distance.

![dim2](docs/usage/images/multimer_neg_example.png)

### How do I get set up? ###

#### Summary of set up ####

You can either install from [pypi](https://pypi.org/project/inMOTIFin/) with the command

```python -m pip install inmotifin```

or pull the container at [dockerhub](https://hub.docker.com/r/cbgr/inmotifin/tags). If you have docker installed, you can run from within the docker container with

```sudo docker run -it cbgr/inmotifin:latest bash ```

Altenarively, you can also clone this repository, you may install the package locally by `pip install -e . ` run in the folder where the `setup.py` file resides.

#### Dependencies ####

The code is written in python 3.9 . Dependencies ([click](https://click.palletsprojects.com/en/stable/), [numpy](https://numpy.org/), [pandas](https://pandas.pydata.org/), [DagSim](https://uio-bmi.github.io/dagsim/quickstart.html), [pyjaspar](https://github.com/asntech/pyjaspar), and [biopython](https://biopython.org/)) are installed with the software.

#### How to run tests ####

Unit tests can be run with the `pytest . ` command after cloning and installing the package locally.

As a developer, you can also see the results of the unit tests and an intergation test at pipelines.


### Contribution guidelines ###

#### Coding style ####

 The code is written in object oriented way. The code is documented with docstring following the numpy style. Please add input and output types to each function. Please set linting with pylint and flake8.

#### Writing tests ####

The aim is to have a decent test coverage, such as your best effort. The test folder mirrors the structure of the source (inmotifin) folder. The tests are using the unittest framework.

If you are not sure what to test, one way to go about it is to find which lines of the code are covered. This can be done using [coverage.py](https://coverage.readthedocs.io/en/7.10.7/) `coverage run -m pytest && coverage html` command. 
This generates multiple outputs, the one to keep an eye on is `htmlcov/index.html`. When opening this in your browser you can check which lines are covered by test and which are not.

#### Code review ####

Upon pull request. Please do not merge to main/dev without contacting the authors.

#### Other guidelines ####

The repository is connected to Jira, where the features and issues are listed. After familiarizing yourself with the current status of the software and the style, pick a feature and (from dev) create a branch for it in Jira. Please work on that branch and use smart commits. Once the feature is added, linting and the unit tests are passing, open a pull request to dev.

### Who do I talk to? ###

#### Repo owner or admin ####

Katalin Ferenc (k.t.ferenc@ncmm.uio.no)

#### Other community or team contact ####

Anthony Mathelier (anthony.mathelier@ncmm.uio.no)

### License
[MIT license](https://opensource.org/license/mit)