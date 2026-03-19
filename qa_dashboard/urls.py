from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    path('', views.overview_dashboard, name='overview'),
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/<int:manager_id>/', views.manager_detail, name='manager_detail'),
    
    path('agent/', views.agent_dashboard, name='agent_dashboard'),
    path('agent/<int:agent_id>/', views.agent_detail, name='agent_detail'),
    
    path('cost/', views.cost_dashboard, name='cost_dashboard'),
]
