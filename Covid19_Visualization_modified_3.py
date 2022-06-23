import dash
import pandas as pd
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
import requests
import dash_extensions as de

# =============================================================================
# from flask import Flask
# =============================================================================

graph_height = 500
graph_width = 850


def load_data():
# =============================================================================
#     us_historic = pd.read_csv('us_historic.csv')
#     world_raw = pd.read_csv('world_raw.csv')
#     world = pd.read_csv('world.csv')
#     world_current = pd.read_csv('world_current.csv')
#     us_state_current = pd.read_csv('us_state_current.csv')
#     al_county_current = pd.read_csv('al_county_current.csv')
# =============================================================================
    
    
    us_historic = pd.read_pickle('us_historic.pkl')
    world_raw = pd.read_pickle('world_raw.pkl')
    world = pd.read_pickle('world.pkl')
    world_current = pd.read_pickle('world_current.pkl')
    us_state_current = pd.read_pickle('us_state_current.pkl')
    al_county_current = pd.read_pickle('al_county_current.pkl')
    
    
# =============================================================================
#     us_historic.Date = pd.to_datetime( us_historic.Date, format='%Y-%m-%d')
# =============================================================================
    
    updatetime = np.datetime64("2021-03-07")
    
    return us_historic, world_raw, world, world_current, us_state_current,  al_county_current, updatetime
    
    

def map_prep(geojson, locations, z, hovertext, center_lon, center_lat, zoom, updatetime, mapstyle = "satellite-streets", title = 'US'):
    
    # prepare token for Mapbox
    token = 'pk.eyJ1IjoiY2h1emhpY29uZyIsImEiOiJjazZoMG5tajIwNmh4M21ueGN0eXdtMmx6In0.kQscrYmKzfyLhN-YgENO0Q'
    
    data = go.Choroplethmapbox(geojson = geojson, locations = locations, 
                               z = z , hovertext = hovertext,
                               hoverinfo = 'text', colorscale = 'YlOrRd',
                               marker_line_width = 0.5, marker_line_color = 'rgb(169, 164, 159)',
                               colorbar=dict(
                                   title="Cases",
                                   titleside="top",
                                   tickmode="array",
                                   tickvals=np.arange(0, 7, 1),
                                   ticktext=["1", "10", "100", "1k", '10k', '100k', '1M'],
                                   ticks="outside"
                                    ))
    
    layout = go.Layout(mapbox = {'accesstoken': token, 'center':{'lon' : center_lon, 'lat': center_lat},'zoom': zoom,  'style' : mapstyle},
                  margin={"r":1,"t":45,"l":45,"b":30}, title = title + ' Case HeatMap',
                  plot_bgcolor = '#D3D3D3',
                  paper_bgcolor = '#D3D3D3',
                  annotations = [dict(
                      x=0.55,
                      y=0.03,
                      xref='paper',
                      yref='paper',
                      text='last update on ' + str(updatetime),
                      showarrow = False
                 )], #height = graph_height, width = graph_width 
        )
        
        
    return data, layout

# load map file
with urlopen('https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json') as response:
    states_geo = json.load(response)
    
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties_geo = json.load(response)    

with urlopen('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json') as response:
    countries_geo = json.load(response)



us_historic, world_raw, world, world_current, us_state_current,  al_county_current, updatetime = load_data( )



# map for confirmed cases

def draw_map( selected_item = "Case by state" ):
    
    if  selected_item == "Case by state":
        data_, layout = map_prep(geojson = states_geo, locations = us_state_current['code'],
                                  z = np.log10(us_state_current['cases']), hovertext = us_state_current['text'],
                                  center_lon = -95.7129, center_lat = 37.0902,
                                  zoom = 2.5, updatetime = updatetime,  mapstyle = 'basic' )
                 
    else:
        data_, layout = map_prep(geojson = counties_geo, locations = al_county_current['code'],
                                  z = np.log10(al_county_current['cases']), hovertext = al_county_current['text'],
                                  center_lon = -86.9023, center_lat = 32.9,
                                  zoom = 5.5, updatetime = updatetime,  mapstyle = 'basic', title = 'AL')
            
    return data_, layout


# Pie chart of Top k states with most confirmed cases
# set value for k

