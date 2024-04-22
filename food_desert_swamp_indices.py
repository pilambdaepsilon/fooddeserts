#Author(s)     : Pedro Espino (pespino@berkeley.edu)
#Licence       : GPLv3

# This script calculates the Food Desert and Food Swamp Indices throughout NYC (see https://sites.google.com/view/pilambdaepsilon/data)
# It takes in data from the NYC Open Data portal and SimplyAnalytics to calculate the average number of accessible supermarkets and bodegas
# throughout the city, and saves the results into a file. It also produces a map of the indices. Specify which boroughs you want to consider below.

import matplotlib.pyplot as plt
from matplotlib import rc
from matplotlib import rcParams
from matplotlib.patches import Circle
import matplotlib
import matplotlib.colorbar as cbar
import pylab
import os
import math
from os.path import exists
from matplotlib.pyplot import figure
import numpy.ma as ma
import pandas
import numpy as np
import cmasher as cmr

from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
from matplotlib.ticker import LogFormatter 
from shapely import geometry
from shapely.geometry import Point, MultiPoint
from shapely.geometry import MultiPolygon, Polygon
import shapely.wkt
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

#specify which boroughs to consider (the more boroughs the longer the analysis takes)
BOROUGHS_TO_CONSIDER=["Bronx"]#, "Brooklyn", "Queens", "Manhattan", "Staten Island"]
#rewrite results from previous runs? (TODO: make this a command line argument)
#rewrite_results=False
rewrite_results=True

if(rewrite_results):
    print("REWRITING RESULTS OF ANALYSIS")
    desert_swamp_results=open("DESERT_SWAMP_INDICES","w")
    desert_swamp_results.write("#[1]Boro [2]CTCode [3]Desert [4]Swamp [5]No.Bodegas [6]No.People\n")

#import the datasets for consumer data on percent of households with one vehicle, population by census tract, and per capita income
car_access_dataframe=pandas.read_csv('/home/pedro/Singularity/Desktop/DS/FoodDeserts/Percent_Households_One_Vehicle_Available.csv')
population_dataframe=pandas.read_csv('/home/pedro/Singularity/Desktop/DS/FoodDeserts/Population_by_CT.csv')
percap_inc_dataframe=pandas.read_csv('/home/pedro/Singularity/Desktop/DS/FoodDeserts/Per_Capita_Income_CT.csv')

#import the geospatial dataset
print("Reading geospatial data")
geo_dataframe = pandas.read_csv('/home/pedro/Singularity/Desktop/DS/FoodDeserts/nyct2010.csv')
#put the geo data into arrays
GEO_BORONAME=np.asarray(geo_dataframe['BoroName'])
GEO_AREAS=np.asarray(geo_dataframe['the_geom'])
GEO_NTANAME=np.asarray(geo_dataframe['NTAName'])
GEO_PUMA=np.asarray(geo_dataframe['PUMA'])
GEO_NTACODE=np.asarray(geo_dataframe['NTACode'])
GEO_CTLAB=np.asarray(geo_dataframe['CTLabel'])
GEO_CT2010=np.asarray(geo_dataframe['CT2010'])
GEO_BOROCT2010=np.asarray(geo_dataframe['BoroCT2010'])

#make numpy arrays from the relevant keys for the auxiliary consumer data
print("Importing relevant consumer data")
CARACCESS_NAME=np.asarray(car_access_dataframe['Name'])
CARACCESS_VEHICLES=np.asarray(car_access_dataframe['% Vehicles Available | 1 vehicle available, 2023 [Estimated]'])
POPULATION_BY_CT=np.asarray(population_dataframe['# Total Population, 2023 [Estimated]'])
PERCAP_INC_BY_CT=np.asarray(percap_inc_dataframe['Per Capita Income, 2023 [Estimated]'])
CARACCESS_CT=[]
#make a dict for parsing borough names to codes used in census tract codes (CT codes)
BORO_NAMES_AND_CODES = {
    "New York": 1,
    "Bronx": 2,
    "Kings": 3,
    "Queens": 4,
    "Richmond": 5
}
#take the boro names and codes from this data and match it to the format of the NYC open data
for i in range(0, len(CARACCESS_NAME)):
    ca_ct=CARACCESS_NAME[i].split(',')[0][2:]
    #full_census_tract=ca_ct
    ca_boroname = CARACCESS_NAME[i].split(',')[1][1:-7]
    ca_borocode = BORO_NAMES_AND_CODES[ca_boroname]
    full_census_tract = int("%d%s"%(ca_borocode, ca_ct))
    neighborhood_indices = np.where(GEO_BOROCT2010 == full_census_tract)[0]
    
    CARACCESS_CT.append(full_census_tract)
    
