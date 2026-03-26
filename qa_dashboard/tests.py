from django.test import TestCase, RequestFactory
from django.utils import timezone
from datetime import timedelta
from .models import CallReport, QACategory, QAQuestion, Utterance, DailyOverviewStat, DailyAgentStat
from . import services

class ServiceLayerTests(TestCase):
    databases = {'default', 'raw_data', 'aggregated_data'}

    def setUp(self):
        self.factory = RequestFactory()
        
        # Create a call report (Agent and Manager are now strings)
        self.call = CallReport.objects.create(
            agent_name="test_agent",
            manager_name="test_manager",
            filename="test_call.mp3",
            date_processed=timezone.now()
        )
        
        # Create QA Category and Questions
        self.cat = QACategory.objects.create(call_report=self.call, category_name="test_category")
        self.q1 = QAQuestion.objects.create(
            qa_category=self.cat, 
            question_id="1", 
            question="Q1", 
            answer="Yes",
            criteria="C1",
            explanation="E1"
        )
        self.q2 = QAQuestion.objects.create(
            qa_category=self.cat, 
            question_id="2", 
            question="Q2", 
            answer="No",
            criteria="C2",
            explanation="E2"
        )
        
        # Reload to get the score updated via signal
        self.call.refresh_from_db()

    def test_denormalized_score_calculation(self):
        """Verify that the signal updated the overall_score correctly."""
        # Q1: Yes, Q2: No -> 50%
        self.assertEqual(self.call.overall_score, 50.0)

    def test_automatic_aggregation(self):
        """Verify that signals automatically update daily aggregations."""
        # The signals should have triggered recalculate_aggregations already
        today = timezone.now().date()
        overview = DailyOverviewStat.objects.get(date=today)
        self.assertEqual(overview.total_calls, 1)
        self.assertEqual(overview.avg_score, 50.0)
        
        agent_stat = DailyAgentStat.objects.get(date=today, agent_name="test_agent")
        self.assertEqual(agent_stat.total_calls, 1)
        self.assertEqual(agent_stat.avg_score, 50.0)

    def test_get_date_range_defaults(self):
        """Verify default date range is last 7 days."""
        request = self.factory.get('/')
        start, end = services.get_date_range(request)
        self.assertEqual(end, timezone.now().date())
        self.assertEqual(start, end - timedelta(days=7))

    def test_get_overview_stats(self):
        """Verify overview stats calculation using aggregated models."""
        # Ensure data is aggregated first (signal does this, but being explicit for test clarity)
        today = timezone.now().date()
        services.recalculate_aggregations(today)
        
        start = today - timedelta(days=1)
        end = today + timedelta(days=1)
        stats = services.get_overview_stats(start, end)
        
        self.assertEqual(stats['total_calls'], 1)
        self.assertEqual(stats['avg_score'], 50.0)
        self.assertIn('Test Category', stats['cat_labels'])
