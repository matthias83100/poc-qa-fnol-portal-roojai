class QADataRouter:
    """
    A router to control all database operations on models in the qa_dashboard app.
    """
    raw_models = {'callreport', 'utterance', 'qacategory', 'qaquestion'}
    aggregated_models = {'dailyoverviewstat', 'dailyagentstat'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'qa_dashboard':
            if model._meta.model_name in self.raw_models:
                return 'raw_data'
            elif model._meta.model_name in self.aggregated_models:
                return 'aggregated_data'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'qa_dashboard':
            if model._meta.model_name in self.raw_models:
                return 'raw_data'
            elif model._meta.model_name in self.aggregated_models:
                return 'aggregated_data'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations if both objects are in the same database
        if obj1._meta.app_label == 'qa_dashboard' and obj2._meta.app_label == 'qa_dashboard':
            if obj1._meta.model_name in self.raw_models and obj2._meta.model_name in self.raw_models:
                return True
            if obj1._meta.model_name in self.aggregated_models and obj2._meta.model_name in self.aggregated_models:
                return True
        elif obj1._meta.app_label != 'qa_dashboard' and obj2._meta.app_label != 'qa_dashboard':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'qa_dashboard':
            if model_name in self.raw_models:
                return db == 'raw_data'
            elif model_name in self.aggregated_models:
                return db == 'aggregated_data'
            return False

        # Ensure all other apps (auth, contenttypes, etc.) go to the default database.
        return db == 'default'
