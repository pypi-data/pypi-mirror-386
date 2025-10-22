from django.urls import path
from .views import MessageListApi, MessageRetrieveApi, MessageActionApi, MessageUnreadCountApi, ProcessApi


urlpatterns = [
    path('message/count/v1', MessageUnreadCountApi.as_view(), name='message-unread-count'),
    path('message/action/<str:pk>/v1', MessageActionApi.as_view(), name='message-action'),
    path('message/<str:pk>/v1', MessageRetrieveApi.as_view(), name='message-retrieve'),
    path('message/v1', MessageListApi.as_view(), name='message-list'),
    path('internal/process/v1', ProcessApi.as_view(), name='internal-process')
    # TODO: Internal message received , save it , link with previous if exists
    # TODO: next: Process a reply message , that should invoke the notifier service to fire further events
]