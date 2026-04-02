from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import datetime
from django.db.models import Count, Avg
from .models import CallReport, DailyAgentStat
from . import services
from . import charts

def overview_dashboard(request):
    """
    Overview: stats for the whole call center with global date filtering.
    """
    start_date, end_date = services.get_date_range(request)
    queue = request.GET.get('queue')
    stats = services.get_overview_stats(start_date, end_date, queue=queue)

    # Python-based chart generation
    cat_chart_json = charts.get_performance_category_chart(stats['cat_labels'], stats['cat_values'])
    trend_chart_json = charts.get_qa_trend_chart(stats['trend_data'])
    
    # New aggregate charts
    speaker_dist_json = charts.get_speaker_distribution(stats['speaker_labels'], stats['speaker_values'])
    lang_usage_json = charts.get_language_usage(stats['lang_labels'], stats['lang_values'])
    emotion_analysis_json = charts.get_emotion_analysis(stats['emotion_plot_data'])

    context = {
        'total_calls': stats['total_calls'],
        'agents_count': stats['agents_count'],
        'avg_score': stats['avg_score'],
        'category_chart_json': cat_chart_json,
        'trend_chart_json': trend_chart_json,
        'speaker_dist_json': speaker_dist_json,
        'lang_usage_json': lang_usage_json,
        'emotion_analysis_json': emotion_analysis_json,
        'agent_list': stats['agent_list'],
        'main_emotion': stats['main_emotion'],
        'emotion_percent': stats['emotion_percent'],
        'emotion_color': stats['emotion_color'],
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'selected_queue': queue,
    }
    return render(request, 'overview.html', context)


def agent_dashboard(request):
    """
    List of all agents with today's summary stats pulled from DailyAgentStat.
    """
    # Get distinct agents from CallReports (to ensure we have the full list)
    agents_data = CallReport.objects.values('agent_name', 'manager_name').distinct()
    
    # Get today's stats from DailyAgentStat
    today = timezone.now().date()
    today_stats = DailyAgentStat.objects.filter(date=today, queue='ALL')
    today_stats_map = {s.agent_name: {'total_calls': s.total_calls, 'avg_score': s.avg_score} for s in today_stats}
    
    # Structure for template compatibility
    agents = []
    total_today_calls = 0
    total_today_score_sum = 0
    active_agents_count = 0
    
    for item in agents_data:
        stats = today_stats_map.get(item['agent_name'], {'total_calls': 0, 'avg_score': 0})
        agent_data = {
            'username': item['agent_name'],
            'manager': {'username': item['manager_name']},
            'name_slug': item['agent_name'], # Used for routing
            'today_calls': stats['total_calls'],
            'today_avg_score': round(stats['avg_score'], 1) if stats['avg_score'] else 0
        }
        agents.append(agent_data)
        
        if agent_data['today_calls'] > 0:
            active_agents_count += 1
            total_today_calls += agent_data['today_calls']
            total_today_score_sum += (agent_data['today_avg_score'] * agent_data['today_calls'])
            
    avg_today_score = (total_today_score_sum / total_today_calls) if total_today_calls > 0 else 0
    
    context = {
        'agents': agents,
        'active_agents_count': active_agents_count,
        'total_today_calls': total_today_calls,
        'avg_today_score': round(avg_today_score, 1)
    }
    return render(request, 'agent.html', context)


def agent_detail(request, agent_name):
    start_date, end_date = services.get_date_range(request)
    queue = request.GET.get('queue')
    stats = services.get_agent_stats(agent_name, start_date, end_date, queue=queue)

    # Python-based chart generation
    qa_progression_json = charts.get_agent_qa_progression(stats['call_labels'], stats['call_scores'])
    speaker_dist_json = charts.get_speaker_distribution(stats['speaker_labels'], stats['speaker_values'])
    lang_usage_json = charts.get_language_usage(stats['lang_labels'], stats['lang_values'])
    emotion_analysis_json = charts.get_emotion_analysis(stats['emotion_plot_data'])

    context = {
        'agent': {'username': agent_name},
        'calls': stats['calls'],
        'qa_progression_json': qa_progression_json,
        'speaker_dist_json': speaker_dist_json,
        'lang_usage_json': lang_usage_json,
        'emotion_analysis_json': emotion_analysis_json,
        'avg_score': stats['period_avg_score'],
        'total_calls': stats['period_total_calls'],
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'selected_queue': queue,
    }
    return render(request, 'agent_detail.html', context)


def cost_dashboard(request):
    start_date, end_date = services.get_date_range(request)
    queue = request.GET.get('queue')
    stats = services.get_cost_stats(start_date, end_date, queue=queue)

    # Python-based chart generation
    cost_trend_json = charts.get_api_expenditure_trend(stats['cost_trend'])

    context = {
        'total_cost': stats['total_cost'],
        'cost_trend_json': cost_trend_json,
        'calls': stats['calls'],
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'selected_queue': queue,
    }
    return render(request, 'cost.html', context)

@csrf_exempt
def trigger_aggregation(request):
    """
    API endpoint for external cronjobs to trigger stats aggregation.
    Expects a POST request. Optionally accepts a JSON body with a 'date' field (YYYY-MM-DD).
    If no date is provided, defaults to today's date.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
        
    target_date = timezone.now().date()
    
    if request.body:
        try:
            data = json.loads(request.body)
            date_str = data.get('date')
            if date_str:
                target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid JSON or date format. Use YYYY-MM-DD'}, status=400)
            
    try:
        services.recalculate_aggregations(target_date)
        return JsonResponse({
            'status': 'success',
            'message': f'Aggregations recalculated successfully for {target_date}'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
