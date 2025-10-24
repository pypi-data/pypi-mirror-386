
from datetime import datetime

from rest_framework import fields
from rest_framework.serializers import Serializer, ValidationError


class DefectReportSerializer(Serializer):
    result_id = fields.IntegerField(read_only=True, source='id')
    defect = fields.CharField(read_only=True, source='jira_key')
    plan_id = fields.CharField(read_only=True, source='test.plan_id')
    plan_name = fields.CharField(read_only=True, source='test.plan.name')
    plan_breadcrumbs = fields.SerializerMethodField()
    result_rank = fields.IntegerField(read_only=True, source='rank')
    test_name = fields.CharField(read_only=True, source='test.case.name')
    test_id = fields.IntegerField(read_only=True)
    result_status = fields.CharField(read_only=True, source='status.name')
    latest_result_status = fields.CharField(read_only=True, source='test.last_status.name')
    latest_result_color = fields.CharField(read_only=True, source='test.last_status.color')
    result_status_color = fields.CharField(read_only=True, source='status.color')
    result_date = fields.DateTimeField(read_only=True, source='updated_at')

    def get_plan_breadcrumbs(self, obj):
        return ' -> '.join([plan.name for plan in obj.test.plan.get_ancestors()])


class JiraWebhookDataSerializer(Serializer):
    key = fields.CharField(required=True)
    status = fields.CharField(required=True)
    updated_at = fields.DateTimeField(required=True)

    def validate(self, data):
        issue = self.initial_data.get('issue', {})
        ticket_fields = issue.get('fields', {})
        data['status'] = ticket_fields.get('status', {}).get('name')
        if not data['status']:
            ValidationError('Status is not found')

        data['key'] = issue.get('key')
        if not data['key']:
            ValidationError('key is not found')

        timestamp = self.initial_data.get('timestamp')
        if timestamp and isinstance(timestamp, int):
            data['updated_at'] = datetime.fromtimestamp(timestamp / 1000)
        else:
            data['updated_at'] = datetime.utcnow()

        return data
