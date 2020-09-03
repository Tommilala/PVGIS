import geopandas as gpd
import pandas as pd
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

def pv_at_area(area_code, geometry, samples):
    sample_pv = pd.Series(index=range(samples), dtype='float64')

    url = 'https://re.jrc.ec.europa.eu/api/mrcalc'
    for sample in range(samples):
        while True:
            point = gpd.GeoSeries(random_point(geometry), crs='EPSG:3067').to_crs('EPSG:4326')[0]
            params = {'lat': point.y, 'lon': point.x, 'optrad': 1}
            res = requests.get(url, params=params)

            if res.status_code == 200:
                break

        data = pd.Series(name='radiation', dtype='float64')

        for row in res.content.decode('utf-8').split('\n')[6:-4]:
            timestamp = pd.Timestamp(datetime.datetime.strptime(row[:9], '%Y\t\t%b'))
            data.loc[timestamp] = float(row.split('\t')[-1].split('\r')[0])

        sample_pv[sample] = data.groupby(data.index.year).sum().mean()

    return sample_pv.mean()



# def mean_yearly_total_pv_at_location(point):
#     url = 'https://re.jrc.ec.europa.eu/api/mrcalc'
#     params = {'lat': point.y, 'lon': point.x, 'optrad': 1}

#     res = requests.get(url, params=params)

#     data = pd.Series(name='radiation', dtype='float64')

#     # TODO: filter out points in water, maybe combine functions as the sampled points do not know if they are feasible (on land)
#     for row in res.content.decode('utf-8').split('\n')[6:-4]:
#         timestamp = pd.Timestamp(datetime.datetime.strptime(row[:9], '%Y\t\t%b'))
#         data.loc[timestamp] = float(row.split('\t')[-1].split('\r')[0])

#     # yearly_averages = pd.Series(name='yearly average PV', dtype='float64')
    
#     # for year, group in data.groupby(data.index.year):
#     #     yearly_averages[str(year)] = group.mean()

#     return data.groupby(data.index.year).sum().mean()


paavo = gpd.read_file('./shapefiles/pno_tilasto_2020.shp')
data = pd.read_excel('./shapefiles/alueryhmittely_posnro_2020_fi.xlsx', skiprows=4, dtype={'Postinumeroalue': 'str'})
data['Geometry'] = paavo
data = data.set_index('Postinumeroalue')                    # read_csv param 'index_col' bugs with dtype

for area_code, area_data in data.iterrows():
    geometry = area_data['Geometry']

    # # Sample 10 points and convert to WGS84, then use PVGIS api to get values for each area code
    # sample_points = gpd.GeoSeries([random_point(polygon) for i in range(10)], crs='EPSG:3067').to_crs('EPSG:4326')
    # sample_pv = pd.Series([mean_yearly_total_pv_at_location(point) for point in sample_points])
    
    mean_pv = pv_at_area(area_code, geometry, 10)

    print(f'area code: {area_code}, mean pv: {mean_pv}')
    data.loc[area_code, 'Mean PV'] = mean_pv

data['Mean PV'].to_csv('results.csv')