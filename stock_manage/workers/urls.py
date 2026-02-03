from django.urls import path
from workers.views import worker_login,work_dash,worker_logout


urlpatterns = [
    path('',worker_login,name='worker_login'),
    path('dashboard',work_dash,name='work_dash'),
    path('work/logout',worker_logout,name='worker_logout')
]