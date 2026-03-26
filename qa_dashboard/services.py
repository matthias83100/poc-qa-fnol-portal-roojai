from django.db.models import Avg, Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
from .models import CallReport, Utterance, QACategory, DailyOverviewStat, DailyAgentStat
from .charts.utils import EMOTION_COLORS, COLORS

def get_date_range(request):
    """
    Extract start and end dates from request GET parameters.
    Defaults to last 7 days if not provided.
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

def get_overview_stats(start_date, end_date):
    """
    Calculate stats for the overview dashboard using aggregated models.
    Ensures today's data is fresh by recalculating it before querying.
    """
    today = timezone.now().date()
    if (not start_date or start_date <= today) and (not end_date or end_date >= today):
        recalculate_aggregations(today)

    stats = DailyOverviewStat.objects.filter(date__range=[start_date, end_date]).order_by('date')
    
    total_calls = stats.aggregate(Sum('total_calls'))['total_calls__sum'] or 0
    agents_count = DailyAgentStat.objects.filter(date__range=[start_date, end_date]).values('agent_name').distinct().count()
    
    # Weighted average score
    total_score_sum = sum(s.avg_score * s.total_calls for s in stats)
    avg_score = (total_score_sum / total_calls) if total_calls > 0 else 0

    # Average of category averages
    cat_totals = defaultdict(float)
    cat_counts = defaultdict(int)
    for stat in stats:
        for cat, val in stat.category_averages.items():
            cat_totals[cat] += val * stat.total_calls
            cat_counts[cat] += stat.total_calls
            
    cat_labels = []
    cat_values = []
    for cat in sorted(cat_totals.keys()):
        cat_labels.append(cat)
        cat_values.append(round(cat_totals[cat] / cat_counts[cat], 1) if cat_counts[cat] > 0 else 0)

    # Trend Data
    delta = end_date - start_date
    trend_x = []
    trend_y = []
    
    stats_dict = {stat.date: stat.avg_score for stat in stats}
    step = max(1, delta.days // 14) 
    
    current_day = start_date
    while current_day <= end_date:
        day_avg = stats_dict.get(current_day, 0)
        trend_x.append(current_day.strftime('%Y-%m-%d'))
        trend_y.append(round(day_avg, 1))
        current_day += timedelta(days=step)

    # Main Emotion (approximate by taking the one from the most recent valid day)
    main_emotion = "N/A"
    emotion_percent = 0.0
    emotion_color = "var(--primary)"
    
    if stats.exists() and total_calls > 0:
        recent_stat = stats.exclude(main_emotion="N/A").last()
        if recent_stat:
            main_emotion = recent_stat.main_emotion
            emotion_percent = recent_stat.emotion_percent
            emotion_color = recent_stat.emotion_color

    # Aggregate Distributions from all agents
    agent_stats = DailyAgentStat.objects.filter(date__range=[start_date, end_date])
    
    combined_speaker = defaultdict(int)
    combined_lang = defaultdict(int)
    combined_emo = defaultdict(int)
    
    for stat in agent_stats:
        for spk, count in stat.speaker_distribution.items():
            combined_speaker[spk] += count
        for lang, count in stat.language_distribution.items():
            combined_lang[lang] += count
        for emo_dict in stat.emotion_distribution:
            spk = emo_dict['speaker']
            emo = emo_dict['emotion']
            combined_emo[(spk, emo)] += emo_dict['count']

    speaker_labels = list(combined_speaker.keys())
    speaker_values = list(combined_speaker.values())
    lang_labels = list(combined_lang.keys())
    lang_values = list(combined_lang.values())

    speakers = list(set([k[0] for k in combined_emo.keys()]))
    emotions = list(set([k[1] for k in combined_emo.keys()]))
    emotion_plot_data = []

    for emo in emotions:
        y_values = []
        for spk in speakers:
            y_values.append(combined_emo.get((spk, emo), 0))
        emotion_plot_data.append({
            'x': speakers,
            'y': y_values,
            'name': emo.title(),
            'type': 'bar',
            'marker': {'color': EMOTION_COLORS.get(emo, COLORS['neutral'])}
        })

    # List of agents for the period with aggregated stats
    agent_summaries = DailyAgentStat.objects.filter(date__range=[start_date, end_date]).values('agent_name').annotate(
        total_calls=Sum('total_calls')
    )
    
    # We need to calculate a real weighted average for the period
    agent_list = []
    # IMPORTANT: We must clear ordering before calling distinct() to prevent 
    # the database from returning one row per agent per day.
    unique_agent_names = agent_stats.values_list('agent_name', flat=True).order_by().distinct()
    
    for name in unique_agent_names:
        a_stats = agent_stats.filter(agent_name=name)
        a_total_calls = a_stats.aggregate(Sum('total_calls'))['total_calls__sum'] or 0
        a_score_sum = sum(s.avg_score * s.total_calls for s in a_stats)
        a_avg_score = (a_score_sum / a_total_calls) if a_total_calls > 0 else 0
        
        agent_list.append({
            'name': name,
            'total_calls': a_total_calls,
            'avg_score': round(a_avg_score, 1)
        })
        
    # Sort by total calls descending
    agent_list = sorted(agent_list, key=lambda x: x['total_calls'], reverse=True)

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
        'speaker_labels': speaker_labels,
        'speaker_values': speaker_values,
        'lang_labels': lang_labels,
        'lang_values': lang_values,
        'emotion_plot_data': emotion_plot_data,
        'agent_list': agent_list,
    }

def get_cost_stats(start_date, end_date):
    """
    Calculate cost metrics using aggregated models.
    """
    stats = DailyOverviewStat.objects.filter(date__range=[start_date, end_date]).order_by('date')
    total_cost = stats.aggregate(Sum('total_cost'))['total_cost__sum'] or 0
    
    cost_dict = {stat.date: stat.total_cost for stat in stats}

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
        'calls': CallReport.objects.filter(date_processed__date__range=[start_date, end_date])
    }

def get_agent_stats(agent_name, start_date, end_date):
    """
    Calculate stats for an individual agent using aggregated models.
    """
    stats = DailyAgentStat.objects.filter(agent_name=agent_name, date__range=[start_date, end_date])
    
    calls = CallReport.objects.filter(agent_name=agent_name, date_processed__date__range=[start_date, end_date]).prefetch_related('transcript', 'qa_categories__questions').order_by('-date_processed')
    
    call_labels = [c.filename.split('_')[0] for c in calls]
    call_scores = [round(c.overall_score, 1) for c in calls]

    combined_speaker = defaultdict(int)
    combined_lang = defaultdict(int)
    combined_emo = defaultdict(int)
    
    for stat in stats:
        for spk, count in stat.speaker_distribution.items():
            combined_speaker[spk] += count
        for lang, count in stat.language_distribution.items():
            combined_lang[lang] += count
        
        for emo_dict in stat.emotion_distribution:
            spk = emo_dict['speaker']
            emo = emo_dict['emotion']
            combined_emo[(spk, emo)] += emo_dict['count']

    speaker_labels = list(combined_speaker.keys())
    speaker_values = list(combined_speaker.values())

    lang_labels = list(combined_lang.keys())
    lang_values = list(combined_lang.values())

    speakers = list(set([k[0] for k in combined_emo.keys()]))
    emotions = list(set([k[1] for k in combined_emo.keys()]))
    emotion_plot_data = []

    for emo in emotions:
        y_values = []
        for spk in speakers:
            y_values.append(combined_emo.get((spk, emo), 0))
        emotion_plot_data.append({
            'x': speakers,
            'y': y_values,
            'name': emo.title(),
            'type': 'bar',
            'marker': {'color': EMOTION_COLORS.get(emo, COLORS['neutral'])}
        })

    lifetime_stats = DailyAgentStat.objects.filter(agent_name=agent_name)
    lifetime_total_calls = lifetime_stats.aggregate(Sum('total_calls'))['total_calls__sum'] or 0
    total_score_sum = sum(s.avg_score * s.total_calls for s in lifetime_stats)
    lifetime_avg_score = (total_score_sum / lifetime_total_calls) if lifetime_total_calls > 0 else 0

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

def recalculate_aggregations(target_date):
    """
    Recalculates the DailyOverviewStat and DailyAgentStat for a specific date
    based on the raw CallReport data. Designed to be called by a webhook or signal.
    """
    if not target_date:
        return
        
    calls_on_date = CallReport.objects.filter(date_processed__date=target_date)
    total_calls = calls_on_date.count()
    
    if total_calls == 0:
        # If there are no calls, ensure no stale daily stats exist
        DailyOverviewStat.objects.filter(date=target_date).delete()
        DailyAgentStat.objects.filter(date=target_date).delete()
        return

    # Update Overview Stats
    agents_count = calls_on_date.values('agent_name').distinct().count()
    avg_score = calls_on_date.aggregate(Avg('overall_score'))['overall_score__avg'] or 0
    total_cost = calls_on_date.aggregate(Sum('cost_thb'))['cost_thb__sum'] or 0

    categories = QACategory.objects.filter(call_report__in=calls_on_date).values('category_name').annotate(
        yes_count=Count('questions', filter=Q(questions__answer='Yes')),
        total_count=Count('questions', filter=Q(questions__answer__in=['Yes', 'No']))
    )
    cat_averages = {}
    for cat in categories:
        label = cat['category_name'].replace('_', ' ').title()
        value = (cat['yes_count'] / cat['total_count'] * 100) if cat['total_count'] > 0 else 0
        cat_averages[label] = round(value, 1)

    customer_utterances = Utterance.objects.filter(call_report__in=calls_on_date, speaker='CUSTOMER')
    total_customer_utterances = customer_utterances.count()
    main_emotion = "N/A"
    emotion_percent = 0.0
    emotion_color = "var(--primary)"
    
    if total_customer_utterances > 0:
        emotion_counts = customer_utterances.values('emotion').annotate(count=Count('id')).order_by('-count')
        if emotion_counts:
            top_emotion_data = emotion_counts[0]
            main_emotion = top_emotion_data['emotion'].title()
            emotion_percent = round((top_emotion_data['count'] / total_customer_utterances) * 100, 1)
            emotion_color = EMOTION_COLORS.get(top_emotion_data['emotion'], COLORS['primary'])

    DailyOverviewStat.objects.update_or_create(
        date=target_date,
        defaults={
            'total_calls': total_calls,
            'agents_count': agents_count,
            'avg_score': avg_score,
            'category_averages': cat_averages,
            'main_emotion': main_emotion,
            'emotion_percent': emotion_percent,
            'emotion_color': emotion_color,
            'total_cost': total_cost
        }
    )

    # Update Agent Stats
    agent_names = list(calls_on_date.values_list('agent_name', flat=True).distinct())
    
    # First delete stats for agents that might not have calls anymore today but had before
    DailyAgentStat.objects.filter(date=target_date).exclude(agent_name__in=agent_names).delete()
    
    for agent_name in agent_names:
        agent_calls = calls_on_date.filter(agent_name=agent_name)
        agent_total_calls = agent_calls.count()
        agent_avg_score = agent_calls.aggregate(Avg('overall_score'))['overall_score__avg'] or 0
        
        all_utterances = Utterance.objects.filter(call_report__in=agent_calls)
        
        speaker_counts = all_utterances.values('speaker').annotate(count=Count('id'))
        speaker_distribution = {s['speaker']: s['count'] for s in speaker_counts}

        lang_counts = all_utterances.values('language').annotate(count=Count('id'))
        language_distribution = {l['language'].title(): l['count'] for l in lang_counts}

        emo_counts = list(all_utterances.values('speaker', 'emotion').annotate(count=Count('id')))

        DailyAgentStat.objects.update_or_create(
            date=target_date,
            agent_name=agent_name,
            defaults={
                'total_calls': agent_total_calls,
                'avg_score': agent_avg_score,
                'speaker_distribution': speaker_distribution,
                'language_distribution': language_distribution,
                'emotion_distribution': emo_counts
            }
        )
