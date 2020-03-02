import dash
from dash.exceptions import PreventUpdate
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
import pandas as pd
import requests


df_hubei = pd.read_csv('df_hubei.csv')
df_China = pd.read_csv('df_China.csv')
df_World = pd.read_csv('df_World.csv')
df_time_agg = pd.read_csv('df_time_agg.csv')

updatetime = 'Unknown'

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

# map for confirmed cases in China

def draw_map( selected_item = "中国分布" ):
    
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
            
    return data_, layout



# Pie chart of Top k provinces with most confirmed cases
# set value for k

def draw_pie():
    province_confirm = df_China[['省简称', '确诊']]
    province_confirm = province_confirm.sort_values(by = ['确诊'], ascending = False)
    k = 10
    
    # aggregate all the rest BGAs to "Other"
    other_province_confirm_sum = sum(province_confirm.iloc[k:, 1])
    labels_prov = list(province_confirm['省简称'][:k]) + ["其他"]
    values_prov = list(province_confirm['确诊'][:k]) + [other_province_confirm_sum ]
    
    data_ = go.Pie(labels=labels_prov, values=values_prov, textinfo='label+ percent' ) 
    layout = go.Layout( title={
            'text': '确诊病例前10省市',
            'y':0.98,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'},  margin={"r":30,"t":40,"l":40,"b":30}, height = 500) 
        
    return data_, layout


# Bar charts for city data in Hubei


def draw_bar():
    
    # create hover txt
    hovertxt = [ str(int(x)) +'确诊' +  '<br>'  +   str(int(y)) + '死亡'  +  '<br>'  +   str(int(z)) + '治愈' \
                for (x, y, z) in zip(df_hubei['确诊'], df_hubei['死亡'], df_hubei['治愈'])]
    
    data_ = go.Bar( 
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
    
    
    layout =go.Layout(title={ 'text' : '湖北城市确诊数柱状图',
                              'y':0.92,
                              'x':0.5,
                              'xanchor': 'center',
                              'yanchor': 'top'}, margin={"r":30,"t":30,"l":60,"b":80},
                       yaxis_title_text='确诊数',
                       height = 450, 
                       yaxis = dict(type = 'log') )
    
    return data_, layout





# line chart for confirmed suspected death and cured cases

def draw_line():
    
    trace0 = go.Scatter(x = df_time_agg['更新日'], y = df_time_agg['确诊'], name = '确诊病例', mode='lines+markers')
    trace1 = go.Scatter(x = df_time_agg['更新日'], y = df_time_agg['疑似'], name = '疑似病例', mode='lines+markers')
    trace2 = go.Scatter(x = df_time_agg['更新日'], y = df_time_agg['治愈'], name = '治愈病例', mode='lines+markers')
    trace3 = go.Scatter(x = df_time_agg['更新日'], y = df_time_agg['死亡'], name = '死亡病例', mode='lines+markers')
    
    data_ = [trace0, trace1, trace2, trace3]
    layout =go.Layout(title={ 'text' : '全国病例数时间走势图',
                              'y':0.92,
                              'x':0.5,
                              'xanchor': 'center',
                              'yanchor': 'top'}, margin={"r":30,"t":80,"l":80,"b":80},
                       yaxis_title_text='病例数',
                       xaxis_title_text='时间',
                       height = 450 )
    
    return data_, layout


data1, layout1 = draw_map()
data2, layout2 = draw_pie()
data3, layout3 = draw_bar()
data4, layout4 = draw_line()

map_dist = dcc.Graph(id = 'map_dist')
pie = dcc.Graph(id = 'pie', animate=True, figure= {'data': [data2], 'layout': layout2})
bar = dcc.Graph(id = 'bar', animate=True, figure= {'data': [data3], 'layout': layout3} )
line = dcc.Graph(id = 'line', animate=True, figure= {'data': data4, 'layout': layout4})


app = dash.Dash('test',  external_stylesheets=[dbc.themes.BOOTSTRAP])

data_dict = {"世界分布": df_World, "中国分布": df_China, 
             "湖北分布": df_hubei}


# arrange app layout
Title =  dbc.Row( [dbc.Col(
                    html.H2('疫情追踪',
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
                    

Dropdown = dbc.Row( [dbc.Col(
                    dcc.Dropdown(id='选择地图区域',
                                 options=[{'label': s, 'value': s}
                                          for s in data_dict.keys()],
                                 value="中国分布",
                                 multi=False,
                                 style = {'margin-left' : 25}
                                 ), width = 3 ),
                    dbc.Col(
                    html.Button('自动更新数据', id='button', n_clicks = 0,  style={'float': 'right'}), width = 2
                    ),
                    dbc.Col(
                    dcc.RadioItems(
                            options=[
                            {'label': '简体中文', 'value': 'CN'},
                            {'label': 'English', 'value': 'EN'}
                        ],
                        value='CN'
                    ), width = 2 )]
                    )
                    
                   
graphRow2 = dbc.Row([dbc.Col(map_dist, width=11, lg=6), dbc.Col(pie, width=11, lg=5)])
graphRow1 = dbc.Row([dbc.Col(line, width=11, lg=6), dbc.Col(bar, width=11, lg=5)])
Graphs = html.Div([graphRow1, graphRow2], id = 'graphs')

Loading = dcc.Loading(id="loading-1", children= Graphs , type="default")
# refresh every 6 hours 
Interval = dcc.Interval( id='interval-component', interval=21600*1000) 
app.layout = html.Div([ Title, Dropdown, Loading, Interval])
    


   
@app.callback(
     Output('map_dist','figure'),
    [Input('选择地图区域', 'value')])

def update_map( selected_item ):
    
    data_, layout = draw_map(selected_item)
    map_figure ={'data': [data_],'layout' : layout}
    
    return map_figure

if __name__ == '__main__':
    app.run_server(debug=True)