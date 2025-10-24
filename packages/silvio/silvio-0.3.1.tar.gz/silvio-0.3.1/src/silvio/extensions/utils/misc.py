"""
Methods that are not yet assigned to another place. They usually include methods before the
restructuring.
TODO: Almost all of the methods inside this file can me integrated into module functions.
"""
import os
from silvio.experiment import ExperimentSettings
import wget
import re
import numpy as np
import pandas as pd
import joblib
import pickle

from scipy.stats import norm
from Bio.Seq import Seq
from cobra.core.model import Model
from cobra.io import load_json_model

from ...random import pick_uniform
from ...outcome import Outcome
from .transform import list_onehot, list_integer
from ...extensions.common import BIGG_dict, TestParams

def Sequence_ReferenceDistance(SeqObj, RefSeq):
    '''Returns the genetic sequence distance to a reference sequence.
    Input:
           SeqDF: list, the sequence in conventional letter format
    Output:
           SequenceDistance: float, genetic distances as determined from the sum of difference in bases divided by total base number, i.e. max difference is 1, identical sequence =0
    '''

    Num_Samp = len(SeqObj)
    SequenceDistance = np.sum([int(seq1 != seq2) for seq1,seq2 in zip(RefSeq, SeqObj)], dtype='float')/Num_Samp

    return SequenceDistance



def check_primer_integrity_and_recombination (Promoter:Seq, Primer:Seq, Tm:int, RefPromoter:Seq, OptPrimerLen:int) -> Outcome :
    '''
    Experiment to clone selected promoter. Return whether the experiment was successful.
    '''

    if Sequence_ReferenceDistance(Promoter, RefPromoter) > .4:
        return Outcome(False, 'Promoter sequence deviates too much from the given structure.')

    NaConc = 0.1 # 100 mM source: https://www.genelink.com/Literature/ps/R26-6400-MW.pdf (previous 50 mM: https://academic.oup.com/nar/article/18/21/6409/2388653)
    AllowDevi = 0.2 # allowed deviation
    Primer_Length = len(Primer)
    Primer_nC = Primer.count('C')
    Primer_nG = Primer.count('G')
    Primer_nA = Primer.count('A')
    Primer_nT = Primer.count('T')
    Primer_GC_content = ((Primer_nC + Primer_nG) / Primer_Length)*100 # unit needs to be percent

    if OptPrimerLen > 25:
        Primer_Tm = 81.5 + 16.6*np.log10(NaConc) + 0.41*Primer_GC_content - 600/Primer_Length # source: https://www.genelink.com/Literature/ps/R26-6400-MW.pdf (previous: https://core.ac.uk/download/pdf/35391868.pdf#page=190)
    else:
        Primer_Tm = (Primer_nT + Primer_nA)*2 + (Primer_nG + Primer_nC)*4
    # Product_Tm = 0.41*(Primer_GC_content) + 16.6*np.log10(NaConc) - 675/Product_Length
    # Ta_Opt = 0.3*Primer_Tm + 0.7*Product_Tm - 14.9
    # source Product_Tm und Ta: https://academic.oup.com/nar/article/18/21/6409/2388653
    # Product_Length would be the length of the promoter (40)? too small -> negative number comes out for Product_Tm
    print('Reference primer T:{}'.format(Primer_Tm))
    error = pick_uniform(-1,1)*0.1*Primer_Tm
#     error_2 = pick_uniform(-1,1)*0.1*Primer_Tm_2
    Primer_Tm_err = error + Primer_Tm
#     Primer_Tm_err_2 = error_2 + Primer_Tm_2

    DeviLen = np.absolute(OptPrimerLen - Primer_Length)/OptPrimerLen
    DeviTm = np.absolute(Primer_Tm_err - Tm)/Primer_Tm_err
