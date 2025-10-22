from django.conf import settings
from dm_core.meta.decorator import api_inbound_validator
from dm_core.meta.pagination import DmPagination
from dm_core.meta.exceptions import RestNotFoundException
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView, GenericAPIView, CreateAPIView
from .pagination import MessagePagination
from .models import MessageTagEnum, MessageModel
from .serializers import MessageDetailSerializer, MessageListInputParamSerializer, ActionChoiceEnum
from .serializers import MessageListSerializer, MessageActionInputParamSerializer
from .serializers import ProcessSerializer
import logging

logger = logging.getLogger()


class MessageUnreadCountApi(GenericAPIView):

    """
    Count unread messages for owner of message in INBOX
    """

    api_id = {
        'GET': f"{settings.SERVICE}.notifier.message.unread-count"
    }

    def get_count(self) -> int:
        return MessageModel.objects.filter(owner_id=self.request.user.resource, read=False,
                                           message_tag=MessageTagEnum.INBOX.value).count()

    @api_inbound_validator()
    def get(self, request, *args, **kwargs):
        return Response({'count': self.get_count()}, status=status.HTTP_200_OK)


class MessageListApi(ListAPIView):
    api_id = {
        'GET': f"{settings.SERVICE}.notifier.message.list",
    }
    pagination_class = MessagePagination
    serializer_class = MessageListSerializer
    params_serializer_class = MessageListInputParamSerializer

    def get_queryset(self):
        return MessageModel.objects.filter(owner_id=self.request.user.resource,
                                           message_tag=self.params_serializer.validated_data['message_tag']).order_by('-message_at')

    @api_inbound_validator()
    def get(self, request, params_serializer, *args, **kwargs):
        self.params_serializer = params_serializer
        return super().get(request, *args, **kwargs)


class MessageRetrieveApi(RetrieveAPIView):
    api_id = {
        'GET': f"{settings.SERVICE}.notifier.message.retrieve",
    }

    serializer_class = MessageDetailSerializer

    def get_object(self, pk):
        try:
            return MessageModel.objects.get(message_id=pk, owner_id=self.request.user.resource)
        except MessageModel.DoesNotExist:
            raise RestNotFoundException()

    @api_inbound_validator()
    def get(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class MessageActionApi(CreateAPIView):
    api_id = {
        'POST': f"{settings.SERVICE}.notifier.message.action",
    }
    input_serializer_class = MessageActionInputParamSerializer
    serializer_class = MessageActionInputParamSerializer

    def get_object(self):
        try:
            return MessageModel.objects.get(message_id=self.kwargs['pk'], owner_id=self.request.user.resource)
        except MessageModel.DoesNotExist:
            raise RestNotFoundException()

    @api_inbound_validator()
    def post(self, request, serializer, pk, *args, **kwargs):
        instance = self.get_object()
        action = serializer.validated_data['action']
        if action == ActionChoiceEnum.READ.value:
            instance.read = True
            instance.save()
        elif action == ActionChoiceEnum.UNREAD.value:
            instance.read = False
            instance.save()
        elif action == ActionChoiceEnum.DELETE.value:
            instance.delete()
        serializer = self.get_serializer(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

class ProcessApi(CreateAPIView):

    api_id = {
        'POST': f"{settings.SERVICE}.notifier.internal.process"
    }
    serializer_class = ProcessSerializer
    input_serializer_class = ProcessSerializer

    @api_inbound_validator()
    def post(self, request, serializer, *args, **kwargs):
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)