import unittest
from bento_meta.model import Model
import sys
sys.path.append('../')
from src.crdclib import crdclib as cl

class TestAddMDFNode(unittest.TestCase):

    def test_mdfAddNodes(self):
        mdf = Model(handle='TestModel', version='1.0.0')
        nodelist = ['nodeA', 'nodeB', 'nodeC']
        bumlist = ['Yabba', 'Dabba', 'Doo']

        mdf = cl.mdfAddNodes(mdf, nodelist)
        self.assertEqual(nodelist, list(mdf.nodes))
        self.assertNotEqual(bumlist, list(mdf.nodes))
        
if __name__ == "__main__":
    unittest.main(verbosity=2)