import unittest
import os
import sys
sys.path.append('../')
from src.crdclib import crdclib as cl

class TestGetCDERecord(unittest.TestCase):

    IN_GITHUB = os.getenv("GITHUB_ACTIONS")
    @unittest.skipIf(IN_GITHUB, "Doesn't run in Github")

    def test_getSTSPVList(self):
        cdeid = '7572817'
        cdeversion = '3.00'
        cdelist = cl.getSTSPVList(cdeid, cdeversion)
        self.assertEqual(cdelist, ['Unknown', 'Male', 'Female'])

        empty_cdeid = '11479876'
        empty_cdeversion = '1.00'
        emptylist = cl.getSTSPVList(empty_cdeid, empty_cdeversion)
        self.assertEqual(emptylist, [])
        
if __name__ == "__main__":
    unittest.main(verbosity=2)