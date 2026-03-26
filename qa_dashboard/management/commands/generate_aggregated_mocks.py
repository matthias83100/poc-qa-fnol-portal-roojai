from django.core.management.base import BaseCommand
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDate
from qa_dashboard.models import CallReport, QACategory, Utterance, DailyOverviewStat, DailyAgentStat
from qa_dashboard.charts.utils import EMOTION_COLORS, COLORS

class Command(BaseCommand):
    help = 'Generates mock aggregated data for DailyOverviewStat and DailyAgentStat based on existing raw mock data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Clearing existing aggregated stats...')
        DailyOverviewStat.objects.all().delete()
        DailyAgentStat.objects.all().delete()

        self.stdout.write('Generating DailyOverviewStat...')
        
        dates = CallReport.objects.annotate(date=TruncDate('date_processed')).values_list('date', flat=True).distinct()
        overview_count = 0
        
        for date in dates:
            if not date: continue
            calls_on_date = CallReport.objects.filter(date_processed__date=date)
            total_calls = calls_on_date.count()
            if total_calls == 0: continue
            
            agents_count = calls_on_date.values('agent_name').distinct().count()
            avg_score = calls_on_date.aggregate(Avg('overall_score'))['overall_score__avg'] or 0
            total_cost = calls_on_date.aggregate(Sum('cost_thb'))['cost_thb__sum'] or 0

            # Category Averages
            categories = QACategory.objects.filter(call_report__in=calls_on_date).values('category_name').annotate(
                yes_count=Count('questions', filter=Q(questions__answer='Yes')),
                total_count=Count('questions', filter=Q(questions__answer__in=['Yes', 'No']))
            )
            cat_averages = {}
            for cat in categories:
                label = cat['category_name'].replace('_', ' ').title()
                value = (cat['yes_count'] / cat['total_count'] * 100) if cat['total_count'] > 0 else 0
                cat_averages[label] = round(value, 1)

            # Emotion Analysis
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

            DailyOverviewStat.objects.create(
                date=date,
                total_calls=total_calls,
                agents_count=agents_count,
                avg_score=avg_score,
                category_averages=cat_averages,
                main_emotion=main_emotion,
                emotion_percent=emotion_percent,
                emotion_color=emotion_color,
                total_cost=total_cost
            )
            overview_count += 1

        self.stdout.write(self.style.SUCCESS(f'Created {overview_count} DailyOverviewStat records.'))

        self.stdout.write('Generating DailyAgentStat...')
        
        agent_dates = CallReport.objects.annotate(date=TruncDate('date_processed')).values('date', 'agent_name').distinct()
        agent_count = 0
        for item in agent_dates:
            date = item['date']
            agent_name = item['agent_name']
            if not date or not agent_name: continue

            calls = CallReport.objects.filter(date_processed__date=date, agent_name=agent_name)
            total_calls = calls.count()
            if total_calls == 0: continue
            
            avg_score = calls.aggregate(Avg('overall_score'))['overall_score__avg'] or 0
            
            all_utterances = Utterance.objects.filter(call_report__in=calls)
            
            speaker_counts = all_utterances.values('speaker').annotate(count=Count('id'))
            speaker_distribution = {s['speaker']: s['count'] for s in speaker_counts}

            lang_counts = all_utterances.values('language').annotate(count=Count('id'))
            language_distribution = {l['language'].title(): l['count'] for l in lang_counts}

            emo_counts = list(all_utterances.values('speaker', 'emotion').annotate(count=Count('id')))

            DailyAgentStat.objects.create(
                date=date,
                agent_name=agent_name,
                total_calls=total_calls,
                avg_score=avg_score,
                speaker_distribution=speaker_distribution,
                language_distribution=language_distribution,
                emotion_distribution=emo_counts
            )
            agent_count += 1

        self.stdout.write(self.style.SUCCESS(f'Created {agent_count} DailyAgentStat records.'))
