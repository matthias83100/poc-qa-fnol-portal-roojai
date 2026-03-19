from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import QAQuestion, CallReport

@receiver(post_save, sender=QAQuestion)
@receiver(post_delete, sender=QAQuestion)
def update_call_report_score(sender, instance, **kwargs):
    """
    Update the overall_score of the CallReport whenever a QAQuestion is changed.
    """
    call_report = instance.qa_category.call_report
    new_score = call_report.calculate_score()
    
    # Use update to avoid triggering signals recursively if there were any on CallReport
    CallReport.objects.filter(id=call_report.id).update(overall_score=new_score)
