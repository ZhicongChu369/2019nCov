import dash
import dash_bootstrap_components as dbc

# bootstrap theme
# https://bootswatch.com/lux/
# external_stylesheets = [dbc.themes.LUX]

app = app = dash.Dash('2019nCov-data',external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags = [{'name': 'viewport', 'content' : 'width=device-width, initial-scale=1.0'}])

server = app.server
app.config.suppress_callback_exceptions = True
