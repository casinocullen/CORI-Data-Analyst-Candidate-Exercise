import psycopg2
import time
import datetime
import pandas as pd
import sys
from carto.auth import APIKeyAuthClient
from geopandas import GeoDataFrame



# # Export Data from PostGreSQL

### Connect to local PostGreSQL account
try:
    connection = psycopg2.connect(database="postgres",user="postgres",password="1LOVEyou")
    print("I have successfully connected to the database")
except Exception as e:
    print("I am unable to connect to the database:" +str(e))

    
### Export broadband data from SQL
try: 
    start_time = time.time()
    cursor = connection.cursor()
    print('Now extracting the data: ' + str(datetime.datetime.now()))
    cmmd_ExtractData = "SELECT * FROM broadband"
    cursor.execute(cmmd_ExtractData)
    
    rows = cursor.fetchall()
   
    print('End time is: ' + str(datetime.datetime.now()))
    time_complete = round((time.time()-start_time)/60,2)
    print('Time to complete: ' + str(time_complete))
    

    connection.commit()

except Exception as e:
    print("Error %s" % e)

### Disconnect
finally:
    if connection:
        connection.close()


# # Process and Clean Data

### Convert broadband data to panda dataframe 
broadBandData = pd.DataFrame(rows, columns = ['LogRecNo','Provider_Id','FRN','ProviderName','DBAName','HoldingCompanyName','HocoNum','HocoFinal','StateAbbr','BlockCode','TechCode','Consumer','MaxAdDown','MaxAdUp','Business','MaxCIRDown','MaxCIRUp'])

### Assign unique geoid to each county 
broadBandData['geoid'] = broadBandData['BlockCode'].astype(str).str[0:5]

### Read the county shaphefile and subset Vermont and New Hampsire counties
county = gpd.read_file('Shapefiles/gz_2010_us_050_00_5m.shp',crs=crs)
county = county.loc[(county['STATE']=="33")|(county['STATE']=="50")]

### Assign unique geoid to each county 
county['geoid'] = county['GEO_ID'].str[9:15]


### Read the population shaphefile 
pop = pd.read_csv("Data/co_est2017_alldata.csv", encoding="cp1252")
### Assign unique geoid to each county
pop['geoid'] = pop['STATE'].apply(lambda x: '{0:0=2}'.format(x)) + pop['COUNTY'].apply(lambda x: '{0:0=3}'.format(x))
pop = pop[['STNAME','geoid','CENSUS2010POP','POPESTIMATE2017']]


### Find the maximum advertised upload speeds in each county
broadBandData_group = broadBandData.groupby(['geoid'], as_index=False)['MaxAdUp','ProviderName','HoldingCompanyName'].max()

### Mergy maximum advertised upload speeds with county information
broadBandData_group = pd.merge(broadBandData_group, county, how="left", on="geoid")
### Mergy maximum advertised upload speeds with population information
broadBandData_group = pd.merge(broadBandData_group, pop, how="left", on="geoid")

### Delete unnecessary column
del broadBandData_group['GEO_ID']

### Find the weighted maximum advertised upload speeds by 2017 population
broadBandData_group["weighted_maxadup"] = broadBandData_group['MaxAdUp']*broadBandData_group["POPESTIMATE2017"]/(broadBandData_group["POPESTIMATE2017"].mean())

### Export the gpkg file and ready to upload to CARTO
geo_df = GeoDataFrame(broadBandData_group, crs = crs, geometry = broadBandData_group['geometry'])
geo_df.to_file("./Result/broadBandData_county.gpkg",driver="GPKG")