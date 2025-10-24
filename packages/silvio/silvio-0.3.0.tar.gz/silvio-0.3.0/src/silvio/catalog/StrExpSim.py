"""
An experiment that uses hosts which implements all currently existing modules.
"""

from __future__ import annotations
from typing import Optional, List, Tuple, Literal
from pathlib import Path

import os
import copy
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.integrate as spi
from cobra.core.model import Model


from silvio import (
    DATADIR, # config
    Experiment, ExperimentException, Host, HostException, ExperimentSettings, # base classes
    alldef, coalesce, first, Generator, # utilities
    DataOutcome, DataWithPlotOutcome, combine_data, add_dfcolumn, # outcome
    GrowthBehaviour, MetabolicFlux, # modules
)
# additional non-renamed utilities
from silvio.extensions.utils.visual import Help_Progressbar
from silvio.extensions.utils.laboratory import ErrorRate
from silvio.extensions.utils.misc import Help_GrowthConstant, Download_GSMM, add_noise
from silvio.extensions.modules.metabolism import HPLCProperties


class DigLabSim (Experiment) :
    """
    Growth experiments on Monod equation with temperature, substrate and sampling times.
    """

    budget: int

    suc_rate: float

    # Keep track of how many hosts were created
    host_counter: int

    # storing HPLC properties
    HPLC = HPLCProperties()

    # Record of all experiments conducted
    class experiment_history:
        pass

    # # Store experiment settings by ExperimentID for easy access
    # experiment_history: dict[str, ExperimentSettings] = {}


    def __init__ ( self, seed:Optional[int] = None, equipment_investment:int = 0, max_budget:int = 10000  ) :

        if equipment_investment > max_budget :
            raise ExperimentException("Investment cost is higher than maximal budget.")

        super().__init__(seed=seed)
        self.budget = max_budget - equipment_investment
        self.suc_rate = ErrorRate(equipment_investment, max_budget)
        self.host_counter = 0
        self.HPLC = HPLCProperties()
        self.experiment_history = {} # initialize empty history dict


    def create_host ( self, name:Optional[str] ) -> GroHost:
        self.host_counter += 1
        seed = self.rnd_gen.pick_seed() # The experiment provides stable seed generation for hosts.
        new_host = None

        new_host = self.build_host( name=name, seed=seed )

        self.bind_host(new_host)
        return new_host



    def build_host ( self, name:str, seed:int ) -> GroHost :
        gen = Generator( seed )
        host = GroHost( name=name, seed=seed )
        GSMM = Download_GSMM(name)
        Yxs = round(gen.pick_uniform(.15, .55), 2) # unit: gDW/gSubstrate, source: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4681042/
        opt_growth_temp= gen.pick_integer(25, 40) # unit: degree celsius, source: https://application.wiley-vch.de/books/sample/3527335153_c01.pdf
        max_biomass= gen.pick_integer(30, 100) # unit: in gDW/L, source (german): https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=2&cad=rja&uact=8&ved=2ahUKEwjzt_aJ9pzpAhWGiqQKHb1jC6MQFjABegQIAhAB&url=https%3A%2F%2Fwww.repo.uni-hannover.de%2Fbitstream%2Fhandle%2F123456789%2F3512%2FDissertation.pdf%3Fsequence%3D1&usg=AOvVaw2XfGH11P9gK2F2B63mY4IM
        Ks = round(gen.pick_uniform(1, 10), 3) # unit: gSubstrate/L, source: https://bionumbers.hms.harvard.edu/bionumber.aspx?s=n&v=3&id=111049, for K12
        k1 = round(gen.pick_uniform(.05, .2), 3)
        umax = round(gen.pick_uniform(.1, 2*Yxs), 3) # unit: /h, the maximum growth rate determines with the biomass yield the max glucose uptake rate. This should be below 10 mmol/gDW/h
        OD2X = round(gen.pick_uniform(0.3, 0.5), 3)
        host.make(
            opt_growth_temp=opt_growth_temp,
            max_biomass=max_biomass,
            Ks=Ks,
            Yxs=Yxs,
            k1=k1,
            umax=umax,
            OD2X=OD2X,
            GSMM=GSMM
        )
        host.sync()
        
        # adding kinetic information to GSMM
        host.metabolism.set_KinParameters()

        return host


    def find_host_or_abort ( self, host_name:str ) -> GroHost :
        """
        Find a host by a given name or abort with an exception.
        Throws: ExperimentException
        """
        host:Optional[GroHost] = first( self.hosts, lambda h: h.name == host_name )
            # Find the first host matching the name.
        if host is None :
            raise ExperimentException("Experiment has not found the host '{}'".format(host_name))
        return host

    def spend_budget_or_abort ( self, amount:int ) -> None :
        """
        Each operation may use up a certain amount of the budget.
        When the budget is not sufficient those operations will all fail.
        By using error handling via raised exceptions we don't need to check each method for a
        success flag on their return value.
        Throws: ExperimentException
        """
        if amount > self.budget :
            raise ExperimentException("Experiment has surpassed its budget. No more operations are allowed.")
        self.budget -= amount

    def record_experiment(self, settings: ExperimentSettings) -> None:
        """
        Record the details of an experiment along with its settings.
        Args:
            settings (ExperimentSettings): The settings of the experiment to be recorded.
        """
        self.experiment_history[settings.ExperimentID] = settings

    def measure_DryWeight( self, host_name:str, Temperature:float, FinalTime:float, SubstrateConc:float, Replicates: int, FileName: str ) -> DataOutcome :
        '''Experiment to determine the correlation between OD and dry weight. The factor depends on the temperature. Get growth phase when substrate is at least half and not fully consumed.
        Args:
            host_name: name of the host
            Temperature: float of temperature for the experiment
            FinalTime: float of total experiment time in h
            SubstrateConc: float of substrate concentration
            Replicates: int of number of replicates
            FileName: name of the file to which the data is saved

        Returns:
            DataOutcome: dataframe with the expected biomass over time
            CSV file: csv file with the data
        '''

        host = self.find_host_or_abort(host_name)
        # Equipment failure can prematurely end the simulation.
        if self.rnd_gen.pick_uniform(0,1) < self.suc_rate :
            return DataOutcome( None, 'Experiment failed, bad equipment.' )

        # calculating the experiment price based on the number of samples
        BaseCost = 25
        TotalCost = round(BaseCost * Replicates)
        self.spend_budget_or_abort( TotalCost )

        OptTemp = host.growth.opt_growth_temp
        Initials={'X0': 0.01, 'S0': SubstrateConc}
        Params={'mumax': host.growth.umax, 'Ks': host.growth.Ks, 'Yxs': host.growth.Yxs, 'max_biomass': host.growth.max_biomass}
        Params['mumax'] = Params['mumax'] * Help_GrowthConstant(host.growth.opt_growth_temp, Temperature, 4)
        ResAll = pd.DataFrame(columns=['t', 'X', 'S', 'OD'])
        for Rep in range(Replicates):
            # solving the Monod equation and adding noise
            MonodSol = add_noise(solve_MonodEqn(Params, Initials, np.linspace(0,FinalTime,50)), self.suc_rate)
            # Last row of MonodSol combined with FinalTime
            Last = np.hstack((FinalTime, MonodSol[-1,:]))
            Result = round(pd.DataFrame(Last.reshape(1,-1), columns=['t', 'X', 'S']),3)
            # adding OD with deviation from Temperature, the variance is set larger (5) so the effect is not too drastic
            OD2X = host.growth.OD2X * Help_GrowthConstant(host.growth.opt_growth_temp, Temperature, 5)
            Result['OD'] = round(X2OD(Result['X'], OD2X),3)
            # add Result dataframe at the bottom of a new dataframe
            ResAll = pd.concat([ResAll, Result], ignore_index=True)
        DataReturn = DataOutcome(ResAll)
        # save DataReturn to csv
        # relative path to the data folder
        FilePath = os.path.join('..', 'Data', FileName)
        DataReturn.export_data(FilePath)
        return DataReturn

    def measure_TemperatureGrowth( self, ExperimentSettings: ExperimentSettings, Test:str = 'Standard') -> DataOutcome :
        """ 
        Simulate a growth under multiple temperatures and return expected biomasses over time.
        Args:
            ExperimentSettings: settings for the experiment
            Analytics: list of analytics to be performed, e.g., ['OD600', 'HPLC']
            Test: if True, a test experiment will be performed with default settings
        Returns:
            GrowthOutcome: dataframe with the expected biomass over time
        """

        host = self.find_host_or_abort( ExperimentSettings.HostName ) #host_name:str
        if Test == 'Standard':
            # check if money is available
            self.spend_budget_or_abort( len(ExperimentSettings.Temperature)*100 )

            Analytics = ExperimentSettings.Analytics

            # the while loop searches for side products until a stable solution is found
            SideProdsNum = self.rnd_gen.pick_integer(2,5)
            # set the random fraction of side products to the substrate carbon molarity
            SideProdFrac = self.rnd_gen.pick_uniform(0.05, 0.3)
            StableSol = False
            while not StableSol:
            # set uptake rate of selected substrate
                host.metabolism.set_resetCarbonExchanges(ExperimentSettings.CarbonSubConc)
                _, StableSol = host.metabolism.add_ProductSpectrum(CarbSubstrate=ExperimentSettings.CarbonID, CarbSideNumb=SideProdsNum, CarbSideFract=SideProdFrac, Test=Test)

            ExperimentSettings.GrowthRate, ExperimentSettings.ExchangeRates = host.metabolism.optimize_ReportExchanges()
            ExperimentSettings.CarbonSolubleExchange = host.metabolism.get_SolubleProducts(ExperimentSettings.ExchangeRates)
            ExperimentSettings.Yield = {rxn: round(ExperimentSettings.GrowthRate/value,2) for rxn, value in ExperimentSettings.CarbonSolubleExchange.items()} # gCDW/mmol
            # calculate biomass capacity in gCDW/L for yields with negative exchange rates (uptake) in ExperimentSettings.Yield dictionary
            BioWeightConc = sum([ExperimentSettings.Yield[rxn] * ExperimentSettings.CarbonSubConc[rxn] for rxn in ExperimentSettings.Yield.keys() if ExperimentSettings.CarbonSolubleExchange[rxn] < 0])  # gCDW/L
            ExperimentSettings.Capacity = BioWeightConc #* (ExperimentSettings.MediumVolume/1000)  # gCDW in the flask
            # ExperimentSettings.Capacity = CapacityWeight / host.growth.OD2X  # convert gCDW to OD600


            # ExpFail_rand= host.make_generator().pick_uniform(0,1)

            # loop over all temperatures
            for TestTemp in ExperimentSettings.Temperature:
                # copy the experiment settings to avoid overwriting and set the temperature
                ExperimentSettings_Temp = copy.deepcopy(ExperimentSettings)
                ExperimentSettings_Temp.Temperature = TestTemp
                # Equipment failure can prematurely end the simulation.
                # if ExpFail_rand > self.suc_rate :
                    # calculating the biomass in gCDW/L over time
                Biomass = host.growth.Stream_TempGrowthExp( ExperimentSettings=ExperimentSettings_Temp, Success_rate=self.suc_rate )
                # else:
                #     # no growth, values around the initial biomass are selected from a normal distribution
                #     Biomass = np.random.normal( ExperimentSettings.InitBiomass, .01*ExperimentSettings.InitBiomass, len(ExperimentSettings_Temp.SampleVector) )

                # create dataframe with time and biomass concentration in OD
                df = pd.DataFrame({'time (h)': ExperimentSettings.SampleVector, 
                                    'biomass (OD600) at {} °C'.format(TestTemp): Biomass/host.growth.OD2X}) # convert gCDW to OD600

                if 'Biomass' in Analytics:
                    # add dry weight concentration over time if selected in analytics to the existing dataframe
                    df['biomass (gCDW/L) at {} °C'.format(TestTemp)] = Biomass

                if 'Carbon-Substrate' in Analytics:
                    Carbon = host.growth.Stream_CalcSubConc( Biomass=Biomass, ExperimentSettings=ExperimentSettings, Success_rate=self.suc_rate )
                    # add substrate concentration over time if selected in analytics to the existing dataframe
                    df['{} conc. (mM) at {} °C'.format(ExperimentSettings.CarbonName, TestTemp)] = Carbon
                    ExperimentSettings.CarbonConcDynamic = Carbon

                if 'Metabolites' in Analytics:
                    # calculate product spectrum based on carbon uptake rate and biomass concentration
                    myProd = host.metabolism.get_SolubleProducts(ExchRct=ExperimentSettings.ExchangeRates)
                    Spectrum = host.growth.Stream_CalcProdConc(Biomass,myProd,ExperimentSettings.SampleVector,self.suc_rate, Test=Test)
                    # converting Spectrum dict to dataframe to merge with df
                    df_Spectrum = pd.DataFrame(Spectrum)
                    # Set entries to zero that are not sampled in ExperimentSettings.AnalyticSampling
                    df_Spectrum = df_Spectrum.reindex(ExperimentSettings.AnalyticSampling, fill_value=0)
                    # add temperature to the column names
                    df_Spectrum.columns = [col + ' conc. (mM) at {} °C'.format(TestTemp) for col in df_Spectrum.columns]
                    # merge df with df_Spectrum based on time
                    df = pd.merge(df, df_Spectrum, left_on='time (h)', right_index=True, how='left')

                if 'HPLC' in Analytics:
                    self.HPLC.run_HPLC('default',Test=True) 
                    # # calculate chromatogram based on metabolite concentrations
                    # Chromatogram = self.HPLC.calc_Chromatogram(df, ExperimentSettings.AnalyticSampling)
                    # # add temperature to the column names
                    # Chromatogram.columns = [col + ' at {} °C'.format(TestTemp) for col in Chromatogram.columns]
                    # # add chromatogram to the experiment settings
                    # if self.Chromatograms is not None:
                    #     self.Chromatograms = pd.merge(self.Chromatograms, Chromatogram, left_on='time (h)', right_index=True, how='outer')
                    # else:
                    #     self.Chromatograms = Chromatogram

                # add biomass to existing dataframe with previous results
                if 'Result' in locals():
                    Result = pd.merge(Result, df, on='time (h)', how='outer') 
                else:
                    Result = df


        elif Test == 'Example': # general test with example parameters
            StableSol = False
            count = 1
            while not StableSol and count < 15:
                host.metabolism.set_resetCarbonExchanges(ExperimentSettings.CarbonSubConc)
                _, StableSol = host.metabolism.add_ProductSpectrum(CarbSubstrates=['EX_glc__D_e'],CarbSideNumb=3, CarbSideFract=0.15, Test=False)
                count += 1
                if count == 15:
                    print('Max iterations reached without convergence')
                    break

            ExperimentSettings.Temperature = host.opt_growth_temp
            ExperimentSettings.GrowthRate, ExperimentSettings.ExchangeRates = host.metabolism.optimize_ReportExchanges()
            ExperimentSettings.CarbonSolubleExchange = host.metabolism.get_SolubleProducts(ExchRct=ExperimentSettings.ExchangeRates)
            ExperimentSettings.Yield = {rxn: round(ExperimentSettings.GrowthRate/value,2) for rxn, value in ExperimentSettings.CarbonSolubleExchange.items()} # gCDW/mmol
            ExperimentSettings.Capacity = sum([abs(ExperimentSettings.Yield[rxn]) * ExperimentSettings.CarbonSubConc[rxn] for rxn in ExperimentSettings.Yield.keys() if ExperimentSettings.CarbonSolubleExchange[rxn] < 0])  # gCDW/L
            ExperimentSettings.Temperature = host.opt_growth_temp
            Biomass = host.growth.Stream_TempGrowthExp( ExperimentSettings=ExperimentSettings, Success_rate=0 )

            # create dataframe with time and biomass concentration in OD
            df = pd.DataFrame({'time (h)': ExperimentSettings.SampleVector, 
                                'biomass (OD600)': Biomass/host.growth.OD2X}) # convert gCDW to OD600
            df.reset_index(drop=True, inplace=True)

            Spectrum = host.growth.calc_CarbonSolubleConcentrationDynamics(Biomass, ExperimentSettings)
            # converting Spectrum dict to dataframe to merge with df
            df_Spectrum = pd.DataFrame(Spectrum)
            df_Spectrum.reset_index(drop=True, inplace=True)


            # # Set entries to zero that are not sampled in ExperimentSettings.AnalyticSampling
            # df_Spectrum = df_Spectrum.reindex(ExperimentSettings.AnalyticSampling, fill_value=0)
            # merge df with df_Spectrum based on time
            Result = pd.concat([df, df_Spectrum], axis=1)

            # generating HPLC sample data
            # first setting random retention times for all metabolites with init_metabolites method in HPLCProperties class
            hplc_df = self.HPLC.run_HPLC(MetaboliteConcentrations=[], Test=True)
            rt = hplc_df['time']
            signals = hplc_df.drop(columns=['time']).T.values
            Result['HPLC'] = add_dfcolumn(
                Vector1=rt,
                Array=signals,
                RowIndex=[0,20], # just as example, adding two chromatograms at time 0 and 20
                n_rows=len(Result))



        elif Test == 'Unit': # unit test with fixed parameters
            emptyExp = ExperimentSettings
            ExperimentSettings.ExperimentID = "Test"
            host = self.find_host_or_abort( [h.name for h in self.hosts][0] ) # take the first host
            Biomass = host.growth.Stream_TempGrowthExp( ExperimentSettings=emptyExp, Test=True )
            # create dataframe with time and biomass concentration in OD
            df = pd.DataFrame({'time (h)': range(10), # in Test the time is just 0-10
                                'biomass (OD600) at Test': Biomass})

            # add biomass to existing dataframe with previous results
            if 'Result' in locals():
                Result = pd.merge(Result, df, on='time (h)', how='outer') 
            else:
                Result = df
        else:
            raise ExperimentException("Test parameter not recognized.")
            
        # rounding the result to 2 decimals
        Result = round(Result, 2)
        DataOutcome = GrowthOutcome(value=Result)

        # adding experiment settings to the history
        self.record_experiment(ExperimentSettings)

        return DataOutcome


    def measure_BiomassSubstrateExp( self, host_name:str, Temperature:float, Sampling:List[float], SubstrateConc:List[float], NightShift:float, FileName:str, wait:float = 0.01, Function='Monod' ) -> DataOutcome :
        """ Simulate a growth under multiple temperatures and return expected biomasses over time. 
        Args:
            host_name: name of the host
            Temperature: float of temperature for the experiment
            Sampling: array of (total experiment time in h, sampling interval in h) with shape (len(temps),2)
            SubstrateConc: float of substrate concentration
            NightShift: time of the night shift in h after which there are no measurements for 6h
            FileName: name of the file to which the data is saved
            Function: optional, function to be used for the simulation, default is Monod
        
        Returns:
            GrowthOutcome: dataframe with the expected biomass over time
        """
        host = self.find_host_or_abort(host_name)
        # Equipment failure can prematurely end the simulation.
        if self.rnd_gen.pick_uniform(0,1) < self.suc_rate :
            print('Experiment failed, bad equipment.')
            return DataOutcome( None, 'Experiment failed, bad equipment.' )

        # The nightshift has to start within a day of the experiment and must be shorter than 15h
        if NightShift > 15:
            raise ExperimentException("Night shift is too late. It has to be within 15h of the experiment.")
        if Function == 'Test':
            import random
            samples = random.randint(8, 12)
            time = np.linspace(0, 10, samples)
            mu = [.5,.2]
            biomass = [.01*np.exp(mu*time) for mu in mu]
            Result = pd.DataFrame(np.vstack((time,biomass)).T)
            DataReturn = DataOutcome(Result)
            DataPlot = GrowthOutcome(Result)
            DataPlot.make_plot()

        elif Function == 'Monod':
            Params={'mumax': host.growth.umax, 'Ks': host.growth.Ks, 'Yxs': host.growth.Yxs, 'max_biomass': host.growth.max_biomass}
            Initials={'X0': 0.01, 'S0': SubstrateConc}
            time=np.linspace(0, Sampling[0], int(Sampling[0]/Sampling[1]))
            # adding night shift
            NightDuration = 6 # This long is a night without measurements
            time = add_NightShift(time, NightShift, NightDuration)
            # calculating the experiment price based on the number of samples
            BaseCost = 100
            TotalCost = round(BaseCost * calculate_ExpPriceFactor(len(time)))
            self.spend_budget_or_abort( TotalCost )
            # adjusting the real growth rate based on the temperature in the experiment, using variance = 4, which leads to half maximum growth rate for 5C difference
            Params['mumax'] = Params['mumax'] * Help_GrowthConstant(host.growth.opt_growth_temp, Temperature, 4)
            # solving the Monod equation and adding noise
            MonodSol = add_noise(solve_MonodEqn(Params, Initials, time), self.suc_rate)
            Result = round(pd.DataFrame(np.vstack((time, MonodSol.T)).T, columns=['t', 'X', 'S']),3)
            # Converting the dry weight to OD
            Result['OD'] = Result['X'].apply(lambda x: round(X2OD(x, host.growth.OD2X),3))
            # Deleting the column X
            Result = Result.drop(columns=['X'])

            # # Experiments take time...
            # pause = len(time)
            # loading_time = wait * pause
            # Help_Progressbar(45, loading_time, ' experiment')

            DataReturn = DataOutcome(Result)
            # DataPlot = GrowthOutcome(Result)
            # DataPlot.make_plot()

        FilePath = os.path.join('..', 'Data', 'GrowthExperiment_StandardFormat.xlsx')
        sheet = FileName
        DataReturn.append_data2xlsx(FilePath, sheet)
        return DataReturn



    def print_status ( self ) -> None :
        print("Experiment:")
        print("  budget = {}".format( self.budget ))
        print("  failure rate = {}".format( round(self.suc_rate, 2) ))
        print("  hosts = [ {} ]".format( " , ".join([h.name for h in self.hosts]) ))
        # Could display the status of each host if wanted.

    def check_Results( self, host_name:str, Results:dict ) :
        '''Check if the results are correct. Some parameters are individually checked, so the code is a little more complex...'''
        host = self.find_host_or_abort(host_name)
        # Reference dictionary to find the right parameter from Results in host growth
        ParID_dict = {'Temperature':'opt_growth_temp', 
                      'MaxBiomass':'max_biomass',
                      'OD2X':'OD2X',
                      'GrowthRate_Avg':'umax', 
                      'GrowthRate':'umax', 
                      'GrowthYield_Avg':'Yxs',
                      'Ks_Avg':'Ks', 
                      'GlcRateMax':'GlcRateMax'}
        # Setting correct units for each parameter
        Units_dict = {'Temperature':u'\u00b0C', 
                'MaxBiomass':'gDW/L',
                'OD2X':'a.u.',
                'GrowthRate':'/h', 
                'GrowthYield':'g/g',
                'Ks':'g/L', 
                'GlcRateMax':'mmol/gDW/h'}

        # Delete all Results which are set to None
        Results = {k: v for k, v in Results.items() if v is not None}
        # Result comparison when standard deviations are available
        for Parameter in np.unique([Parameter.split('_')[0] for Parameter in Results.keys()]):
            if ''.join([Parameter,'_Std']) in Results.keys() and Parameter != 'GlcRateMax':
                refval = getattr(host.growth, ParID_dict[''.join([Parameter,'_Avg'])]) #vars(host.growth)
                value = Results[''.join([Parameter,'_Avg'])]
                stdev = Results[''.join([Parameter,'_Std'])]
                upper = value + stdev
                lower = value - stdev
            # only one value for the parameter exists, no standard deviation, e.g. Temperature
                if  refval < upper and refval > lower:
                    print(f'{Parameter}: {value}±{stdev} {Units_dict[Parameter]}',u'\u2705')
                else:
                    # calculating the fold of standard deviation between reference value and test value
                    Fold = np.abs(value - refval)/stdev
                    print(f'{Parameter}: {value}±{stdev} {Units_dict[Parameter]}', u'\u274C', f'Value is {Fold:.1f}x standard deviations from the reference value')
            # calculating the solution for the maximum glucose uptake rate which is the quotient of maximum growth rate and yield coefficient
            elif Parameter == 'GlcRateMax':
                refval = getattr(host.growth,'umax')/getattr(host.growth,'Yxs')/.18 # Yxs is given as g/g, but we need mmol/g
                value = Results[''.join([Parameter,'_Avg'])]
                stdev = Results[''.join([Parameter,'_Std'])]
                upper = value + stdev
                lower = value - stdev
            # only one value for the parameter exists, no standard deviation, e.g. Temperature
                if  refval < upper and refval > lower:
                    print(f'{Parameter}: {value}±{stdev} {Units_dict[Parameter]}',u'\u2705')
                else:
                    # calculating the fold of standard deviation between reference value and test value
                    Fold = np.abs(value - refval)/stdev
                    print(f'{Parameter}: {value}±{stdev} {Units_dict[Parameter]}', u'\u274C', f'Value is {Fold:.1f}x standard deviations from the reference value')
            else:
                # calculating ratio of experimental and theoretical value
                Ratio = Results[Parameter]/getattr(host.growth,ParID_dict[Parameter])
                # if Ratio close around 1 then the measurement is right:
                if Ratio < 1.05 and Ratio > .95:
                    print(f'{Parameter}: {Results[Parameter]} {Units_dict[Parameter]}',u'\u2705')
                else:
                    print(f'{Parameter}: {Results[Parameter]} {Units_dict[Parameter]}',u'\u274C')



