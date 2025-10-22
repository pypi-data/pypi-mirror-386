from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from collections import OrderedDict


def _positive_int(integer_string, strict=False, cutoff=None):
    """
    Cast a string to a strictly positive integer.
    """
    ret = int(integer_string)
    if ret < 0 or (ret == 0 and strict):
        raise ValueError()
    if cutoff:
        return min(ret, cutoff)
    return ret


class DmPagination(LimitOffsetPagination):

    max_limit = 20
    default_limit = 20

    def get_limit(self, request):
        if self.limit_query_param:
            try:
                return _positive_int(
                    request.dm_query_params[self.limit_query_param],
                    strict=True,
                    cutoff=self.max_limit
                )
            except (KeyError, ValueError):
                pass

        return self.default_limit

    def get_offset(self, request):
        try:
            return _positive_int(
                request.dm_query_params[self.offset_query_param],
            )
        except (KeyError, ValueError):
            return 0

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('start', self.offset),
            ('limit', self.limit),
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))