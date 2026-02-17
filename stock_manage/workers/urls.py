from django.urls import path
from workers.views import *


urlpatterns = [
    path('',worker_login,name='worker_login'),
    path('dashboard',work_dash,name='work_dash'),
    path('work/logout',worker_logout,name='worker_logout'),
    path('api/holidays', holidays_api, name='wk_holidays_api'),
    path('api/leaves', leaves_api, name='wk_leaves_api'),
    path('leave', wk_leave, name='wk_leave'),
    path('leave/add', add_leave, name='wk_add_leave'),
    path('leave/edit/<int:id>/', edit_leave, name='wk_edit_leave'),
    path('leave/delete/<int:id>/', delete_leave, name='wk_delete_leave'),
]