class GroHost (Host) :

    growth: GrowthBehaviour
    metabolism: MetabolicFlux

    def make ( self, opt_growth_temp:int, max_biomass:int , GSMM:Model, Ks:float, Yxs:float, k1:float, umax:float, OD2X:float ) -> None :

        if not alldef( opt_growth_temp, GSMM, max_biomass, Ks, Yxs, k1, umax, OD2X ) :
            raise HostException("Host not initialized. Reason: incomplete arguments.")

        # Setup GrowthBehaviour module
        self.growth = GrowthBehaviour()
        self.opt_growth_temp = opt_growth_temp
        self.max_biomass = max_biomass


        self.growth.make2(
            opt_growth_temp=opt_growth_temp, max_biomass=max_biomass, Ks=Ks, Yxs=Yxs, k1=k1, umax=umax, OD2X=OD2X
        )

        # Setup Metabolism module
        self.metabolism = MetabolicFlux()
        self.metabolism.bind( host=self )
        self.metabolism.make( model=GSMM )

        self.growth.bind2( host=self )



    def copy ( self, ref:GroHost ) -> None :

        # Setup GrowthBehaviour module using the ref
        self.growth = GrowthBehaviour()
        self.growth.copy( ref=ref.growth )
        self.growth.bind2( host=self )



    def sync ( self ) -> None :
        self.sync_modules([ self.growth ])




    def print_status ( self ) -> None :
        print("Host [{}]:".format( self.name ))
        print("  seed plus counter = {} + {}".format( self.rnd_seed, self.rnd_counter ))
        print("  optimal growth temperature = {}".format( self.growth.opt_growth_temp ))
        print("  max biomass = {}".format( self.growth.max_biomass ))
        print("  Event History: {} events".format(len(self.event_log)))
        for el in self.event_log :
            print("  - {}".format(el))


class GrowthOutcome ( DataWithPlotOutcome ) :

    def make_plot ( self , XName: str, YNames: list) -> plt.Figure :
        """
        Plotting with pyplot is unfortunately unintuitive. You cannot display a single figure by
        using the object-oriented API. When you do `plt.subplots` (or create a plot by any other
        means) it will be stored in the global context. You can only display things from the glbbal
        context, and displaying it will remove it from there.
        """
        x = self.value.loc[:, XName]
        # LnBiomass = np.log(Biomass)

        fig, ax = plt.subplots()
        for YName in YNames: # LnBiomass.iteritems(), Biomass.iteritems()
            ax.scatter(x, self.value.loc[:, YName], label=YName)
        ax.set_xlabel(XName)
        ax.legend()
        return fig, ax

    def make_3dplot ( self, Column: str, Dictx: dict, Dicty: dict ) -> plt.Figure :
        """
        Make a 3D plot of the data in the DataFrame.
        Column: column name to plot on z-axis
        Dictx: dictionary mapping x-axis values to column names
        Dicty: dictionary mapping y-axis values to column names
        """
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        Data = self.value.dropna(subset=[Column])[Column]

        for i, entry in enumerate(Data.values):
            x_data = entry[Dictx]
            y_data = entry[Dicty]

            ax.plot(x_data, y_data, i, zdir='y', label=f'HPLC {i}')

        ax.set_xlabel(Dictx)
        ax.set_ylabel(Dicty)
        ax.set_zlabel(Column)

        return fig, ax


