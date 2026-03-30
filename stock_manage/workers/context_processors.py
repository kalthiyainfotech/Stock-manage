from admin_panel.models import Workers

def current_worker(request):
    worker_id = request.session.get('worker_id')
    if worker_id:
        try:
            worker = Workers.objects.get(id=worker_id)
            return {'worker': worker}
        except Workers.DoesNotExist:
            return {}
    return {}
