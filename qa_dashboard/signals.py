from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import QAQuestion, CallReport
from . import services

@receiver(post_save, sender=QAQuestion)
@receiver(post_delete, sender=QAQuestion)
def update_call_report_score(sender, instance, **kwargs):
    """
    Update the overall_score of the CallReport whenever a QAQuestion is changed.
    Then trigger aggregation update.
    """
    call_report = instance.qa_category.call_report
    new_score = call_report.calculate_score()
    
    # Use update to avoid triggering signals recursively if there were any on CallReport
    CallReport.objects.filter(id=call_report.id).update(overall_score=new_score)
    
    # Manually trigger aggregation update for the date of this call
    services.recalculate_aggregations(call_report.date_processed.date())

@receiver(post_save, sender=CallReport)
@receiver(post_delete, sender=CallReport)
def trigger_daily_aggregation(sender, instance, **kwargs):
    """
    Recalculate daily aggregations whenever a CallReport is added, updated, or deleted.
    """
    if instance.date_processed:
        services.recalculate_aggregations(instance.date_processed.date())
