import unittest
import bento_mdf
import sys
sys.path.append('../')
from src.crdclib import crdclib as cl

class TestAnnotateMDFTerms(unittest.TestCase):

    def test_mdfBuildLoadsheets(self):
        #Using the GC/CDS Model for testing
        mdffiles = ['https://raw.githubusercontent.com/CBIIT/cds-model/refs/heads/10.0.0/model-desc/cds-model.yml','https://raw.githubusercontent.com/CBIIT/cds-model/refs/heads/10.0.0/model-desc/cds-model-props.yml']
        mdf = bento_mdf.MDF(*mdffiles)
        loadsheets = cl.mdfBuildLoadSheets(mdf)

        #Check that nodes match
        startnodes = list(mdf.model.nodes)
        sheetnodes = list(loadsheets.keys())
        
        self.assertEqual(startnodes, sheetnodes)

        # Test that the properties are in the model
        for node, loadsheet in loadsheets.items():
            sourceprops = list(mdf.model.nodes[node].props)
            sheetprops = loadsheet.columns.tolist()
            for sheetprop in sheetprops:
                if "." not in sheetprop:
                    self.assertIn(sheetprop, sourceprops)

        # Edges in the loadsheet are expressed as node.property.  Check that they exist
        for node, loadsheet in loadsheets.items():
            sheetprops = loadsheet.columns.tolist()
            for sheetprop in sheetprops:
                if "." in sheetprop:
                    temp = sheetprop.split(".")
                    node = temp[0]
                    prop = temp[1]
                    testsheet = loadsheets[node]
                    testprops = testsheet.columns.tolist()
                    self.assertIn(prop, testprops)






if __name__ == "__main__":
    unittest.main(verbosity=2)