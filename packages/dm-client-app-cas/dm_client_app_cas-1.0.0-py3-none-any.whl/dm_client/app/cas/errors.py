from django.utils.translation import gettext_lazy as _


errors = {
    'DMCLIENTAPPCAS001': 'Invalid service ticket',
    'DMCLIENTAPPCAS002': 'Invalid service ticket',
    'DMCLIENTAPPCAS003': 'Client authentication failed',
    'DMCLIENTAPPCAS004': 'Invalid service {}'
}


def GET_ERROR(key, *args, **kwargs):
    return {key: _(errors.get(key).format(*args, **kwargs))}