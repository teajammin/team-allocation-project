from django.contrib import admin
from django.urls import path

from allocations import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('log_in/', views.log_in, name='log_in'),
    path('log_out/', views.log_out, name='log_out'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('projects/<int:project_id>/cohort/', views.cohort_upload, name='cohort_upload'),
    path('projects/<int:project_id>/allocate/', views.allocation_create, name='allocation_create'),
    path(
        'projects/<int:project_id>/runs/<int:run_id>/',
        views.allocation_run_detail,
        name='allocation_run_detail',
    ),
    path(
        'projects/<int:project_id>/runs/<int:run_id>/export/',
        views.allocation_export,
        name='allocation_export',
    ),
    path('profile/', views.profile, name='profile'),
    path('password/', views.password, name='password'),
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/update/', views.user_update, name='user_update'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
]
