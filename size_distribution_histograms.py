#Author(s)     : Pedro Espino (pespino@berkeley.edu)
#Licence       : GPLv3

# This script takes in a dataset of food store locations in NYC (using NYC Open Data datasets) and parses them into lists of
# stores with "supermarket", "bodega/grocery", "market", etc. in the name. It then plots the size distribution (Sq. Ft.) of these stores
# on a histogram, useful for seeing the typical store size for each type of food store.

import matplotlib.pyplot as plt
from matplotlib import rc
import matplotlib
from matplotlib import rcParams
from matplotlib.patches import Circle
import matplotlib.colorbar as cbar
import pylab
from os.path import exists
from matplotlib.pyplot import figure
import pandas
import numpy as np

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

#Make a figure to save histograms in
hfig, hax= plt.subplots(nrows=2, ncols=2,figsize=(16,16))

zipcode_dataframe = pandas.read_csv('path to zipcode DB')
#Get all NYC Zipcodes - useful for things later on
ZCTA = np.asarray(zipcode_dataframe['ZCTA'])
NYC_ZIPCODES=[]
for i in range(0, len(ZCTA)-1):
    for j in range(0, len(ZCTA[i].split(','))): 
        zipcode=ZCTA[i].split(',')[j].strip()
        NYC_ZIPCODES.append(zipcode)

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

#Import the food store database from NYC Open Data
foodstore_dataframe = pandas.read_csv('path to retail store db')
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
print("Considering %d foodstores across NYC -- making plots of their distributions" %len(NYC_FOODSTORE_ADDRESSFULL))

#FIRST ROW CONSIDERS SIZE DISTRIBUTION OF BODEGAS AND SUPERMARKETS
#SECOND ROW CONSIDERS SIZE DISTRIBUTION OF MARKETS AND ALL FOOD STORES
print(len(NYC_FOODSTORE_ADDRESSFULL))
dummy=0
FFSSIZEDIST=[]
FFSTYPEDIST=[]
FFSOPTYPEDIST=[]
FFS_COORDS_NYCOD=[]
BODEGASIZEDIST=[]
BODEGATYPEDIST=[]
BODEGAOPTYPEDIST=[]
BODEGA_COORDS_NYCOD=[]
SUPERMARKETSIZEDIST=[]
SUPERMARKETTYPEDIST=[]
SUPERMARKETOPTYPEDIST=[]
SUPERMARKET_COORDS_NYCOD=[]

FDSTSIZEDIST=[]
FDSTTYPEDIST=[]
FDSTOPTYPEDIST=[]
acceptable_types=['JACD', 'JACK', 'JABC', 'JABCK', 'JABCD', 'JAC', 
                  'JAD', 'JACH', 'JABCH', 'JABHK', 'JACDK']
for i in range(0, len(NYC_FOODSTORE_ADDRESSFULL)):
    dbaname=NYC_FOODSTORE_DBANAME[i]
    storename=NYC_FOODSTORE_NAME[i]
    storetype=NYC_FOODSTORE_TYPE[i]
    store_name_reference='\t'.join([storename, dbaname])
    if("DELI" in store_name_reference or "GROCER" in store_name_reference or "BODEG" in store_name_reference):
        BODEGASIZEDIST.append(NYC_FOODSTORE_AREASQFT[i])
        BODEGATYPEDIST.append(NYC_FOODSTORE_TYPE[i])
        BODEGAOPTYPEDIST.append(NYC_FOODSTORE_OPTYPE[i])
        BODEGA_COORDS_NYCOD.append(NYC_FOODSTORE_COORDS[i])
    elif(("SUPERMARKET" in store_name_reference or "COOP" in store_name_reference or " MARKET " in store_name_reference) and storetype in acceptable_types):
        FFSSIZEDIST.append(NYC_FOODSTORE_AREASQFT[i])
        FFSTYPEDIST.append(NYC_FOODSTORE_TYPE[i])
        FFSOPTYPEDIST.append(NYC_FOODSTORE_OPTYPE[i])
        FFS_COORDS_NYCOD.append(NYC_FOODSTORE_COORDS[i])
    if(("SUPERMARKET" in store_name_reference or "COOP" in store_name_reference) and storetype in acceptable_types):
        SUPERMARKETSIZEDIST.append(NYC_FOODSTORE_AREASQFT[i])
        SUPERMARKETTYPEDIST.append(NYC_FOODSTORE_TYPE[i])
        SUPERMARKETOPTYPEDIST.append(NYC_FOODSTORE_OPTYPE[i])
        SUPERMARKET_COORDS_NYCOD.append(NYC_FOODSTORE_COORDS[i])
    if(True):
        FDSTSIZEDIST.append(NYC_FOODSTORE_AREASQFT[i])
        FDSTTYPEDIST.append(NYC_FOODSTORE_TYPE[i])
        FDSTOPTYPEDIST.append(NYC_FOODSTORE_OPTYPE[i])

#FIRST HISTOGRAM
hax[0][0].hist(BODEGASIZEDIST, bins=[0,2000,5000,15000,20000])
hax[0][1].hist(FFSSIZEDIST, bins=[0,2000,5000,15000,20000])
hax[0][0].set_yscale('log')
hax[0][1].set_yscale('log')
hax[1][0].hist(SUPERMARKETSIZEDIST, bins=[0,2000,5000,15000,20000])
hax[1][1].hist(FDSTSIZEDIST, bins=[0,2000,5000,15000,20000], color="crimson")
hax[1][0].set_yscale('log')
hax[1][1].set_yscale('log')

