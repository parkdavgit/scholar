from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
   
    path('score/', views.submit_score, name='submit_score'),
    path('edit-score/<int:score_id>/', views.edit_score, name='edit_score'),
    path('my-scores/', views.my_scores, name='my_scores'),
    path('report/<int:scholarship_id>/', views.scholarship_report, name='scholarship_report'),
    path('reviewer_report/<int:scholarship_id>/', views.reviewer_report, name='reviewer_report'),
    path('export_scores_excel/<int:scholarship_id>/', views.export_scores_excel, name='export_scores_excel'),
    path('complete/', views.mark_review_complete, name='mark_review_complete'),
    path('admin-dashboard/', views.admin_index, name='admin_index'),

]
