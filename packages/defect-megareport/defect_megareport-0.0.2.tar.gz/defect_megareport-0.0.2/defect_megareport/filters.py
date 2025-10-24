
from django_filters import rest_framework as filters

from testy.tests_representation.models import TestPlan, TestResult
from .selectors import DefectReportSelector


class DefectReportFilter(filters.FilterSet):
    plan_id = filters.NumberFilter(field_name='test__plan_id', required=False, method='search_plan')
    project_id = filters.NumberFilter(required=True)
    just_last_result = filters.BooleanFilter(method='search_last_result')
    search = filters.CharFilter(method='filter_by_attributes')

    def search_plan(self, queryset, name, value):
        root_plan = TestPlan.objects.get(id=value)
        return queryset.filter(test__plan__path__descendant=root_plan.path)

    def search_last_result(self, queryset, name, value):
        if value:
            return queryset.filter(rank=1)
        return queryset

    def filter_by_attributes(self, queryset, name, value):
        filtered_by_jira_key = DefectReportSelector.filter_jira_key(queryset, jira_key=value)
        return queryset.filter(test__case__name__icontains=value).union(filtered_by_jira_key)

    class Meta:
        model = TestResult
        fields = ['project_id', 'plan_id', 'just_last_result']
