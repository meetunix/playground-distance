#!/usr/bin/env python3

import pandas as pd

def avg(distList):
    print(len(distList))
    distSum = 0
    for dist in distList:
        distSum += dist
    return distSum/len(distList)

csvFrame = pd.read_csv('results.csv')

print(avg(list(csvFrame['distance'])))



