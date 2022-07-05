# Import necessary libraries 
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# Connect to main app.py file
from app import app

# Connect to your app pages
from pages import page_us, page_world

# Connect the navbar to the index
import dash_bootstrap_components as dbc 




navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src="https://prod.smassets.net/assets/cms/sm/uploads/sites/7/taller-header-coronavirus-resources-768x604.png", height="40px")),
                        dbc.Col(dbc.NavbarBrand("COVID-19 Dash Demo", className="ml-2")),
                    ],
                    align="start",
                    no_gutters=True,
                ),
                href="/page_world",
            ),
            html.Div([
                dcc.Link('Global Stats |', href="/page_world", style = {'color' : 'white'}),
                dcc.Link('| US Stats', href="/page_us", style = {'color' : 'white'})], className = 'row'
            ),
        ]
    ),
    color="dark",
    dark=True,
    className="mb-4",
)


navigation_bar = dbc.Row( dbc.Col( navbar) )


# Define the index page layout
app.layout = html.Div([dcc.Location(id='url', refresh=False),
    navigation_bar, 
    html.Div(id='page-content'), 
])

# Create the callback to handle mutlipage inputs
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/page_us':
        return page_us.layout
    else: 
        return page_world.layout



# Run the app on localhost:8050
if __name__ == '__main__':
    app.run_server(debug=True)