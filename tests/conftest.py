import os
import sys

import matplotlib
matplotlib.use('Agg')

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, os.path.abspath(SRC))
