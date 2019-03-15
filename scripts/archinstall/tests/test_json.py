import json
import sys
import os

def test_json_syntax():
    json_dir = os.path.join(sys.path[1], 'json')
    for json_file in os.listdir(json_dir):
        print('loading', json_file)
        with open(os.path.join(json_dir, json_file)) as fp:
            json.load(fp)
    print('done')

