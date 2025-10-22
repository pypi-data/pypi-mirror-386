from django.utils.translation import gettext_lazy as _


errors = {
    'DMCLIENTMETA001': 'Invalid token header, No credentials provided',
    'DMCLIENTMETA002': 'Invalid token header. Token string should not contain spaces.',
    'DMCLIENTMETA003': 'Invalid token header. Token string should not contain invalid characters.',
    'DMCLIENTMETA004': 'Invalid authentication token',
    'DMCLIENTMETA005': 'Authentication failed',
    'DMCLIENTMETA006': 'Authentication failed',
    'DMCLIENTMETA007': 'Authentication token expired',
    'DMCLIENTMETA008': 'Authentication failed signature verification',
    'DMCLIENTMETA009': 'Invalid signature',
    'DMCLIENTMETA010': 'Authorization failed',
    'DMCLIENTMETA011': 'Authorization denied',
    'DMCLIENTMETA012': 'Internal request timedout'
}


def GET_ERROR(key, *args, **kwargs):
    return {key: _(errors.get(key).format(*args, **kwargs))}