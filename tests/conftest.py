import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_dir = os.path.join(root_dir, 'src')
ui_dir = os.path.join(src_dir, 'ui')

for d in (root_dir, src_dir, ui_dir):
    if d not in sys.path:
        sys.path.insert(0, d)
