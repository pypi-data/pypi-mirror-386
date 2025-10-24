
from django.conf import settings
from django.db import models

from testy.root.models import BaseModel


class JiraTicketStatus(BaseModel):
    key = models.CharField(max_length=settings.CHAR_FIELD_MAX_LEN, db_index=True, unique=True)
    status = models.CharField(max_length=settings.CHAR_FIELD_MAX_LEN)