#arrays are better
CARACCESS_CT=np.array(CARACCESS_CT)

#get the NYC zipcodes to find all NYC supermarkets
zipcode_dataframe = pandas.read_csv('/home/pedro/Singularity/Desktop/DS/FoodDeserts/Modified_Zip_Code_Tabulation_Areas__MODZCTA__20240229.csv')
ZCTA = np.asarray(zipcode_dataframe['ZCTA'])
NYC_ZIPCODES=[]
for i in range(0, len(ZCTA)-1):
    for j in range(0, len(ZCTA[i].split(','))):
        zipcode=ZCTA[i].split(',')[j].strip()
        NYC_ZIPCODES.append(zipcode)

#Import the food store database from NYC Open Data
#foodstore_dataframe = pandas.read_csv('path to retail store db')
print("Parsing NYC Open Data for NYC area supermarkets")
foodstore_dataframe = pandas.read_csv('/home/pedro/Singularity/Desktop/DS/FoodDeserts/Retail_Food_Stores_20240226.csv')
FOODSTORE_BORO=np.asarray(foodstore_dataframe['County'])
FOODSTORE_TYPE=np.asarray(foodstore_dataframe['Establishment Type'])
FOODSTORE_OPTYPE=np.asarray(foodstore_dataframe['Operation Type'])
FOODSTORE_LICENSE=np.asarray(foodstore_dataframe['License Number'])
FOODSTORE_DBANAME=np.asarray(foodstore_dataframe['DBA Name'])
FOODSTORE_NAME=np.asarray(foodstore_dataframe['Entity Name'])
FOODSTORE_ADDNUMS = np.asarray(foodstore_dataframe['Street Number'])
FOODSTORE_ADDNAMES=np.asarray(foodstore_dataframe['Street Name'])
FOODSTORE_ZIPCODES=np.asarray(foodstore_dataframe['Zip Code'])
FOODSTORE_COORDS=np.asarray(foodstore_dataframe['Georeference'])
FOODSTORE_AREASQFT=np.asarray(foodstore_dataframe['Square Footage'])
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

#find all NYC foodstores
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

        
#FIRST ROW CONSIDERS SIZE DISTRIBUTION OF BODEGAS AND SUPERMARKETS
#SECOND ROW CONSIDERS SIZE DISTRIBUTION OF MARKETS AND ALL FOOD STORES
print("Parsing NYC food stores to find supermarkets and bodegas")
BODEGASIZEDIST=[]
BODEGATYPEDIST=[]
BODEGAOPTYPEDIST=[]
BODEGA_COORDS_NYCOD=[]
SUPERMARKETSIZEDIST=[]
SUPERMARKETTYPEDIST=[]
SUPERMARKETOPTYPEDIST=[]
SUPERMARKET_COORDS_NYCOD=[]

#acceptable store types - mainly excludes wholesale that doesn't specialize in food
acceptable_types=['JACD', 'JACK', 'JABC', 'JABCK', 'JABCD', 'JAC','JAD', 'JACH', 'JABCH', 'JABHK', 'JACDK']


