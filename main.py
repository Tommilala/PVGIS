import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point
import random
import requests
import datetime

def random_point(geometry):
    # very sparse multipolygons can take long times in theory with simple bounds
    minx, miny, maxx, maxy = geometry.bounds
    point = Point()
    
    while(not geometry.contains(point)):
        # uniform in carthesian projection, skewed towards the poles in polar coordinates
        point = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
    
    return point

def average_yearly_total_pv_at_area(area_code, geometry, samples):
    sample_pv = pd.Series(index=range(samples), dtype='float64')

    url = 'https://re.jrc.ec.europa.eu/api/mrcalc'
    for sample in range(samples):
        
        attempts = 0
        while attempts < 50:

            # use GeoSeries to convert crs and then select the only point
            point = gpd.GeoSeries(random_point(geometry), crs='EPSG:3067').to_crs('EPSG:4326')[0]
            params = {'lat': point.y, 'lon': point.x, 'optrad': 1}
            res = requests.get(url, params=params)

            # points in water return 400
            if res.status_code == 200:
                break
            
            print(f'status: {res.status_code}, content: {res.content.decode("utf-8")}')
            attempts += 1

        if attempts == 50:
            return np.nan
        
        data = pd.Series(name='radiation', dtype='float64')

        for row in res.content.decode('utf-8').split('\n')[6:-4]:
            timestamp = pd.Timestamp(datetime.datetime.strptime(row[:9], '%Y\t\t%b'))
            data.loc[timestamp] = float(row.split('\t')[-1].split('\r')[0])

        # average of the sum of total PV radiation during each year
        sample_pv[sample] = data.groupby(data.index.year).sum().mean()

    return sample_pv.mean()

try:
    paavo = gpd.read_file('./shapefiles/pno_tilasto_2020.shp')
    data = pd.read_excel('./shapefiles/alueryhmittely_posnro_2020_fi.xlsx', skiprows=4, dtype={'Postinumeroalue': 'str'})
    data['Geometry'] = paavo
    data = data.set_index('Postinumeroalue')                    # read_csv param 'index_col' bugs with dtype

    for area_code, area_data in data.iterrows():
        geometry = area_data['Geometry']
        
        mean_pv = average_yearly_total_pv_at_area(area_code, geometry, 10)

        print(f'area code: {area_code}, mean pv: {mean_pv}')
        data.loc[area_code, 'Mean PV'] = mean_pv
    data['Mean PV'].to_csv('results.csv')

except KeyboardInterrupt:
    data['Mean PV'].to_csv('results.csv')

finally: 
    data['Mean PV'].to_csv('results.csv')