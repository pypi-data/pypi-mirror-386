"""
GenomeLibrary is a more complex version of GenomeList:
  - support for genome sequences
  - genes are located inside the sequence
"""
from __future__ import annotations
from typing import Callable, Set
from math import copysign
from copy import copy
import numpy as np

# from numpy.random import Generator
from ...random import Generator
from cobra.core import Model as CobraModel
from cobra.core.solution import Solution as CobraSolution
from cobra.manipulation import delete_model_genes

from ...host import Host
from ...module import Module, ModuleException
from ...events import EventEmitter, EventLogger
from ..records.gene.stub_gene import StubGene
from ..all_events import InsertGeneEvent, RemoveGeneEvent, AlterGeneExpressionEvent
from ...extensions.modules.metabolism import SideProducts
from ...extensions.utils.misc import Help_setDeactivateCExchanges, Help_getCarbonExchange, Help_CalcRate, Help_countCatoms
from ...extensions.common import GasCarbMets


class MetabolicFlux (Module) :
    """
    MetabolicFlux can handle cobrapy models and interfaces them with module events.

    This module can start with an non-existing model, which can then be integrated as an event.

    TODO: Its probably not elegant to allow non-existing models, but this makes it easier to add
    all genes in that model later on (as events). If we would be really pedantic and needed a
    strictly-existinging model we could implement an initialization step where a module calls
    multiple events on the host in order to "initialize" the module properly. To achieve that,
    modules themselves need to be able to generate events (right now only a Host can send events
    down to modules, events never go up the chain) and prevent infinite event loops. But maybe
    there are better alternatives altogether.
    """
    # Creator of random number generators. Host will bind this.
    make_generator: Callable[[],Generator]

    model: CobraModel

    # Since cobra models have limited methods to manage knocked-out genes, we need to keep track
    # of them in this list. A set of gene names.
    koed_genes: Set[str]

    # initiating potential sideproducts
    SideProducts: SideProducts

    def make ( self, model:CobraModel ) -> None :
        self.model = model
        self.model_tmp = self.model.copy()
        self.koed_genes = set()
        self.SideProducts = SideProducts()


    def copy ( self, ref:'MetabolicFlux' ) -> None :
        self.model = ref.model.copy()
        self.koed_genes = ref.koed_genes.copy()


    def bind ( self, host:Host ) -> None :
        self.make_generator = host.make_generator
        # host.observe( InsertGeneEvent, self.listen_insert_gene )
        # host.observe( RemoveGeneEvent, self.listen_remove_gene )
        # host.observe( AlterGeneExpressionEvent, self.listen_alter_gene_expression )


    def sync ( self, emit:EventEmitter, log:EventLogger ) -> None :
        log("MetabolicFlux: share model genes")
        for gene in self.model.genes : # Add all genes from the metabolic model.
            stub = StubGene( name=gene.name )
            emit( InsertGeneEvent(stub,locus=None) )

    def set_KinParameters ( self ) -> None :
        """
        Set kinetic parameters in the model. Each excahnge reaction is assigned with a random Vmax and Km.
        """

        CarbonExchanges = Help_getCarbonExchange(self.model)
        for ExRxn in CarbonExchanges:
            Vmax = round(self.make_generator().pick_uniform(low=2, high=20),1)
            Km = round(self.make_generator().pick_uniform(low=0.05, high=1),2)
            setattr(self.model.reactions.get_by_id(ExRxn), 'Vmax', Vmax)
            setattr(self.model.reactions.get_by_id(ExRxn), 'Km', Km)
            setattr(self.model_tmp.reactions.get_by_id(ExRxn), 'Vmax', Vmax)
            setattr(self.model_tmp.reactions.get_by_id(ExRxn), 'Km', Km)

    def reset( self ) -> None :
        self.model_tmp = self.model.copy()

    def optimize ( self ) -> CobraSolution :
        return self.model_tmp.optimize()
    
    def slim_optimize( self ) -> float :
        return round(self.model_tmp.slim_optimize(),2)
    
    def optimize_ReportExchanges ( self ) -> Tuple[ float, dict ] :
        solution = self.model_tmp.optimize()
        Exchanges = {}
        for rxn in self.model_tmp.exchanges:
            Exchanges[rxn.id] = round(solution.fluxes[rxn.id],2)
        return (round(solution.objective_value,2), Exchanges)

    def summary ( self ) -> str :
        return self.model_tmp.summary()

    def set_resetCarbonExchanges ( self , CarbonSubstrate:dict, Test:bool=False) -> None :
        """
        Set all carbon exchange reactions to zero uptake (lower_bound=0). Activate exchange reactions for input carbon sources.

        Inputs:
            CarbonSubstrate: dict, dictionary with carbon substrate exchange reactions as keys and their concentration in mmol/L as values
        Outputs:

        """
        if Test:
            print("MetabolicFlux: Test mode - not changing carbon exchange reactions")
            return
        # Deactivate all carbon exchange reactions 
        # using the original model to reset all changes
        self.reset()
        self.model_tmp = Help_setDeactivateCExchanges(self.model_tmp) 
        # Activate exchange reactions for input carbon sources
        for ExRxn, Conc in CarbonSubstrate.items():
            Vmax = getattr(self.model_tmp.reactions.get_by_id(ExRxn), 'Vmax')
            Km = getattr(self.model_tmp.reactions.get_by_id(ExRxn), 'Km')
            UptakeRate = round(Help_CalcRate(Conc, Vmax, Km, Law='Michaelis-Menten'),1)
            setattr(self.model_tmp.reactions.get_by_id(ExRxn), 'lower_bound', -abs(UptakeRate))  # set uptake rate

    # def calc_CarbonMetaboliteYields ( self, GrowthRate: float, ExchangeRates: dict ) -> dict :
    #     '''Calculate metabolite yields from the solution object of the model. Return a dictionary with exchange reactions and their yields in mmol/gCDW'''
    #     BiomassFlux = SolBiomass.fluxes['BIOMASS_Ecoli_core_w_GAM'] # in mmol/gDW/h
    #     MetYields = {rxn.id: round(SolBiomass.fluxes[rxn.id] / BiomassFlux,3) for rxn in self.model_tmp.exchanges if SolBiomass.fluxes[rxn.id] > 0 and not any(gas in rxn.id for gas in GasCarbMets)}
    #     return MetYields

    def add_ProductSpectrum ( self, CarbSubstrates:list, CarbSideNumb:int, CarbSideFract:float, Test:bool=False) -> dict:
        '''Add product spectrum to the model. The carbon uptake flux is used to calculate the overall uptake of carbon atoms. A random selection of exchange reactions is then activated to secrete carbon atoms in a defined range.
        Inputs:
            CarbSubstrate: list, Exchange reaction ids of carbon substrates
            CarbSideNumb: int, number of carbon side products to be secreted
            CarbSideFract: float, number with lower and upper limits of the overall carbon atoms fraction in the side products, e.g. .1 for 10%'''
        # find carbon exchange reactions in model_tmp
        CarbonExchanges = Help_getCarbonExchange(self.model_tmp) # list with carbon exchange reaction ids
        # Check whether the metabolism class has already asigned sideproduct for the ActiveCExchanges
        if CarbSubstrates in list(self.SideProducts.Substrates):
            print('Side product association exists.')
        # setdiff of CarbonExchanges and ActiveCExchanges. Substrates are not secreted
        SecretedCExchanges = list(set(CarbonExchanges) - set(CarbSubstrates))
        OverallC_Uptake = np.sum([abs(self.model_tmp.reactions.get_by_id(rxn).lower_bound * Help_countCatoms(self.model_tmp, rxn)) for rxn in CarbSubstrates])

        if Test:
            print(f"Test Total uptake: {OverallC_Uptake} C-mmol/h")


        # not all assignments of secretion fluxes lead to a feasible solution. Count the number of tries.
        StableSol = False
        # count = 0 
        # while count<50 and not StableSol:
        SecretionFluxDict = {}
        SecrFluxNorm = {}
        # randomly select exchange reactions to secrete carbon atoms but ignore substrate uptake reactions
        SecretedSelect = self.make_generator().pick_samples(SecretedCExchanges, min(CarbSideNumb, len(SecretedCExchanges)))
        # print(f"MetabolicFlux: selected secreted metabolites {SecretedSelect}")
        # assign random secretion fluxes to selected exchange reactions
        # generate three random numbers whose sum is 1
        MetVec = [self.make_generator().pick_uniform(0.1, 1.0) for _ in range(CarbSideNumb)]
        SideMetsFlux = np.round(MetVec / np.sum(MetVec) * CarbSideFract, 2)  # c-molar fraction of each side product

            
        for i, rxn in enumerate(SecretedSelect):
            # assign random carbon secretion flux from SideMetsFlux
            C_SecretionFlux = round(OverallC_Uptake * SideMetsFlux[i],1)
            # correct c-molar flux to mmol flux
            SecretionFlux = round(C_SecretionFlux / Help_countCatoms(self.model_tmp, rxn),2)
            # set secretion flux as lower_bound of exchange reaction
            setattr(self.model_tmp.reactions.get_by_id(rxn), 'lower_bound', abs(SecretionFlux))
            # dictionary with secreted metabolites and their fluxes
            SecretionFluxDict[rxn] = SecretionFlux
            # normalized fluxes from SideMetsFlux for each secreted metabolite
            SecrFluxNorm[rxn] = SideMetsFlux[i] # fraction of overall carbon secretion flux in cmmol(Side)/cmmol(Substrate)

        # check if the model is still feasible
        sol = self.model_tmp.slim_optimize()
        print(f"MetabolicFlux: assigned secretion fluxes, solution={sol}")
        if sol > 0.01:
            StableSol = True
        else:
            # reset secretion fluxes to zero
            [setattr(self.model_tmp.reactions.get_by_id(rxn), 'lower_bound', 0) for rxn in SecretedSelect]
        #     # print(f"MetabolicFlux: infeasible solution - retrying to assign secretion fluxes (try {count})")
        # count += 1

        # print(f"MetabolicFlux: assigned secretion fluxes after {count} tries.")
        # each substrate is associated with the same side products
        self.SideProducts.add_substrate({CarbSubstrate:SecrFluxNorm for CarbSubstrate in CarbSubstrates})
        return SecretionFluxDict, StableSol

    def get_SolubleProducts ( self, ExchRct:dict ) -> dict :
        '''Get all soluble products from the model. Return a dictionary with exchange reactions and their fluxes'''
        # find carbon exchange reactions in model_tmp and filter for metabolites that are not gases
        SolProdRate = {rxn: ExchRct[rxn] for rxn in Help_getCarbonExchange(self.model_tmp) if abs(ExchRct[rxn]) > 0 and not any(gas in rxn for gas in GasCarbMets)}
        return SolProdRate

    def listen_insert_gene ( self, event:InsertGeneEvent, emit:EventEmitter, log:EventLogger ) -> None :
        if event.gene.name in self.koed_genes :
            self.koed_genes.remove( event.gene.name )
            delete_model_genes( self.model, list(self.koed_genes), cumulative_deletions=False )
            log( "MetabolicFlux: reinserted gene={}".format(event.gene.name) )



    def listen_remove_gene ( self, event:RemoveGeneEvent, emit:EventEmitter, log:EventLogger ) -> None :
        """
        When a gene is removed we perform a knockout in the model.
        """
        found_genes = [ gene for gene in self.model.genes if gene.name == event.gene.name ]
        if len(found_genes) > 0 :
            self.koed_genes.add( event.gene.name )
            delete_model_genes( self.model, list(self.koed_genes), cumulative_deletions=False )
            log( "MetabolicFlux: knocked out gene={}".format(event.gene.name) )



    def listen_alter_gene_expression ( self, event:AlterGeneExpressionEvent, emit:EventEmitter, log:EventLogger ) -> None :
        """
        When a gene expression changes, we adapt the bounds.
        TODO: This method should be wrong. Please rewrite logic on how gene expression affects the
          metabolic model.
        """
        found_genes = [ gene for gene in self.model.genes if gene.name == event.gene.name ]
        if len(found_genes) > 0 :
            for gene in found_genes :
                for rct in gene.reactions :
                    rct.upper_bound = event.new_expression * copysign(1,rct.upper_bound)
                    log( "MetabolicFlux: changed upper_bound on reaction={} to {}".format(rct.id,rct.upper_bound) )