#     DeviTm_2 = np.absolute(Primer_Tm_err_2 - Tm)/Primer_Tm_err_2
#     DeviTm = min(DeviTm_1, DeviTm_2)

    # create the complementary sequence of the primer to check for mistakes:
    PrimerComp = Primer.complement()

    if DeviLen <= AllowDevi and DeviTm <= AllowDevi/2 and Primer_Length <= 30 and PrimerComp == Promoter[:len(Primer)]:
        return Outcome(True)

    if not DeviLen <= AllowDevi :
        return Outcome(False, 'Primer length deviation too big.')
    if not DeviTm <= AllowDevi/2 :
        return Outcome(False, 'Temperature deviation too big.')
    if not Primer_Length <= 30 :
        return Outcome(False, 'Primer length too big.')
    if not PrimerComp == Promoter[:len(Primer)] :
        return Outcome(False, 'Primer not compatible with promoter.')

    return Outcome(False, 'Cloning failed')



def Help_PromoterStrength(
    PromSequence, RefPromoter:str, Scaler=1, Similarity_Thresh=.4, Regressor_File=None, AddParams_File=None
) -> float :
    '''
    TODO: Some arguments are missing.
    Expression of the recombinant protein.
        Arguments:
            Host:       class, contains optimal growth temperature, production phase
            Sequence:     string, Sequence for which to determine promoter strength
            Scaler:       int, multiplied to the regression result for higher values
            Predict_File: string, address of regression file
        Output:
            Expression: float, expression rate
    '''

    if Sequence_ReferenceDistance(PromSequence, RefPromoter) > Similarity_Thresh:
        Expression = 0
    else:
        Predictor = joblib.load(Regressor_File)
        Params = pickle.load(open(AddParams_File, 'rb'))
        Positions_removed = Params['Positions_removed']
        # Expr_Scaler = Params[Scaler_DictName]

        X = np.array(list_onehot(np.delete(list_integer(PromSequence),Positions_removed, axis=0))).reshape(1,-1)
        GC_cont = (PromSequence.count('G') + PromSequence.count('C'))/len(PromSequence)
        X = np.array([np.append(X,GC_cont)])
        Y = Predictor.predict(X)
        Expression = round(float(Y)*Scaler,3)

    return Expression


def Help_GrowthRandom() -> np.array :
    '''
    Function to generate a random growth curve.
    Output:
        Growth: np.array, random growth curve
    '''
    # in test mode, generate 10 samples with logistic growth curve, x values 0-9, y values 0-5, steepest growth at x=8
    x = np.arange(TestParams['Time'])
    L = 5  # maximum value
    k = 2  # steepness
    x0 = 5  # inflection point
    Biomass = L / (1 + np.exp(-k * (x - x0)))

    return Biomass

def Help_GrowthConstant(OptTemp, CultTemp, var=5):
    '''Function that generates the growth rate constant. The growth rate constant depends on the optimal growth temperature and the cultivation temperature. It is sampled from a Gaussian distribution with the mean at the optimal temperature and variance 1.
    Arguments:
        Opt_Temp: float, optimum growth temperature, mean of the Gaussian distribution
        Cult_Temp: float, cultivation temperature for which the growth constant is evaluated
        var: float, variance for the width of the Gaussian covering the optimal growth temperature
    Output:
        growth_rate_const: float, constant for use in logistic growth equation
    '''
    r_pdf = norm(OptTemp, var)
    # calculation of the growth rate constant, by picking the activity from a normal distribution

    growth_rate_const = r_pdf.pdf(CultTemp) / r_pdf.pdf(OptTemp)

    return growth_rate_const


def Calc_GSMMYield (model:Model, CarbExRxnID:str, MolarMass:float, UnitTest:bool=False) -> float :
    '''Function to calculate the growth rate for a genome scale metabolic model. The substrate and its concentration is used from the user input. 
    
    Inputs:
    '''

    if UnitTest:
        # for unit testing we want to have a fixed value
        Yield = 0.5
    else:
        solution = model.optimize()
        Yield = round(solution.objective_value / (abs(solution.fluxes[CarbExRxnID]) * MolarMass/1000),2)  # gDW / gSubstrate

    return Yield


def Growth_Maxrate(growth_rate_const, Biomass):
    '''
    TODO: Documentation is out of sync.
    The function calculates the maximum slope during growth.
        Arguments:
            Host: class, contains maximum biomass concentration as carrying capacity
            growth_rate_const: float, maximum growth rate constant
        Output:
            growth_rate_max: float, maximum growth rate
    '''
    # biomass checks
    # if Biomass > Mutant._Mutantmax_biomass or not Biomass:
    #     print('Error, no biomass was set or unexpected value or the maximum possible biomass was exceeded. Enter a value for the biomass again.')

    # Equation for calculating the maximum slope
    # https://www.tjmahr.com/anatomy-of-a-logistic-growth-curve/
    GrowthMax = Biomass * growth_rate_const / 4

    return GrowthMax

