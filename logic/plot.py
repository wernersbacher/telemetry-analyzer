import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json


def create_telem_plot(df, df2):
    """ Todo: add race times as title? and driver"""

    # subplot setup
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05)

    trace_speed_1 = {
        "x": df["dist_lap"],
        "y": df["speedkmh"],
        "mode": "lines",
        "name": 'Speed',
        "type": 'scatter',
        "line": {"color": 'blue', 'shape': 'spline', 'smoothing': 0.5}
    }
    trace_throttle_1 = {
        "x": df["dist_lap"],
        "y": df["throttle"],
        "mode": "lines",
        "name": 'Throttle',
        "type": 'scatter',
        "line": {"color": 'green', 'shape': 'spline', 'smoothing': 0.5}
    }
    trace_brake_1 = {
        "x": df["dist_lap"],
        "y": df["brake"],
        "mode": "lines",
        "name": 'Brake',
        "type": 'scatter',
        "line": {"color": 'red', 'shape': 'spline', 'smoothing': 0.5}
    }

    if df2 is not None:
        trace_speed_2 = {
            "x": df2["dist_lap"],
            "y": df2["speedkmh"],
            "mode": "lines",
            "name": 'Speed 2',
            "type": 'scatter',
            "line": {"color": 'grey', 'shape': 'spline', 'smoothing': 0.5}
        }
        trace_throttle_2 = {
            "x": df2["dist_lap"],
            "y": df2["throttle"],
            "mode": "lines",
            "name": 'Throttle 2',
            "type": 'scatter',
            "line": {"color": 'grey', 'shape': 'spline', 'smoothing': 0.5}
        }
        trace_brake_2 = {
            "x": df2["dist_lap"],
            "y": df2["brake"],
            "mode": "lines",
            "name": 'Brake 2',
            "type": 'scatter',
            "line": {"color": 'grey', 'shape': 'spline', 'smoothing': 0.5}
        }

        fig.append_trace(trace_speed_2, row=1, col=1)
        fig.append_trace(trace_throttle_2, row=2, col=1)
        fig.append_trace(trace_brake_2, row=3, col=1)

    # append normal traces
    fig.append_trace(trace_speed_1, row=1, col=1)
    fig.append_trace(trace_throttle_1, row=2, col=1)
    fig.append_trace(trace_brake_1, row=3, col=1)

    # add x axis title
    fig['layout']['xaxis3']['title'] = 'Distance (meters)'

    # add fix y axis
    fig.update_yaxes(fixedrange=True)

    figure_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return figure_json
