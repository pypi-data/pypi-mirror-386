from dm_core.meta.pagination import DmPagination
from rest_framework.response import Response
from collections import OrderedDict
from math import ceil

class MessagePagination(DmPagination):

    def get_paginated_response(self, data):
        endIndex = self.offset + self.limit if self.offset + self.limit < self.count else self.count
        lastPage = ceil(self.count / self.limit)
        currentPage = (self.offset // self.limit) + 1
        return Response(OrderedDict([
            ('startIndex', self.offset),
            ('endIndex', endIndex - 1 if endIndex > 0 else 0),
            ('resultsPerPage', self.limit),
            ('lastPage', lastPage),
            ('currentPage', currentPage),
            ('totalResults', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))