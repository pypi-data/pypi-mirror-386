""" Data storage for multimer parameters """
from typing import List
from dataclasses import dataclass


@dataclass
class MultimerParams:
    """ Class for keeping track of parameters for multimers

    Class parameters
    ----------------
    motif_files: List[str]
        List of motif file(s) to use for multimerisation
    jaspar_db_version: str
        Version of the JASPAR database to use when Jaspar \
        IDs are provided in the motif file(s)
    multimerisation_rule_path: str
        Path to the multimerisation rules file
    """
    motif_files: List[str]
    multimerisation_rule_path: str
    jaspar_db_version: str = None