def Download_GSMM (Organism:str, ModelDir:str = 'Data') -> Model :
    '''Function to download a genome scale metabolic model from the BiGG database.
    
    Inputs:
        Organism: str, name of the organism in the BiGG database, e.g. 'e_coli_core'
        ModelFile: str, address to store the downloaded model
    Outputs:
        model: cobra Model, genome scale metabolic model
    '''

    ModelFile = os.path.join(ModelDir, f'{BIGG_dict[Organism]}.json')
    if os.path.isfile(ModelFile):
        # check if the file exists already
        model = load_json_model(ModelFile)
    else:
        # download the model from the BiGG database
        wget.download(f'http://bigg.ucsd.edu/static/models/{BIGG_dict[Organism]}.json')
        # move the file to the target directory
        os.rename(f'{BIGG_dict[Organism]}.json', ModelFile)
        model = load_json_model(ModelFile)

    return model

def Help_getCarbonExchange (model:Model) -> list :
    '''Function to get all exchange carbon metabolites from a genome scale metabolic model.
    
    Inputs:
        model: cobra Model, genome scale metabolic model
    Outputs:
        CarbonExchange: list, list of all carbon substrates in the model
    '''
    CarbonExchange = []
    for exchange in model.exchanges:
        metab = list(exchange.metabolites.keys())[0]
        # check if formula exist
        if bool(metab.formula):
            Carbon = bool(re.search(r'(?<![A-Za-z])C([A-Z]|\d)', metab.formula))
            if Carbon: # 'C' in metab.formula:
                CarbonExchange.append(exchange.id)

    return CarbonExchange

def Help_setDeactivateCExchanges (model:Model) -> Model :
    '''Function to deactivate all carbon exchange reactions.
    
    Inputs:
        model: cobra Model, genome scale metabolic model
        CarbonExchange: list, list of all carbon exchange reactions in the model
    Outputs:
        model: cobra Model, genome scale metabolic model with deactivated carbon exchange reactions
    '''
    CarbonExchange = Help_getCarbonExchange(model)

    for exchange in CarbonExchange:
        model.reactions.get_by_id(exchange).lower_bound = 0  # deactivate uptake

    return model


def Help_countCatoms(model, ex_rxn_id):
    """
    Count the number of carbon atoms in the main metabolite of a given exchange reaction.
    """
    rxn = model.reactions.get_by_id(ex_rxn_id)
    for met in rxn.metabolites:
        # Typically, the main substrate is in the extracellular compartment (e)
        if met.compartment == 'e' and met.formula:
            match = re.search(r'C(\d*)', met.formula)
            if match:
                return int(match.group(1)) if match.group(1) else 1
    return 0

#     for ExRxn, rate in CarbonSubstrate.items():
#         model.reactions.get_by_id(ExRxn).lower_bound = -abs(rate)  # activate uptake

#     return model

def Help_CalcRate(S, Vmax, Km, Law:str='Michaelis-Menten') -> float :
    '''Function to calculate the carbon uptake rate based on Michaelis-Menten kinetics.
    
    Inputs:
        S: float, substrate concentration in mM
        Vmax: float, maximum uptake rate in mmol/gDW/h
        Km: float, Michaelis constant in mM
    Outputs:
        Rate: float, uptake rate in mmol/gDW/h
    '''
    if Law == 'Michaelis-Menten':
        Rate = (Vmax * S) / (Km + S)
    else:
        raise ValueError('Only Michaelis-Menten kinetics is implemented so far.')
    return Rate

