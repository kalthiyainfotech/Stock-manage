from django.apps import AppConfig


class AdminPanelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_panel'

    def ready(self):
        import admin_panel.signals
        from django.db.models.signals import post_save, post_delete
        from django.apps import apps
        
        Buyer = apps.get_model('buyers', 'Buyer')
        Order = apps.get_model('buyers', 'Order')
        
        post_save.connect(admin_panel.signals.dashboard_models_changed, sender=Buyer)
        post_delete.connect(admin_panel.signals.dashboard_models_changed, sender=Buyer)
        post_save.connect(admin_panel.signals.dashboard_models_changed, sender=Order)
        post_delete.connect(admin_panel.signals.dashboard_models_changed, sender=Order)
