
import logging

from celery import shared_task
from defect_megareport.models import JiraTicketStatus
from defect_megareport.serializers import JiraWebhookDataSerializer

logger = logging.getLogger('defect-megareport')


@shared_task()
def handle_jira_ticket_change(data):
    serializer = JiraWebhookDataSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    key = serializer.validated_data['key']
    status = serializer.validated_data['status']
    updated_at = serializer.validated_data['updated_at']

    logger.info(f'Jira ticket change: {key} - {status} - {updated_at}')

    ticket, _ = JiraTicketStatus.objects.update_or_create(
        key=key, defaults={
            'status': status,
            'updated_at': updated_at,
            'is_deleted': False,
        },
    )
