from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import datetime
from .models import CallReport
from . import services
from . import charts

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


def agent_dashboard(request):
    # Get distinct agents from CallReports
    agents_data = CallReport.objects.values('agent_name', 'manager_name').distinct()
    
    # Structure for template compatibility
    agents = []
    for item in agents_data:
        agents.append({
            'username': item['agent_name'],
            'manager': {'username': item['manager_name']},
            'name_slug': item['agent_name'] # Used for routing
        })
        
    context = {'agents': agents}
    return render(request, 'agent.html', context)


def agent_detail(request, agent_name):
    start_date, end_date = services.get_date_range(request)
    stats = services.get_agent_stats(agent_name, start_date, end_date)

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
        'lifetime_avg_score': stats['lifetime_avg_score'],
        'lifetime_total_calls': stats['lifetime_total_calls'],
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
    }
    return render(request, 'agent_detail.html', context)


def cost_dashboard(request):
    start_date, end_date = services.get_date_range(request)
    stats = services.get_cost_stats(start_date, end_date)

    # Python-based chart generation
    cost_trend_json = charts.get_api_expenditure_trend(stats['cost_trend'])

    context = {
        'total_cost': stats['total_cost'],
        'cost_trend_json': cost_trend_json,
        'calls': stats['calls'],
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
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
