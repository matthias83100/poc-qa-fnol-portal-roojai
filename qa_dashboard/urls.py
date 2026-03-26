from django.urls import path
from . import views

urlpatterns = [
    path('', views.overview_dashboard, name='overview'),
    
    path('agent/', views.agent_dashboard, name='agent_dashboard'),
    path('agent/<str:agent_name>/', views.agent_detail, name='agent_detail'),
    
    path('cost/', views.cost_dashboard, name='cost_dashboard'),
    
    # API endpoints
    path('api/trigger-aggregation/', views.trigger_aggregation, name='trigger_aggregation'),
]
