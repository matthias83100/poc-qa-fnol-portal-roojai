import plotly.graph_objects as go
from .utils import COLORS, apply_standard_layout

def get_agent_qa_progression(call_labels, call_scores):
    """
    Agent Detail: Individual QA score trend.
    """
    fig = go.Figure(data=[
        go.Scatter(
            x=call_labels,
            y=call_scores,
            mode='lines+markers',
            line=dict(color=COLORS['primary'], width=3, shape='spline'),
            fill='tozeroy',
            fillcolor='rgba(255, 79, 24, 0.05)'
        )
    ])
    
    apply_standard_layout(fig)
    fig.update_layout(yaxis=dict(range=[0, 105]))
    
    return fig.to_json()

def get_speaker_distribution(labels, values):
    """
    Agent Detail: Talk-time doughnut chart.
    """
    fig = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            hole=0.5,
            marker_colors=[COLORS['primary'], COLORS['success'], COLORS['info']]
        )
    ])
    
    apply_standard_layout(fig, height=250, show_legend=True)
    
    return fig.to_json()

def get_language_usage(labels, values):
    """
    Agent Detail: Bar chart for bilingual distribution.
    """
    fig = go.Figure(data=[
        go.Bar(
            x=labels,
            y=values,
            marker_color=COLORS['info'],
            opacity=0.7
        )
    ])
    
    apply_standard_layout(fig, height=250)
    
    return fig.to_json()

def get_emotion_analysis(emotion_plot_data):
    """
    Agent Detail: Grouped bar chart for emotions per speaker.
    """
    fig = go.Figure()
    
    for trace in emotion_plot_data:
        fig.add_trace(go.Bar(
            x=trace['x'],
            y=trace['y'],
            name=trace['name'],
            marker_color=trace['marker']['color']
        ))
        
    apply_standard_layout(fig, height=250, show_legend=True)
    fig.update_layout(barmode='group')
    
    return fig.to_json()
