#Author(s)     : Pedro Espino (pespino@berkeley.edu)
#Licence       : GPLv3

# This script takes in NYC Open Data datsets to map the food store locations with the word "supermarket" in their name throughout NYC.
# It also considers a list of supermarkets scraped from the web using the pull_supermarkets_from_web.py script. It plots these on NYC maps 
# saves that to a pdf.

import matplotlib.pyplot as plt
from matplotlib import rc
import matplotlib
from matplotlib import rcParams
from matplotlib.patches import Circle
import matplotlib.colorbar as cbar
import pylab
import os
import time
import math
from os.path import exists
from matplotlib.pyplot import figure
import numpy.ma as ma
import pandas
import numpy as np
import cmasher as cmr

from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
from shapely import geometry
from shapely.geometry import Point, MultiPoint
from shapely.geometry import MultiPolygon, Polygon
import shapely.wkt
import random
from datetime import datetime

universal_fontsize=20
universal_linewidth=2

rcParams.update({'figure.autolayout': True})
matplotlib.rc('text', usetex = True)
matplotlib.rc('font', **{'family': 'serif', 'serif':['Computer Modern'], 'size':11})
matplotlib.rcParams['text.latex.preamble']=r"\usepackage{amsmath,amssymb}"
matplotlib.rcParams['xtick.minor.size'] = 1
matplotlib.rcParams['xtick.minor.width'] = 1
matplotlib.rcParams['xtick.labelsize'] = universal_fontsize
matplotlib.rcParams['ytick.labelsize'] = universal_fontsize
matplotlib.rc('legend', fontsize=universal_fontsize)

#specify which boroughs to consider in the mapping
BOROUGHS_TO_CONSIDER=["Bronx", "Brooklyn", "Queens", "Manhattan", "Staten Island"]

#Import the food store data
foodstore_dataframe = pandas.read_csv('/home/pedro/Singularity/Desktop/DS/FoodDeserts/Retail_Food_Stores_20240226.csv')

#Import the zipcode data and store the NYC zip codes
zipcode_dataframe = pandas.read_csv('/home/pedro/Singularity/Desktop/DS/FoodDeserts/Modified_Zip_Code_Tabulation_Areas__MODZCTA__20240229.csv')
ZCTA = np.asarray(zipcode_dataframe['ZCTA'])
NYC_ZIPCODES=[]
for i in range(0, len(ZCTA)-1):
    for j in range(0, len(ZCTA[i].split(','))):
        zipcode=ZCTA[i].split(',')[j].strip()
        NYC_ZIPCODES.append(zipcode)

#make numpy arrays from some of the useful keys
FOODSTORE_BORO=np.asarray(foodstore_dataframe['County'])
FOODSTORE_TYPE=np.asarray(foodstore_dataframe['Establishment Type'])
FOODSTORE_OPTYPE=np.asarray(foodstore_dataframe['Operation Type'])
FOODSTORE_LICENSE=np.asarray(foodstore_dataframe['License Number'])
FOODSTORE_DBANAME=np.asarray(foodstore_dataframe['DBA Name'])
FOODSTORE_NAME=np.asarray(foodstore_dataframe['Entity Name'])
FOODSTORE_ADDNUMS = np.asarray(foodstore_dataframe['Street Number'])
FOODSTORE_ADDNAMES=np.asarray(foodstore_dataframe['Street Name']) #+ np.asarray(foodstore_dataframe['Street Name'])
FOODSTORE_ZIPCODES=np.asarray(foodstore_dataframe['Zip Code'])
FOODSTORE_COORDS=np.asarray(foodstore_dataframe['Georeference'])
FOODSTORE_AREASQFT=np.asarray(foodstore_dataframe['Square Footage'])

#make empty arrays in which to store parsed data
NYC_FOODSTORE_ADDRESSFULL=[]
NYC_FOODSTORE_BORO=[]
NYC_FOODSTORE_ZIPCODE=[]
NYC_FOODSTORE_COORDS=[]
NYC_FOODSTORE_AREASQFT=[]
NYC_FOODSTORE_NAME=[]
NYC_FOODSTORE_DBANAME=[]
NYC_FOODSTORE_TYPE=[]
NYC_FOODSTORE_OPTYPE=[]
NYC_FOODSTORE_LICENSE=[]

