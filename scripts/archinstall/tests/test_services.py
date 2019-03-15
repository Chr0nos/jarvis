import arch.services
import inspect

from tools import check_packages

def test_services_class():
    for item, obj in inspect.getmembers(arch.services):
        if not inspect.isclass(obj) or item in ('ServicesManager', 'Service'):
            print('skipping', item)
            continue
        print('checking', item)
        assert issubclass(obj, arch.services.Service)
        assert isinstance(obj.name, str)
        assert isinstance(obj.desc, str)
        assert isinstance(obj.packages, list)
        check_packages(obj.packages)
        assert isinstance(obj.enable, bool)
        assert isinstance(obj.groups, list)
        assert obj.service is None or isinstance(obj.service, str)
