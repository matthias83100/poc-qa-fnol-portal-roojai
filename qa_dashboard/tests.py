from django.test import TestCase, RequestFactory
from django.utils import timezone
from datetime import timedelta
from .models import CustomUser, CallReport, QACategory, QAQuestion, Utterance
from . import services

class ServiceLayerTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.manager = CustomUser.objects.create_user(username='manager', password='pw', role='MANAGER')
        self.agent = CustomUser.objects.create_user(username='agent', password='pw', role='AGENT', manager=self.manager)
        
        # Create a call report
        self.call = CallReport.objects.create(
            agent=self.agent,
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
        
        # Denormalized score should be updated via signals
        self.call.refresh_from_db()

    def test_denormalized_score_calculation(self):
        """Verify that the signal updated the overall_score correctly."""
        # Q1: Yes (50), Q2: No (0) -> (50+0)/100 * 100 = 50%
        self.assertEqual(self.call.overall_score, 50.0)

    def test_get_date_range_defaults(self):
        """Verify default date range is last 30 days."""
        request = self.factory.get('/')
        start, end = services.get_date_range(request)
        self.assertEqual(end, timezone.now().date())
        self.assertEqual(start, end - timedelta(days=30))

    def test_get_date_range_custom(self):
        """Verify custom date parsing."""
        request = self.factory.get('/', {'start_date': '2026-01-01', 'end_date': '2026-01-15'})
        start, end = services.get_date_range(request)
        self.assertEqual(start.strftime('%Y-%m-%d'), '2026-01-01')
        self.assertEqual(end.strftime('%Y-%m-%d'), '2026-01-15')

    def test_get_overview_stats(self):
        """Verify overview stats calculation."""
        start = timezone.now().date() - timedelta(days=1)
        end = timezone.now().date() + timedelta(days=1)
        stats = services.get_overview_stats(start, end)
        
        self.assertEqual(stats['total_calls'], 1)
        self.assertEqual(stats['avg_score'], 50.0)
        self.assertIn('Test Category', stats['cat_labels'])

    def test_get_cost_stats(self):
        """Verify cost stats calculation."""
        self.call.cost_thb = 5.5
        self.call.save()
        
        start = timezone.now().date() - timedelta(days=1)
        end = timezone.now().date() + timedelta(days=1)
        stats = services.get_cost_stats(start, end)
        
        self.assertEqual(stats['total_cost'], 5.5)
        self.assertEqual(len(stats['cost_trend']['x']), 3) # Start, Now, End days if step is 1
