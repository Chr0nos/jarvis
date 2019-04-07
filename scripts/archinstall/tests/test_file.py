from arch.archinstall import File
from tempfile import TemporaryDirectory
import os

def test_file_put():
    with TemporaryDirectory() as tmp:
        file = File(tmp + '/test')
        test_content = 'test\ndata\nfor\fun\n\n'
        file.put(test_content)
        with open(file.filepath, 'r') as fd:
            assert fd.read() == test_content

# def test_file_insert():
#     original_content = [
#         'line 1',
#         'something here',
#         'and here',
#         'also here'
#     ]
#     inserted_line = 'my custom line'
#     with TemporaryDirectory() as tmp:
#         testpath = os.path.join(tmp, 'test.txt')
#         with open(testpath, 'w') as test_file:
#             test_file.write('\n'.join(original_content))
#         file = File(testpath)
#         file.insert(inserted_line, 2)
#         with open(testpath) as test_file:
#             file_content = test_file.readlines()
#         assert '\n'.join(original_content) == '\n'.join(file_content)