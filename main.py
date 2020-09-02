import requests
import pandas as pd
import datetime
import numpy as np

url = 'https://re.jrc.ec.europa.eu/api/mrcalc'

for lat in np.linspace(60,70,20):
  for lon in np.linspace(20,30,20):

    params = {'lat': lat,
              'lon': lon,
              'optrad': 1}

    res = requests.get(url, params=params)

    data = res.content.decode('utf-8')

    df = pd.DataFrame(columns=['radiation'])

    for row in res.content.decode('utf-8').split('\n')[6:-4]:
      timestamp = pd.Timestamp(datetime.datetime.strptime(row[:9], '%Y\t\t%b'))
      df.loc[timestamp, 'radiation'] = float(row.split('\t')[-1].split('\r')[0])

    mean = df.mean()
    print(f'lat: {lat}, lon: {lon}, mean: {mean}')
# for month, group in df.groupby(df.index.month):
#   print(f'{month}: {group.mean()}')