for i in range(0, len(NYC_FOODSTORE_ADDRESSFULL)):
    dbaname=NYC_FOODSTORE_DBANAME[i]
    storename=NYC_FOODSTORE_NAME[i]
    storetype=NYC_FOODSTORE_TYPE[i]
    store_name_reference='\t'.join([storename, dbaname])
    #get the bodegas into their separate arrays
    if("DELI" in store_name_reference or "GROCER" in store_name_reference or "BODEG" in store_name_reference):
        BODEGASIZEDIST.append(NYC_FOODSTORE_AREASQFT[i])
        BODEGATYPEDIST.append(NYC_FOODSTORE_TYPE[i])
        BODEGAOPTYPEDIST.append(NYC_FOODSTORE_OPTYPE[i])
        BODEGA_COORDS_NYCOD.append(NYC_FOODSTORE_COORDS[i])
    elif(("SUPERMARKET" in store_name_reference or "COOP" in store_name_reference) and storetype in acceptable_types):
        SUPERMARKETSIZEDIST.append(NYC_FOODSTORE_AREASQFT[i])
        SUPERMARKETTYPEDIST.append(NYC_FOODSTORE_TYPE[i])
        SUPERMARKETOPTYPEDIST.append(NYC_FOODSTORE_OPTYPE[i])
        SUPERMARKET_COORDS_NYCOD.append(NYC_FOODSTORE_COORDS[i])

print("Importing web-scraped supermarket locations")        
#Import the list of supermarket coordinates and addresses (output from script pull_supermarkets_from_web.py)
SUPERMARKET_COORDS_web=[]
SUPERMARKET_ZIPCODES_web=[]
SUPERMARKET_ADDRESSES_web=[]
supermarketpage_file='SUPERMARKET_ADDRESSES_AND_COORDINATES_WEB'
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

#find potential duplicate supermarkets between those scraped from the web and the ones in the NYC Open Data dataset
#define useful conversion factors for analysis
conv_deg_to_km = 1e4/90.
conv_km_to_ft = 3280.84
conv_km_to_mi=0.6213712
conv_mi_to_km=1./conv_km_to_mi
conv_km_to_deg=1./conv_deg_to_km

#make an empty array in which to store the combined, non-duplicate supermarket coordinates
print("Cross-referencing and combining supermarket lists to avoid duplicate locations")
SUPERMARKET_COORDS_COMBINED=[]
minindices=[]
#loop through supermarket locations scraped from web, and calculate the distance from those from the NYCOD dataset
#if they are within 200 ft. of each other, then they are duplicates
for i in range(0, len(SUPERMARKET_COORDS_web)):
    absdiff_x = np.abs(SUPERMARKET_COORDS_web[i][0] - np.asarray(SUPERMARKET_COORDS_NYCOD)[:,0])
    reldiff_x = absdiff_x/SUPERMARKET_COORDS_web[j][0]
    
    absdiff_y = np.abs(SUPERMARKET_COORDS_web[i][1] - np.asarray(SUPERMARKET_COORDS_NYCOD)[:,1])
    reldiff_y = absdiff_y/SUPERMARKET_COORDS_web[i][1]
    
    absdiff_comb = (absdiff_x**2 + absdiff_y**2)*(conv_deg_to_km*conv_km_to_ft)**2
    reldiff_comb = reldiff_x**2 + reldiff_y**2
    
    minindexrel=np.argmin(reldiff_comb)
    minindexabs=np.argmin(absdiff_comb)
    if(np.sqrt(absdiff_comb[minindexabs]) <= 200.0):
        minindices.append(minindexabs)
    SUPERMARKET_COORDS_COMBINED.append(SUPERMARKET_COORDS_web[i])

#keep the nonduplicates (TODO: find more efficient pythonic way of doing this with list comprehension)
for i in range(0, len(SUPERMARKET_COORDS_NYCOD)):
    if(i not in minindices):
        SUPERMARKET_COORDS_COMBINED.append(SUPERMARKET_COORDS_NYCOD[i])
        
#=======================================================================
#  __  __       _                              _           _     
# |  \/  |     (_)           /\               | |         (_)    
# | \  / | __ _ _ _ __      /  \   _ __   __ _| |_   _ ___ _ ___ 
# | |\/| |/ _` | | '_ \    / /\ \ | '_ \ / _` | | | | / __| / __|
# | |  | | (_| | | | | |  / ____ \| | | | (_| | | |_| \__ \ \__ \
# |_|  |_|\__,_|_|_| |_| /_/    \_\_| |_|\__,_|_|\__, |___/_|___/
#                                                 __/ |          
#                                                |___/           
#=======================================================================
#calculate the food insecurity index and map it
fig, ax= plt.subplots(nrows=1, ncols=2,figsize=(16,8))
cmap1 = matplotlib.cm.get_cmap('PiYG_r')
cmap2 = matplotlib.cm.get_cmap('PRGn_r')

