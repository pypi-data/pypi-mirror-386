
from typing import Tuple, List, Callable
from collections import namedtuple
from copy import copy

import numpy as np
import pandas as pd
from pandas import DataFrame

from ...host import Host
from ...module import Module
from ...outcome import Outcome
from ...events import EventEmitter, EventLogger
from ...random import Generator
from ..records.gene.gene import Gene
from ..utils.misc import Help_GrowthConstant, Growth_Maxrate, add_noise, add_noise2, Help_BiomassTimeIntegral, Help_GrowthRandom
from .genome_expression import GenomeExpression
from ...experiment import ExperimentSettings
from ..common import GasCarbMets, TestParams


class GrowthBehaviour ( Module ) :

    # Creator of random number generators. Host will bind this.
    make_generator: Callable[[],Generator]

    # Dependent module Genome Expression holding the genes to express.
    genexpr: GenomeExpression

    opt_growth_temp: int
    max_biomass: int

    # Monod Parameters
    # Monod Substrate affinity
    Ks: float
    # Monod Yield coefficient
    Yxs: float
    # Monod Maximum growth rate
    umax: float



    def make ( self, opt_growth_temp:int, max_biomass:int, umax:float ) -> None :
        self.opt_growth_temp = opt_growth_temp
        self.max_biomass = max_biomass
        self.umax = umax

    def make2 ( self, opt_growth_temp:int, max_biomass:int , Ks:float, Yxs:float, k1:float, umax:float, OD2X ) -> None :
        self.opt_growth_temp = opt_growth_temp
        self.max_biomass = max_biomass
        self.Ks = Ks
        self.Yxs = Yxs
        self.k1 = k1
        self.umax = umax
        self.OD2X = OD2X


    def copy ( self, ref:'GrowthBehaviour' ) -> None :
        self.opt_growth_temp = ref.opt_growth_temp
        self.max_biomass = ref.max_biomass



    def bind ( self, host:Host, genexpr:GenomeExpression ) -> None :
        self.make_generator = host.make_generator # Pass bound method Host.make_generator
        self.genexpr = genexpr

    def bind2 ( self, host:Host ) -> None :
        self.make_generator = host.make_generator # Pass bound method Host.make_generator


    def sync ( self, emit:EventEmitter, log:EventLogger ) -> None :
        pass # Nothing to sync.



    def Make_TempGrowthExp ( self, CultTemps:list[int], exp_suc_rate:float ) -> Tuple[ pd.DataFrame, List[Tuple] ]:
        """
        TODO: Ideally, growth should return a table with enough information to contain the
        biomass results and to infer the loading times. Loading times is a synthetic construct
        that should be contained in a catalog Host, while the Module should only contain efficient
        calculations. The Host is an API for the User and may add interaction such as
        Resource management and loading times.

        TODO: If loading time should really be calculated here, then think about returning an
        additional record-oriented dataframe with columns (exp, temp, loading_len).

        TODO: I'm not sure oh the nuances but propose the following changes to make this conforming:
        - Remove the Experiment Success Rate and only use it at the "catalog.recexpsim.Host" level.
        - Make each simulation  call use a single temperature. (though, some calculations use all temps)
        - Each simulation returns a Series with the mass-over-time values.
        - Rename this method to "sim_cultivation" with renamed arguments.

        Returns
        =======
        [ mass_over_time_for_temp, pauses ]
            mass_over_time_for_temp
                Dataframe holding the mass over time for each temperature in a column.
            pauses
                List of tuples containing loading time information.

        """
        rnd = self.make_generator()

        CultTemps = np.array(CultTemps)
        Exp_Duration = 48

        capacity = self.max_biomass
        # the time of the half maximum population (inflection point) is calculated according to here:
        # https://opentextbc.ca/calculusv2openstax/chapter/the-logistic-equation/
        d_mult = 2  # we multiply the inflection point with 'd_mult' to increase cultivation time
        P0 = 0.1

        # determine time vector with maximum length:
        OptTemp = self.opt_growth_temp
        # Selecting the temperature that is most distant from the optimal temperature
        Temp_tmax = CultTemps[np.argmax(np.absolute(CultTemps-OptTemp))]
        # using the worst temperature to calculate lowest growth rate
        r_tmax = self.umax * Help_GrowthConstant(OptTemp, Temp_tmax)
        # using the worst temperature growth rate to compute longest simulation time, maximum set to 72 h
        duration_tmax = d_mult * 1/r_tmax * np.log((capacity - P0)/P0) + 1
        t_max = np.arange(np.minimum(Exp_Duration, duration_tmax))

        # create an empty DataFrame with t_max as first column
        col = []
        col.append('time [h]')
        for i in range(len(CultTemps)):
            col.append('exp.{} biomass conc. at {} °C'.format(i, (CultTemps[i])))

        df = pd.DataFrame(np.empty(shape=(len(t_max), len(CultTemps)+1), dtype=float), columns=col)
        df[:len(t_max)] = np.nan
        new_df = pd.DataFrame({'time [h]': t_max})
        df.update(new_df)

        PauseEntry = namedtuple('PauseEntry', 'exp loading_len')
        pauses = []

        # computing of biomass data and updating of DataFrame
        for i in range(len(CultTemps)):

            if rnd.pick_uniform(0,1) > exp_suc_rate: # TODO: Too nested. # experiment failure depending on investment to equipment
                r = self.umax * Help_GrowthConstant(OptTemp, CultTemps[i])
                # the result can reach very small values, which poses downstream problems, hence the lowest value is set to 0.05
                if r > 0.05: # under process conditions it might be realistic, source : https://www.thieme-connect.de/products/ebooks/pdf/10.1055/b-0034-10021.pdf
                    duration = Exp_Duration # d_mult * 1/r * np.log((capacity - P0)/P0) + 1
                else:
                    duration = Exp_Duration
                t = np.arange(np.minimum(Exp_Duration, duration))

                # biomass data is calculated according to https://en.wikipedia.host/wiki/Logistic_function
                mu = capacity / (1 + (capacity-P0) / P0 * np.exp(-r * t))
                sigma = 0.1*mu

                exp_TempGrowthExp = [rnd.pick_normal(mu[k], sigma[k]) for k in range(len(mu))]

                loading_len = len(t)
                exp = ' of exp.{} at {} °C'.format(i, (CultTemps[i]))
                pauses.append(PauseEntry( exp, loading_len ))

            else:
                mu = P0
                sigma = 0.08*mu
                exp_TempGrowthExp = [rnd.pick_normal(mu, sigma) for i in range(Exp_Duration)] # if cells haven't grown, the measurement is only continued for 6h

                loading_len = 7
                exp = ' of exp.{} at {} °C'.format(i, (CultTemps[i]))
                pauses.append(PauseEntry( exp, loading_len ))


            new_df = pd.DataFrame({'exp.{} biomass conc. at {} °C'.format(i, (CultTemps[i])): exp_TempGrowthExp})
            df.update(new_df)

        return ( df, pauses )

    def Make_MonodExperiment( self, CultTemps:list[int], exp_suc_rate:float ) -> Tuple[ pd.DataFrame, List[Tuple] ]:
        """

        Returns
        =======
        [ mass_over_time_for_temp, pauses ]
            mass_over_time_for_temp
                Dataframe holding the mass over time for each temperature in a column.
            pauses
                List of tuples containing loading time information.

        """
        rnd = self.make_generator()

        CultTemps = np.array(CultTemps)
        Exp_Duration = 48

        capacity = self.max_biomass
        # the time of the half maximum population (inflection point) is calculated according to here:
        # https://opentextbc.ca/calculusv2openstax/chapter/the-logistic-equation/
        d_mult = 2  # we multiply the inflection point with 'd_mult' to increase cultivation time
        P0 = 0.1

        # determine time vector with maximum length:
        OptTemp = self.opt_growth_temp
        # Selecting the temperature that is most distant from the optimal temperature
        Temp_tmax = CultTemps[np.argmax(np.absolute(CultTemps-OptTemp))]
        # using the worst temperature to calculate lowest growth rate
        r_tmax = Help_GrowthConstant(OptTemp, Temp_tmax)
        # using the worst temperature growth rate to compute longest simulation time, maximum set to 72 h
        duration_tmax = d_mult * 1/r_tmax * np.log((capacity - P0)/P0) + 1
        t_max = np.arange(np.minimum(Exp_Duration, duration_tmax))

        # create an empty DataFrame with t_max as first column
        col = []
        col.append('time [h]')
        for i in range(len(CultTemps)):
            col.append('exp.{} biomass conc. at {} °C'.format(i, (CultTemps[i])))

        df = pd.DataFrame(np.empty(shape=(len(t_max), len(CultTemps)+1), dtype=float), columns=col)
        df[:len(t_max)] = np.nan
        new_df = pd.DataFrame({'time [h]': t_max})
        df.update(new_df)

        PauseEntry = namedtuple('PauseEntry', 'exp loading_len')
        pauses = []

        # computing of biomass data and updating of DataFrame
        for i in range(len(CultTemps)):

            if rnd.pick_uniform(0,1) > exp_suc_rate: # TODO: Too nested. # experiment failure depending on investment to equipment
                r = Help_GrowthConstant(OptTemp, CultTemps[i])
                # the result can reach very small values, which poses downstream problems, hence the lowest value is set to 0.05
                if r > 0.05: # under process conditions it might be realistic, source : https://www.thieme-connect.de/products/ebooks/pdf/10.1055/b-0034-10021.pdf
                    duration = Exp_Duration # d_mult * 1/r * np.log((capacity - P0)/P0) + 1
                else:
                    duration = Exp_Duration
                t = np.arange(np.minimum(Exp_Duration, duration))

                # biomass data is calculated according to https://en.wikipedia.host/wiki/Logistic_function
                mu = capacity / (1 + (capacity-P0) / P0 * np.exp(-r * t))
                sigma = 0.1*mu

                exp_TempGrowthExp = [rnd.pick_normal(mu[k], sigma[k]) for k in range(len(mu))]

                loading_len = len(t)
                exp = ' of exp.{} at {} °C'.format(i, (CultTemps[i]))
                pauses.append(PauseEntry( exp, loading_len ))

            else:
                mu = P0
                sigma = 0.08*mu
                exp_TempGrowthExp = [rnd.pick_normal(mu, sigma) for i in range(Exp_Duration)] # if cells haven't grown, the measurement is only continued for 6h

                loading_len = 7
                exp = ' of exp.{} at {} °C'.format(i, (CultTemps[i]))
                pauses.append(PauseEntry( exp, loading_len ))


            new_df = pd.DataFrame({'exp.{} biomass conc. at {} °C'.format(i, (CultTemps[i])): exp_TempGrowthExp})
            df.update(new_df)

        return ( df, pauses )

    def Make_ProductionExperiment ( self, gene:Gene, CultTemp, GrowthRate, Biomass, ref_prom:str, accuracy_Test=.9 ) -> Outcome :
        """
        Return an outcome with the expression rate.
        """
        growth_const = Help_GrowthConstant(self.opt_growth_temp, self.opt_growth_temp)

        # testing whether the determined maximum biomass and the determined maximum growth rate are close to the actual ones
        if not (
            1 - np.abs(Biomass-self.max_biomass) / self.max_biomass > accuracy_Test
            and 1 - np.abs(GrowthRate-growth_const) / growth_const > accuracy_Test
        ) :
            return Outcome[float]( 0, 'Maximum biomass and/or maximum growth rate are incorrect.' )

        # Growth rate was only checked, for the calculation the rate resulting from the temperature is used
        r = Help_GrowthConstant(self.opt_growth_temp, CultTemp)
        GrowthMax = Growth_Maxrate(r, Biomass)
        PromStrength = self.genexpr.calc_prom_str( gene=gene, ref_prom=ref_prom )
        AbsRate = round(GrowthMax * PromStrength,2)
        FinalRelRate = round(AbsRate/self.Calc_MaxExpress(),2)
        return Outcome[float]( FinalRelRate )



    def Calc_MaxExpress (self) -> float :
        '''Function to calculate the maximum possible expression rate.'''
        BiomassMax = self.max_biomass
        OptTemp = self.opt_growth_temp
        factor = self.genexpr.infl_prom_str
        species_str = self.genexpr.species_prom_str
        MaximumPromoterStrength = round(species_str * factor,2)
        r = Help_GrowthConstant(self.opt_growth_temp, OptTemp)
        GrowthMax = Growth_Maxrate(r, BiomassMax)
        return round(GrowthMax * MaximumPromoterStrength,2)


    def Stream_TempGrowthExp ( self, ExperimentSettings:ExperimentSettings, Success_rate:float, Test:bool = False ) -> np.array :
        """
        Return a list of biomass values over time for a given experiment setting.
        The growth rate is adjusted according to the temperature using a growth constant function.
        The biomass values are perturbed with a normal distribution to simulate measurement noise.

        Arguments:
            ExperimentSetting: ExperimentSettings, settings for the experiment
        Outputs:
            List of biomass values over time        
        """
        if not Test:
            ExpFail_rand= 1#self.make_generator().pick_uniform(0,1)
            if ExpFail_rand > Success_rate:
                # calculating the variation of the growth rate based on the temperature difference
                GrowthRate = ExperimentSettings.GrowthRate * Help_GrowthConstant(self.opt_growth_temp, ExperimentSettings.Temperature)

                # biomass data is calculated according to https://en.wikipedia.org/wiki/Logistic_function
                K = ExperimentSettings.Capacity  # in gCDW/L
                P0 = ExperimentSettings.InitBiomass # in gCDW/L
                # calculate biomass over time
                Biomass = K / (1 + (K-P0) / P0 * np.exp(-GrowthRate * ExperimentSettings.SampleVector))

            else:
                # no growth, values around the initial biomass are selected from a normal distribution
                Biomass = np.tile(ExperimentSettings.InitBiomass, ExperimentSettings.SampleVector.shape)

            Biomass_perturbed = Biomass
            # np.array([np.random.normal(Biomass[k], sigma[k]) for k in range(len(Biomass))])

            return ( add_noise2(Biomass_perturbed, Success_rate) )

        # Unit testing mode
        else:
            # in test mode, generate 10 samples with logistic growth curve, x values 0-9, y values 0-5, steepest growth at x=8
            x = np.arange(TestParams['Time'])
            L = 5  # maximum value
            k = 2  # steepness
            x0 = 8  # inflection point
            Test = L / (1 + np.exp(-k * (x - x0)))
            return Test


    def Stream_CalcSubConc ( self, Biomass:np.array, ExperimentSettings:ExperimentSettings, Success_rate:float) -> List[float] :
        """
        Return a list of metabolite concentrations over time for a given biomass list.
        The metabolite concentration is calculated based on the biomass and the yield coefficient.

        Arguments:
            Biomass: list of biomass values over time
            ExperimentSetting: ExperimentSettings, settings for the experiment
        Outputs:
            List of metabolite concentrations over time        
        """
        MetConc = abs(ExperimentSettings.CarbonSubConc['EX_glc__D_e'] - (Biomass - ExperimentSettings.InitBiomass) / ExperimentSettings.Yields['EX_glc__D_e'])
        Result = add_noise2(MetConc, Success_rate)

        return Result
    


    def Stream_CalcProdConc ( self, Biomass:np.array, SolProd:dict, SampleVector:np.array, Success_rate:float, Test:bool=False) -> dict :
        """
        Return a list of product concentrations over time for a given biomass list.
        The product concentration is calculated based on the biomass and the yield coefficient.
        The product concentration is calculated based on the biomass and the yield coefficient.

        Arguments:
            Biomass: list of biomass values over time
            ExperimentSetting: ExperimentSettings, settings for the experiment
        Outputs:
            List of product concentrations over time        
        """
        if Test:
            # in test mode, generate 10 random  samples without input parameters
            Biomass = Help_GrowthRandom()
            Test = {f'Product_{i}': Biomass * np.random.uniform(.1,5) for i in range(3)}
            return ( Test )
        
        # integrate biomass over time 
        BiomassInt_t = Help_BiomassTimeIntegral(Biomass, SampleVector) # in gCDW/L * h
        # calculating the biomass differences at each time point
        BiomassDiff_t = np.insert(np.diff(BiomassInt_t), 0, 0) # in gCDW/L * h
        # calculating the product concentration at each time point based on the biomass differences
        ProdConc = {rxn: np.cumsum(BiomassDiff_t * float(value)) for rxn,value in SolProd.items()} # in mM
        return ProdConc

    def calc_CarbonSolubleConcentrationDynamics (self, Biomass:np.array, ExperimentSettings:ExperimentSettings, Test:bool=False ) -> dict :
        if Test:
            # in test mode, generate 10 random  samples without input parameters
            Biomass = Help_GrowthRandom()
            Test = {f'Product_{i}': Biomass * np.random.uniform(.1,5) for i in range(3)}
            return ( Test )
        else:
            # integrate biomass over time 
            BiomassInt_t = Help_BiomassTimeIntegral(Biomass, ExperimentSettings.SampleVector) # in gCDW/L * h
            # calculating the biomass differences at each time point
            BiomassDiff_t = np.insert(np.diff(BiomassInt_t), 0, 0) # in gCDW/L * h
            # setting the initial metabolite concentrations in a dictionary. 
            # First initializing all concentrations with 0
            MetInitConc = {rxn: 0 for rxn in ExperimentSettings.CarbonSolubleExchange.keys()}
            # then setting the initial concentrations for the carbon substrates defined in ExperimentSettings.CarbonSubConc
            MetInitConc.update({rxn: value for rxn,value in ExperimentSettings.CarbonSubConc.items() if rxn in MetInitConc})
            # calculating the product concentration at each time point based on the biomass differences
            CarbSolConcDyn = {rxn: MetInitConc[rxn] + Biomass / ExperimentSettings.Yield[rxn] for rxn in ExperimentSettings.CarbonSolubleExchange} # in mM MetInitConc[rxn] + np.cumsum(BiomassDiff_t * CarbonExch[rxn])

            return CarbSolConcDyn