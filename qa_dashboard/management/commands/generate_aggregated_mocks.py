from django.core.management.base import BaseCommand
from django.db.models.functions import TruncDate
from qa_dashboard.models import CallReport, DailyOverviewStat, DailyAgentStat
from qa_dashboard import services

class Command(BaseCommand):
    help = 'Generates mock aggregated data for DailyOverviewStat and DailyAgentStat based on existing raw mock data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Clearing existing aggregated stats...')
        DailyOverviewStat.objects.all().delete()
        DailyAgentStat.objects.all().delete()

        self.stdout.write('Identifying dates to process...')
        dates = CallReport.objects.annotate(date=TruncDate('date_processed')).values_list('date', flat=True).distinct()
        
        count = 0
        for date in dates:
            if not date: continue
            self.stdout.write(f'Processing aggregations for {date}...')
            services.recalculate_aggregations(date)
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully recalculated aggregations for {count} days (including ALL and specific queues).'))

