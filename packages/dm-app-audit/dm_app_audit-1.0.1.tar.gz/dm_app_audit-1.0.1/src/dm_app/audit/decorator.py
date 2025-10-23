from django.conf import settings
from .models import EventLogModelCd
import pickle


def audit_log(event_type, owner_type):
    if not hasattr(settings, 'AUDIT_LOG_TYPES'):
        raise Exception('AUDIT_LOG_TYPES not defined in settings')
    if event_type not in settings.AUDIT_LOG_TYPES:
        raise TypeError('{} is not defined in {}'.format(event_type, list(settings.AUDIT_LOG_TYPE)))

    def wrapper(func):
        def f(audit_owner_id, audit_data=None, *args, **kwargs):
            result = func(*args, **kwargs)
            EventLogModelCd.objects.create(
                event_type=event_type,
                owner_type=owner_type,
                owner_id=audit_owner_id,
                data=pickle.dumps(audit_data))
            return result
        return f
    return wrapper
