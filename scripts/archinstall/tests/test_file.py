from arch.archinstall import File
from tempfile import TemporaryDirectory

def test_install_put():
    with TemporaryDirectory() as tmp:
        file = File(tmp + '/test')
        test_content = 'test\ndata\nfor\fun\n\n'
        file.put(test_content)
        with open(file.filepath, 'r') as fd:
            assert fd.read() == test_content
