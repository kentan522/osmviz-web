'''
dcc - Dash Core Components - include high-level components like dropdowns, graphs, markdown blocks etc.
html - For setting html divs etc.
Dash - for initialising the web app
'''
from dash import Dash, html, dcc
from dash import Input, Output, State # To work with callbacks
from dash import dash_table # Working with tables
import plotly.express as px
import pandas as pd
from multiprocessing import Process, Queue
from examples.multiple_trackvizs import main
import time
import contextlib, io
from dash_extensions import DeferScript
import json
import os, shutil
import logging

############################################################################################
###--------------------### GLOBAL QUEUE OBJECTS FOR DATA TRANSFER ###--------------------###
############################################################################################
def globalQueueInit():
    global dataQueueInput, dataQueueOutput, consoleQueue, commandQueue
    dataQueueInput = Queue()
    dataQueueOutput = Queue()
    consoleQueue = Queue()
    commandQueue = Queue()

globalQueueInit()

############################################################################
###--------------------### GLOBAL BUTTON COUNTERS ###--------------------###
############################################################################
def buttonCountInit():
    global prevSeshStart, prevSeshStop, clearButtonCount, sendCommandCount
    prevSeshStart = 0
    prevSeshStop = 0
    clearButtonCount = 0
    sendCommandCount = 0    

buttonCountInit()

######################################################################
###--------------------### GLOBAL PROCESSES ###--------------------###
######################################################################

# Initialise chronosProcess as a process to prevent referencing errors
chronosProcess = Process(target=main, args=(dataQueueInput, dataQueueOutput, consoleQueue))

########################################################################
###--------------------### DEFINED FUNCTIONS ### --------------------###
########################################################################

###--------------------### HTML STUFF ###--------------------###
def control_panel_header():
    """
    A Div containing control panel title and description
    """
    return html.Div(
        id="control-panel-header",
        children=[
            html.H5("Chronos: A Multi-Agent Simulation Framework"),
            html.H3("Control Panel"),
            html.Div(
                id="intro",
                children="The control panel defines the initialisation of Chronos.",
            ),
            html.Br(), 
            html.Div(
                id='hidden-div-refresh', 
                style={'display':'none'}
            )
        ],
    )

def control_panel_body():
    '''
    - The control panel defines the agents/logics/tasks
    - Allows number of agents to be altered in real time
    - Allows the changing of time step and simulation speed etc.
    '''

    agent_list = ['Agent Group 1', 'Agent Group 2', 'Agent Group 3']

    return html.Div( # Main control panel 
        id="control-panel-main-body",
        children=[
            # Agent panel
            html.Div(
                id="agent-control-main",
                children=[
                    html.Div(
                        className="agent-control",
                        children=[
                            html.P('Select no. of agents'),
                            dcc.Input(
                                id='agent-input-no', 
                                type='number', 
                                min=1, max=10, step=1,
                            )
                        ]
                    ),
                    html.Div(
                        className="agent-control",
                        children=[
                            html.P('Select agent group'),
                            dcc.Dropdown(
                                id="agent-select",
                                options=[{"label": i, "value": i} for i in agent_list],
                            )
                        ]
                    )
                ]
            ),
            html.Br(),
            
            # Button to add agent
            html.Button('Add agent(s)', id='button-1'),
            html.Div(
                id="hidden-div-dialog",
                style=dict(display='none'),
                children=[
                    html.P('Some of the fields are left empty!')
                ]
            ),

            html.Br(),
            html.Br(),

            # Time step panel
            html.P("Time-step (dT)"),
            dcc.Slider(
                1, 15, 1,
                value=1,
                id="time-step-slider"
            ),

            html.Br(),
            html.Br(),

            # Button to START chronos simulation
            html.Button('Initialise Chronos Simulation', id='button-2'),
            html.Div(
                id="hidden-div-dialog-2",
                style=dict(display='none'),
                children=[
                    html.P('Chronos has started!')
                ]
            ),

            html.Br(),

            # Button to STOP chronos simulation
            html.Button('STOP', id='button-4'),
            html.Div(
                id="hidden-div-dialog-3",
                style=dict(display='none'),
                children=[
                    html.P('Chronos has stopped!')
                ]
            )
        ]
    )

