import os

import analyzer
import loader

CUR_DIR = os.path.dirname(__file__)

TELEM_DIR = os.path.join(CUR_DIR, "telem")


def list_files():
    for root, dirs, files in os.walk(TELEM_DIR, topdown=False):
        for name in files:
            if name.endswith(".ld"):
                source_file = os.path.join(root, name)
                yield source_file


for file in list_files():
    analyzer.analyze(file)

