import sys, os;
sys.path.insert(0, os.getcwd())

from arch.tools import Cd

def test_cd():
    pwd = os.getcwd()
    with Cd('/tmp'):
        assert os.getcwd() == '/tmp', pwd
    assert os.getcwd() == pwd
