#!/usr/bin/env python3

import time
import csv
from random import uniform
from math import sqrt
from pathlib import Path

import pandas as pd
import openrouteservice as ors
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely import wkt

# erstellt eine Liste bestehend aus shapely-MultiPolygon-Objekten
def buildMultipolgonList():
    wohList = kbk[(kbk['nutzung'] == 'Wohnbebauung') | (kbk['nutzung'] == 'Stadtkern')]
    wohList.to_csv('wohList.csv',index=False)
    polyStrings = list(wohList['geometrie_wkt']) 
    polyList = []
    for string in polyStrings:
        polyList.append(MultiPolygon(wkt.loads(string)))
    return polyList

# gibt wahr zurück, wenn Koordinaten in einem der MultiPolygone liegen
def pointInPolyList(coords):
    point = Point(coords)
    for mPoly in polyList:
        if point.within(mPoly):
            return True
    return False

def getRandomCoordinate():
    lon = uniform(12.02,12.25)
    lat = uniform(54.05,54.25)
    return lon,lat

# gibt eine Liste mit Zufallskoordinaten, die sich in bewohntem Gebiet befinden, zurück 
def getRandomPointList():
    validCoordList = []
    tries = 0
    while len(validCoordList) < 600:
        tries += 1
        c = getRandomCoordinate()
        if pointInPolyList(c):
            validCoordList.append(c)
    print("Tries: " + str(tries))
    return validCoordList

# gibt die Koordinatenliste aller Spielanlagen zurück
def getSpielanlagenCoords():
    lons = list(gspa['longitude'])
    lats = list(gspa['latitude'])
    return [(lons[i],lats[i]) for i in range(len(lats))]

def getEuclideanDistance(coordA, coordB):
    return sqrt((coordB[0] - coordA[0])**2 + (coordB[1] - coordA[1])**2)

def setupORS(apikey):
    return ors.Client(key=apikey)

def getDistanceFromORS(coordA, coordB):
    json = client.directions( coordinates = (coordA, coordB),
                              profile = 'foot-walking',
                              instructions = False, geometry = False)
    return json['routes'][0]['summary']['distance']

# gibt eine Liste der drei räumlich nächsten Spielanlagen zurück
def getCandidateCoords(randCoord):
    distList = []
    for spC in spCoords:
        distList.append((spC,getEuclideanDistance(spC,randCoord)))
    distList = sorted(distList, key=lambda tup: tup[1])
    return distList[:3]

# gibt eine Liste mit allen kürzesten Distanzen zur nächstgelegenen Spielanlage zurück
def getDistances():
    finalDistances = []
    counter = 0
    for randCoord in randCoords:
        candidates = getCandidateCoords(randCoord)
        orsDists = []
        for cand in candidates:
            orsDists.append(getDistanceFromORS(randCoord,cand[0]))
            counter += 1
            # throtteling due to api restrictions ca. (40 req/minute)
            if counter % 10 == 0:
                print("req: " + str(counter))
            time.sleep(1.55)
        orsDists.sort()
        finalDistances.append(orsDists[0])
        saveToCSV(randCoord,orsDists[0], 'results.csv')
    return finalDistances

def saveToCSV(coord,dist,csvPath):
    path = Path(csvPath)
    if not path.is_file():
        with open(csvPath, 'w', newline='') as f:
            csvWriter = csv.writer(f)
            csvWriter.writerow(['randomLon','randomLat','distance'])
    else:
        with open(csvPath, 'a', newline='') as f:
            csvWriter = csv.writer(f)
            csvWriter.writerow([coord[0],coord[1],dist])

gspa = pd.read_csv('geraetespielanlagen.csv')
kbk = pd.read_csv('konzeptbodenkarte_2018_anthropogene_ueberpraegung.csv')
polyList = buildMultipolgonList()
client = setupORS('5b3ce3597851110001cf6248be724e36a89d4b688daebc96d82395b4')
print("Anzahl geladener Multipolygone: " + str(len(polyList)))

# should be true
#print(pointInPolyList((12.09029,54.09432)))
#print(pointInPolyList((12.07145,54.13041)))
#should be false
#print(pointInPolyList((10.07145,51.13041)))

randCoords = getRandomPointList()
spCoords = getSpielanlagenCoords()

finDistances = getDistances()
print(len(finDistances))

