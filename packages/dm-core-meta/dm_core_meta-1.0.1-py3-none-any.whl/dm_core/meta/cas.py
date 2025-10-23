class AppData(object):
    """
    Application specific data for a user
    This object is serialized and is added to every api request object
    """
    def __init__(self, *args, **kwargs):
        self.tenant_id = kwargs.pop('tenant_id', None)
        self.group_id = kwargs.pop('group_id', None)

    def __eq__(self, other):
        for k, v in self.__dict__.items():
            if v != other.__dict__[k]:
                return False
        return True

    def to_dict(self):
        data = {}
        for k, v in sorted(self.__dict__.items()):
            if hasattr(v, 'to_dict'):
                data[k] = v.to_dict()
            else:
                data[k] = v
        return data
