#Author(s)     : Pedro Espino (pespino@berkeley.edu)
#Licence       : GPLv3

# This script takes in NYC Open Data datsets as well as consumer data (available through SimplyAnalytics) to map the quantities relevant to food insecurity in NYC.
# including: (1) Percentage of households with at least one vehicle available, (2) Population by census tract, (3) Per-capita income.
# These quantities are plotted and the map is saved to a pdf.

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

#from matplotlib import pyplot

from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
from matplotlib.ticker import LogFormatter 
from shapely import geometry
from shapely.geometry import Point, MultiPoint
from shapely.geometry import MultiPolygon, Polygon
import shapely.wkt

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

#import the datasets for consumer data on percent of households with one vehicle, population by census tract, and per capita income
car_access_dataframe=pandas.read_csv('/home/pedro/Singularity/Desktop/DS/FoodDeserts/Percent_Households_One_Vehicle_Available.csv')
population_dataframe=pandas.read_csv('/home/pedro/Singularity/Desktop/DS/FoodDeserts/Population_by_CT.csv')
percap_inc_dataframe=pandas.read_csv('/home/pedro/Singularity/Desktop/DS/FoodDeserts/Per_Capita_Income_CT.csv')

#import the geospatial dataset
geo_dataframe = pandas.read_csv('/home/pedro/Singularity/Desktop/DS/FoodDeserts/nyct2010.csv')

GEO_BORONAME=np.asarray(geo_dataframe['BoroName'])
GEO_AREAS=np.asarray(geo_dataframe['the_geom'])
GEO_NTANAME=np.asarray(geo_dataframe['NTAName'])
GEO_PUMA=np.asarray(geo_dataframe['PUMA'])
GEO_NTACODE=np.asarray(geo_dataframe['NTACode'])
GEO_CTLAB=np.asarray(geo_dataframe['CTLabel'])
GEO_CT2010=np.asarray(geo_dataframe['CT2010'])
GEO_BOROCT2010=np.asarray(geo_dataframe['BoroCT2010'])

#make numpy arrays from the relevant keys
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

#plot these data
fig, ax= plt.subplots(nrows=1, ncols=3,figsize=(24,8))

#specify color maps
cmap1 = matplotlib.cm.get_cmap('cmr.ember')
cmap2 = matplotlib.cm.get_cmap('cmr.cosmic')
cmap3 = matplotlib.cm.get_cmap('cmr.toxic')

#specify normalizations and bounds for colorbars
normalize1 = plt.Normalize(vmin=0.0, vmax=100)
normalize2 = matplotlib.colors.LogNorm(vmin=1e2, vmax=1e4)
normalize3 = matplotlib.colors.LogNorm(vmin=1e3, vmax=1e5)

#plot the NYC map, and color each census tract according to the relevant data above
print("Mapping relevant consumer data including:")
print("(1) Percentage of vehicles with at least one car available")
print("(2) Population by census tract")
print("(3) Per-capita income")
for i in range(0, len(GEO_AREAS)):
    valid_points=[]
    MP = shapely.wkt.loads(GEO_AREAS[i])
    #do it for all boroughs - visualization purposes
    if(True):
        boro_census_tract=GEO_BOROCT2010[i]
        ca_matching_index = np.where(CARACCESS_CT==boro_census_tract)
        #these will end up in a quantitative metric of car access to supermarkets, 
        #so keep valid entries and set others to zero (TODO: use masks to make this cleaner)
        try:
            percentage_of_vehicles_in_ct=CARACCESS_VEHICLES[ca_matching_index][0]
        except:
            percentage_of_vehicles_in_ct=0.0
        try:
            population_in_ct=POPULATION_BY_CT[ca_matching_index][0]
        except:
            population_in_ct=0.0
        try:
            percap_inc_in_ct=PERCAP_INC_BY_CT[ca_matching_index][0]
        except:
            percap_inc_in_ct=0.0
        for geom in MP.geoms:
            xs, ys = geom.exterior.xy
            if(GEO_NTACODE[i][-2:]!='99'):
                ax[0].fill(xs, ys, alpha=0.5, color=cmap1(normalize1(percentage_of_vehicles_in_ct)))
                ax[1].fill(xs, ys, alpha=0.5, color=cmap2(normalize2(population_in_ct)))
                ax[2].fill(xs, ys, alpha=0.5, color=cmap3(normalize3(percap_inc_in_ct)))
            else:
                ax[0].fill(xs, ys, alpha=0.15, color='green')
                ax[1].fill(xs, ys, alpha=0.15, color='green')
                ax[2].fill(xs, ys, alpha=0.15, color='green')

#set the plot titles and labels
ax[0].set_title("Percentage of Households with 1 Vehicle Available: The Bronx", fontsize=universal_fontsize)
ax[1].set_title("Population by Census Tract: The Bronx", fontsize=universal_fontsize)
ax[2].set_title("Per-capita Income: The Bronx", fontsize=universal_fontsize)
ax[0].set_xlabel("Longitude", fontsize=universal_fontsize)
ax[1].set_xlabel("Longitude", fontsize=universal_fontsize)
ax[2].set_xlabel("Longitude", fontsize=universal_fontsize)
ax[0].set_ylabel("Latitude", fontsize=universal_fontsize)
cb_ax1 = fig.add_axes([0.047, 1.05, 0.29, 0.02])
cb1 = cbar.ColorbarBase(cb_ax1, cmap=cmap1,norm=plt.Normalize(0, 100),orientation='horizontal')

cb_ax2 = fig.add_axes([0.375, 1.05, 0.29, 0.02])
cb2 = cbar.ColorbarBase(cb_ax2, cmap=cmap2,norm=matplotlib.colors.LogNorm(vmin=1e2, vmax=1e4), orientation='horizontal')

cb_ax3 = fig.add_axes([0.7, 1.05, 0.29, 0.02])
cb3 = cbar.ColorbarBase(cb_ax3, cmap=cmap3,norm=matplotlib.colors.LogNorm(vmin=1e3, vmax=1e5),orientation='horizontal')

plt.savefig('figures/consumer_data_map.pdf')
print("Done")