for j in range(0, 2):
    hax[0][j].axvline(2e3, color="red")
    hax[0][j].axvline(5e3, color="red")
    hax[0][j].axvline(15e3, color="red")
    hax[0][j].axvline(20e3, color="red")
    hax[0][j].set_xlim([0,20000])
    hax[1][j].set_xlabel(r"$\text{Sq. Ft.}$", fontsize=universal_fontsize)
hax[0][0].set_ylabel(r"$\text{Number of Locations}$", fontsize=universal_fontsize)
hax[1][0].set_ylabel(r"$\text{Number of Locations}$", fontsize=universal_fontsize)
hax[0][0].set_title(r"$\text{Area Distribution for Locations}$"+'\n'+r"$\text{with ``Deli'' or ``Grocery'' in Name}$", wrap=True, fontsize = universal_fontsize)
hax[0][1].set_title(r"$\text{Area Distribution for Locations with ``Supermarket''}$"+'\n'+r"$\text{ ``Market'', or ``Cooperative'' in Name}$", wrap=True, fontsize = universal_fontsize)
hax[1][1].set_title(r"$\text{Area Distribution for all NYC Food Stores}$", wrap=True, fontsize = universal_fontsize)
hax[1][0].set_title(r"$\text{Area Distribution for Locations with ``Supermarket''}$"+'\n'+r"$\text{ in Name}$", wrap=True, fontsize = universal_fontsize)

changefontsize=5
hax[0][0].text(1e2, 1e2, r"$\mathbf{\sim 86\%}$", color="white", fontsize=universal_fontsize-changefontsize)
hax[0][0].text(2.5e3, 50, r"$\mathbf{\sim 12\%}$", color="white", fontsize=universal_fontsize-changefontsize)
hax[0][0].text(9e3, 10, r"$\mathbf{\sim 1\%}$", color="white", fontsize=universal_fontsize-changefontsize)
hax[0][0].text(16500, 2, r"$\mathbf{\lesssim 0.1 \%}$", color="white", fontsize=universal_fontsize-changefontsize)

hax[0][1].text(1e2, 1e2, r"$\mathbf{\sim 53\%}$", color="white", fontsize=universal_fontsize-changefontsize)
hax[0][1].text(2.5e3, 50, r"$\mathbf{\sim 23\%}$", color="white", fontsize=universal_fontsize-changefontsize)
hax[0][1].text(9e3, 10, r"$\mathbf{\sim 18\%}$", color="white", fontsize=universal_fontsize-changefontsize)
hax[0][1].text(16500, 2, r"$\mathbf{\sim 5 \%}$", color="white", fontsize=universal_fontsize-changefontsize)

hax[0][0].text(8e3, 6e3, r"$\mathbf{Tot: %d}$" %len(BODEGASIZEDIST), color="black", fontsize=universal_fontsize)
hax[0][1].text(8e3, 6e3, r"$\mathbf{Tot: %d}$" %len(FFSSIZEDIST), color="black", fontsize=universal_fontsize)

#SECOND HISTOGRAM
hax[1][0].axvline(2e3, color="red")
hax[1][0].axvline(5e3, color="red")
hax[1][0].axvline(15e3, color="red")
hax[1][0].axvline(20e3, color="red")
hax[1][0].set_xlim([0,20000])
hax[1][1].set_xlim([0,20000])

hax[1][1].axvline(2e3, color="blue")
hax[1][1].axvline(5e3, color="blue")
hax[1][1].axvline(15e3, color="blue")
hax[1][1].axvline(20e3, color="blue")

hax[1][0].text(1e2, 50, r"$\mathbf{\sim 25\%}$", color="white", fontsize=universal_fontsize-changefontsize)
hax[1][0].text(2.5e3, 30, r"$\mathbf{\sim 18\%}$", color="white", fontsize=universal_fontsize-changefontsize)
hax[1][0].text(9e3, 100, r"$\mathbf{\sim 40\%}$", color="white", fontsize=universal_fontsize-changefontsize)
hax[1][0].text(16500, 20, r"$\mathbf{\sim 15 \%}$", color="white", fontsize=universal_fontsize-changefontsize)

hax[1][1].text(1e2, 1e2, r"$\mathbf{\sim 70\%}$", color="black", fontsize=universal_fontsize-changefontsize)
hax[1][1].text(2.5e3, 50, r"$\mathbf{\sim 18\%}$", color="black", fontsize=universal_fontsize-changefontsize)
hax[1][1].text(9e3, 10, r"$\mathbf{\sim 10\%}$", color="black", fontsize=universal_fontsize-changefontsize)
hax[1][1].text(16500, 2, r"$\mathbf{\sim 2\%}$", color="black", fontsize=universal_fontsize-changefontsize)

hax[1][0].text(8e3, 6e3, r"$\mathbf{Tot: %d}$" %len(SUPERMARKETSIZEDIST), color="black", fontsize=universal_fontsize)
hax[1][1].text(8e3, 6e3, r"$\mathbf{Tot: %d}$" %len(FDSTSIZEDIST), color="black", fontsize=universal_fontsize)

hax[0][0].set_ylim([1e0, 1e4])
hax[0][1].set_ylim([1e0, 1e4])
hax[1][0].set_ylim([1e0, 1e4])
hax[1][1].set_ylim([1e0, 1e4])

plt.savefig('size_distribution_histograms.pdf')
