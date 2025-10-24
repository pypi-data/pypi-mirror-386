from typing import Set

import numpy as np

from silvio.extensions.utils.misc import (
    Help_simulateHPLCBackground, Help_simulateHPLCTarget, Help_addHPLCPeaks, Help_mergeHPLCChromatograms
)

class SubstrateSideProducts:
    def __init__(self, side_products_dict):
        # side_products_dict: {side_product_name: fractional_flux, ...}
        self.SideProducts = side_products_dict

    def export_dict(self):
        return self.SideProducts


class SideProducts:
    """Class representing side products of metabolic activity."""

    Substrates: Set[str]

    def __init__(self):
        self.Substrates = set()
        # Initialize an empty set of substrates
        # Each substrate will be added as an attribute dynamically


    def add_substrate(self, SubstrateSpectrumDict: dict):
        # SubstrateSpectrumDict: {substrate: {side_product: fractional_flux, ...}, ...}
        # update the set of substrates
        self.Substrates.update(SubstrateSpectrumDict.keys())
        # Dynamically add an attribute for each substrate
        for substrate, side_products in SubstrateSpectrumDict.items():
            setattr(self, substrate, SubstrateSideProducts(side_products))

# Example usage:
# SubstrateSpectrumDict = {
#     'a': {'sp1': 0.5, 'sp2': 0.5},
#     'b': {'sp3': 1.0}
# }

# sp = SideProducts(SubstrateSpectrumDict)
# print(sp.Substrates)  # {'a', 'b'}
# print(sp.a.SideProducts)  # {'sp1': 0.5, 'sp2': 0.5}
# print(sp.b.SideProducts)  # {'sp3': 1.0}

    def exportAll_dict(self):
        '''Export the side products information as a nested dictionary. First level keys are substrates, second level keys are side products with their fractional fluxes.'''
        export = {}
        for substrate in self.Substrates:
            side_products_obj = getattr(self, substrate)
            export[substrate] = side_products_obj.SideProducts
        return export
    
class HPLCProperties:
    class MetaboliteProperties:
        def __init__(self, RetentionTime: float):
            self.RetentionTime = RetentionTime

    def __init__(self):
        self.Metabolites = set()

    def add_metabolite(self, Metabolite: str, RetentionTime: float):
        self.Metabolites.add(Metabolite)
        setattr(self, Metabolite, self.MetaboliteProperties(RetentionTime))

    def init_metabolites(self, MetaboliteList: list):
        for Metabolite in MetaboliteList:
            self.add_metabolite(Metabolite, RetentionTime=np.random.uniform(1.0, 20.0))

    def export_dict(self):
        return {
            'Metabolites': list(self.Metabolites),
        }
    def run_HPLC(self, MetaboliteConcentrations: dict, Test:bool=False):
        '''Simulate HPLC chromatogram based on metabolite concentrations.'''
        # MetaboliteConcentrations: {metabolite_name: concentration, ...}
        # Generate a chromatogram with peaks at the retention times of the metabolites
        # time = np.arange(0, 30.0, 0.01)  # 0 to 30 minutes with 0.01 min resolution
        # signal = np.zeros_like(time)

        if Test:
            MetaboliteConcentrations = {'Product1': [1.0,5.0], 'Product2': [0.0,3.0]}
            df_hplc = Help_simulateHPLCBackground(runtime=30, n_peaks=5, seed=42)
            # construct a list of DataFrames for the combined products at each sampling time
            # For each sampling point, combine all products' peaks with the background
            combined_chroms = []
            for i in range(len(MetaboliteConcentrations['Product1'])):
                temp = df_hplc.copy()
                for prod in MetaboliteConcentrations.keys():
                    prod_peak = Help_simulateHPLCTarget(
                        Elutiontime=np.random.uniform(1.0, 20.0),
                        Concentration=MetaboliteConcentrations[prod][i]
                    )
                    temp = Help_addHPLCPeaks(temp, prod_peak)
                combined_chroms.append(temp)

            # Merge all combined chromatograms into a single DataFrame with one column per sample
            df_prod = Help_mergeHPLCChromatograms(combined_chroms)
            return df_prod
        # for metabolite, concentration in MetaboliteConcentrations.items():
        #     if metabolite in self.Metabolites:
        #         rt = getattr(self, metabolite).RetentionTime
        #         peak = concentration * np.exp(-0.5 * ((time - rt) / 0.1) ** 2)  # Gaussian peak
        #         signal += peak

        # return {
        #     'time': time,
        #     'signal': signal
        # }