
from defect_megareport import views
from django.urls import path
from rest_framework.routers import SimpleRouter

router = SimpleRouter()
router.register(
    'api/defect-report',
    views.DefectReportViewSet,
    basename='defect-report-api',
)
urlpatterns = [
    path(
        'defect-report-page/',
        views.DefectReportPageView.as_view(),
        name='defect-report-page',
    ),
    path(
        'api/jira_ticket_change_webhook',
        views.JiraTicketChangeView.as_view(),
        name='jira-ticket-change-webhook',
    ),
]
urlpatterns += router.urls
