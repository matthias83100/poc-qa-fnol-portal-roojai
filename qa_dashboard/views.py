from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from .models import CustomUser, CallReport, QACategory, QAQuestion, Utterance
from django.db.models import Avg, Count, F, Q
from django.utils import timezone
from datetime import timedelta
import json
from collections import Counter
from . import charts

from . import services

@login_required
def overview_dashboard(request):
    """
    Overview: stats for the whole call center with global date filtering.
    """
    start_date, end_date = services.get_date_range(request)
    stats = services.get_overview_stats(start_date, end_date)

    # Python-based chart generation
    cat_chart_json = charts.get_performance_category_chart(stats['cat_labels'], stats['cat_values'])
    trend_chart_json = charts.get_qa_trend_chart(stats['trend_data'])

    context = {
        'total_calls': stats['total_calls'],
        'agents_count': stats['agents_count'],
        'avg_score': stats['avg_score'],
        'category_chart_json': cat_chart_json,
        'trend_chart_json': trend_chart_json,
        'main_emotion': stats['main_emotion'],
        'emotion_percent': stats['emotion_percent'],
        'emotion_color': stats['emotion_color'],
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
    }
    return render(request, 'overview.html', context)


@login_required
@role_required('TOP_MANAGEMENT', 'MANAGER')
def manager_dashboard(request):
    if request.user.role == 'TOP_MANAGEMENT':
        managers = CustomUser.objects.filter(role='MANAGER')
    else:
        managers = CustomUser.objects.filter(id=request.user.id)
        
    context = {'managers': managers}
    return render(request, 'manager.html', context)


@login_required
@role_required('TOP_MANAGEMENT', 'MANAGER')
def manager_detail(request, manager_id):
    manager = get_object_or_404(CustomUser, id=manager_id, role='MANAGER')
    if request.user.role == 'MANAGER' and request.user.id != manager.id:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Access Denied")
        
    start_date, end_date = services.get_date_range(request)
    stats = services.get_manager_stats(manager, start_date, end_date)

    # Python-based chart generation
    comparison_chart_json = charts.get_agent_comparison_chart(stats['agent_names'], stats['agent_scores'])

    context = {
        'manager_user': manager,
        'agents': stats['agents'],
        'calls_count': stats['calls_count'],
        'comparison_chart_json': comparison_chart_json,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
    }
    return render(request, 'manager_detail.html', context)


@login_required
def agent_dashboard(request):
    if request.user.role == 'TOP_MANAGEMENT':
        agents = CustomUser.objects.filter(role='AGENT')
    elif request.user.role == 'MANAGER':
        agents = CustomUser.objects.filter(role='AGENT', manager=request.user)
    today = timezone.now().date()
    agents = agents.annotate(
        today_calls_count=Count('calls', filter=Q(calls__date_processed__date=today)),
        today_avg_score=Avg('calls__overall_score', filter=Q(calls__date_processed__date=today))
    )
    
    context = {'agents': agents}
    return render(request, 'agent.html', context)


@login_required
def agent_detail(request, agent_id):
    agent = get_object_or_404(CustomUser, id=agent_id, role='AGENT')
    if request.user.role == 'AGENT' and request.user.id != agent.id:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Access Denied")
    elif request.user.role == 'MANAGER' and agent.manager_id != request.user.id:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Access Denied")
        
    start_date, end_date = services.get_date_range(request)
    stats = services.get_agent_stats(agent, start_date, end_date)

    # Python-based chart generation
    qa_progression_json = charts.get_agent_qa_progression(stats['call_labels'], stats['call_scores'])
    speaker_dist_json = charts.get_speaker_distribution(stats['speaker_labels'], stats['speaker_values'])
    lang_usage_json = charts.get_language_usage(stats['lang_labels'], stats['lang_values'])
    emotion_analysis_json = charts.get_emotion_analysis(stats['emotion_plot_data'])

    context = {
        'agent': agent,
        'calls': stats['calls'],
        'lifetime_total_calls': stats['lifetime_total_calls'],
        'qa_progression_json': qa_progression_json,
        'speaker_dist_json': speaker_dist_json,
        'lang_usage_json': lang_usage_json,
        'emotion_analysis_json': emotion_analysis_json,
        'lifetime_avg_score': stats['lifetime_avg_score'],
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
    }
    return render(request, 'agent_detail.html', context)


@login_required
@role_required('TOP_MANAGEMENT')
def cost_dashboard(request):
    start_date, end_date = services.get_date_range(request)
    stats = services.get_cost_stats(start_date, end_date)
    
    cost_trend_json = charts.get_api_expenditure_trend(stats['cost_trend'])
    
    context = {
        'calls': stats['calls'],
        'total_cost': stats['total_cost'],
        'cost_trend_json': cost_trend_json,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
    }
    return render(request, 'cost.html', context)

def custom_403_view(request, exception=None):
    """
    Custom 403 Forbidden handler.
    """
    error_msg = str(exception)
    if not error_msg or 'PermissionDenied' in error_msg:
        error_msg = "It looks like you've tried to access a section of the dashboard that is restricted to higher management levels."
        
    context = {
        'error_message': error_msg
    }
    return render(request, '403.html', context, status=403)
