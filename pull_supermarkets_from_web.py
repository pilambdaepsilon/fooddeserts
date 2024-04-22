#Author(s)     : Pedro Espino (pespino@berkeley.edu)
#Licence       : GPLv3

# This script pulls a list of supermarket locations from supermarketpage.com, a third party website listing stores across the US.
# After scraping that page for supermarket locations in NY, it cross-references the addresses with a list of NYC zipcodes, to parse
# into a list of NYC supermarkets. It then queries Bing Maps to find the supermarket latitude and longitude. A Bing Maps API key is required.

#IMPORT THE LIBRARIES
import os
from os.path import exists
import numpy.ma as ma
import pandas
import numpy as np

import geocoder

#SET THE BING MAPS API KEY
API_key='Place Bing Maps API key here! If you would like to use one but cannot create one, please contact me at pe7868@princeton.edu'

#Do you want to query Bing Maps API to get the coordinates for each address?
query_bing=False
if(query_bing):
    f_supermarket_results=open("SUPERMARKET_ADDRESSES_AND_COORDINATES_WEB","w")
    f_supermarket_results.write("#INFORMATION ON SUPERMARKETS IN NYC - PARSED FROM http://supermarketpage.com/supermarkets and Bing maps API\n")
    f_supermarket_results.write("#ADDRESS, LATITUDE, LONGITUDE\n")

#URL parsing libraries
import re
from urllib.request import Request, urlopen

#Define a function for grabbing the raw page content
def get_page_content(url, head):

    req = Request(url, headers=head)
    return urlopen(req)
#the following helps with sites that block automated scraping
head = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
    "Accept-Encoding": "none",
    "Accept-Language": "en-US,en;q=0.8",
    "Connection": "keep-alive",
    "refere": "https://example.com",
    "cookie": """your cookie value ( you can get that from your web page) """,
}

#import the zipcode data
zipcode_dataframe = pandas.read_csv('PATH_TO_ZIPCODE_DATABASE')
#Get all NYC Zipcodes - useful for things later on
ZCTA = np.asarray(zipcode_dataframe['ZCTA'])
NYC_ZIPCODES=[]
for i in range(0, len(ZCTA)-1):
    for j in range(0, len(ZCTA[i].split(','))):
        zipcode=ZCTA[i].split(',')[j].strip()
        NYC_ZIPCODES.append(zipcode)

#SCRAPE AND PARSE SUPERMARKET PAGE 
metasite_url = "http://supermarketpage.com/state/NY/"

#pull the meta site data and html
metasites_data = get_page_content(metasite_url,head).read()
metasites_data_html = metasites_data.decode("utf-8")
metasites_data_html_bytes = metasites_data_html.split('href="')

#make empty arrays in which to store things
supermarket_websites=[]
SUPERMARKET_ADDRESSES_web=[]
SUPERMARKET_ZIPCODES_web=[]
SUPERMARKET_ADDNUMS_web=[]
SUPERMARKET_COORDS_web=[]
print("parsing list of NYC supermarkets from the web:\n")
for i in range(0, len(metasites_data_html_bytes)):
    nested_site=metasites_data_html_bytes[i].split('>')[0][:-1]
    #parse things based on structure of html
    if(nested_site[-3:]=='htm'):
        supermarket_websites.append(nested_site)
        market_data = get_page_content(nested_site, head).read()
        market_html = market_data.decode("utf-8")
        market_html_bytes=market_html.split('</td><td>')
        for j in range(0, len(market_html_bytes)):
            #keep the supermarkets in NY state
            if market_html_bytes[j]=='NY':
                zipcode=market_html_bytes[j+1]
                borough=market_html_bytes[j-1].split(' ')[-2][:-1]
                #keep the supermarkets in NYC 
                if zipcode in NYC_ZIPCODES:
                    #joing things to make a full address and store it in the proper array
                    full_address = ' '.join(map(str, [market_html_bytes[j-1], market_html_bytes[j], market_html_bytes[j+1]]))
                    SUPERMARKET_ADDRESSES_web.append(full_address.upper())
                    SUPERMARKET_ADDNUMS_web.append(full_address.split(' ')[0])
                    SUPERMARKET_ZIPCODES_web.append(zipcode)
                    print(full_address)
                    #if Bing query is true, then search Bing Maps for the address and grab the coordinates
                    if(query_bing==1):
                        print("Querying Bing...")
                        long_lat_mont = [-73.89523018917087, 40.847372509635]

                        geocode_bing = geocoder.bing('%s'%full_address, key=API_key)
                        try:
                            checktype = geocode_bing.type
                            print("COULD NOT FIND ADDRESS COORDINATES... USING DEFAULT ADDRESS")
                            long_lat_mont = [0.0, 0.0]
                        except:
                            latlong_results = geocode_bing.json
                            long_lat_mont = [latlong_results['lng'], latlong_results['lat']]
                            print("ADDRESS COORDS: ", latlong_results['lat'], latlong_results['lng'])

                        SUPERMARKET_COORDS_web.append([long_lat_mont[1], long_lat_mont[0]])
                        f_supermarket_results.write("%s, %s, %s\n" %(full_address.upper(), str(long_lat_mont[1]), str(long_lat_mont[0])))

print("\nDone. %d supermarkets found" %(len(SUPERMARKET_ADDRESSES_web)))
if(query_bing):
    f_supermarket_results.close()
