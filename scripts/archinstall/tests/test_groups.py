from arch.tools import Groups

def test_groups_parse():
    grps = Groups()
    grps.parse()
    assert grps.list()


def test_groups_user():
    grps = Groups()
    grps.parse()
    lst = grps.user_groups('root')
    for x in lst:
        assert isinstance(x, int)
    assert 1 in lst
    assert 10 in lst
