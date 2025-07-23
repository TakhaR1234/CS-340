#!/usr/bin/env python
# coding: utf-8

# In[1]:


# DASH Framework for Jupyter
from jupyter_dash import JupyterDash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import dash_leaflet as dl
import pandas as pd
from pymongo import MongoClient


# CRUD Module
class AnimalShelter(object):
    """ CRUD operations for Animal collection in MongoDB """

    def __init__(self, user, password, host='nv-desktop-services.apporto.com', port=32508, db='AAC', col='animals'):
        self.client = MongoClient(f'mongodb://{user}:{password}@{host}:{port}')
        self.database = self.client[db]
        self.collection = self.database[col]

    def read(self, query):
        """Method to query documents from the MongoDB collection."""
        try:
            return list(self.collection.find(query))
        except Exception as e:
            print(f"An error occurred during the read operation: {e}")
            return []

    def filter_by_rescue_type(self, rescue_type):
        """Fetch animals based on rescue type."""
        query = {"rescueType": rescue_type}
        return self.read(query)


# Instantiate the CRUD module
username = "aacuser"
password = "YourSecurePassword123"  # Replace with your password
shelter = AnimalShelter(username, password)

# Fetch initial data
df = pd.DataFrame.from_records(shelter.read({}))
if '_id' in df.columns:
    df.drop(columns=['_id'], inplace=True)

# Initialize the Dash app
app = JupyterDash(__name__)

# Define the layout
app.layout = html.Div([
    html.Center(html.H1("Animal Outcomes Dashboard")),
    html.Hr(),
    # Filter options
    html.Div([
        dcc.RadioItems(
            id='filter-rescue-type',
            options=[
                {'label': 'Water Rescue', 'value': 'Water Rescue'},
                {'label': 'Mountain/Wilderness Rescue', 'value': 'Mountain or Wilderness Rescue'},
                {'label': 'Disaster/Tracking', 'value': 'Disaster or Individual Tracking'},
                {'label': 'Reset', 'value': 'All'}
            ],
            value='All',
            labelStyle={'display': 'inline-block'}
        )
    ]),
    html.Hr(),
    # Data Table
    dash_table.DataTable(
        id='datatable-id',
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        page_size=10,
        style_table={'height': '300px', 'overflowY': 'auto'},
        row_selectable="single",
        style_cell={'textAlign': 'left', 'padding': '5px'},
    ),
    html.Hr(),
    # Charts and Map
    html.Div([
        dcc.Graph(id='bar-chart-id'),
        html.Div(id='map-id', className='col s12 m6'),
    ])
])


# Callbacks for filtering data
@app.callback(
    Output('datatable-id', 'data'),
    [Input('filter-rescue-type', 'value')]
)
def update_table(selected_filter):
    if selected_filter == 'All':
        filtered_data = shelter.read({})
    else:
        filtered_data = shelter.filter_by_rescue_type(selected_filter)
    return pd.DataFrame.from_records(filtered_data).to_dict('records')


# Callback for geolocation map
@app.callback(
    Output('map-id', "children"),
    [Input('datatable-id', "derived_virtual_data"),
     Input('datatable-id', "derived_virtual_selected_rows")]
)
def update_map(viewData, selected_rows):
    if not viewData:
        return []
    dff = pd.DataFrame.from_dict(viewData)
    row = selected_rows[0] if selected_rows else 0
    return [
        dl.Map(style={'width': '1000px', 'height': '500px'},
               center=[30.75, -97.48], zoom=10, children=[
            dl.TileLayer(id="base-layer-id"),
            dl.Marker(position=[dff.iloc[row, 13], dff.iloc[row, 14]], children=[
                dl.Tooltip(dff.iloc[row, 4]),
                dl.Popup([
                    html.H1("Animal Name"),
                    html.P(dff.iloc[row, 9])
                ])
            ])
        ])
    ]


# Callback for bar chart
@app.callback(
    Output('bar-chart-id', 'figure'),
    [Input('datatable-id', 'data')]
)
def update_bar_chart(data):
    if not data:
        return {'data': [], 'layout': {'title': 'Preferred Dog Breeds'}}
    dff = pd.DataFrame.from_records(data)
    breed_counts = dff['breed'].value_counts()
    return {
        'data': [
            {'x': breed_counts.index, 'y': breed_counts.values, 'type': 'bar', 'name': 'Breeds'}
        ],
        'layout': {
            'title': 'Preferred Dog Breeds',
            'xaxis': {'title': 'Breed'},
            'yaxis': {'title': 'Count'}
        }
    }


# Run the app
app.run_server(debug=True, port=8061)


# In[ ]:




