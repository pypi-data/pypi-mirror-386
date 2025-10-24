
from django.contrib.auth.decorators import login_required
from django.urls import path

from testrail_megamigrator import views

urlpatterns = [
    path('', views.redirect_index, name='migrator-index'),

    path('download/project/', login_required(views.download_project_view), name='download-project'),
    path('download/milestones/', login_required(views.download_milestones_view), name='download-milestones'),
    path('download/suites/', login_required(views.download_suites_view), name='download-suites'),
    path('download/plans/', login_required(views.download_plans_runs_view), name='download-plans'),
    path('upload/project/', login_required(views.upload_project_view), name='upload-project'),
    path('upload/milestones/', login_required(views.upload_milestones_view), name='upload-milestones'),
    path('upload/suites/', login_required(views.upload_suites_view), name='upload-suites'),
    path('upload/plans/', login_required(views.upload_plans_runs_view), name='upload-plans'),

    path('configs/', login_required(views.TestrailSettingsListView.as_view()), name='settings-list'),
    path('configs/add/', login_required(views.TestrailSettingsCreateView.as_view()), name='settings-add'),
    path('configs/edit/<int:pk>/', login_required(views.TestrailSettingsUpdateView.as_view()), name='settings-edit'),
    path(
        'configs/delete/<int:pk>/',
        login_required(views.TestrailSettingsDeleteView.as_view()),
        name='settings-delete'
    ),

    path('backups/', login_required(views.TestrailBackupListView.as_view()), name='backup-list'),
    path('backups/delete/<int:pk>/', login_required(views.TestrailBackupDeleteView.as_view()), name='backup-delete'),

    path('task_status/<str:task_id>/', views.task_status, name='task_status')
]
