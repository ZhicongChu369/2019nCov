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

# load map file
with urlopen('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json') as response:
    world_geo = json.load(response)
# load map file
with urlopen('https://raw.githubusercontent.com/johan/world.geo.json/6a1119de83dad01e07524e2ab97c2a1f54b9ef53/countries/CHN.geo.json') as response:
    china_geo = json.load(response)
# load map file
with urlopen('https://raw.githubusercontent.com/longwosion/geojson-map-china/master/geometryProvince/42.json') as response:
    hubei_geo = json.load(response)

# use API to retrieve hubei cities data
def hubei_retrieve():
    
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

def world_china_retrieve():
    
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
    updatetime = dt.fromtimestamp(China_summary_json['updateTime'] / 1000)
    
    return df_World, df_China, updatetime

def update_obd_values(hubei_geo, china_geo, world_geo):
    df_hubei = hubei_retrieve()
    df_World, df_China, updatetime = world_china_retrieve()
    
    # set up hovertext
    text = [ df_World['国家'][i] + '\n' +  str(df_World['确诊'][i]) + '例确诊'  for i in range(len(df_World))]
    df_World['text'] = text

    # extract province ids (used for locations) from json file
    ids, provinces = [], []
    
    for i in range(len(china_geo['features'])):
        ids.append( china_geo['features'][i]['id'] )
        provinces.append( china_geo['features'][i]['properties']['name'] )
        
    df_province_code = pd.DataFrame({'省简称': provinces, 'code': ids})
    df_China = df_China.merge(df_province_code, how = 'left', on = '省简称')
    
    # set up hovertext
    text = [ df_China['省简称'][i] + '\n' +  str(df_China['确诊'][i]) + '例确诊'  for i in range(len(df_China))]
    df_China['text'] = text

    
    # reorganize ids
    hubei_features = []
    for i in range(len(hubei_geo['features'])):
        temp_feature = hubei_geo['features'][i]
        temp_feature['id'] = temp_feature['properties']['id']
        hubei_features.append(temp_feature)
    
    hubei_geo['features'] = hubei_features
    # extract province ids (used for locations) from json file
    ids, cities = [], []
    
    for i in range(len(hubei_geo['features'])):
        ids.append( hubei_geo['features'][i]['id'] )
        cities.append( hubei_geo['features'][i]['properties']['name'] )
        
    df_city_code = pd.DataFrame({'城市全称': cities, 'code': ids})
    df_city_code['城市'] = ['恩施州', '十堰', '宜昌', '襄阳', '黄冈', '荆州', '荆门', '咸宁', '随州',
                           '孝感', '武汉', '黄石', '神农架林区', '天门', '仙桃', '潜江', '鄂州']
    df_hubei = df_hubei.merge(df_city_code, how = 'left', on = '城市')
    
    # set up hovertext
    text = [ df_hubei['城市'][i] + '\n' +  str(df_hubei['确诊'][i]) + '例确诊'  for i in range(len(df_hubei))]
    df_hubei['text'] = text
    
    return df_hubei, df_World, df_China, updatetime


def graph_prep(geojson, locations, z, hovertext, center_lon, center_lat, zoom, title, updatetime):
    
    # prepare token for Mapbox
    token = 'pk.eyJ1IjoiY2h1emhpY29uZyIsImEiOiJjazZoMG5tajIwNmh4M21ueGN0eXdtMmx6In0.kQscrYmKzfyLhN-YgENO0Q'
    
    data = go.Choroplethmapbox(geojson = geojson, locations = locations, 
                               z = z , hovertext = hovertext,
                               hoverinfo = 'text', colorscale = 'YlOrRd',
                               marker_line_width = 0.5, marker_line_color = 'rgb(169, 164, 159)',
                               colorbar=dict(
                                   title="确诊病例数",
                                   titleside="top",
                                   tickmode="array",
                                   tickvals=np.arange(0, 5, 1),
                                   ticktext=["1", "10", "100", "1k", '10k', '100k'],
                                   ticks="outside"
                                    ))
    
    layout = go.Layout(mapbox = {'accesstoken': token, 'center':{'lon' : center_lon, 'lat': center_lat},'zoom': zoom},
                  margin={"r":1,"t":45,"l":45,"b":1}, title = '疫情地图 ' + title,
                  annotations = [dict(
                      x=0.55,
                      y=0.03,
                      xref='paper',
                      yref='paper',
                      text='数据更新于 ' + str(updatetime),
                      showarrow = False
                 )])
        
    return data, layout


df_hubei, df_World, df_China, updatetime = update_obd_values(hubei_geo, china_geo, world_geo)

app = dash.Dash('vehicle-data')

data_dict = {"世界分布": df_World, "中国分布": df_China, 
             "湖北分布": df_hubei}



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

def update_graph(data_names, updatetime, df_hubei, df_World, df_China):
    graphs = []
    df_hubei, df_World, df_China, updatetime = update_obd_values(hubei_geo, china_geo, world_geo)
    
    if len(data_names)>2:
        class_choice = 'col s12 m6 l4'
    elif len(data_names) == 2:
        class_choice = 'col s12 m6 l6'
    else:
        class_choice = 'col s12'



    if "世界分布" in data_names:
        data, layout = graph_prep(geojson = world_geo, locations = df_World['code'],
                                  z = np.log10(df_World['确诊']), hovertext = df_World['text'],
                                  center_lon = 109.469607, center_lat = 37.826077,
                                  zoom = 1, title = "世界", updatetime = updatetime)
        
            
        graphs.append(html.Div(dcc.Graph(id="世界分布", animate=True, 
                                         figure={'data': [data],'layout' : layout}), className=class_choice))
        
    if "中国分布" in data_names:
        data, layout = graph_prep(geojson = china_geo, locations = df_China['code'],
                                  z = np.log10(df_China['确诊']), hovertext = df_China['text'],
                                  center_lon = 109.469607, center_lat = 37.826077,
                                  zoom = 2.6, title = "中国", updatetime = updatetime)
        
            
        graphs.append(html.Div(dcc.Graph(id="中国分布", animate=True, 
                                         figure={'data': [data],'layout' : layout}), className=class_choice))
        
    if "湖北分布" in data_names:
        data, layout = graph_prep(geojson = hubei_geo, locations = df_China['code'],
                                  z = np.log10(df_China['确诊']), hovertext = df_China['text'],
                                  center_lon = 112.1994, center_lat = 31.0354,
                                  zoom = 2.6, title = "湖北", updatetime = updatetime)
        
            
        graphs.append(html.Div(dcc.Graph(id="湖北分布", animate=True, 
                                         figure={'data': [data],'layout' : layout}), className=class_choice))

    return graphs

external_css = ["https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/css/materialize.min.css"]
for css in external_css:
    app.css.append_css({"external_url": css})

external_js = ['https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/js/materialize.min.js']
for js in external_css:
    app.scripts.append_script({'external_url': js})


if __name__ == '__main__':
    app.run_server(debug=True)