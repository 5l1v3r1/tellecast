# -*- coding: utf-8 -*-

from social.pipeline.user import USER_FIELDS


def create_user(details, strategy, user=None, *args, **kwargs):
    if user:
        return {
            'is_new': False,
        }
    fields = dict(
        (name, kwargs.get(name) or details.get(name)) for name in strategy.setting('USER_FIELDS', USER_FIELDS)
    )
    if not fields:
        return
    user = strategy.create_user(**fields)
    return {
        'is_new': True,
        'user': user,
    }