def control_panel_data_table():
    # Header and cell styles
    table_header_style = {
        "backgroundColor": "#afbdcf",
        "color": "black", 
        "textAlign": "center"
    }

    table_cell_style = {
        "padding-right": 20,
        "padding-left": 20
    }

    emptyList = []
    df = pd.DataFrame({
            "Agent ID": emptyList,
            "Agent Group": emptyList,
            "Current Task": emptyList
            })   

    return html.Div( # Data table (updates according to control panel)
        className = "control-panel-data-table",
        children=[
            dash_table.DataTable(
                id="data-table",
                data=df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df.columns],
            editable=True,
            style_header=table_header_style,
            style_cell=table_cell_style
            )
        ],
    )

def stats_header():
    '''
    Header for the stats section
    '''
    return html.Div(
        id='stats-panel-header',
        children=[
            html.P('The stats panel allows the user to interact with the map to obtain agent attributes.')
        ]
    )

def stats_body():
    '''
    - Renders Chronos console
    - Allows commands to be entered by the user
    - Shows global stats data such as tasks left, num of active tasks etc.
    - Allow individual agent attributes to be assessed as well through hovering(?)
    '''

    return html.Div(
        id='stats-panel-body',
        children=[
            html.P('The body of the stats panel will be here.'),

            # Text above the console
            html.Div(
                id='above-console-div',
                children=[
                    html.P(
                        id='live-update-test'
                    ),
                    html.Button(
                        'Clear console',
                        id='button-5'
                    ),
                    dcc.Interval(
                        id='interval-component',
                        interval=1000,
                        n_intervals=0
                    ),
                ]
            ),

            # Console
            html.Div(
                id='console-div',
                children=[
                    dcc.Interval(
                        id='logger-interval', 
                        interval=50, 
                        n_intervals=0),
                    html.Iframe(
                        id='console-out', 
                        srcDoc='', 
                        style={
                            'width': '100%',
                            'height': '400'
                            },
                    )
                ]

            ),
            html.Br(),

            # Command line
            html.Div(
                id="command-line-container",
                children=[
                    dcc.Input(
                        id='command-line-input', 
                        type='text',
                        placeholder="Insert commands to be sent here"
                    ),
                    html.Button(
                        'Send command', 
                        id='button-3'),
                ]
            ),
            html.Div(
                id="hidden-div-dialog-4",
                style=dict(display='none'),
                children=[
                    html.P('Command has been sent!')
                ]
            ),
            html.Br(),
            html.Hr(),

            # Table of commands
            html.Div(
                id="commands-section",
                children=[
                    html.H5("List of commands:"),
                    html.P('Commands will be taken converted to a dict format to be parsed in Chronos.'),
                    html.Div(
                        id="table-of-commands",
                        children=[
                            html.P(
                                'Create agents: ',
                                style={'font-weight':'bold'}
                            ),
                            html.Li(
                                children=[
                                    # html.Code('{"command" : "create", "agent-group": "[agentgroup]", "id": "[id]"}')
                                    html.Code('create [agent group] [id]')
                                ]
                            ),
                            html.P(
                                'Remove agents: ',
                                style={'font-weight':'bold'}
                            ),
                            html.Li(
                                children=[
                                    # html.Code('{"command" : "remove", "agent-group": "[agentgroup]", "id": "[id]"}')
                                    html.Code('remove [agent group] [id]')
                                ]
                            ),
                            html.P(
                                'Initialise Chronos: ',
                                style={'font-weight':'bold'}
                            ),
                            html.Li(
                                children=[
                                    html.Code('start')
                                ]
                            ),
                            html.P(
                                'Stop Chronos: ',
                                style={'font-weight':'bold'}
                            ),
                            html.Li(
                                children=[
                                    html.Code('stop')
                                ]
                            ),
                            html.P(
                                'Clear console: ',
                                style={'font-weight':'bold'}
                            ),
                            html.Li(
                                children=[
                                    html.Code('clear')
                                ]
                            )
    
    
                        ]
                    )
                ]
            )
        ]
    )

