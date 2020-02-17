import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import time
from collections import deque
import plotly.graph_objs as go
import numpy as np
import urllib
import json
from datetime import datetime as dt
from urllib.request import urlopen
from bs4 import BeautifulSoup
import lxml.html as lh
import pandas as pd
import plotly.graph_objects as go
from time import sleep
import sys
import requests
import random

# scrap iso code table from wikipedia with beautifulsoup
website_url = requests.get("https://zh.wikipedia.org/zh-cn/ISO_3166-1%E4%B8%89%E4%BD%8D%E5%AD%97%E6%AF%8D%E4%BB%A3%E7%A0%81").text
soup = BeautifulSoup(website_url, 'lxml')
table = soup.find('table')
table_rows = table.find_all('tr')[1:]

country, code = [], []
for tr in table_rows:
    td = tr.find_all('td')
    row = [i.text for i in td]
    code.append(row[0])
    country.append(row[1][1:])
    
index = country.index('中国台湾省[注 1]')
country[index] = '中国台湾省'

# store info in a pandas df
df_iso = pd.DataFrame({'国家': country, 'code': code})

# use API to retrive hubei cities data
def hubei_data():
    
    # allow for 10 retreive attemps max
    for i in range(10):
        response = requests.get("https://lab.isaaclin.cn/nCoV/api/area?latest=1&province=湖北省")
        if response.status_code == 200:
            exit
    # verify everything went okay, and the result has been returned
    assert response.status_code == 200
    # extract city data in Hubei
    city_data_json = response.json()['results'][0]['cities']
    
    # empty lists to store record values
    cityName, confirmedCount, curedCount, deadCount, locationId= [], [], [], [], []
    
    for i in range(len(city_data_json)):
        cityName.append(city_data_json[i]['cityName'])
        confirmedCount.append(city_data_json[i]['confirmedCount'])
        curedCount.append(city_data_json[i]['curedCount'])
        deadCount.append(city_data_json[i]['deadCount'])
        locationId.append(city_data_json[i]['locationId'])
        
    # create a table to store info
    df_hubei = pd.DataFrame({'城市': cityName, '确诊':confirmedCount, '治愈':curedCount,
                             '死亡':deadCount, '地区代码':locationId})
    return df_hubei

def world_china_data():
    
    # allow for 10 retreive attemps max
    for i in range(10):
        response = requests.get("https://lab.isaaclin.cn/nCoV/api/area?latest=1")
        if response.status_code == 200:
            exit
    # verify everything went okay, and the result has been returned
    assert response.status_code == 200
    raw_data_json = response.json()['results']
    
    country, provinceName, provinceShortName, confirmedCount, suspectedCount, \
    curedCount, deadCount = [],[],[],[],[],[],[]
    
    for i in range(len(raw_data_json)):
        country.append(raw_data_json[i]['countryName'])
        provinceName.append(raw_data_json[i]['provinceName'])
        provinceShortName.append(raw_data_json[i]['provinceShortName'])
        confirmedCount.append(raw_data_json[i]['confirmedCount'])
        suspectedCount.append(raw_data_json[i]['suspectedCount'])
        curedCount.append(raw_data_json[i]['curedCount'])
        deadCount.append(raw_data_json[i]['deadCount'])
        
    # create a table to store info
    df_raw = pd.DataFrame({'国家': country, '省': provinceName, '省简称':provinceShortName, 
                       '确诊':confirmedCount, '疑似': suspectedCount, '治愈':curedCount,'死亡':deadCount}) 
    
    # clean and reorganize table
    df_raw = df_raw.loc[df_raw['省']!= '待明确地区', :]
    df_China = df_raw.loc[df_raw['国家'] == '中国', :]
    df_World = df_raw.loc[df_raw['国家'] != '中国', ['国家','确诊','疑似', '治愈', '死亡']]
    
    # allow for 10 retreive attemps max
    for i in range(10):
        response = requests.get("https://lab.isaaclin.cn/nCoV/api/overall")
        if response.status_code == 200:
            exit
            
    assert response.status_code == 200
    China_summary_json = response.json()['results'][0] 
    China_counts = {'国家':'中国',  '确诊': China_summary_json['confirmedCount'], 
                                  '疑似': China_summary_json['suspectedCount'], 
                                  '治愈': China_summary_json['curedCount'],
                                  '死亡': China_summary_json['deadCount']}
    # append China data to World data table
    df_World = df_World.append(China_counts, ignore_index=True)
    
    # merge iso code to df
    df_World = df_World.merge(df_iso, how = 'left', on = '国家')
    
    # correct TW
    TW_correct = {'国家':'中国',  '确诊': China_summary_json['confirmedCount'], 
                                  '疑似': China_summary_json['suspectedCount'], 
                                  '治愈': China_summary_json['curedCount'],
                                  '死亡': China_summary_json['deadCount'], 
                  'code': 'TWN'}
    
    # append China data to World data table
    df_World = df_World.append(TW_correct, ignore_index=True)
    time_stamp = dt.fromtimestamp(China_summary_json['updateTime'] / 1000)
    
    return df_World, df_China, time_stamp


hubei_data = hubei_data()
World_data, China_data, updatetime = world_china_data()


app = dash.Dash('vehicle-data')

data_dict = {"世界分布":World_data, "中国分布": China_data, 
             "湖北分布": hubei_data}

def update_obd_values( updatetime, hubei_data, World_data, China_data):
    
    hubei_data = hubei_data()
    World_data, China_data, updatetime = world_china_data()

    return hubei_data, World_data, China_data, updatetime

# =============================================================================
# hubei_data, World_data, China_data, updatetime = update_obd_values(updatetime, hubei_data, World_data, China_data)
# =============================================================================

app.layout = html.Div([
    html.Div([
        html.H2('疫情地图',
                style={'float': 'left',
                       }),
        ]),
    dcc.Dropdown(id='选择地图区域',
                 options=[{'label': s, 'value': s}
                          for s in data_dict.keys()],
                 value=["世界分布","中国分布","湖北分布"],
                 multi=True
                 ),
    html.Div(children=html.Div(id='graphs'), className='row'),
    dcc.Interval(
        id='graph-update',
        interval=120000),
    ], className="container",style={'width':'98%','margin-left':10,'margin-right':10,'max-width':50000})
    
@app.callback(
    dash.dependencies.Output('graphs','children'),
    [dash.dependencies.Input('选择地图区域', 'value')],
    events=[dash.dependencies.Event('graph-update', 'interval')])

def update_graph(data_names, updatetime, hubei_data, World_data, China_data):
    graphs = []
    hubei_data, World_data, China_data, updatetime = update_obd_values(updatetime, hubei_data, World_data, China_data)
    
# =============================================================================
#     if len(data_names)>2:
#         class_choice = 'col s12 m6 l4'
#     elif len(data_names) == 2:
#         class_choice = 'col s12 m6 l6'
#     else:
#         class_choice = 'col s12'
# =============================================================================


    for data_name in data_names:

        data = go.Scatter(
            x=list(times),
            y=list(data_dict[data_name]),
            name='Scatter',
            fill="tozeroy",
            fillcolor="#6897bb"
            )

        graphs.append(html.Div(dcc.Graph(
            id=data_name,
            animate=True,
            figure={'data': [data],'layout' : go.Layout(xaxis=dict(range=[min(times),max(times)]),
                                                        yaxis=dict(range=[min(data_dict[data_name]),max(data_dict[data_name])]),
                                                        margin={'l':50,'r':1,'t':45,'b':1},
                                                        title='{}'.format(data_name))}
            ), className=class_choice))

    return graphs