from enum import Enum
from rest_framework import serializers
from .models import MessageModel, MessageTagEnum


class ActionChoiceEnum(Enum):
    READ = 'READ'
    UNREAD = 'UNREAD'
    DELETE = 'DELETE'


class MessageListInputParamSerializer(serializers.Serializer):

    message_tag = serializers.ChoiceField(choices=[(tag.name, tag.value) for tag in MessageTagEnum])
    limit = serializers.IntegerField(required=False)
    offset = serializers.IntegerField(required=False)


class MessageActionInputParamSerializer(serializers.Serializer):

    action = serializers.ChoiceField(choices=[(tag.name, tag.value) for tag in ActionChoiceEnum])


class MessageListSerializer(serializers.ModelSerializer):

    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = MessageModel
        fields = ['message_id', 'message_group_id', 'message_at', 'message_tag', 'subject', 'message', 'can_reply', 'read', 'sender', 'sender_name', 'recipient']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['message'] = ret['message'][:37] + '...' if len(ret['message']) > 100 else ret['message'][:100]
        ret['subject'] = ret['subject'][:20] + '...' if len(ret['subject']) > 50 else ret['subject'][:50]
        return ret

    def get_sender_name(self, obj):
        if obj.sender and hasattr(obj.sender, 'profile'):
            return obj.sender.profile.name
        return 'System Notification'


class MessageDetailSerializer(serializers.ModelSerializer):

    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = MessageModel
        fields = ['message_id', 'message_group_id', 'message_at', 'message_tag', 'subject', 'message', 'can_reply', 'read', 'sender', 'sender_name', 'recipient']

    def get_sender_name(self, obj):
        if obj.sender and hasattr(obj.sender, 'profile'):
            return obj.sender.profile.name
        return 'System Notification'


class ProcessSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = MessageModel
        fields = ['subject', 'message', 'recipient']

    def save(self, **kwargs):
        return MessageModel.objects.create(owner_id=self.validated_data['recipient'].id, **self.validated_data)