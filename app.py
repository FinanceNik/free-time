# Import external libraries
import dash_bootstrap_components as dbc
import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table
import dash_ag_grid as dag
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pandas as pd

# import local libraries
import Styles
import data_handler as dh
import configuration as cfg

base_path = '/time-management'
# Create the Flask app
server = Flask(__name__)
app = dash.Dash(__name__, suppress_callback_exceptions=True,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                url_base_pathname='/', assets_folder='assets')
app.title = 'Free Time'

# Configure Flask-SQLAlchemy
app.server.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///time_management.db'  # Adjust the URI as needed
app.server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking

# Create the SQLAlchemy object and associate it with the Flask app
db = SQLAlchemy(app.server)
with app.server.app_context():
    class CreateDBEntry(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        date = db.Column(db.String(255), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        start_time = db.Column(db.String(255))
        end_time = db.Column(db.String(255))
        break_time = db.Column(db.String(255))
        total_time = db.Column(db.String(255))
        employer = db.Column(db.String(255))
        remarks = db.Column(db.String(255))


    db.create_all()


def get_callback_times():
    create_db_entry = CreateDBEntry.query.all()
    df = pd.DataFrame([(record.date,
                        record.start_time,
                        record.end_time,
                        record.break_time,
                        record.total_time,
                        record.employer,
                        record.remarks) for record in create_db_entry],
                      columns=['Date', 'Start Time', 'End Time', 'Break Time', 'Total Time', 'Employer', 'Remarks'])
    df = df[::-1]
    return df


# Callback to update the table based on date range and employer
@app.callback(
    Output('invoice-table', 'data'),
    Output('invoice-table', 'columns'),
    Input('filter-button', 'n_clicks'),
    State('date-range-picker', 'start_date'),
    State('date-range-picker', 'end_date'),
    State('employer-dropdown', 'value'),
)
def update_invoice_table(n_clicks, start_date, end_date, selected_employer):
    if n_clicks is None:
        return dash.no_update, dash.no_update

    # Convert the input dates to datetime objects
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Add one day to include end date

    # Query the database for entries within the date range and optional employer condition
    if selected_employer:
        entries = CreateDBEntry.query.filter(
            CreateDBEntry.date.between(start_datetime, end_datetime),
            CreateDBEntry.employer == selected_employer
        ).all()
    else:
        entries = CreateDBEntry.query.filter(CreateDBEntry.date.between(start_datetime, end_datetime)).all()

    # Convert the result to a list of dictionaries for easier use in Dash
    entries_list = [
        {
            'date': entry.date,
            'start_time': entry.start_time,
            'end_time': entry.end_time,
            'break_time': entry.break_time,
            'total_time': entry.total_time,
            'employer': entry.employer,
            'remarks': entry.remarks
        }
        for entry in entries
    ]

    # Check if entries_list is not empty
    if not entries_list:
        return [], []

    # Convert columns to the required format for dash_table.DataTable
    columns = [{'name': col, 'id': col} for col in entries_list[0].keys()]
    return entries_list, columns


def get_entries_between_dates_and_employer(start_date, end_date, employer=None):
    # Convert the input dates to datetime objects
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Add one day to include end date

    # Query the database for entries within the date range and optional employer condition
    if employer:
        entries = CreateDBEntry.query.filter(
            CreateDBEntry.date.between(start_datetime, end_datetime),
            CreateDBEntry.employer == employer
        ).all()
    else:
        entries = CreateDBEntry.query.filter(CreateDBEntry.date.between(start_datetime, end_datetime)).all()

    # Convert the result to a list of dictionaries for easier use in Dash
    entries_list = [
        {
            'id': entry.id,
            'date': entry.date,
            'start_time': entry.start_time,
            'end_time': entry.end_time,
            'break_time': entry.break_time,
            'total_time': entry.total_time,
            'employer': entry.employer,
            'remarks': entry.remarks
        }
        for entry in entries
    ]

    return entries_list


sidebar = html.Div(
    [
        html.H1(f"Free Time", style={'fontSize': '36px', 'fontWeight': 'bold'}),
        html.Hr(style={'borderColor': Styles.greys[3]}),
        html.H2("Section", className="lead", style={'fontSize': '28px'}),
        html.Hr(style={'borderColor': Styles.greys[3]}),
        dbc.Nav(
            [
                dbc.NavLink("Home", href=f"{base_path}/", active="exact"),
                dbc.NavLink("Enter Time", href=f"{base_path}/enter-time", active="exact"),
                dbc.NavLink("Create Invoice", href=f"{base_path}/invoice-creator", active="exact"),
                dbc.NavLink("About", href=f"{base_path}/about", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=Styles.SIDEBAR_STYLE,
)

content = html.Div(id="page-content", style=Styles.CONTENT_STYLE)

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == f"{base_path}/":
        df = get_callback_times()
        return html.Div(children=[
            html.H1("Worktime Management", style={'fontSize': '36px', 'fontWeight': 'bold'}),
            html.Hr(),
            html.Div([
                dag.AgGrid(
                    id="getting-started-themes-example",
                    columnDefs=[{"headerName": x, "field": x, 'sortable': True} for x in df.columns],
                    rowData=df.to_dict('records'),
                    columnSize="sizeToFit",
                    style={'height': '800px'}
                )
            ]),
            html.Hr(),
        ])

    elif pathname == f"{base_path}/enter-time":
        return html.Div([
            html.H1("Time Tracker", style={'fontSize': '36px', 'fontWeight': 'bold'}),
            html.Hr(),
            html.Div([dcc.Input(id='date-input',
                                type='text',
                                placeholder='Date',
                                className='form-control',
                                value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))], className="mt-3",
                     style={"width": Styles.WIDTH}),
            html.Div([dcc.Input(id='start-time-input',
                                type='text',
                                placeholder='Start Time',
                                className='form-control',
                                value=datetime.now().strftime('%H:%M:%S'))], className="mt-3",
                     style={"width": Styles.WIDTH}),
            html.Div([dcc.Input(id='end-time-input',
                                type='text',
                                placeholder='End Time',
                                className='form-control',
                                value=datetime.now().strftime('%H:%M:%S'))], className="mt-3",
                     style={"width": Styles.WIDTH}),
            html.Div([dcc.Input(id='break-time-input',
                                type='text',
                                className='form-control',
                                placeholder='Break Time')], className="mt-3", style={"width": Styles.WIDTH}),
            html.Div([dcc.Dropdown(
                id='employer-input',
                options=cfg.employers_list(),
                value=cfg.employers_list()[0]['label'],
                className='form-control',
                placeholder='Employer'
            )], className="mt-3", style={"width": Styles.WIDTH}),
            html.Div([dcc.Textarea(
                id='remarks-input',
                value='',
                className='form-control',
                placeholder='Remarks',
                style={'height': '100px', 'overflowY': 'auto'},  # Set the height to 100px and allow overflow
            )], className="mt-3", style={"width": Styles.WIDTH}),
            html.Br(),
            html.Div([
                html.Button('Submit Worktime Entry', id='submit-button', className='btn btn-primary'),
                html.Div(id='connection-status'),
            ]),
            html.Hr(),
        ])

    elif pathname == f"{base_path}/invoice-creator":
        return html.Div([
            html.H1("Invoice Creator", style={'fontSize': '36px', 'fontWeight': 'bold'}),
            html.Hr(),
            html.H4("Select Date Range:"),
            dcc.DatePickerRange(
                id='date-range-picker',
                display_format='YYYY-MM-DD',
                start_date='',
                end_date='',
            ),
            html.Br(),
            html.Br(),
            html.H4("Select Employer:"),
            dcc.Dropdown(
                id='employer-dropdown',
                options=[
                    {'label': 'Employer 1', 'value': 'Employer 1'},
                    {'label': 'Employer 2', 'value': 'Employer 2'},
                    # Add other employers as needed
                ],
                placeholder='Select Employer',
                className='form-control',
            ),
            html.Br(),
            html.Button('Select Your Work Sessions', id='filter-button', className='btn btn-primary'),
            html.Hr(),
            html.H4("Your Work Sessions in selected Period:"),
            dash_table.DataTable(id='invoice-table'),
            html.Hr(),

        ])

    elif pathname == f"{base_path}/about":
        return html.Div([])


# Define callback to handle button click and print connection details
@app.callback(
    Output('connection-status', 'children'),
    [Input('submit-button', 'n_clicks')],
    [State('date-input', 'value'),
     State('start-time-input', 'value'),
     State('end-time-input', 'value'),
     State('break-time-input', 'value'),
     State('employer-input', 'value'),
     State('remarks-input', 'value')]
)
def time_entry_form(n_clicks, date, start_time, end_time, break_time, employer, remarks):
    if n_clicks is not None:
        create_entry = CreateDBEntry(date=date,
                                     start_time=start_time,
                                     end_time=end_time,
                                     break_time=break_time,
                                     total_time=dh.time_difference(start_time, end_time),
                                     employer=employer,
                                     remarks=remarks)
        db.session.add(create_entry)
        db.session.commit()
        return (f"Created entry with values: {date}, {start_time}, {end_time}, {break_time}, "
                f"{dh.time_difference(start_time, end_time)}, {employer}, {remarks}")


if __name__ == "__main__":
    app.run_server(host='0.0.0.0', port=8080, debug=True)