def calculate_ExpPriceFactor(SampleAmount, PlotExample=False):
    '''logit function to generate the price-factor for amount of sampling
        https://nathanbrixius.wordpress.com/2016/06/04/functions-i-have-known-logit-and-sigmoid/
        increasing sampling amount will increase the price until a certain point
        after that the price will remain constant until a certain point
        after that the price will increase again
        the input needs to be between 0 and 1, otherwise the function will return an error
        therefore we need to normalize the input with a saturation function
        the saturation function is a tanh function
        the saturation function will be used to normalize the input

        Args:
            SampleAmount (float): amount of sampling
            PlotExample (bool): if True, the function will plot an example of the function
        Returns:
            PriceFactor (float): price factor for the amount of sampling
        '''
    myTanh = lambda x: np.tanh(x/20) #+ np.tanh(1/20)
    myLogit = lambda x: (np.log(x/(1-x))**3 - np.log(myTanh(1)/(1-myTanh(1)))**3 + 1)/26
    PriceFactor = myLogit(myTanh(SampleAmount))
    if PlotExample:
        x = np.linspace(1,SampleAmount,SampleAmount)
        y = myLogit(myTanh(x))
        plt.plot(x,y, label='logit function', marker='o', linestyle='None')
        plt.xlabel('Sampling amount')
        plt.ylabel('Price factor')
        plt.show()

    return PriceFactor


