import plotly.graph_objects as go
from .utils import COLORS, apply_standard_layout

def get_agent_comparison_chart(agent_names, agent_scores):
    """
    Manager Detail: Compare agent scores within a team.
    """
    fig = go.Figure(data=[
        go.Bar(
            x=agent_names,
            y=agent_scores,
            marker_color=COLORS['info'],
            opacity=0.8,
            text=[f"{s}%" for s in agent_scores],
            textposition='auto',
        )
    ])
    
    apply_standard_layout(fig, height=250)
    fig.update_layout(yaxis=dict(range=[0, 105]))
    
    return fig.to_json()