def draw_pie( date = updatetime ):
    
    data_of_date = us_historic.loc[us_historic.Date == date, ['positive', 'negative', 'pending']]
    labels = ['Postive Cumulative' , 'Negative Cumulative', 'Pending']
    values = [ int(data_of_date['positive']), int(data_of_date['negative']), int(data_of_date['pending'])]
    
    data_ = go.Pie(labels=labels, values=values, textinfo='label+ percent' ) 
    layout = go.Layout( title={
            'text': 'US tested cases breakdown on ' + str(date).split()[0],
            'y':0.98,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
            plot_bgcolor = '#D3D3D3',
            paper_bgcolor = '#D3D3D3',
            margin={"r":30,"t":40,"l":40,"b":30}, 
            # height = graph_height, width = graph_width
            ) 
        
    return data_, layout


# line chart for confirmed suspected death and cured cases
def draw_line():
    
    trace0 = go.Scatter(x = us_historic['Date'], y = us_historic['Positive Increase'], name = 'Positive Increase', mode='lines+markers')
    trace1 = go.Scatter(x = us_historic['Date'], y = us_historic['Negative Increase'], name = 'Negative Increase', mode='lines+markers')
    trace2 = go.Scatter(x = us_historic['Date'], y = us_historic['Hospitalized Increase'], name = 'Hospitalized Increase', mode='lines+markers')
    trace3 = go.Scatter(x = us_historic['Date'], y = us_historic['Death Increase'], name = 'Death Increase', mode='lines+markers')
    
    data_ = [trace1, trace0, trace2, trace3]
    
    layout =go.Layout(title={ 'text' : 'US case daily increase',
                              'y':0.92,
                              'x':0.5,
                              'xanchor': 'center',
                              'yanchor': 'top'}, margin={"r":30,"t":80,"l":80,"b":80},
                       yaxis_title_text='case increase',
                       xaxis_title_text='date',
                       plot_bgcolor = '#D3D3D3',
                       paper_bgcolor = '#D3D3D3',
                       legend=dict( yanchor="top",
                                    y=0.99,
                                    xanchor="left",
                                    x=0.01
                                )
                      # height = graph_height, width = graph_width 
                      )
    
    return data_, layout

# Bar charts for city data in Hubei


def draw_bar(selected_item = "Case by state" ):
    
    k = 15
    
    if selected_item == "Case by AL county":
        data_set = al_county_current
        title = 'Top 15 AL counties by cases'
        bar_x = 'county'
        #color_scale = 'blues'
    else:
        data_set = us_state_current
        title = 'Top 15 US states by cases'
        bar_x = 'state'
        #color_scale = 'reds'
        
    data_set_sort = data_set.sort_values(by = 'cases', ascending = False)
    data_topk = data_set_sort.iloc[:k, :]
        
    # create hover txt
    hovertxt = [ str(int(x)) +' cases' +  '<br>'  +   str(int(y)) + ' deaths'  +  '<br>' \
                for (x, y) in zip(data_topk['cases'], data_topk['deaths'])]
    
    data_ = go.Bar( 
        x = data_topk[bar_x],
        y = data_topk['cases'],
        hoverinfo = 'x+text',
        hovertext = hovertxt,
        marker={'color': np.log10(data_topk['deaths']),
                'colorscale' :  'reds',  #color_scale,
                'showscale': True,
                'colorbar.title': 'deaths',
                'colorbar.tickmode':"array",
                'colorbar.tickvals': np.arange(0, 6, 1),
                'colorbar.ticktext': ["1", "10", "100", "1k", '10k', '100k'],
                } 
        )
         
        
    
    layout =go.Layout(title={ 'text' : title,
                              'y':0.92,
                              'x':0.5,
                              'xanchor': 'center',
                              'yanchor': 'top'}, margin={"r":30,"t":30,"l":60,"b":80},
                       yaxis_title_text='cases',
                     #  height = graph_height, width = graph_width,
                       plot_bgcolor = '#D3D3D3',
                       paper_bgcolor = '#D3D3D3',
                       yaxis = dict(type = 'log') )
    
    return data_, layout


def map_frames():
    token = 'pk.eyJ1IjoiY2h1emhpY29uZyIsImEiOiJjazZoMG5tajIwNmh4M21ueGN0eXdtMmx6In0.kQscrYmKzfyLhN-YgENO0Q'
    
    frames = [{   
    'name':'frame_{}'.format(day),
    'data':[{
        'type':'scattermapbox',
        'lat':world.loc[world.date == day, 'lat'],
        'lon':world.loc[world.date == day, 'lon'],
        'hovertext' : world.loc[world.date == day, 'text'],
        'hoverinfo' : 'text',
        'marker':go.scattermapbox.Marker(
            size=world.loc[world.date == day, 'size'],
        ),
    }],
    
    } for day in world_raw.date]  
        
    
    sliders = [{
    'transition':{'duration': 0},
    'x':0.08, 
    'len':0.88,
    'currentvalue':{'font':{'size':15}, 'prefix':'📅 ', 'visible':True, 'xanchor':'center'},  
    'steps':[
        {
            'label':str(day).split()[0],
            'method':'animate',
            'args':[
                ['frame_{}'.format(day)],
                {'mode':'immediate', 'frame':{'duration':100, 'redraw': True}, 'transition':{'duration':50}}
              ],
        } for day in world_raw.date]
    }]

    play_button = {
    'type':'buttons',
    'showactive':True,
    'x':0.045, 'y':-0.08,
    'buttons':[{ 
        'label':'🎬', # Play
        'method':'animate',
        'args':[
            None,
            {
                'frame':{'duration':100, 'redraw':True},
                'transition':{'duration':50},
                'fromcurrent':True,
                'mode':'immediate',
            }
        ]
    }]
    },
        
    data = frames[0]['data']

    # Adding all sliders and play button to the layout
    layout = go.Layout(
        sliders=sliders,
        updatemenus=play_button,
        title = 'World Case Map by Date',
        height = graph_height + 100, 
       # width = graph_width + 300, 
        plot_bgcolor = '#D3D3D3',
        paper_bgcolor = '#D3D3D3',
        mapbox={
            'accesstoken':token,
            'center':{"lat": 37.86, "lon": -30},
            'zoom':1.7,
            'style':'streets',
        }
    )
    
    return data, layout, frames




# =============================================================================
# data1, layout1 = draw_map()
# data2, layout2 = draw_pie()
# =============================================================================
data3, layout3 = draw_bar()
data4, layout4 = draw_line()
data5, layout5, frames = map_frames()

map_dist = dcc.Graph(id = 'map_dist')
pie = dcc.Graph(id = 'pie')
bar = dcc.Graph(id = 'bar' )
line = dcc.Graph(id = 'line', animate=True, figure= {'data': data4, 'layout': layout4})
map_frame = dcc.Graph(id = 'frame', animate=True, figure= {'data': data5, 'layout': layout5, 'frames': frames})

app = dash.Dash('2019nCov-data',  external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags = [{'name': 'viewport', 'content' : 'width=device-width, initial-scale=1.0'}])

data_dict = {"Case by state": us_state_current, 
             "Case by AL county": al_county_current}


lottie = html.Div(de.Lottie(
        options = dict(loop = True, autoplay =True, rendererSettings = dict(preserveAspectRatio = 'xMidYMid slice')),
        width = '35%',
        height = '10%',
        url = 'https://assets8.lottiefiles.com/private_files/lf30_5P4pCA.json',
             )) 

# =============================================================================
# image = html.Img(
#         src = 'https://www.cbp.gov/sites/default/files/covidimage2.png',
#         style = {
#                 'height': '28%',
#                 'width' : '45%',
#                 'float' : 'right',
#                 'position' : 'relative',
#                 'margin-top' : 20 },
#         )
# =============================================================================

# arrange app layout
Title =  dbc.Row( [dbc.Col(
                    html.H2('Covid19 Tracker Demo',
                            style={'float': 'right',
                                   }
                            ), width = 7, align="start"
                          )])
                    
Lottie = dbc.Row( [dbc.Col(width = 7),  dbc.Col(lottie, width = 5, align = 'end')])

Dropdown = dbc.Row( [dbc.Col(
                    dcc.Dropdown(id='Choose Analysis',
                                 options=[{'label': s, 'value': s}
                                          for s in data_dict.keys()],
                                 placeholder = 'Choose analysis level',
                                 value="Case by state",
                                 multi=False,
                                 style = {'margin-left' : 0}
                                 ), width = {"size": 2, "offset": 1} ),
                    dbc.Col(
                    dcc.ConfirmDialogProvider(id = 'update provider',
                    children = html.Button('Auto-Update', id='button', n_clicks = 0,  style={'float': 'right'}),
                    message='Swithing on Auto-Update may take couple of minutes. Are you sure you want to continue?',
                    submit_n_clicks = 0), width = 3)]
                    )
                    
                    
Loading = dcc.Loading(id="loading-1", children= bar, type="cube", fullscreen = True)      




                                          
                   
graphRow1 = dbc.Row([dbc.Col(Loading, width={'size':5, 'offset' : 1}, lg= {'size':5, 'offset' : 1}, xs=11, sm =11, md =11), 
                     dbc.Col( map_dist, width={'size':5, 'offset' : 0}, lg={'size':5, 'offset' : 0}, xs=11, sm =11, md =11)],  justify="start")
graphRow2 = dbc.Row([dbc.Col(line, width={'size':5, 'offset' : 1}, lg={'size':5, 'offset' : 1}, xs=11, sm =11, md =11),
                     dbc.Col(pie, width={'size':5, 'offset' : 0}, lg={'size':5, 'offset' : 0}, xs=11, sm =11, md =11)],  justify="start")
graphRow3 = dbc.Row([dbc.Col(map_frame, width={"size": 6, "offset": 1}, lg={'size':6, 'offset' : 1}, xs=11, sm =11, md =11),
                     dbc.Col( width= 4, lg=3, xs= 7, sm =7, md =7)], justify="start",  align="center",)

Graphs = html.Div([graphRow1,
                   html.Br(),
                   html.Br(),
                   graphRow2, 
                   html.Br(),
                   html.Br(),
                   graphRow3], id = 'graphs')


# refresh every 6 hours 
Interval = dcc.Interval( id='interval-component', interval=21600*1000) 
# =============================================================================
# app.layout = html.Div([ Title, Dropdown, 
#                        html.Br(),
#                        html.Br(),
#                        Graphs,
#                        # Loading, 
#                        Interval
#                        ])
# =============================================================================
    
def serve_layout():
    app_layout = html.Div([ Title, Lottie, Dropdown, 
                       html.Br(),
                       html.Br(),
                       Graphs,
                       Interval
                       ])
    return app_layout

app.layout = serve_layout
   
@app.callback(
     [Output('map_dist','figure'),
     Output('bar','figure')],
    [Input('Choose Analysis', 'value')])

def update_map_bar( selected_item ):
    
    data_, layout = draw_map(selected_item)
    map_figure ={'data': [data_],'layout' : layout}
    
    data_2, layout2 = draw_bar(selected_item)
    bar_figure ={'data': [data_2],'layout' : layout2}
    
    return map_figure, bar_figure


@app.callback(
     Output('pie','figure'),
    [Input('line', 'hoverData')])

def update_pie( hov_data ):
    
    if hov_data is None:
        data_, layout = draw_pie( )
        pie_figure= {'data': [data_], 'layout': layout}
    
    else:
        #print(hov_data)
        date = hov_data['points'][0]['x']
        data_, layout = draw_pie( date )
        pie_figure= {'data': [data_], 'layout': layout}
    
    return pie_figure




@app.callback(
     Output('graphs','children'),
    [Input('interval-component', 'n_intervals'),
     Input('update provider', 'submit_n_clicks')])
def update_graphs( n, submit_n_clicks):
    
    raise PreventUpdate
# =============================================================================
#     # initialize the app with update off
#     if submit_n_clicks == 0:
#         raise PreventUpdate
#         
#     else:
#         us_historic, world_raw, world,  world_current, us_state_current,  al_county_current, max_date = update_obd_values( )
#         
#         data1, layout1 = draw_map()
#         data2, layout2 = draw_pie()
#         data3, layout3 = draw_bar()
#         data4, layout4 = draw_line()
#         data5, layout5, frames = map_frames()
#         
#         map_dist = dcc.Graph(id = 'map_dist', figure= {'data': [data1], 'layout': layout1})
#         pie = dcc.Graph(id = 'pie', animate=True, figure= {'data': [data2], 'layout': layout2})
#         bar = dcc.Graph(id = 'bar', animate=True, figure= {'data': [data3], 'layout': layout3} )
#         line = dcc.Graph(id = 'line', animate=True, figure= {'data': data4, 'layout': layout4})
#         
#         Loading = dcc.Loading(id="loading-1", children= bar, type="default", fullscreen = True)   
#         
#         graphRow1 = dbc.Row([dbc.Col(map_dist, width=11, lg=6), dbc.Col(Loading, width=11, lg=5)],  justify="center")
#         graphRow2 = dbc.Row([dbc.Col(line, width=11, lg=6), dbc.Col(pie, width=11, lg=5)],  justify="center")
#         graphRow3 = dbc.Row([dbc.Col(map_frame, width={"size": 17, "offset": 0}, lg=8), dbc.Col( width=5, lg=3)], justify="center")
# 
#         Graphs = html.Div([graphRow1,
#                            html.Br(),
#                            html.Br(),
#                            graphRow2, 
#                            html.Br(),
#                            html.Br(),
#                            graphRow3], id = 'graphs')
#         
#         return Graphs
# =============================================================================
    

if __name__ == '__main__':
    app.run_server(debug=True)