#find the foodstores in NYC
for i in range(0, len(FOODSTORE_BORO)):
    if(str(FOODSTORE_ZIPCODES[i]) in NYC_ZIPCODES):
        NYC_FOODSTORE_ADDRESSFULL.append("%s %s" %(FOODSTORE_ADDNUMS[i], FOODSTORE_ADDNAMES[i]))
        NYC_FOODSTORE_BORO.append(FOODSTORE_BORO[i])
        NYC_FOODSTORE_ZIPCODE.append(FOODSTORE_ZIPCODES[i])
        NYC_FOODSTORE_COORDS.append([float(FOODSTORE_COORDS[i].split(' ')[1][1:]),float(FOODSTORE_COORDS[i].split(' ')[2][:-1])])
        NYC_FOODSTORE_AREASQFT.append(FOODSTORE_AREASQFT[i])
        NYC_FOODSTORE_NAME.append(FOODSTORE_NAME[i])
        NYC_FOODSTORE_DBANAME.append(FOODSTORE_DBANAME[i])
        NYC_FOODSTORE_TYPE.append(FOODSTORE_TYPE[i])
        NYC_FOODSTORE_OPTYPE.append(FOODSTORE_OPTYPE[i])
        NYC_FOODSTORE_LICENSE.append(FOODSTORE_LICENSE[i])
        #print(FOODSTORE_BORO[i], FOODSTORE_DBANAME[i], FOODSTORE_TYPE[i], "---", FOODSTORE_ADDNUMS[i], 
        #      FOODSTORE_ADDNAMES[i], "---", FOODSTORE_ZIPCODES[i])

#make more empty arrays for specifically the supermarkets        
SUPERMARKETSIZEDIST=[]
SUPERMARKETTYPEDIST=[]
SUPERMARKETOPTYPEDIST=[]
SUPERMARKET_COORDS_NYCOD=[]

#acceptable store types, these types mainly exclude wholesale places that do not specialize in food
acceptable_types=['JACD', 'JACK', 'JABC', 'JABCK', 'JABCD', 'JAC', 'JAD', 'JACH', 'JABCH', 'JABHK', 'JACDK']

#find the NYC stores thata are supermarkets and are acceptable in type
for i in range(0, len(NYC_FOODSTORE_ADDRESSFULL)):
    dbaname=NYC_FOODSTORE_DBANAME[i]
    storename=NYC_FOODSTORE_NAME[i]
    storetype=NYC_FOODSTORE_TYPE[i]
    store_name_reference='\t'.join([storename, dbaname])
    if(("SUPERMARKET" in store_name_reference or "COOP" in store_name_reference) and storetype in acceptable_types):
        SUPERMARKETSIZEDIST.append(NYC_FOODSTORE_AREASQFT[i])
        SUPERMARKETTYPEDIST.append(NYC_FOODSTORE_TYPE[i])
        SUPERMARKETOPTYPEDIST.append(NYC_FOODSTORE_OPTYPE[i])
        SUPERMARKET_COORDS_NYCOD.append(NYC_FOODSTORE_COORDS[i])

#import the geospatial data for mapping
geo_dataframe = pandas.read_csv('/home/pedro/Singularity/Desktop/DS/FoodDeserts/nyct2010.csv')
GEO_BORONAME=np.asarray(geo_dataframe['BoroName'])
GEO_AREAS=np.asarray(geo_dataframe['the_geom'])
GEO_NTANAME=np.asarray(geo_dataframe['NTAName'])
GEO_PUMA=np.asarray(geo_dataframe['PUMA'])
GEO_NTACODE=np.asarray(geo_dataframe['NTACode'])
GEO_CTLAB=np.asarray(geo_dataframe['CTLabel'])
GEO_CT2010=np.asarray(geo_dataframe['CT2010'])
GEO_BOROCT2010=np.asarray(geo_dataframe['BoroCT2010'])

#plot these on a map
fig, ax= plt.subplots(nrows=1, ncols=2,figsize=(16,8))

