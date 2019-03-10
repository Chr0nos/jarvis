from mock import patch
import sys, os; sys.path.insert(0, os.getcwd())


def test_packages():
    from arch.metapkg import DEFAULT
    for pkg in DEFAULT:
        if ' ' in pkg:
            raise ValueError(pkg)
