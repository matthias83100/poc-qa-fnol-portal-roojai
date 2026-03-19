from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, CallReport, Utterance, QACategory, QAQuestion

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'manager', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'manager')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('role', 'manager')}),
    )

class UtteranceInline(admin.TabularInline):
    model = Utterance
    extra = 0
    ordering = ['order']

class QACategoryInline(admin.TabularInline):
    model = QACategory
    extra = 0

@admin.register(CallReport)
class CallReportAdmin(admin.ModelAdmin):
    list_display = ('filename', 'agent', 'date_processed', 'duration', 'cost_thb')
    list_filter = ('agent', 'date_processed')
    search_fields = ('filename', 'agent__username')
    inlines = [QACategoryInline]

class QAQuestionInline(admin.TabularInline):
    model = QAQuestion
    extra = 0

@admin.register(QACategory)
class QACategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'call_report')
    list_filter = ('call_report',)
    inlines = [QAQuestionInline]

@admin.register(Utterance)
class UtteranceAdmin(admin.ModelAdmin):
    list_display = ('call_report', 'speaker', 'timestamp', 'emotion', 'language', 'order')
    list_filter = ('speaker', 'language')
    ordering = ('call_report', 'order')

@admin.register(QAQuestion)
class QAQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_id', 'qa_category', 'question', 'answer')
    list_filter = ('answer', 'qa_category__category_name')
