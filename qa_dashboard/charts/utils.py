import plotly.graph_objects as go

# Brand and Functional Colors
COLORS = {
    'primary': '#ff5011',     # Roojai Orange
    'primary_dark': '#212529',
    'secondary': '#003b71',    # Roojai Blue
    'success': '#198754',
    'warning': '#ffc107',
    'danger': '#dc3545',
    'info': '#0dcaf0',
    'neutral': '#94A3B8',      # Slate
    'grid': '#E2E8F0',         # Light Border
    'bg_transparent': 'rgba(0,0,0,0)',
}

EMOTION_COLORS = {
    'satisfied': COLORS['success'],
    'professional': COLORS['info'],
    'neutral': COLORS['neutral'],
    'anxious': COLORS['warning'],
    'frustrated': COLORS['danger'],
}

def apply_standard_layout(fig, title=None, height=None, show_legend=False):
    """
    Applies consistent styling, fonts, and margins to any Plotly figure.
    """
    layout_update = {
        'font': dict(family='Outfit, sans-serif', color=COLORS['secondary']),
        'margin': dict(t=40 if title else 20, b=40, l=40, r=20),
        'paper_bgcolor': COLORS['bg_transparent'],
        'plot_bgcolor': COLORS['bg_transparent'],
        'xaxis': dict(
            gridcolor=COLORS['grid'],
            linecolor=COLORS['grid'],
            tickfont=dict(size=11, color=COLORS['neutral'])
        ),
        'yaxis': dict(
            gridcolor=COLORS['grid'],
            linecolor=COLORS['grid'],
            tickfont=dict(size=11, color=COLORS['neutral'])
        ),
        'showlegend': show_legend,
        'autosize': True,
    }
    
    if height:
        layout_update['height'] = height
    
    if title:
        layout_update['title'] = {
            'text': title,
            'font': dict(size=16, weight='bold')
        }
        
    fig.update_layout(**layout_update)
    return fig