startTime = datetime.now()

#these bounds make for nice plots
minsupes=[1e1, 1e-1]
maxsupes=[1e5, 1e1]
normalize1 = matplotlib.colors.LogNorm(vmin=minsupes[0], vmax=maxsupes[0])
normalize2 = matplotlib.colors.LogNorm(vmin=minsupes[1], vmax=maxsupes[1])

startTime = datetime.now()

#set up a discrete grid, each point separated by 0.15 miles, also specify what we consider walking distance
#and driving distance
resolution=0.15/(conv_km_to_mi*conv_deg_to_km)
walking_distance=0.5/(conv_km_to_mi*conv_deg_to_km)
driving_distance=2.0/(conv_km_to_mi*conv_deg_to_km)

#make a list of points corresponding to  supermarket_coords
supermarket_points = MultiPoint(SUPERMARKET_COORDS_COMBINED)
bodega_points = MultiPoint(BODEGA_COORDS_NYCOD)

#make empty arrays for some of the quantities we want to keep from the analysis
FOOD_ACCESSIBILITY=[]
NUMBER_OF_BODEGAS=[]
NUMBER_OF_PEOPLE=[]
FOOD_DESERT_INDEX=[]
FOOD_SWAMP_INDEX=[]

print("Calculating/Mapping Food Desert and Swamp Indices")
for i in range(0, len(GEO_AREAS)):
    #for each geometric area, we want to enumerate the number of supermarkets and bodegas in walking and driving distance
    valid_points=[]
    supermarket_enumerator_walking=[]
    supermarket_enumerator_driving=[]
    bodega_enumerator_walking=[]
    MP = shapely.wkt.loads(GEO_AREAS[i])
    if(GEO_BORONAME[i] in BOROUGHS_TO_CONSIDER):
        boro_census_tract=GEO_BOROCT2010[i]
        ca_matching_index = np.where(CARACCESS_CT==boro_census_tract)
        #get the fraction of households with one vehicle in this CT
        try:
            fraction_of_vehicles_in_ct=CARACCESS_VEHICLES[ca_matching_index][0]/100.0
        except:
            fraction_of_vehicles_in_ct=0.0
        try:
            population_in_ct = POPULATION_BY_CT[ca_matching_index][0]
        except:
            population_in_ct = 1.0 #this drives the relevant index to the bounds
        #for each geometry, calculate the relevant quantity and map it
        for geom in MP.geoms:
            xs, ys = geom.exterior.xy
            #areas ending in '99' are parks or cemeteries
            if(GEO_NTACODE[i][-2:]!='99'):
                #get the bounds of the geometry
                lonmin, latmin, lonmax, latmax = geom.bounds
                #make a grid of points which we sample in this geometry
                xgrid, ygrid = np.meshgrid(np.arange(lonmin, lonmax, resolution), np.arange(latmin, latmax, resolution))
                points = MultiPoint(list(zip(xgrid.flatten(),ygrid.flatten())))
                #see which points fall inside the geometry
                valid_points.extend([j for j in points if geom.contains(j)])
                xps = [point.x for point in valid_points]
                yps = [point.y for point in valid_points]
                #for each point in the geometry make buffers corresponding to walking and driving distances
                for a in range(0, len(valid_points)):
                    local_xcoord=xps[a]
                    local_ycoord=yps[a]
                    localbuffer_walking = Point(local_xcoord,local_ycoord).buffer(walking_distance)
                    localbuffer_driving = Point(local_xcoord,local_ycoord).buffer(driving_distance)
                    
                    locbuffxs_walking,locbuffys_walking = localbuffer_walking.exterior.xy
                    locbuffxs_driving,locbuffys_driving = localbuffer_driving.exterior.xy
                    
                    #for each sample point, count the number of supermarkets within walking and driving distance, and the bodegas within walking distance
                    supermarket_enumerator_walking.extend([j for j in supermarket_points if localbuffer_walking.contains(j)])
                    supermarket_enumerator_driving.extend([k for k in supermarket_points if localbuffer_driving.contains(k)])
                    bodega_enumerator_walking.extend([l for l in bodega_points if localbuffer_walking.contains(l)])
                #make these quantities useable (TODO: find a more efficient pythonic way of doing this with masks)
                try:
                    avg_walking_distance_supermarkets = len(supermarket_enumerator_walking)/len(valid_points)
                except:
                    avg_walking_distance_supermarkets = 0.0
                try:
                    avg_driving_distance_supermarkets = len(supermarket_enumerator_driving)/len(valid_points)
                except:
                    avg_driving_distance_supermarkets = 0.0
                try:
                    avg_walking_distance_bodegas = len(bodega_enumerator_walking)/len(valid_points)
                except:
                    avg_walking_distance_bodegas = 0.0
                
                #calculate the number of accessible markets and other relevant quantities
                food_access_ind = np.maximum(1.0, avg_walking_distance_supermarkets + avg_driving_distance_supermarkets*fraction_of_vehicles_in_ct)
                #number_of_bodegas = np.maximum(0.0, avg_walking_distance_bodegas)
                number_of_bodegas = avg_walking_distance_bodegas
                FOOD_ACCESSIBILITY.append(food_access_ind)
                NUMBER_OF_BODEGAS.append(number_of_bodegas)
                NUMBER_OF_PEOPLE.append(population_in_ct)
                
                food_desert_index = population_in_ct/food_access_ind
                food_swamp_index = number_of_bodegas/food_access_ind
                FOOD_DESERT_INDEX.append(food_desert_index)
                FOOD_SWAMP_INDEX.append(food_swamp_index)
                
                if(rewrite_results):
                    #print("%s %s %1.5e %1.5e %1.5e %1.5e" %(GEO_BORONAME[i], boro_census_tract, food_desert_index, food_swamp_index, number_of_bodegas, population_in_ct))
                    desert_swamp_results.write("%s %s %1.5e %1.5e %1.5e %1.5e \n" %(GEO_BORONAME[i], boro_census_tract, food_desert_index, food_swamp_index, number_of_bodegas, population_in_ct))
                
                ax[0].fill(xs, ys, alpha=0.75, color=cmap1(normalize1(food_desert_index)))
                ax[1].fill(xs, ys, alpha=0.75, color=cmap2(normalize2(food_swamp_index)))
            else:
                ax[0].fill(xs, ys, alpha=1.0, color='black')
                ax[1].fill(xs, ys, alpha=1.0, color='black')
