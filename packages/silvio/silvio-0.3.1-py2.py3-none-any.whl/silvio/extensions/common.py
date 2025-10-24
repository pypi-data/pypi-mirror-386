"""
Common datatypes between the different extensions.
"""

from typing import List, Literal, Optional


# One of the simple 4 nucleic bases, plus the unknown base.
Base = Literal['A','C','G','T']


# Well distinguished promoter sites.
PromoterSite = Literal[ '-10', '-35' ]


# Read methods usable by the sequencer.
ReadMethod = Literal[ 'single-read', 'paired-end' ]


# BIGG organism dictionary for model download
BIGG_dict = {'E.coli-core':'e_coli_core', 'E.coli': 'iML1515','B.subtilis': 'iYO844', 'P.putida': 'iJN1463', 'S.cerevisiae': 'iMM904'}

# standard units of ExperimentSettings variables
myUnits = {
    'Temperature': 'Celsius',
    'CultivationTime': 'hours',
    'SamplingInterval': 'hours',
    'InitBiomass': 'OD600',
    'MediumVolume': 'mL',
    'CarbonConc': 'mM',
}

# Carbon containing metabolites that are gases, they are treated differently for analytics
GasCarbMets = ['co2', 'ch4']

# Dictionary with analytics and their prices relative to full budget
AnalyticsCosts = {
    'OD600': 0.1,
    'Carbon-Substrate': 0.2,
    'Metabolites': 0.5,
    'pH': 0.1,
    'Biomass': 0.3,
    'HPLC': 0.7,
}

# Dictionary with parameters for unit testing
TestParams = {
    'Time': 10, # hours
}