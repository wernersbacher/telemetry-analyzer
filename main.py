import os

import analyzer

CUR_DIR = os.path.dirname(__file__)

TELEM_DIR = os.path.join(CUR_DIR, "telem")


def list_files():
    for root, dirs, files in os.walk(TELEM_DIR, topdown=False):
        for name in files:
            if name.endswith(".ld"):
                source_file = os.path.join(root, name)
                yield source_file


FAST_FILE = "monza-lamborghini_huracan_gt3_evo-14-2022.02.06-14.56.03.ld"
fast_file_path = os.path.join(TELEM_DIR, FAST_FILE)
analyzer.analyze(fast_file_path)

print("-"*10)

ANALYZE_FILE = "monza-lamborghini_huracan_gt3_evo-11-2022.02.08-19.23.07.ld"
analyze_file_path = os.path.join(TELEM_DIR, ANALYZE_FILE)
analyzer.analyze(analyze_file_path)

#for file in list_files():
#    analyzer.analyze(file)

