from dm_core.meta.filters import AbstractFilter, FilterValue


class MessageListFilter(AbstractFilter):

    message_tag = FilterValue(field='message_tag', lookup_expr='eq')