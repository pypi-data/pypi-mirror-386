import unittest
from pathlib import Path
import sys
sys.path.append('../')
from src.crdclib import crdclib as cl


class TestReadYaml(unittest.TestCase):

    def test_readyaml(self):
        TESTPATH = Path(__file__).parent
        answer = {'first': ['second', 'third', 'fourth'], 'fifth': {'sixth': 'seventh'}}
        yamltestfile = TESTPATH /'data/yamlexamplefile.yml'
        self.assertEqual(cl.readYAML(yamltestfile), answer)


if __name__ == "__main__":
    unittest.main(verbosity=2)
