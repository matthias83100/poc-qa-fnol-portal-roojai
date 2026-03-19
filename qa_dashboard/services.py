from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from .models import CustomUser, CallReport, QACategory, Utterance, QAQuestion
from .charts.utils import EMOTION_COLORS, COLORS

def get_date_range(request):
    """
    Extract start and end dates from request GET parameters.
    Defaults to last 30 days if not provided.
    """
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    today = timezone.now().date()
    
    if end_date_str:
        end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        end_date = today
        
    if start_date_str:
        start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        start_date = end_date - timedelta(days=7)
        
    return start_date, end_date

def filter_calls_by_date(queryset, start_date, end_date):
    """
    Filter a CallReport queryset by date range.
    """
    return queryset.filter(date_processed__date__range=[start_date, end_date])

def get_overview_stats(start_date, end_date):
    """
    Calculate stats for the overview dashboard within a date range.
    """
    calls = filter_calls_by_date(CallReport.objects.all(), start_date, end_date)
    total_calls = calls.count()
    agents_count = CustomUser.objects.filter(role='AGENT').count()
    
    avg_score = calls.aggregate(Avg('overall_score'))['overall_score__avg'] or 0
    
    # Category Averages
    categories = QACategory.objects.filter(call_report__in=calls).values('category_name').annotate(
        yes_count=Count('questions', filter=Q(questions__answer='Yes')),
        total_count=Count('questions', filter=Q(questions__answer__in=['Yes', 'No']))
    )
    
    cat_labels = []
    cat_values = []
    for cat in categories:
        label = cat['category_name'].replace('_', ' ').title()
        value = (cat['yes_count'] / cat['total_count'] * 100) if cat['total_count'] > 0 else 0
        cat_labels.append(label)
        cat_values.append(round(value, 1))

    # Trend Data
    delta = end_date - start_date
    trend_x = []
    trend_y = []
    
    # Calculate daily averages in a single query
    daily_stats = calls.annotate(
        date=TruncDate('date_processed')
    ).values('date').annotate(
        daily_avg=Avg('overall_score')
    ).order_by('date')
    
    # Create a fast lookup dictionary
    stats_dict = {stat['date']: stat['daily_avg'] or 0 for stat in daily_stats if stat['date']}
    
    # Limit trend points to avoid overcrowding if range is huge
    step = max(1, delta.days // 14) 
    
    current_day = start_date
    while current_day <= end_date:
        day_avg = stats_dict.get(current_day, 0)
        trend_x.append(current_day.strftime('%Y-%m-%d'))
        trend_y.append(round(day_avg, 1))
        current_day += timedelta(days=step)
    
    # Emotion Analysis
    customer_utterances = Utterance.objects.filter(call_report__in=calls, speaker='CUSTOMER')
    total_customer_utterances = customer_utterances.count()
    
    main_emotion = "N/A"
    emotion_percent = 0
    emotion_color = "var(--primary)"
    
    if total_customer_utterances > 0:
        emotion_counts = customer_utterances.values('emotion').annotate(count=Count('id')).order_by('-count')
        top_emotion_data = emotion_counts[0]
        main_emotion = top_emotion_data['emotion'].title()
        emotion_percent = round((top_emotion_data['count'] / total_customer_utterances) * 100, 1)
        
        emotion_color = EMOTION_COLORS.get(top_emotion_data['emotion'], COLORS['primary'])

    return {
        'total_calls': total_calls,
        'agents_count': agents_count,
        'avg_score': round(avg_score, 1),
        'cat_labels': cat_labels,
        'cat_values': cat_values,
        'trend_data': {'x': trend_x, 'y': trend_y},
        'main_emotion': main_emotion,
        'emotion_percent': emotion_percent,
        'emotion_color': emotion_color,
    }

def get_cost_stats(start_date, end_date):
    """
    Calculate cost metrics and trends.
    """
    calls = filter_calls_by_date(CallReport.objects.all(), start_date, end_date)
    total_cost = calls.aggregate(Sum('cost_thb'))['cost_thb__sum'] or 0
    
    # Calculate daily costs in a single query
    daily_costs = calls.annotate(
        date=TruncDate('date_processed')
    ).values('date').annotate(
        daily_total=Sum('cost_thb')
    ).order_by('date')
    
    cost_dict = {stat['date']: stat['daily_total'] or 0 for stat in daily_costs if stat['date']}

    # Real dynamic trend
    delta = end_date - start_date
    cost_x = []
    cost_y = []
    step = max(1, delta.days // 10)
    
    current_day = start_date
    while current_day <= end_date:
        day_cost = cost_dict.get(current_day, 0)
        cost_x.append(current_day.strftime('%Y-%m-%d'))
        cost_y.append(round(float(day_cost), 2))
        current_day += timedelta(days=step)
        
    return {
        'total_cost': round(total_cost, 2),
        'cost_trend': {'x': cost_x, 'y': cost_y},
        'calls': calls
    }

def get_manager_stats(manager, start_date, end_date):
    """
    Calculate stats for a manager's team within a date range.
    """
    agents = manager.team_members.all()
    calls = filter_calls_by_date(CallReport.objects.filter(agent__in=agents), start_date, end_date)
    
    # Annotate agents with their average score in a single query
    agents_annotated = agents.annotate(
        avg_score=Avg(
            'calls__overall_score', 
            filter=Q(calls__date_processed__date__range=[start_date, end_date])
        )
    )
    
    agent_names = []
    agent_scores = []
    for agent in agents_annotated:
        agent_names.append(agent.username.title())
        agent_scores.append(round(agent.avg_score or 0, 1))
        
    return {
        'agents': agents,
        'calls_count': calls.count(),
        'agent_names': agent_names,
        'agent_scores': agent_scores,
    }

def get_agent_stats(agent, start_date, end_date):
    """
    Calculate stats for an individual agent within a date range.
    """
    calls = filter_calls_by_date(CallReport.objects.filter(agent=agent), start_date, end_date).prefetch_related('transcript', 'qa_categories__questions').order_by('-date_processed')
    
    call_labels = [c.filename.split('_')[0] for c in calls]
    call_scores = [round(c.overall_score, 1) for c in calls]

    all_utterances = Utterance.objects.filter(call_report__in=calls)
    
    # Speaker Distribution
    speaker_counts = all_utterances.values('speaker').annotate(count=Count('id'))
    speaker_labels = [s['speaker'] for s in speaker_counts]
    speaker_values = [s['count'] for s in speaker_counts]

    # Language Distribution
    lang_counts = all_utterances.values('language').annotate(count=Count('id'))
    lang_labels = [l['language'].title() for l in lang_counts]
    lang_values = [l['count'] for l in lang_counts]

    # Emotion Distribution
    emo_counts = all_utterances.values('speaker', 'emotion').annotate(count=Count('id'))
    speakers = list(set([e['speaker'] for e in emo_counts]))
    emotions = list(set([e['emotion'] for e in emo_counts]))
    emotion_plot_data = []
    
    lookup = {(e['speaker'], e['emotion']): e['count'] for e in emo_counts}
    
    for emo in emotions:
        y_values = []
        for spk in speakers:
            match = lookup.get((spk, emo), 0)
            y_values.append(match)
        emotion_plot_data.append({
            'x': speakers,
            'y': y_values,
            'name': emo.title(),
            'type': 'bar',
            'marker': {'color': EMOTION_COLORS.get(emo, COLORS['neutral'])}
        })

    # Lifetime Stats (Ignoring date range)
    lifetime_calls_qs = CallReport.objects.filter(agent=agent)
    lifetime_avg_score = lifetime_calls_qs.aggregate(Avg('overall_score'))['overall_score__avg'] or 0
    lifetime_total_calls = lifetime_calls_qs.count()

    return {
        'calls': calls,
        'call_labels': call_labels,
        'call_scores': call_scores,
        'speaker_labels': speaker_labels,
        'speaker_values': speaker_values,
        'lang_labels': lang_labels,
        'lang_values': lang_values,
        'emotion_plot_data': emotion_plot_data,
        'lifetime_avg_score': round(lifetime_avg_score, 1),
        'lifetime_total_calls': lifetime_total_calls,
    }
