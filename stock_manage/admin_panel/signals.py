from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Count

# Import models dynamically to avoid circular imports if needed
from .models import Suppliers, Workers, ProductVariant, Contact
# For models in other apps, we can use apps.get_model
from django.apps import apps

def broadcast_dashboard_update():
    Buyer = apps.get_model('buyers', 'Buyer')
    Order = apps.get_model('buyers', 'Order')
    
    suppliers_count = Suppliers.objects.count()
    workers_count = Workers.objects.count()
    buyers_count = Buyer.objects.count()
    inventory_count = ProductVariant.objects.count()
    orders_count = Order.objects.count()
    contacts_count = Contact.objects.count()
    
    recent_orders_qs = Order.objects.order_by('-created_at')[:5]
    recent_orders = []
    for o in recent_orders_qs:
        recent_orders.append({
            'order_number': o.order_number,
            'first_name': o.first_name,
            'last_name': o.last_name,
            'total': str(o.total),
            'status': o.status,
            'status_display': o.get_status_display()
        })
        
    recent_contacts_qs = Contact.objects.order_by('-created_at')[:5]
    recent_contacts = []
    for c in recent_contacts_qs:
        recent_contacts.append({
            'first_name': c.first_name,
            'last_name': c.last_name,
            'email': c.email,
            'message': c.message,
            'created_at': c.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(c.created_at, 'strftime') else str(c.created_at)
        })

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "dashboard",
        {
            "type": "dashboard_update",
            "data": {
                'suppliers_count': suppliers_count,
                'workers_count': workers_count,
                'buyers_count': buyers_count,
                'inventory_count': inventory_count,
                'orders_count': orders_count,
                'contacts_count': contacts_count,
                'recent_orders': recent_orders,
                'recent_contacts': recent_contacts
            },
        },
    )

@receiver(post_save, sender=Suppliers)
@receiver(post_delete, sender=Suppliers)
@receiver(post_save, sender=Workers)
@receiver(post_delete, sender=Workers)
@receiver(post_save, sender=ProductVariant)
@receiver(post_delete, sender=ProductVariant)
@receiver(post_save, sender=Contact)
@receiver(post_delete, sender=Contact)
def dashboard_models_changed(sender, **kwargs):
    broadcast_dashboard_update()

# For models in other apps, we connect them in ready() or here if imported correctly
# But it's safer to use the string name in ready() if they aren't loaded yet.