#show areas
NEIGHBORHOODS=[[],[]]
neighborhood_name="X"
neighborhood_code="X"

print("Available boroughs: ", set(GEO_BORONAME))
print("Considering boroughs: ", BOROUGHS_TO_CONSIDER)

#go through each census tract and plot it on a map, along with the location of each store
print("Plotting NYC map and supermarket locations...")
for i in range(0, len(GEO_AREAS)):
    MP = shapely.wkt.loads(GEO_AREAS[i])
    #use this code to find the name and code of a neighborhood housing a certain supermarket
    #if(MP.contains(testpoint)):
    #        neighborhood_name=GEO_NTANAME[i]
    #        neighborhood_code=GEO_NTACODE[i]
    #        print(neighborhood_name, neighborhood_code)
    #        break
    #loop through the geometries
    for geom in MP.geoms:
        xs, ys = geom.exterior.xy
        #if we are considering the borough, then plot the census tract on the map
        if(GEO_BORONAME[i] in BOROUGHS_TO_CONSIDER):
            #things that end in '99' are parks or cemeteries
            if(GEO_NTACODE[i][-2:]=='99'):
                ax[0].fill(xs, ys, alpha=0.1, color='green')
                ax[1].fill(xs, ys, alpha=0.1, color='green')
            else:
                ax[0].fill(xs, ys, alpha=0.15, color='black')
                ax[1].fill(xs, ys, alpha=0.15, color='black')
            if(GEO_NTANAME[i] not in NEIGHBORHOODS[0]):
                NEIGHBORHOODS[0].append(GEO_NTANAME[i])
                NEIGHBORHOODS[1].append(GEO_NTACODE[i])

#import the data for the supermarkets from the web (see pull_supermarkets.py script)
SUPERMARKET_COORDS_web=[]
SUPERMARKET_ZIPCODES_web=[]
SUPERMARKET_ADDRESSES_web=[]
supermarketpage_file='/home/pedro/Singularity/Desktop/DS/FoodDeserts/SUPERMARKET_ADDRESSES_AND_COORDINATES_WEB'
SUPERMARKET_COORDS_long, SUPERMARKET_COORDS_lat = np.genfromtxt(supermarketpage_file,
             usecols=(3,2), delimiter=',', unpack=True, comments="#")
f=open(supermarketpage_file,"r")
lines=f.readlines()[2:]
for x in lines:
    addline=x.split(',')[0]
    zipline=x.split(',')[1]
    loclong=x.split(',')[3]
    loclat=x.split(',')[2]
    SUPERMARKET_ZIPCODES_web.append(zipline.split(' ')[3])
    SUPERMARKET_ADDRESSES_web.append(addline)
    SUPERMARKET_COORDS_web.append([float(loclong), float(loclat)])
f.close()

#plot the web and NYC open data supermarkets on separate maps
for i in range(0, len(SUPERMARKET_COORDS_web)):
    ax[0].scatter(SUPERMARKET_COORDS_web[i][0], SUPERMARKET_COORDS_web[i][1], color="red", marker='o', 
               alpha=0.5, s=5)
for i in range(0, len(SUPERMARKET_COORDS_NYCOD)):
    ax[1].scatter(SUPERMARKET_COORDS_NYCOD[i][0], SUPERMARKET_COORDS_NYCOD[i][1], color="blue", marker='o', 
               alpha=0.5, s=5)
#set the map bounds
for i in range(0, 2):
    ax[i].set_xlim([-74.3, -73.7])
    ax[i].set_ylim([40.5, 40.92])
    ax[i].set_xlabel(r"$\text{Longitude}$", fontsize=universal_fontsize)
    ax[i].set_ylabel(r"$\text{Latitude}$", fontsize=universal_fontsize)
ax[0].set_title(r"$\text{Locations of Supermarkets from ``supermarketpage.com''}$", fontsize=universal_fontsize)
ax[1].set_title(r"$\text{Locations with ``Supermarket'' in Name (NYC Open Data)}$", fontsize=universal_fontsize)

plt.savefig('figures/supermarket_location_map.pdf')
print("Done")
