from dataclasses import dataclass
from typing import Optional, Callable


@dataclass
class FilterValue(object):

    field: str
    lookup_expr: str
    cast: Optional[Callable] = None


@dataclass
class OrderValue(object):

    field: str
    default: str
    priority: int


class AbstractFilter(object):

    def __init__(self, queryset):
        self.queryset = queryset

    def _sort(self, order_dict):
        orderby_attrs = []
        for attr in dir(self):
            orderby_attr = getattr(self, attr)
            if isinstance(orderby_attr, OrderValue):
                orderby_attrs.append((getattr(self, attr), order_dict.get(attr, orderby_attr.default)))
        orderby_attrs = sorted(orderby_attrs, key=lambda o: o[0].priority)
        order = []
        for orderby_arg in orderby_attrs:
            order.append(f"-{orderby_arg[0].field}" if orderby_arg[1] == 'desc' else orderby_arg[0].field)
        return order

    def _filter(self, filter_dict):
        filter_kwargs = {}
        for k, v in filter_dict.items():
            if hasattr(self, k):
                attr = getattr(self, k, None)
                if isinstance(attr, FilterValue):
                    filter_kwargs[f"{attr.field}__{attr.lookup_expr}"] = v if attr.cast is None else attr.cast(v)
        return filter_kwargs

    def filter(self, filter_dict):
        filter_kwargs = self._filter(filter_dict)
        self.queryset = self.queryset.filter(**filter_kwargs)
        return self

    def sort(self, order_dict):
        order = self._sort(order_dict)
        self.queryset = self.queryset.order_by(*order)
        return self

    def get_sortset(self, order_dict):
        return self._sort(order_dict)

    def get_filterset(self, filter_dict):
        return self._filter(filter_dict)

    def get_queryset(self):
        return self.queryset
