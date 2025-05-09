"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('create_new_user/', views.create_new_user_view, name='create_new_user'),
    path('race_results/', views.race_results_view, name='race_results'),
    path('add_race_result/', views.add_race_result_view, name='add_race_result'),
    path('team_management/', views.team_management_view, name='team_management'),
    path('my_team/', views.my_team_view, name='my_team'),
    path('training_log/', views.training_log_view, name='training_log'),
    path('meet_list/', views.meet_list_view, name='meet_list'),
    path('meet_list/<int:meet_id>/', views.meet_details_view, name='meet_details'),
    path('logout/', views.logout_view, name='logout'),
    path('add_athlete/', views.add_athlete_view, name='add_athlete'),
    path('manage_workouts/', views.manage_workouts_view, name='manage_workouts'),
    path('profile/', views.profile_view, name='profile'),
    path('change_password/', views.change_password_view, name='change_password'),
    path('delete_athlete/', views.delete_athlete_view, name='delete_athlete'),
]
