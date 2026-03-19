from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Count, Q

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('TOP_MANAGEMENT', 'Top Management'),
        ('MANAGER', 'Manager'),
        ('AGENT', 'Agent'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='AGENT', db_index=True)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='team_members')

    @property
    def total_calls(self):
        if self.role == 'AGENT':
            return self.calls.count()
        elif self.role == 'MANAGER':
            return CallReport.objects.filter(agent__manager=self).count()
        return CallReport.objects.count()

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"

class CallReport(models.Model):
    agent = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='calls')
    filename = models.CharField(max_length=255)
    date_processed = models.DateTimeField(auto_now_add=True, db_index=True)
    duration = models.CharField(max_length=50) 
    system_processing_time = models.FloatField(help_text="Processing time in seconds", null=True, blank=True)
    prompt_tokens = models.IntegerField(null=True, blank=True)
    candidates_tokens = models.IntegerField(null=True, blank=True)
    cost_thb = models.FloatField(null=True, blank=True)
    overall_score = models.FloatField(default=0.0, help_text="Denormalized QA score")
    
    @property
    def overall_qa_score(self):
        return self.overall_score

    def calculate_score(self):
        """
        Calculate the score from related categories and questions using DB aggregates.
        """
        stats = self.qa_categories.aggregate(
            total=Count('questions', filter=Q(questions__answer__in=['Yes', 'No'])),
            yes=Count('questions', filter=Q(questions__answer='Yes'))
        )
        total = stats['total'] or 0
        yes = stats['yes'] or 0
        return (yes / total * 100) if total > 0 else 0

    def __str__(self):
        return f"{self.filename} by {self.agent.username}"

class Utterance(models.Model):
    call_report = models.ForeignKey(CallReport, on_delete=models.CASCADE, related_name='transcript')
    timestamp = models.CharField(max_length=50)
    speaker = models.CharField(max_length=50, db_index=True)
    text = models.TextField()
    emotion = models.CharField(max_length=50)
    language = models.CharField(max_length=20, db_index=True)
    order = models.IntegerField(help_text="Sequential order of the utterance in the call", default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"[{self.timestamp}] {self.speaker}"

class QACategory(models.Model):
    call_report = models.ForeignKey(CallReport, on_delete=models.CASCADE, related_name='qa_categories')
    category_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.category_name} for {self.call_report.filename}"

class QAQuestion(models.Model):
    qa_category = models.ForeignKey(QACategory, on_delete=models.CASCADE, related_name='questions')
    question_id = models.CharField(max_length=10)
    question = models.CharField(max_length=255)
    criteria = models.TextField()
    answer = models.CharField(max_length=10, choices=[('Yes', 'Yes'), ('No', 'No'), ('NA', 'NA')])
    evidence = models.TextField(default="N/A")
    explanation = models.TextField()

    def __str__(self):
        return f"Q{self.question_id}: {self.question}"
