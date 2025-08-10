#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# DASH Framework for Jupyter 
from jupyter_dash import JupyterDash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import dash_leaflet as dl
import pandas as pd
from pymongo import MongoClient




# In[ ]:


# Enhancement: Input validation function for MongoDB queries
def validate_input(data):
    if not isinstance(data, dict):
        raise ValueError("Input must be a dictionary.")
    allowed_rescue_types = [
        "Water Rescue",
        "Mountain or Wilderness Rescue",
        "Disaster or Individual Tracking",
        "All"
    ]
    if "rescueType" in data and data["rescueType"] not in allowed_rescue_types:
        raise ValueError("Invalid rescue type selected.")

# Enhancement: Pseudocode access control logic (admin vs. user)
def get_animals_by_role(user_role, user_id=None):
    """
    Demonstrates how access control could work:
    Admins see all records, regular users see only their own.
    """
    if user_role == "admin":
        return shelter.read({})
    else:
        return shelter.read({"userId": user_id})


# In[ ]:


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
            validate_input(query)  # Enhancement: Validate query input
            return list(self.collection.find(query))
        except Exception as e:
            print(f"An error occurred during the read operation: {e}")
            return []

    def filter_by_rescue_type(self, rescue_type):
        """Fetch animals based on rescue type."""
        query = {"rescueType": rescue_type}
        return self.read(query)


# In[ ]:


# Instantiate the CRUD module
username = "aacuser"
password = "Takhmina123"  # Replace with your password
shelter = AnimalShelter(username, password)

# Fetch initial data
df = pd.DataFrame.from_records(shelter.read({}))
if '_id' in df.columns:
    df.drop(columns=['_id'], inplace=True)


# In[ ]:


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


# In[ ]:


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


# In[ ]:


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


# In[ ]:


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


# In[ ]:


# Run the app
app.run_server(debug=True, port=8061)


# ## Future Enhancement: SQL Migration Plan
# 
# This dashboard currently uses MongoDB, a NoSQL database. To improve schema normalization, query performance, and enforce foreign key constraints, the system could be migrated to MySQL.
# 
# ### Database Improvements
# - Normalize data into separate tables:
#   - `animals` (animal_id, name, breed_id, rescue_type_id, user_id)
#   - `breeds` (breed_id, breed_name)
#   - `rescue_types` (rescue_type_id, type_name)
#   - `users` (user_id, username, role)
# - Apply indexes on rescue_type, breed, and user_id columns.
# 
# ### Example SQL Query:
# ```sql
# SELECT * FROM animals
# JOIN rescue_types ON animals.rescue_type_id = rescue_types.rescue_type_id
# WHERE rescue_types.type_name = 'Water Rescue';
# 
