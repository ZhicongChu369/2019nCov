import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import numpy as np
import json
from datetime import datetime as dt
from urllib.request import urlopen
from bs4 import BeautifulSoup
import lxml.html as lh
import pandas as pd
import requests

# use API to retrieve hubei cities data
def hubei_retrieve():
    
    # allow for 10 retreive attemps max
    for i in range(10):
        response = requests.get("https://lab.isaaclin.cn/nCoV/api/area?latest=1&province=湖北省")
        if response.status_code == 200:
            break
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
            break
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
            break
            
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



def overall__retrieve():
    # time series summary stats
    response = requests.get("https://lab.isaaclin.cn/nCoV/api/overall?latest=0")
    # verify everything went okay, and the result has been returned
    assert response.status_code == 200
    raw_series_json = response.json()['results']
    
    confirmedCount, suspectedCount, curedCount, deadCount, seriousCount, \
    suspectedIncr, confirmedIncr, curedIncr, deadIncr, seriousIncr, updateTime, update_date \
    = [], [], [], [], [], [], [], [], [], [], [], []
    
    for i in range(len(raw_series_json)):
        confirmedCount.append(raw_series_json[i]['confirmedCount'])
        suspectedCount.append(raw_series_json[i]['suspectedCount'])
        curedCount.append(raw_series_json[i]['curedCount'])
        deadCount.append(raw_series_json[i]['deadCount'])
        updateTime.append(raw_series_json[i]['updateTime'])
        update_date.append(dt.fromtimestamp(raw_series_json[i]['updateTime']/1000).date())
        
        if 'seriousCount' in raw_series_json[i].keys():
            seriousCount.append(raw_series_json[i]['seriousCount'])
        else:
            seriousCount.append( np.nan )
        
        if 'suspectedIncr' in raw_series_json[i].keys():
            suspectedIncr.append(raw_series_json[i]['suspectedIncr'])
            confirmedIncr.append(raw_series_json[i]['confirmedIncr'])
            curedIncr.append(raw_series_json[i]['curedIncr'])
            deadIncr.append(raw_series_json[i]['deadIncr'])
            seriousIncr.append(raw_series_json[i]['seriousIncr'])
            
        else:
            suspectedIncr.append( np.nan )
            confirmedIncr.append( np.nan )
            curedIncr.append( np.nan )
            deadIncr.append( np.nan )
            seriousIncr.append( np.nan )
      
    df_time = pd.DataFrame({'确诊':confirmedCount, '疑似': suspectedCount, '治愈':curedCount,
                            '死亡':deadCount, '重症':seriousCount, '疑似增数':suspectedIncr,
                            '确诊增数':confirmedIncr, '治愈增数':curedIncr, '死亡增数':deadIncr,
                            '重症增数':seriousIncr, '更新时间值':updateTime, '更新日': update_date}) 
    
    df_time_agg = df_time.drop_duplicates(subset = '更新日', keep = 'first')
    
    return df_time_agg
    
     
    
def update_obd_values(hubei_geo, china_geo, world_geo):
    df_hubei = hubei_retrieve()
    df_World, df_China, updatetime = world_china_retrieve()
    df_time_agg = overall__retrieve()
    
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
    
    # sort by confirmed cases 
    df_hubei = df_hubei.sort_values(by= '确诊', ascending = False)
    # set up hovertext
    text = [ df_hubei['城市'][i] + '\n' +  str(df_hubei['确诊'][i]) + '例确诊'  for i in range(len(df_hubei))]
    df_hubei['text'] = text
    
    return df_hubei, df_World, df_China, updatetime, df_time_agg


def map_prep(geojson, locations, z, hovertext, center_lon, center_lat, zoom, title, updatetime):
    
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
                  margin={"r":1,"t":45,"l":45,"b":30}, title = '累计确诊' + title + '分布图',
                  annotations = [dict(
                      x=0.55,
                      y=0.03,
                      xref='paper',
                      yref='paper',
                      text='数据更新于 ' + str(updatetime),
                      showarrow = False
                 )], height =500 )
        
    return data, layout



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


df_hubei, df_World, df_China, updatetime, df_time_agg = update_obd_values(hubei_geo, china_geo, world_geo)
# sort by confirmed cases 
df_hubei = df_hubei.sort_values(by= '确诊', ascending = False)





# map for confirmed cases in China

data1, layout1 = map_prep(geojson = china_geo, locations = df_China['code'],
                                  z = np.log10(df_China['确诊']), hovertext = df_China['text'],
                                  center_lon = 109.469607, center_lat = 37.826077,
                                  zoom = 2.6, title = "中国", updatetime = updatetime)


# Pie chart of Top k provinces with most confirmed cases
# set value for k

province_confirm = df_China[['省简称', '确诊']]
province_confirm = province_confirm.sort_values(by = ['确诊'], ascending = False)
k = 10

# aggregate all the rest BGAs to "Other"
other_province_confirm_sum = sum(province_confirm.iloc[k:, 1])
labels_prov = list(province_confirm['省简称'][:k]) + ["其他"]
values_prov = list(province_confirm['确诊'][:k]) + [other_province_confirm_sum ]

data2 = go.Pie(labels=labels_prov, values=values_prov, textinfo='label+ percent' ) 
layout2 = go.Layout( title={
        'text': '确诊病例前10省市',
        'y':0.98,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},  margin={"r":30,"t":40,"l":40,"b":30}, height = 500) 



# Bar charts for city data in Hubei

# create hover txt
hovertxt = [ str(int(x)) +'确诊' +  '<br>'  +   str(int(y)) + '死亡'  +  '<br>'  +   str(int(z)) + '治愈' \
            for (x, y, z) in zip(df_hubei['确诊'], df_hubei['死亡'], df_hubei['治愈'])]

data3 = go.Bar( 
    x = df_hubei['城市'],
    y = df_hubei['确诊'],
    hoverinfo = 'x+text',
    hovertext = hovertxt,
    marker={'color': np.log10(df_hubei['死亡']),
            'colorscale' : 'Reds',
            'showscale': True,
            'colorbar.title': '死亡病例',
            'colorbar.tickmode':"array",
            'colorbar.tickvals': np.arange(0, 5, 1),
            'colorbar.ticktext': ["1", "10", "100", "1k", '10k'],
            } 
)


layout3 =go.Layout(title={ 'text' : '湖北城市确诊数柱状图',
                          'y':0.92,
                          'x':0.5,
                          'xanchor': 'center',
                          'yanchor': 'top'}, margin={"r":30,"t":30,"l":60,"b":80},
                   yaxis_title_text='确诊数',
                   height = 450, 
                   yaxis = dict(type = 'log') )




# line chart for confirmed suspected death and cured cases

trace0 = go.Scatter(x = df_time_agg['更新日'], y = df_time_agg['确诊'], name = '确诊病例', mode='lines+markers')
trace1 = go.Scatter(x = df_time_agg['更新日'], y = df_time_agg['疑似'], name = '疑似病例', mode='lines+markers')
trace2 = go.Scatter(x = df_time_agg['更新日'], y = df_time_agg['治愈'], name = '治愈病例', mode='lines+markers')
trace3 = go.Scatter(x = df_time_agg['更新日'], y = df_time_agg['死亡'], name = '死亡病例', mode='lines+markers')

data4 = [trace0, trace1, trace2, trace3]
layout4 =go.Layout(title={ 'text' : '全国病例数时间走势图',
                          'y':0.92,
                          'x':0.5,
                          'xanchor': 'center',
                          'yanchor': 'top'}, margin={"r":30,"t":80,"l":80,"b":80},
                   yaxis_title_text='病例数',
                   xaxis_title_text='时间',
                   height = 450 )