def MonodEqnODE(MonodVars, t, mumax, Ks, Yxs, max_biomass):
    """
    Monod bioprocess model with ODEs. Based on the model described in:
    Hemmerich et al., doi:10.1002/elsc.202000088, Fig. 6

    Args:
        MonodVars (list): list of variables [X, S]
        t (float): time
        mumax (float): maximum specific growth rate
        Ks (float): half-saturation constant, unit: g/L
        Yxs (float): yield coefficient, unit: gDW/gSubstrate

    Returns:
        list: list of derivatives [dX_dt, dS_dt]
    """
    # Unpack y and z
    X, S = MonodVars

    mu = mumax * S / (Ks + S)
    # Compute biomass growth rate with  a Verhulst growth function
    dX_dt = mu * X * (1 - X / max_biomass)

    # Compute substrate consumption rate
    dS_dt = -mu * X  * (1 - X / max_biomass) / Yxs

    # Return the result as a NumPy array
    return np.array([dX_dt, dS_dt])

def solve_MonodEqn(Params, Initials, t):
    """
    Solve the Monod bioprocess model with ODEs.

    Args:
        Params (dict): dictionary of parameters
        Initials (dict): dictionary of initial conditions
        t (list): list of time points

    Returns:
        list: list of solutions [X, S]
    """
    # Unpack parameters
    mumax, Ks, Yxs, max_biomass = Params['mumax'], Params['Ks'], Params['Yxs'], Params['max_biomass']
    # Initial condition
    MonodVars_0 = [Initials['X0'], Initials['S0']]

    # Parameters
    args = (mumax, Ks, Yxs, max_biomass)

    # Integrate ODES
    MonodSol = spi.odeint(MonodEqnODE, MonodVars_0, t, args=args)

    # Return the result as a NumPy array
    return MonodSol

