"""
Experiment is the top-most scope. It includes all hosts and registries and acts as a global
namespace.
"""

import numpy as np
from typing import Set, Optional, Union
from abc import ABC
import pandas as pd

from numpy.random import SeedSequence

from .host import Host
from .random import Generator



class ExperimentException (Exception) :
    """ Exception that is triggered by an experiment. """
    pass



class Experiment (ABC) :
    """ The basic experiment will hold the hosts and a random-generator. """

    hosts: Set[Host]

    # The experiment will hold an internal random generator to allow repeatability.
    rnd_gen: Generator



    def __init__ ( self, seed:Optional[Union[int,SeedSequence]] = None ) :
        self.hosts = set()
        self.rnd_gen = Generator(seed)



    def bind_host ( self, host:Host ) -> None :
        """Keep the host accessible via the experiment."""
        self.hosts.add(host)



    # def create_host ( self, host_class:Type[Host], **kwargs ) -> None :
    #     host = host_class( exp=self, **kwargs )
    #     self.hosts.append( host )

class ExperimentSettings (ABC):
    """Class to hold experiment settings and parameters."""

    # Dictionary to store chromatograms for time point
    Chromatograms: pd.DataFrame


    # definition of Experiment class with experiment settings
    Test: bool = False # flag to indicate if the experiment is a test
    ExperimentID: str # unique identifier for the experiment
    ExperimentType: str # e.g., "Batch", "Fed-Batch", "Continuous"
    Analytics: list # list of analytics to be performed, e.g., ['OD600', 'HPLC']
    HostName: str # name of the host organism
    Temperature: list # values in Celsius
    CultivationTime: int # default value in hours
    SamplingInterval: float # default sampling interval in hours
    AnalyticSampling: list # specific time points for analytics
    InitBiomass: float # default initial biomass concentration in g/L
    MediumVolume: int # default value in mL
    MediumComposition: dict # key: name of the component, value: concentration in mM
    # CarbonID: str # identifier for the main carbon substrate, following BiGG nomenclature in the GSM model
    CarbonName: list # names of the main carbon substrate
    CarbonSubConc: dict # key: name, as exchange reaction id in model, value: concentration of the carbon substrate in mM
    CarbonUptakeRate: dict # key: name, as exchange reaction id in model, value: uptake rate of the carbon substrate in mmol/gCDW/h
    CarbonSolubleExchange: dict # key: name, carbon exchange reaction id in model, value: exchange rate of carbon metabolite in mmol/gCDW/h (-: uptake, +: secretion)
    CarbonConcDynamic: list # dynamic concentration profile of the carbon substrate over time
    GrowthRate: float # specific growth rate in 1/h
    Yield: dict # key: exchange reactionid, value: biomass yields for soluble metabolites in gCDW/mmol
    Capacity: int # maximum biomass concentration in g/L
    ExchangeRates: dict # key: name, as exchange reaction id in model, value: exchange rate of the metabolite in mmol/gCDW/h
    Results: str # file path to save experiment results

    def __init__(self, Test: bool=False) -> None :
        # initializing the experiment settings with empty values
        self.Test = Test
        self.ExperimentID = ""
        self.ExperimentType = ""
        self.Analytics = []
        self.HostName = ""
        self.Temperature = []
        self.CultivationTime = 0
        self.SamplingInterval = 1.0
        self.AnalyticSampling = []
        self.InitBiomass = 0.0
        self.MediumVolume = 0
        self.MediumComposition = {}
        # self.CarbonID = ""
        self.CarbonName = []  # names of the main carbon substrate
        self.CarbonSubConc = {}
        self.CarbonUptakeRate = {}
        self.CarbonSolubleExchange = {}
        self.CarbonConcDynamic = []
        self.GrowthRate = 0.0
        self.Yield = {}
        self.Capacity = 0
        self.ExchangeRates = {}
        self.Results = ""

        if self.Test:
            self.HostName = "E.coli-core"
            self.InitBiomass = 0.1  # g/L
            # self.CarbonName = ['EX_glc__D_e']
            self.CarbonSubConc = {'EX_glc__D_e': 10.0}  # mM
            self.SamplingInterval = .5
            self.CultivationTime = 10.0

    def set_SamplingVector(self) -> None :
        """Method to generate the sampling vector based on CultivationTime and SamplingInterval."""
        self.SampleVector = np.arange(0, self.CultivationTime + self.SamplingInterval, self.SamplingInterval)

    # the chromatograms dictionary will hold the chromatograms for each time with analytics
    def add_Chromatograms(self, Chromatograms: pd.DataFrame) -> None :
        self.Chromatograms = Chromatograms