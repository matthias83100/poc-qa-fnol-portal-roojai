import plotly.graph_objects as go
from .utils import COLORS, apply_standard_layout

def get_performance_category_chart(cat_labels, cat_values):
    """
    Overview: Bar chart showing scores across different QA categories.
    """
    fig = go.Figure(data=[
        go.Bar(
            x=cat_labels,
            y=cat_values,
            marker_color=[COLORS['success'] if v > 80 else COLORS['warning'] for v in cat_values],
            text=[f"{v}%" for v in cat_values],
            textposition='auto',
        )
    ])
    
    apply_standard_layout(fig)
    fig.update_layout(yaxis=dict(range=[0, 105]))
    
    return fig.to_json()

def get_qa_trend_chart(trend_data):
    """
    Overview: Trend line chart for QA scores over time.
    """
    fig = go.Figure(data=[
        go.Scatter(
            x=trend_data['x'],
            y=trend_data['y'],
            mode='lines+markers',
            line=dict(color=COLORS['primary'], width=4, shape='spline'),
            marker=dict(size=8, color=COLORS['primary']),
            fill='tozeroy',
            fillcolor=f"rgba(255, 79, 24, 0.1)"
        )
    ])
    
    apply_standard_layout(fig)
    fig.update_layout(yaxis=dict(range=[0, 105]))
    
    return fig.to_json()