def add_NightShift(time, NightStart, NightShift):
    """
    Add a night shift to the data. The night shift is a time period where no measurements are taken.
    Args:
    time: List, time vector
    NightStart: Float, time point where the night shift starts
    NightShift: Float, time period of the night shift

    Returns:
    time: List, time vector with night shift
    """
    # if the time vector/experiment is smaller than 15h there is no night shift
    if time[-1] < 15:
        return time
    else:
        # finding all nights in the sampling period
        NightStart = np.arange(NightStart,time[-1],24)

        # Get the index of the row with the value closest to NightStart
        idx_start = np.abs(np.tile(time, (len(NightStart),1)).T - np.tile(NightStart, (len(time),1))).argmin(axis=0)
        # Get the index of the row with the value closest to NightStart+NightShift
        idx_end = np.abs(np.tile(time, (len(NightStart),1)).T - np.tile(NightStart+NightShift, (len(time),1))).argmin(axis=0)
        # storing all indices for all night shifts
        nights = np.hstack([np.arange(start,stop) for start, stop in zip(idx_start, idx_end)])
        # Delete the rows between idx_start and idx_end
        return np.delete(time, np.s_[nights])

def OD2X(OD, OD2X):
    """
    Convert OD to biomass concentration.
    """
    return OD * OD2X
def X2OD(X, OD2X):
    """
    Convert biomass concentration to OD.
    """
    return X / OD2X