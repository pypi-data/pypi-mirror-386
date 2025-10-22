from django.utils.translation import gettext_lazy as _

errors = {
    'DMAPPAUTHZ001': 'User not authorised for the requested resource',
    'DMAPPAUTHZ002': 'Invalid session signature'
}


def GET_ERROR(key, *args, **kwargs):
    return {key: _(errors.get(key).format(*args, **kwargs))}