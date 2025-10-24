
from defect_megareport.filters import DefectReportFilter
from defect_megareport.models import JiraTicketStatus
from defect_megareport.selectors import DefectReportSelector
from defect_megareport.serializers import DefectReportSerializer
from defect_megareport.tasks import handle_jira_ticket_change
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from testy.core.selectors.projects import ProjectSelector
from testy.paginations import StandardSetPagination
from testy.tests_representation.models import TestResult


@method_decorator(csrf_exempt, name='dispatch')
class JiraTicketChangeView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        handle_jira_ticket_change.delay(data=request.data)
        return Response(status=status.HTTP_200_OK)


class DefectReportPageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return render(
            request,
            template_name='defect_report_page.html',
            context={
                'projects': [x for x in ProjectSelector(request.user).project_list_statistics() if x.is_visible],
            },
        )


class DefectReportViewSet(ListModelMixin, GenericViewSet):
    serializer_class = DefectReportSerializer
    queryset = TestResult.objects.none()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardSetPagination
    filterset_class = DefectReportFilter

    def get_queryset(self):
        attributes = self.request.GET.getlist('attributes', ['Defects'])
        return DefectReportSelector.prepare_defect_list(attributes=attributes)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        paginated_data = self.paginator.get_paginated_response(serializer.data).data
        return JsonResponse(paginated_data)
