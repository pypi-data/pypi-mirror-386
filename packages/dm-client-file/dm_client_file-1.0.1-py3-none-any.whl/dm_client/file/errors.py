from django.utils.translation import gettext_lazy as _

errors = {
    'DMCLIENTFILE001': 'Error uploading'
}


def GET_ERROR(key, *args, **kwargs):
    return {key: _(errors.get(key).format(*args, **kwargs))}