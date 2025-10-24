
from defect_megareport import views
from django.urls import path
from rest_framework.routers import SimpleRouter

router = SimpleRouter()
router.register(
    'api/defect-megareport',
    views.DefectReportViewSet,
    basename='defect-megareport-api',
)
urlpatterns = [
    path(
        'defect-megareport-page/',
        views.DefectReportPageView.as_view(),
        name='defect-megareport-page',
    ),
    path(
        'api/jira_ticket_change_webhook',
        views.JiraTicketChangeView.as_view(),
        name='jira-ticket-change-webhook',
    ),
]
urlpatterns += router.urls
