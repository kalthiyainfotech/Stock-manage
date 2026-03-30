from admin_panel.models import Suppliers

def current_supplier(request):
    supplier_id = request.session.get('supplier_id')
    if supplier_id:
        try:
            supplier = Suppliers.objects.get(id=supplier_id)
            return {'supplier': supplier}
        except Suppliers.DoesNotExist:
            return {}
    return {}