ax[0].set_title(r"$\text{Food Desert Index } C_{\rm desert} \text{ throughout NYC}$", fontsize=universal_fontsize)
ax[1].set_title(r"$\text{Food Swamp Index } C_{\rm swamp} \text{ throughout NYC}$", fontsize=universal_fontsize)
ax[0].set_xlabel("Longitude", fontsize=universal_fontsize)
ax[1].set_xlabel("Longitude", fontsize=universal_fontsize)
ax[0].set_ylabel("Latitude", fontsize=universal_fontsize)

cb_ax1 = fig.add_axes([0.062, 1.05, 0.425, 0.02])
cb1 = cbar.ColorbarBase(cb_ax1, cmap=cmap1,norm=matplotlib.colors.LogNorm(vmin=minsupes[0], vmax=maxsupes[0]), orientation='horizontal')

cb_ax2 = fig.add_axes([0.547, 1.05, 0.425, 0.02])
cb2 = cbar.ColorbarBase(cb_ax2, cmap=cmap2,norm=matplotlib.colors.LogNorm(vmin=minsupes[1], vmax=maxsupes[1]),orientation='horizontal')
#for aind in range(0, 2):
#    ax[aind].set_xlim([-74.3, -73.7])
#    ax[aind].set_ylim([40.5, 40.95])
if(rewrite_results):
    desert_swamp_results.close()
print("Done")
print((datetime.now() - startTime))

plt.savefig('figures/food_desert_food_swamp.pdf')
