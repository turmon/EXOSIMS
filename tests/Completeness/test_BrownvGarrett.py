import unittest
from tests.TestSupport.Info import resource_path
from tests.TestSupport.Utilities import RedirectStreams
import EXOSIMS.Completeness.BrownCompleteness
import EXOSIMS.Completeness.GarrettCompleteness
from EXOSIMS.Prototypes.TargetList import TargetList
from EXOSIMS.util.get_module import get_module
import os
import pkgutil
import numpy as np
import astropy.units as u
import json
import copy

class TestBrownvGarrett(unittest.TestCase):
    """ 

    Compare results of Brown and Garrett completeness modules

    """
    
    def setUp(self):

        self.dev_null = open(os.devnull, 'w')
        self.script = resource_path('test-scripts/template_minimal.json')
        self.spec = json.loads(open(self.script).read())
        

    def test_target_completeness_def(self):
        """
        Compare calculated completenesses for multiple targets under default population
        settings.
        """
            
        with RedirectStreams(stdout=self.dev_null):
            TL = TargetList(ntargs=100,**copy.deepcopy(self.spec))

            mode = filter(lambda mode: mode['detectionMode'] == True, TL.OpticalSystem.observingModes)[0]
            IWA = mode['IWA']
            OWA = mode['OWA']
            rrange = TL.PlanetPopulation.rrange
            maxd = (rrange[1]/np.tan(IWA)).to(u.pc).value
            mind = (rrange[0]/np.tan(OWA)).to(u.pc).value

            #want distances to span from outer edge below IWA to inner edge above OWA
            TL.dist = np.logspace(np.log10(mind/10.),np.log10(maxd*10.),TL.nStars)*u.pc


        Brown = EXOSIMS.Completeness.BrownCompleteness.BrownCompleteness(**copy.deepcopy(self.spec))
        Garrett = EXOSIMS.Completeness.GarrettCompleteness.GarrettCompleteness(**copy.deepcopy(self.spec))

        cBrown = Brown.target_completeness(TL)
        cGarrett = Garrett.target_completeness(TL)

        np.testing.assert_allclose(cGarrett,cBrown,rtol=0.1,atol=1e-6)

    def test_target_completeness_constrainOrbits(self):
        """
        Compare calculated completenesses for multiple targets with constrain orbits set to true
        """
            
        
        with RedirectStreams(stdout=self.dev_null):
            TL = TargetList(ntargs=100,constrainOrbits=True,**copy.deepcopy(self.spec))

            mode = filter(lambda mode: mode['detectionMode'] == True, TL.OpticalSystem.observingModes)[0]
            IWA = mode['IWA']
            OWA = mode['OWA']
            rrange = TL.PlanetPopulation.rrange
            maxd = (rrange[1]/np.tan(IWA)).to(u.pc).value
            mind = (rrange[0]/np.tan(OWA)).to(u.pc).value

            #want distances to span from outer edge below IWA to inner edge above OWA
            TL.dist = np.logspace(np.log10(mind/10.),np.log10(maxd*10.),TL.nStars)*u.pc


        Brown = EXOSIMS.Completeness.BrownCompleteness.BrownCompleteness(constrainOrbits=True,**copy.deepcopy(self.spec))
        Garrett = EXOSIMS.Completeness.GarrettCompleteness.GarrettCompleteness(constrainOrbits=True,**copy.deepcopy(self.spec))

        cBrown = Brown.target_completeness(TL)
        cGarrett = Garrett.target_completeness(TL)

        np.testing.assert_allclose(cGarrett,cBrown,rtol=0.1,atol=1e-6)


    def test_target_completeness_scaleOrbits(self):
        """
        Compare calculated completenesses for multiple targets with scale orbits set to true
        """
                   
        with RedirectStreams(stdout=self.dev_null):
            TL = TargetList(ntargs=100,**copy.deepcopy(self.spec))
            TL.dist =  np.exp(np.random.uniform(low=np.log(1.0), high=np.log(30.), size=TL.nStars))*u.pc
            TL.L = np.exp(np.random.uniform(low=np.log(0.1), high=np.log(10.), size=TL.nStars))

        Brown = EXOSIMS.Completeness.BrownCompleteness.BrownCompleteness(scaleOrbits=True,**copy.deepcopy(self.spec))
        Garrett = EXOSIMS.Completeness.GarrettCompleteness.GarrettCompleteness(scaleOrbits=True,**copy.deepcopy(self.spec))

        cBrown = Brown.target_completeness(TL)
        cGarrett = Garrett.target_completeness(TL)
        
        cGarrett = cGarrett[cBrown != 0 ]
        cBrown = cBrown[cBrown != 0]
        meandiff = np.mean(np.abs(cGarrett - cBrown)/cBrown)

        self.assertLessEqual(meandiff,0.1)

    def test_target_completeness_varrange(self):
        """
        Garrett completeness takes different logical pathways depending on which parameters are 
        held constant.  Checking all of these against BrownCompleteness would take multiple hours
        so we'll just run through the Garrett logical branches and check for self-consistency.

        The comparison tests already cover Rp and p constant, so we need to check a constant, e constant
        a + e constant.
        """
            
        with RedirectStreams(stdout=self.dev_null):
            TL = TargetList(ntargs=100,**copy.deepcopy(self.spec))

            mode = filter(lambda mode: mode['detectionMode'] == True, TL.OpticalSystem.observingModes)[0]
            IWA = mode['IWA']
            OWA = mode['OWA']
            rrange = TL.PlanetPopulation.rrange
            maxd = (rrange[1]/np.tan(IWA)).to(u.pc).value
            mind = (rrange[0]/np.tan(OWA)).to(u.pc).value

            #want distances to span from outer edge below IWA to inner edge above OWA
            TL.dist = np.logspace(np.log10(mind/10.),np.log10(maxd*10.),TL.nStars)*u.pc


        #a constant, everything else var
        spec = copy.deepcopy(self.spec)
        spec['arange'] = [1,1]
        spec['Rprange'] = [1,10]
        spec['prange'] = [0.2,0.5]
        Garrett = EXOSIMS.Completeness.GarrettCompleteness.GarrettCompleteness(**copy.deepcopy(spec))
        cGarrett = Garrett.target_completeness(TL)
        self.assertTrue(np.all(cGarrett[TL.dist > maxd*u.pc] == 0))

        #e constant everything else var
        spec = copy.deepcopy(self.spec)
        spec['erange'] = [0,0]
        spec['Rprange'] = [1,10]
        spec['prange'] = [0.2,0.5]
        Garrett = EXOSIMS.Completeness.GarrettCompleteness.GarrettCompleteness(**copy.deepcopy(spec))
        cGarrett = Garrett.target_completeness(TL)
        self.assertTrue(np.all(cGarrett[TL.dist > maxd*u.pc] == 0))

        #a and e constant, everything else var
        spec = copy.deepcopy(self.spec)
        spec['arange'] = [1,1]
        spec['erange'] = [0,0]
        spec['Rprange'] = [1,10]
        spec['prange'] = [0.2,0.5]
        Garrett = EXOSIMS.Completeness.GarrettCompleteness.GarrettCompleteness(**copy.deepcopy(spec))
        cGarrett = Garrett.target_completeness(TL)
        self.assertTrue(np.all(cGarrett[TL.dist > maxd*u.pc] == 0))

        #a constant and constrainOrbits
        spec = copy.deepcopy(self.spec)
        spec['arange'] = [1,1]
        spec['constrainOrbits'] = True
        spec['Rprange'] = [1,10]
        spec['prange'] = [0.2,0.5]
        Garrett = EXOSIMS.Completeness.GarrettCompleteness.GarrettCompleteness(**copy.deepcopy(spec))
        cGarrett = Garrett.target_completeness(TL)
        self.assertTrue(np.all(cGarrett[TL.dist > maxd*u.pc] == 0))