map_dist = dcc.Graph(id = 'map_dist')
pie = dcc.Graph(id = 'pie', animate=True, figure= {'data': [data2], 'layout': layout2})
bar = dcc.Graph(id = 'bar', animate=True, figure= {'data': [data3], 'layout': layout3} )
line = dcc.Graph(id = 'line', animate=True, figure= {'data': data4, 'layout': layout4})


app = dash.Dash('2019nCov-data',  external_stylesheets=[dbc.themes.BOOTSTRAP])

data_dict = {"世界分布": df_World, "中国分布": df_China, 
             "湖北分布": df_hubei}


# arrange app layout
Title =  dbc.Row( [dbc.Col(
                    html.H2('疫情地图',
                            style={'float': 'right',
                                   }
                            ), width = 6
                          ),
                  dbc.Col(
                    html.Img(
                            src = 'https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcTsIw6JB33EyGMmepsH2jbA_IJnPb2Bnj6WnlSslZV4IB_fFIs8',
                            style = {
                                    'height': '44%',
                                    'width' : '20%',
                                    'float' : 'right',
                                    'position' : 'relative',
                                    'margin-right' : 120,
                                    'margin-top' : 20 },
                            ), width = 6      
                          
                          )]
                )
                    

Dropdown = dbc.Row( dbc.Col(
                    dcc.Dropdown(id='选择地图区域',
                                 options=[{'label': s, 'value': s}
                                          for s in data_dict.keys()],
                                 value="中国分布",
                                 multi=False,
                                 style = {'margin-left' : 25}
                                 ), width = 3 )
                    )
                    
# =============================================================================
# Graphs = html.Div( children = html.Div( id="map_dist"))  
# =============================================================================

Loading = dcc.Loading(id="loading-1", children= [html.Div(id="loading-output-1")], type="default")


graphRow2 = dbc.Row([dbc.Col(map_dist, md=6), dbc.Col(pie, md=5)])
graphRow1 = dbc.Row([dbc.Col(line, md=6), dbc.Col(bar, md=5)])

# =============================================================================
# bc_img_link = 'https://www.eehealth.org/-/media/images/modules/blog/posts/2020/01/2019-novel-coronavirus.jpg'
# =============================================================================
Graphs= html.Div([graphRow1, graphRow2], id = 'graphs')
           

app.layout = html.Div([ Title, Dropdown, Loading, Graphs])
    
# =============================================================================
# dcc.Interval(
#     id='graph-update',
#     interval=120000),
# ], className="container",style={'width':'98%','margin-left':10,'margin-right':10,'max-width':50000})
# =============================================================================

   
@app.callback(
     Output('map_dist','figure'),
    [Input('选择地图区域', 'value')])

def update_graph( selected_item ):
# =============================================================================
#     df_hubei, df_World, df_China, updatetime, df_time_agg = update_obd_values(hubei_geo, china_geo, world_geo)
# =============================================================================
    
    if  selected_item == "世界分布":
        data_, layout = map_prep(geojson = world_geo, locations = df_World['code'],
                                  z = np.log10(df_World['确诊']), hovertext = df_World['text'],
                                  center_lon = 109.469607, center_lat = 37.826077,
                                  zoom = 1, title = "世界", updatetime = updatetime)
        
        
    elif  selected_item == "中国分布" :
        data_, layout = map_prep(geojson = china_geo, locations = df_China['code'],
                                  z = np.log10(df_China['确诊']), hovertext = df_China['text'],
                                  center_lon = 109.469607, center_lat = 37.826077,
                                  zoom = 2.6, title = "中国", updatetime = updatetime)
        
        
    else:
        data_, layout = map_prep(geojson = hubei_geo, locations = df_hubei['code'],
                                  z = np.log10(df_hubei['确诊']), hovertext = df_hubei['text'],
                                  center_lon = 112.1994, center_lat = 31.0354,
                                  zoom = 5.8, title = "湖北", updatetime = updatetime)
        
            
    map_figure ={'data': [data_],'layout' : layout}
        
    return map_figure


if __name__ == '__main__':
    app.run_server(debug=True)