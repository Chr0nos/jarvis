def check_packages(packages):
    for pkg in packages:
        print('checking for package validity', pkg)
        assert pkg.count('.') < 2
        assert pkg.count(' ') == 0
        assert pkg.lower() == pkg
        assert len(pkg) != 0
