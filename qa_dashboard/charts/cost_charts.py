import plotly.graph_objects as go
from .utils import COLORS, apply_standard_layout

def get_api_expenditure_trend(trend_data):
    """
    Finance Detail: API Trend over time.
    """
    fig = go.Figure(data=[
        go.Scatter(
            x=trend_data['x'],
            y=trend_data['y'],
            fill='tozeroy',
            fillcolor='rgba(16, 185, 129, 0.1)',
            line=dict(color=COLORS['success'], width=3)
        )
    ])
    
    apply_standard_layout(fig)
    
    return fig.to_json()
