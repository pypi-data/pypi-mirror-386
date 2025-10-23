from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from dm_core.meta.utils import uuid_generator
from enum import Enum


class MessageTagEnum(Enum):
    INBOX = "INBOX"
    SENT = "SENT"


class MessageModel(models.Model):

    """
    Message Model stores message for (1) Sender and (2) Recipient

    group_id is used to group the messages, so that it can be displayed together

    can_reply will be set by the internal services while inititating the messages
    read boolean is False for Inbox while true for Outbox messages
    Sender and Recipient fields to store the values redundantly
    """
    message_id = models.CharField(max_length=32, primary_key=True, default=uuid_generator)
    message_group_id = models.CharField(max_length=32, default=uuid_generator)
    message_at = models.DateTimeField(db_index=True, default=timezone.now)
    message_tag = models.CharField(max_length=255, choices=[(tag.value, tag.value) for tag in MessageTagEnum], default=MessageTagEnum.INBOX.value)
    subject = models.CharField(max_length=255, default='')
    message = models.TextField(default='')
    can_reply = models.BooleanField(default=False)
    owner_id = models.CharField(max_length=255)
    read = models.BooleanField(default=False)
    sender = models.ForeignKey('core.AccountModel', related_name='sender', on_delete=models.CASCADE, null=True, blank=True)
    recipient = models.ForeignKey('core.AccountModel', related_name='recipient', on_delete=models.CASCADE, null=False, blank=False)

    class Meta:
        db_table = 'dm_app_notifier_message'
        ordering = ['-message_at']
