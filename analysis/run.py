#!/usr/bin/env python3
import argparse
import re
from ase.io import read
from datetime import datetime
from pathlib import Path
import json
import numpy as np
import pandas as pd
import csv

def main():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('-r', '--read', type=str, required=False, default='SBATCH_DFT_VASP.tpl',
                        help='Input tpl file to read from')
    parser.add_argument('-l', '--lower', type=str, required=False, default=None,
                        help='Filter results by lower material (e.g. Si, Ge, Sn)')
    parser.add_argument('-u', '--upper', type=str, required=False, default=None,
                        help='Filter results by upper material (e.g. Si, Ge, Sn)')
    parser.add_argument('--lower-miller', type=str, required=False, default=None,
                        help='Filter results by lower miller index (e.g. 001)')
    parser.add_argument('--upper-miller', type=str, required=False, default=None,
                        help='Filter results by upper miller index (e.g. 001)')
    args = parser.parse_args()

if __name__ == '__main__':
    main()