def Help_BiomassTimeIntegral( Biomass:np.array, SampleVector:np.array ) -> np.array :
    """
    Return the biomass time integral for a given biomass list.
    The biomass time integral is calculated based on the biomass and the sampling vector for each sampling point.

    Arguments:
        Biomass: list of biomass values over time
        SampleVector: float, time vector corresponding to the biomass samples
    Outputs:
        float: biomass time integral
    """
    # Biomass_integral = np.array([np.trapz(Biomass[:i+1], SampleVector[:i+1]) for i in range(len(SampleVector))])
    Biomass_integral = np.cumsum(
        (Biomass[1:] + Biomass[:-1]) / 2 * (SampleVector[1:] - SampleVector[:-1])
    )
    Biomass_integral = np.insert(Biomass_integral, 0, 0)

    return Biomass_integral


def add_noise(data, noise):
    """
    Add noise to data.
    """
    # Each column get a different noise based on the average value of the column
    noise = noise * np.min(data, axis=0)   # np.mean(data, axis=0)  
    # ensure that there are no negative values
    return np.abs(data + np.random.normal(0, noise, data.shape))

def add_noise2(data, noise):
    '''
    Add noise to a vector, where each element is treated individually.
    '''
    return np.array([np.random.normal(data[k], noise*data[k]) for k in range(len(data))])

def Help_simulateHPLCBackground(
    runtime=30.0,          # total run time in minutes
    step=0.01,             # time resolution (min)
    n_peaks=50,            # number of peaks
    peak_height_range=(0.1, 2.0),   # min/max peak height (mAU)
    peak_width_range=(0.05, 0.8),   # min/max peak width (min)
    noise_std=0.02,        # detector noise (mAU)
    baseline_slope=0.002,  # slope of baseline drift (mAU/min)
    baseline_intercept=0.05,  # starting baseline (mAU)
    seed=None              # random seed for reproducibility
):
    """
    Simulate a synthetic HPLC chromatogram (UV absorbance vs. time).

    Returns
    -------
    df : pandas.DataFrame
        Two columns: 'time_min', 'absorbance_mAU'
    """

    if seed is not None:
        np.random.seed(seed)

    # Time axis
    time = np.arange(0, runtime + step, step)

    # Generate random peak properties
    peak_positions = np.random.uniform(0.5, runtime - 2, n_peaks)
    peak_heights = np.random.uniform(*peak_height_range, n_peaks)
    peak_widths = np.random.uniform(*peak_width_range, n_peaks)

    # Build chromatogram from Gaussian peaks
    signal = np.zeros_like(time)
    for pos, height, width in zip(peak_positions, peak_heights, peak_widths):
        signal += height * np.exp(-0.5 * ((time - pos) / width) ** 2)

    # Add baseline drift
    baseline = baseline_intercept + baseline_slope * time

    # Add Gaussian noise
    noise = np.random.normal(0, noise_std, len(time))

    # Final signal
    chromatogram = signal + baseline + noise
    chromatogram[chromatogram < 0] = 0  # absorbance cannot be negative

    # Put into DataFrame
    df = pd.DataFrame({
        "time": time,
        "signal": chromatogram
    })

    return df

def Help_simulateHPLCTarget(Elutiontime, Concentration):
    '''Generates a target peak for HPLC simulation. Only the peak is generated, no noise or baseline. The result can be added to a background chromatogram.'''
    time = np.arange(0, 30.0, 0.01)
    signal = np.zeros_like(time)

    # Generate a Gaussian peak
    peak_width = 0.1  # fixed width
    # the peak area and height are proportional to concentration
    peak_area = Concentration * peak_width * np.sqrt(2 * np.pi)
    peak_height = peak_area / peak_width  # peak height from area

    signal += peak_height * np.exp(-0.5 * ((time - Elutiontime) / peak_width) ** 2)

    # Put into DataFrame
    df = pd.DataFrame({
        "time": time,
        "signal": signal
    })

    return df
def Help_addHPLCPeaks(df_background, df_peaks):
    '''Adds target peaks to a background chromatogram.'''
    df_combined = df_background.copy()
    df_combined['signal'] += df_peaks['signal']
    return df_combined

def Help_mergeHPLCChromatograms(df_list):
    '''Merges multiple chromatograms at different sampling times into one DataFrame. Each sampling time is a column.'''
    df_merged = pd.DataFrame()
    for df in df_list:
        df_merged = pd.concat([df_merged, df.set_index('time')], axis=1)
    df_merged.columns = [f"sample_{i}" for i in range(df_merged.shape[1])]
    df_merged = df_merged.reset_index()
    return df_merged