
from typing import TYPE_CHECKING, Any, Iterable, Optional

from django.db.models import OuterRef, Subquery

from testy.tests_representation.models import Test, TestPlan, TestResult

from defect_megareport import raw_sql
from django.db.models import CharField, F, Func, Q, Window
from django.db.models.expressions import RawSQL
from django.db.models.functions import RowNumber

from testy.tests_representation.selectors.results import TestResultSelector
from django.db import models


class Unnest(Func):
    function = 'unnest'
    output_field = CharField()


class DefectReportSelector:
    jira_key_regex = r'[A-Z]{2,10}-\d+'
    array_splits = ',|;|\\n|\\r'


    @staticmethod
    def _prepare_base_qs():
        return (
            TestResultSelector.result_list()
            .select_related('test', 'test__plan', 'test__case', 'test__last_status')
        )

    @classmethod
    def prepare_defect_list(cls, attributes):
        attribute_cases = []
        attribute_include_conditions = []


        queryset = cls._prepare_base_qs()

        for attribute in attributes:
            attribute_cases.append(
                raw_sql.ATTRIBUTE_CASE_SQL.format(attribute=attribute, array_splits=cls.array_splits)
            )

            attribute_include_condition = (
                    Q(**{f'attributes__{attribute}__isnull': False}) &
                    ~Q(**{f'attributes__{attribute}': ''}) &
                    ~Q(**{f'attributes__{attribute}': []}) &
                    ~Q(**{f'attributes__{attribute}': ['']})
            )
            attribute_include_conditions.append(attribute_include_condition)

        if attribute_include_conditions:
            final_condition = attribute_include_conditions[0]
            for condition in attribute_include_conditions[1:]:
                final_condition = final_condition | condition
            queryset = queryset.filter(attributes__has_any_keys=attributes).filter(final_condition)

        queryset = queryset.annotate(
            jira_key=Unnest(RawSQL(cls._prepare_unnest_sql(attributes), []),),
            rank=Window(
                expression=RowNumber(),
                partition_by=[F('test_id')],
                order_by=F('id').desc(),
            ),
        )

        return queryset.order_by('jira_key', 'test__plan__name', 'test__case__name', 'rank', '-updated_at').distinct()


    @classmethod
    def _prepare_unnest_sql(cls, attributes, jira_key=None):
        attribute_cases = [
            raw_sql.ATTRIBUTE_CASE_SQL.format(
                attribute=attribute,
                array_splits=cls.array_splits,
            ) for attribute in attributes
        ]
        array_unpack_prepared_sql = raw_sql.ARRAY_UNPACK_SQL.format(
            attribute_cases=' \n '.join(attribute_cases),
            jira_key_regex=cls.jira_key_regex,
            search_condition=f" AND jira_key ilike '%%{jira_key}%%' " if jira_key else ''
        )
        return array_unpack_prepared_sql

    @classmethod
    def filter_jira_key(cls, queryset, jira_key):
        attributes = [x.rhs for x in queryset.query.where.children if isinstance(x, models.fields.json.HasAnyKeys)][0]
        queryset = queryset.annotate(
            jira_key=Unnest(RawSQL(cls._prepare_unnest_sql(attributes, jira_key), []),),
        )
        return queryset
