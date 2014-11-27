from amivapi import models
from eve.io.sql.decorators import registerSchema
from inspect import getmembers, isclass


def load_domain(config):
    domain = config['DOMAIN'] = {}

    for cls_name, cls in getmembers(models):
        if(isclass(cls)
                and cls.__module__ == "amivapi.models"
                and cls.__expose__ is True):
            registerSchema(cls.__tablename__)(cls)
            domain.update(cls._eve_schema)

    """ Definition of additional projected fields """
    domain[models.User.__tablename__]['datasource']['projection'].update({
        'groups': 1
    })
    domain[models.Group.__tablename__]['datasource']['projection'].update({
        'members': 1
    })
    domain[models.Forward.__tablename__]['datasource']['projection'].update({
        'user_subscribers': 1,
        'address_subscribers': 1
    })
    domain[models.ForwardUser.__tablename__]['datasource']['projection'] \
        .update({
            'forward': 1,
            'user': 1
        })
    domain[models.ForwardAddress.__tablename__]['datasource']['projection'] \
        .update({
            'forward': 1
        })
    domain[models.Session.__tablename__]['datasource']['projection'].update({
        'user': 1
    })
    domain[models.Event.__tablename__]['datasource']['projection'].update({
        'signups': 1
    })
    domain[models.EventSignup.__tablename__]['datasource']['projection'] \
        .update({
            'event': 1,
            'user': 1
        })
    domain[models.StudyDocument.__tablename__]['datasource']['projection'] \
        .update({
            'files': 1
        })

    """ Make it possible to retrive a user with his username (/users/name) """
    domain['users'].update({
        'additional_lookup': {
            'url': 'regex(".*[\w].*")',
            'field': 'username',
        }
    })