###--------------------### WEB APP INITIALISATION ###--------------------###
def web_init():

    app = Dash(
            __name__, 
            update_title=None,
            )  

    app.title = "Chronos Web Interface"
    # server = app.server # not sure if needed?

    ## MAIN LAYOUT SECTION ## -----
    app.layout = html.Div(
        id="app-container", 
        children=[
            # Banner
            html.Div(
                id="banner",
                className="banner",
                children=[
                    html.A(
                        children=[
                            html.Img(
                                # src=app.get_asset_url("TSLpic.png")
                                src='https://imperialtsl-shift.github.io/delos-outputs/svg/logo.svg'
                            )
                        ],
                        href='https://transport-systems.imperial.ac.uk/'
                    ),
                    html.A(
                        html.Button(
                            'Refresh Session',
                            id='button-refresh'
                        ),
                        href='/'
                    ),
                ],
            ),

            # Left column
            html.Div(
                id="left-column",
                className="four columns",
                children=[control_panel_header(), control_panel_body(), control_panel_data_table()]
            ),

            # Right column
            html.Div(
                id="right-column",
                className="eight columns",
                children=[

                    # Real-time Map Simulation
                    html.Div(   
                        id="map-simulation",
                        children=[
                            html.B("Real time visualisation stream of the Chronos simulation"),
                            html.Hr(),
                            html.P('Please refresh using the refresh button after stopping Chronos to start a new session.'),
                            html.Iframe(
                                id='video-streamer',
                                src="assets/hls.html",
                                style={
                                    "height": "520px",
                                    "width": "100%"
                                }
                            ),
                            dcc.Interval(
                                id='streamer-interval',
                                interval=2000,
                                n_intervals=0
                            ),
                            html.P(
                                '',
                                id='streamer-text',
                                style=dict(display='none'),
                            )
                        ],
                    ),

                    # Real-time Agent Stats
                    html.Div(
                        id="agent-stats",
                        children=[
                            html.B("Real-Time Agent Stats"),
                            html.Hr(),
                            html.Div(id="Stats", children=[stats_header(), stats_body()]),
                        ],
                    ),
                ],
            ),

            # Defer the custom javascript file so that it gets called after the web interface is rendered
            DeferScript(src="/assets/custom.ignore.js")
        ], 
    )

    ## CALLBACKS ## -----
    # Call back that updates the table, and clear fields in the control panel when "add agent" is pressed
    @app.callback(
        Output("data-table", "data"), 
        Output("hidden-div-dialog", "style"), # Show warning message beneath the button when fields are empty
        
        # Returning empty input fields as outputs
    [
            Output("agent-input-no", "value"), # Agent number field
            Output("agent-select", "value"), # Agent group field
    ],
    [    
            Input("button-1", "n_clicks"),
            State("agent-input-no", "value"), # Agent number input
            State("agent-select", "value"), # Agent group input
            State("data-table", "data") # Old data
    ],
    )
    def update_data_table(n_clicks, agent_inputs, agent_group, data):
        n_clicks_last = 0

        # Just to prevent errors
        if n_clicks is None:
            n_clicks = 0

        # Just to prevent errors
        if agent_inputs is None:
            agent_inputs = 0
        
        button_is_pressed = n_clicks > n_clicks_last # True if the button is pressed
        n_clicks_last = n_clicks # Update the previous n_click counter to the current one

        # Produce a warning if the button are pressed when some of the fields aren't filled
        buttonStyle = dict(display='none')
        if (any([agent_inputs==None, agent_group==None])) and button_is_pressed:
            buttonStyle = {'color': 'red'}
            return data, buttonStyle, None, None

        newData = data.copy() 
        
        # Initalise the first ID as 1 if there's no data entry yet
        if data == []:
            nextID = 1

        # Otherwise the last ID is the final data entry's ID + 1
        else:
            lastID = data[-1]['Agent ID'] 
            nextID = lastID + 1 

        for _ in range(0, agent_inputs):
            newData.append({
                'Agent ID': nextID, 
                'Agent Group': agent_group
                }
            )
            nextID += 1

        return newData, buttonStyle, None, None
    
    # Call back for real-time update of the stats board (under development currently)
    @app.callback(
    Output('live-update-test', 'children'),
    Input('interval-component', 'n_intervals')
    )
    def update_test(n):
        return html.P('Current elapsed time of session: ' + str(n))
    
    # Call back that starts/stop the Chronos simulation
    @app.callback(
        Output("hidden-div-dialog-2", "style"), 
        Output("hidden-div-dialog-2", "children"),
        Output("hidden-div-dialog-3", 'style'),
        Output('hidden-div-dialog-3', 'children'),
        Input("button-2", "n_clicks"),
        Input('button-4', 'n_clicks')
    )
    def start_stop_chronos(n_clicks_start, n_clicks_stop):

        global prevSeshStart, prevSeshStop, chronosProcess
    
        startButtonStyle = dict(display='none')
        stopButtonStyle = dict(display='none')
        startDialogText = html.P('Chronos has started!')
        stopDialogText = html.P('Chronos has stopped!')

        # Just to prevent errors
        if (n_clicks_start is None) and (n_clicks_stop is None):
            return startButtonStyle, startDialogText, stopButtonStyle, stopDialogText
        
        if n_clicks_start is None:
            n_clicks_start = 0
        
        if n_clicks_stop is None:
            n_clicks_stop = 0

        n_clicks_start_actual = n_clicks_start - prevSeshStart
        n_clicks_stop_actual = n_clicks_stop - prevSeshStop

        # If start button is pressed when stop button is not pressed yet
        if n_clicks_start_actual >= 1 and n_clicks_stop_actual == 0:
            startButtonStyle = {'color': 'black'}

            # This part allows Chronos to be start again when the program finishes
            if not chronosProcess.is_alive():
                prevSeshStart = n_clicks_start; prevSeshStop = n_clicks_stop

            if not chronosProcess.is_alive() and n_clicks_start_actual == 1:

                streamer_file_path = 'assets/hls'
                shutil.rmtree(streamer_file_path)
                os.makedirs(streamer_file_path)

                consoleQueue.put('-----### CHRONOS IS STARTING ###-----')
                chronosProcess = Process(
                        target=main, 
                        args=(
                            dataQueueInput, # Input parameters
                            dataQueueOutput, # Output from Chronos
                            consoleQueue, # Console outputs
                            commandQueue # Command-line inputs
                        )
                    )
                chronosProcess.start() 

            elif chronosProcess.is_alive() and n_clicks_start_actual >= 1:
                startDialogText = html.P('Chronos is already running!')

            return startButtonStyle, startDialogText, stopButtonStyle, stopDialogText

        # If stop button is pressed when start button is not pressed yet
        if n_clicks_stop_actual >= 1 and not chronosProcess.is_alive():
            stopDialogText = html.P('Nothing to stop, please start Chronos!')
            stopButtonStyle = {'color': 'red'} 
            prevSeshStart = n_clicks_start; prevSeshStop = n_clicks_stop

            return startButtonStyle, startDialogText, stopButtonStyle, stopDialogText
        
        # If stop button is pressed when start button is pressed 
        if n_clicks_stop_actual == 1 and chronosProcess.is_alive():
            stopButtonStyle = {'color': 'red'}

            # This is for safely stopping the streamer process
            commandQueue.put('stop stream')

            # Code to clear the console queue so that it stops outputting stuff
            while not consoleQueue.empty():
                consoleQueue.get()  # Removes and returns items from the queue

            prevSeshStart = n_clicks_start; prevSeshStop = n_clicks_stop

            return startButtonStyle, startDialogText, stopButtonStyle, stopDialogText


    # Call back that obtains output from python console and puts them on the web interface 
    # the output will be cleared when "clear console" is pressed
    @app.callback(
        Output('console-out', 'srcDoc'),
        Input('logger-interval', 'n_intervals'),
        Input('button-5', 'n_clicks'),
        Input('console-out', 'srcDoc')
    )
    def render_console_tf(n, n_clicks, initialConsole):
        global clearButtonCount

        if n_clicks is None:
            n_clicks = 0 
        
        buttonIsPressed = n_clicks > clearButtonCount
        
        # When "clear console" button is pressed, the console will be cleared
        if buttonIsPressed:
            initialConsole = ''
            clearButtonCount = n_clicks
        
        # Obtains elements in the queue and outputs them to the console window
        while not consoleQueue.empty():
            lines = consoleQueue.get().splitlines()

            if lines == ['stop chronos']:
                chronosProcess.terminate()
                consoleQueue.put('<br>-----### CHRONOS HAS TERMINATED ###-----<br>')
                break
            
            initialConsole += '<br>'.join(lines)
            return initialConsole + '<br>' # Append new lines to the console if consoleQueue is not empty
        
        return initialConsole
    
    # Call back that refreshes the session - not sure if this works entirely?
    @app.callback(
        Output('hidden-div-refresh', 'children'),
        Input('button-refresh', 'n_clicks')
    )
    def refresh_page(n_clicks):
        # Delete the assets > hls > live.m3u8 file to reset the session
        streamer_file_path = 'assets/hls/live.m3u8'

        # Code to clear the console queue so that it stops outputting stuff
        while not consoleQueue.empty():
            consoleQueue.get()  # Removes and returns items from the queue
        buttonCountInit() # Reload the global button counts

        # This is for stopping the streamer process before killing the Chronos process
        if n_clicks == 1 and chronosProcess.is_alive(): # To avoid putting this into the queue when the web loads for the first time 
            commandQueue.put('stop stream')
        
        # Delete the live.m3u8 file (first instance)
        if os.path.isfile(streamer_file_path):
            os.remove(streamer_file_path)
        
        return ''
    
    # Call back that obtains command from the interface command line in the form of JSON strings, and parses them to be processed in Chronos
    @app.callback(
        Output('hidden-div-dialog-4', 'children'),
        Output('hidden-div-dialog-4', 'style'),
        Output('command-line-input', 'value'),
        State('command-line-input', 'value'),
        Input('button-3', 'n_clicks')
    )
    def send_commands(input, n_clicks):
        global sendCommandCount

        sendCommandText = html.P('Your command has been sent!')
        sendCommandStyle = dict(display='none')

        if n_clicks is None:
            n_clicks = 0 
            return sendCommandText, sendCommandStyle, ''
        
        buttonIsPressed = n_clicks > sendCommandCount

        commandList = ['create', 'remove', 'start', 'stop', 'clear']

        # Functions that will be called based on the command input
        def create_agents():

        
            keyList = ['command', 'agent-group', 'id']
            inputList = input.split()
            inputDict = dict()

            if len(inputList) != 3:
                return None

            for i in range(len(keyList)):                        
                inputDict[keyList[i]] = inputList[i]

            # insert additional create agent logic here
            
            commandQueue.put(inputDict)

            return sendCommandText, sendCommandStyle, ''  

        def remove_agents(inputList):

            keyList = ['command', 'agent-group', 'id']
            inputList = input.split()
            inputDict = dict()

            if len(inputList) != 3:
                return None

            for i in range(len(keyList)):                        
                inputDict[keyList[i]] = inputList[i]

            # insert additional remove agent logic here

            commandQueue.put(inputDict)

            return sendCommandText, sendCommandStyle, ''  

        def js_buttons():
            return sendCommandText, sendCommandStyle, '' 

        ## Hash table mapping the commands and their functions
        commandHash = {
            'create': create_agents,
            'remove': remove_agents,
            'start': js_buttons,
            'stop': js_buttons,
            'clear': js_buttons
        }

        if buttonIsPressed:
            sendCommandStyle = {'color': 'black'}
            if input == '':
                sendCommandText = html.P('You have not inserted any commands!')
                return sendCommandText, sendCommandStyle, ''

            if (input.split()[0] in commandHash.keys()):
                callbackOutput = commandHash[input.split()[0]]()
                if callbackOutput is not None:
                    return callbackOutput        

            # If its not a valid command
            sendCommandText = html.P('\'' + input + '\' ' + 'is not a valid command!')
            return sendCommandText, sendCommandStyle, ''

    @app.callback(
        Output('streamer-text', 'children'),
        Output('streamer-interval', 'disabled'),
        Input('streamer-interval', 'n_intervals'),
        Input('streamer-interval', 'disabled') 
    )
    def stream_reload(n, dont_disable):
        streamer_file_path = 'assets/hls/live.m3u8'

        # dont_disable is by default 'None', which ensures that this callback function gets called every n_interval
        # when 'not None' is returned to the dcc.Interval element, this callback function stops being called
        if os.path.isfile(streamer_file_path):
            return 'a', not dont_disable

        return '', dont_disable

    app.run_server(debug=False, host='0.0.0.0', port=8050) 

# Test Function - to be deleted later
def testFun123(dataQueueInput, dataQueueOutput, consoleQueue, commandQueue):
    # i = 0
    def printingFun():
        print('print statement 1')
        print('print statement 2')
    i = 0
    with contextlib.redirect_stdout(io.StringIO()) as output:
        while True:
            i += 1
            print(i)
            # printingFun()
            consoleQueue.put(output.getvalue())
    
if __name__ == '__main__':

    # Delete the assets > hls > files to reset the session
    streamer_file_path = 'assets/hls'
    shutil.rmtree(streamer_file_path)
    os.makedirs(streamer_file_path)

    # Supresses Flask HTTP request logs from the console
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    # Initialise the web interface
    web_init() 

'''
Some quick keybinds (for VS Code):
1. Toggle Fold at cursor -> CMD K + L
2. Fold recursvely at cursor -> CMD K + [ (fold) or CMD K + ] (unfold)
3. Fold all (whole script) -> CMD K + 0
4. Unfold all (whole script) -> CMD K + J
5. Fold levels (except at cursor) -> CMD K + [level number]
6. Fold all block comments -> CMD K + /
'''