import dash_table
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import numpy as np
import dash_extensions as de

graph_height = 500
graph_width = 850



def load_data_world():
      
    world_raw = pd.read_pickle('world_raw.pkl')
    world = pd.read_pickle('world.pkl')
    world_current = pd.read_pickle('world_current.pkl')
    
    updatetime = np.datetime64("2021-03-07")
    
    return world_raw, world, world_current, updatetime


world_raw, world, world_current, updatetime = load_data_world()

continents = ['Africa', 'Asia',  'Europe', 
              'North America', 'Oceania', 'South America']

population = [ 1340598147, 4641054775, 747636026, 592072212, 43111704, 430759766]

world_current_continents = world_current.loc[world_current.country.isin(continents), ['country', 'cases']]
world_current_continents['population'] = population
world_current_continents.columns = ['continent', 'cases', 'population']
world_current_continents['cases per 1M'] = round(world_current_continents.cases / population * 1000000, 1)

global_sum = int(sum(world_current_continents.cases))

def comma_num_format( num ):
    return "{:,}".format(num)

world_current_continents['cases'] = world_current_continents['cases'].apply(comma_num_format)
world_current_continents['population'] = world_current_continents['population'].apply(comma_num_format)
world_current_continents['cases per 1M'] = world_current_continents['cases per 1M'].apply(comma_num_format)
world_current_continents = world_current_continents[['continent', 'cases', 'cases per 1M']]

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
                'frame':{'duration':40, 'redraw':True},
                'transition':{'duration':20},
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


data5, layout5, frames = map_frames()

map_frame = dcc.Graph(id = 'frame', animate=True, figure= {'data': data5, 'layout': layout5, 'frames': frames})

        
# arrange app layout

dropdown = dbc.DropdownMenu(
    children=[
        dbc.DropdownMenuItem("Global Stats", href="/haha"),
        dbc.DropdownMenuItem("US Stats", href="/global_situation"),
    ],
    nav = True,
    in_navbar = True,
    label = "Global Stats",
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src="https://prod.smassets.net/assets/cms/sm/uploads/sites/7/taller-header-coronavirus-resources-768x604.png", height="30px")),
                        dbc.Col(dbc.NavbarBrand("COVID-19 Dash Demo", className="ml-2")),
                    ],
                    align="start",
                    no_gutters=True,
                ),
                href="/home",
            ),
            dbc.NavbarToggler(id="navbar-toggler2"),
            dbc.Collapse(
                dbc.Nav(
                    # right align dropdown menu with ml-auto className
                    [dropdown], className="ml-auto", navbar=True
                ),
                id="navbar-collapse2",
                navbar=True,
            ),
        ]
    ),
    color="dark",
    dark=True,
    className="mb-4",
)





# 3. Add DBC component
card = dbc.Card(
    [
        dbc.Row(        # Row container
            [
                dbc.Col(        # Column container
                    de.Lottie(
        options = dict(loop = True, autoplay =True, rendererSettings = dict(preserveAspectRatio = 'xMidYMid slice')),
        width = '120%',
        height = '55%',
        url = 'https://assets8.lottiefiles.com/private_files/lf30_5P4pCA.json',
             ),
                    className="col-md-4",   # 4/12
                ),
                dbc.Col(        # Column container
                    dbc.CardBody(   # Card body
                        [
                            html.H4("World Cumulative Cases", className="card-title"),
                            html.H5("{:,}".format(global_sum), className="card-title"),
                            html.Small(     # Small text label
                                "last update on " + str(updatetime),
                                className="card-text text-muted",
                            ),
                        ]
                    ),
                    className="col-md-8",   # 8/12
                ),
            ],
            className="g-0 d-flex align-items-center",
        )
    ],
    className="mb-3",
    style={"maxWidth": "540px"},
)



source = dbc.Row([
            dbc.Col(dbc.Card(children=[html.H3(children='Original Datasets',
                                               className="text-center"),
                                       dbc.Row([dbc.Col(dbc.Button("Global", href="https://github.com/nytimes/covid-19-data",
                                                                   color="primary"), width = {"offset": 0.5},
                                                        className="mt-3"),
                                                dbc.Col(dbc.Button("US", href="https://covidtracking.com/data/api",
                                                                   color="primary"), width = {"offset": 1},
                                                        className="mt-3")], justify="center")
                                       ],
                             body=True, color="dark", outline=True)
                    , width=8, className="mb-4")
        ], className="mb-5")



card_table = dbc.Container( 
        
    [  
       dbc.Row(card),
       html.Br(),     
       dbc.Row(        # Put the column container list in the row container
        # Put the card container in the column container, and outline=True sets the simple outline sample color
           dbc.Col(dash_table.DataTable(data = world_current_continents.to_dict('records'), style_cell={'textAlign': 'center'},
                                        columns = [{"name": i, "id": i} for i in world_current_continents.columns]), 
                                        className="tb-1"
                   )
              ),
       html.Br(),  
       html.Br(),                
       source
    ]
)
    
graph = dbc.Container( dbc.Row(dbc.Col(map_frame) ) )

card_table_graph = dbc.Row([dbc.Col(card_table, width={"size": 2.5, "offset": 1}), 
                            dbc.Col(graph, width={"size": 6, "offset": 0.5}, lg={'size':6, 'offset' : 0.5}, xs=11, sm =11, md =11)])

# =============================================================================
# navigation_bar = dbc.Row( dbc.Col( navbar) )
# =============================================================================


# uncomment if single-page app
# =============================================================================
# app = dash.Dash('2019nCov-data',  external_stylesheets=[dbc.themes.BOOTSTRAP],
#                 meta_tags = [{'name': 'viewport', 'content' : 'width=device-width, initial-scale=1.0'}])
# =============================================================================

# =============================================================================
# def serve_layout():
#     app_layout = html.Div([ navigation_bar,    
#                        html.Br(),
#                        card_table_graph,
#                        ])
#     return app_layout
# =============================================================================

# change to app.layout if single page app
layout = html.Div([    html.Br(),
                       card_table_graph,
                       ])

# uncomment if single-page app
# =============================================================================
# if __name__ == '__main__':
#     app.run_server(debug=True)
# =============================================================================
