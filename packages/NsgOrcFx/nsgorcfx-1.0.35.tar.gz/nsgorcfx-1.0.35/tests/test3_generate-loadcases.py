"""
Example of generating load cases 
"""

import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from src import NsgOrcFx as ofx

model = ofx.Model()
model.CreateLine()


directions = [0, 45, 90]
heights = [1.5, 2.0, 3.0]
periods = [5, 7, 9]
outFolder = r'tests\tmptestfiles'

# Regular waves
model.GenerateLoadCases('Dean stream', directions, heights, periods, outFolder)

# Irregular waves
model.GenerateLoadCases('JONSWAP', directions, heights, periods, outFolder)

# Irregular waves with reduced simulation time (200s, with the largest rise at half)
model.GenerateLoadCases('JONSWAP', directions, heights, periods, outFolder, reducedIrregDuration=200)
