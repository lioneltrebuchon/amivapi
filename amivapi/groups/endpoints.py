# -*- coding: utf-8 -*-
#
# license: AGPLv3, see LICENSE for details. In addition we strongly encourage
#          you to buy us beer if we meet and you like the software.
"""Api group resource settings.

Contains groups, groupmemberships, groupaddresses and forwards.
"""


groupdomain = {
    'groupaddresses': {
        'datasource': {
            'projection': {'_author': 1,
                           'email': 1,
                           'group': 1,
                           'group_id': 1,
                           'id': 1},
            'source': 'GroupAddress'},
        'description': {
            'fields': {'email': 'E-Mail address for the group'},
            'general': 'An email address associated with a group. By adding '
            'an address here, all mails sent to that address will be '
            'forwarded to all members and forwards of the associated group.'},
        'embedded_fields': {},
        'item_lookup': True,
        'item_lookup_field': '_id',
        'item_url': 'regex("[0-9]+")',
        'owner': ['group.moderator_id'],
        'owner_methods': ['GET', 'DELETE'],
        'public_item_methods': [],
        'public_methods': [],
        'registered_methods': ['POST'],
        'schema': {'_author': {'data_relation': {'resource': 'users'},
                               'nullable': True,
                               'readonly': True,
                               'type': 'objectid'},
                   'email': {'maxlength': 100,
                             'regex': '^.+@.+$',
                             'required': True,
                             'type': 'string',
                             'unique': True,
                             'unique_combination': ['group_id']},
                   'group': {'data_relation': {'embeddable': True,
                                               'resource': 'groups'},
                             'type': 'objectid'},
                   'group_id': {'data_relation': {'resource': 'groups'},
                                'not_patchable': True,
                                'only_groups_you_moderate': True,
                                'required': True,
                                'type': 'objectid',
                                'unique_combination': ['email']}}},

    'groupforwards': {
        'datasource': {
            'projection': {'_author': 1,
                           'email': 1,
                           'group': 1,
                           'group_id': 1,
                           'id': 1,
                           'user': 1},
            'source': 'GroupForward'},
        'description': {
            'fields': {'email': 'E-Mail address to which mails will be '
                       'forwarded'},
            'general': 'All messages to the group will be additionally '
            'forwardedto this address The group will NOT receive messages '
            'sent to this address, see /groupaddress for this.'},
        'embedded_fields': {},
        'item_lookup': True,
        'item_lookup_field': '_id',
        'item_url': 'regex("[0-9]+")',
        'owner': ['group.moderator_id'],
        'owner_methods': ['GET', 'DELETE'],
        'public_item_methods': [],
        'public_methods': [],
        'registered_methods': ['POST'],
        'schema': {'_author': {'data_relation': {'resource': 'users'},
                               'nullable': True,
                               'readonly': True,
                               'type': 'objectid'},
                   'email': {'maxlength': 100,
                             'regex': '^.+@.+$',
                             'required': True,
                             'type': 'string',
                             'unique_combination': ['group_id']},
                   'group': {'data_relation': {'embeddable': True,
                                               'resource': 'groups'},
                             'type': 'objectid'},
                   'group_id': {'data_relation': {'resource': 'groups'},
                                'not_patchable': True,
                                'only_groups_you_moderate': True,
                                'required': True,
                                'type': 'objectid',
                                'unique_combination': ['email']}}},

    'groupmembers': {
        'datasource': {'projection': {'_author': 1,
                                      'group': 1,
                                      'group_id': 1,
                                      'id': 1,
                                      'user': 1,
                                      'user_id': 1},
                       'source': 'GroupMember'},
        'description': {'general': 'Assignment of registered users to groups.'},
        'embedded_fields': {},
        'item_lookup': True,
        'item_lookup_field': '_id',
        'item_methods': ['GET', 'DELETE'],
        'item_url': 'regex("[0-9]+")',
        'owner': ['user_id', 'group.moderator_id'],
        'owner_methods': ['GET', 'DELETE'],
        'public_item_methods': [],
        'public_methods': [],
        'registered_methods': ['POST'],
        'schema': {
            '_author': {'data_relation': {'resource': 'users'},
                        'nullable': True,
                        'readonly': True,
                        'type': 'objectid'},
            'group': {'data_relation': {'embeddable': True,
                                        'resource': 'groups'},
                      'type': 'objectid'},
            'group_id': {'data_relation': {'resource': 'groups'},
                         'required': True,
                         'self_enrollment_must_be_allowed': True,
                         'type': 'objectid',
                         'unique_combination': ['user_id']},
            'user_id': {'data_relation': {'resource': 'users'},
                        'only_self_enrollment_for_group': True,
                        'required': True,
                        'type': 'objectid',
                        'unique_combination': ['group_id']}}},

    'groups': {
        'datasource': {'projection': {
            '_author': 1,
            'addresses': 1,
            'allow_self_enrollment': 1,
            'forwards': 1,
            'has_zoidberg_share': 1,
            'id': 1,
            'members': 1,
            'moderator_id': 1,
            'name': 1,
            'owner': 0,
            'permissions': 1}, 'source': 'Group'},
        'description': {
            'fields': {'allow_self_enrollment': 'If true, the group can be '
                       'seen by all users and they can subscribe themselves',
                       'has_zoidberg_share': 'If the group has a share in the '
                       'amiv storage',
                       'permissions': 'permissions the group grants. has to '
                       'be according to the jsonschema available at '
                       '/notyetavailable'},
            'general': "This resource describes the different teams in AMIV.A "
            "group can grant API permissions and can be reached with several "
            "addresses. To see the addresses of this group, see "
            "/groupaddressesTo see the members, have a look at "
            "'/groupmembers'. To see the addresses messages are forwarded to, "
            "see /groupforwards"},
        'embedded_fields': {'addresses': 1, 'forwards': 1, 'members': 1},
        'item_lookup': True,
        'item_lookup_field': '_id',
        'item_url': 'regex("[0-9]+")',
        'owner': ['moderator_id', 'members.user_id'],
        'owner_methods': ['GET'],
        'public_item_methods': [],
        'public_methods': [],
        'registered_methods': ['GET'],
        'schema': {
            '_author': {'data_relation': {'resource': 'users'},
                        'nullable': True,
                        'readonly': True,
                        'type': 'objectid'},
            'addresses': {'data_relation': {'embeddable': True,
                                            'resource': 'groupaddresses'},
                          'type': 'objectid'},
            'allow_self_enrollment': {'required': True,
                                      'type': 'boolean'},
            'forwards': {'data_relation': {'embeddable': True,
                                           'resource': 'groupforwards'},
                         'type': 'objectid'},
            'has_zoidberg_share': {'required': True,
                                   'type': 'boolean'},
            'members': {'data_relation': {'embeddable': True,
                                          'resource': 'groupmembers'},
                        'type': 'objectid'},
            'moderator_id': {'data_relation': {'resource': 'users'},
                             'required': True,
                             'type': 'objectid'},
            'name': {'maxlength': 100,
                     'required': True,
                     'type': 'string',
                     'unique': True},
            'owner': {'data_relation': {'embeddable': True,
                                        'resource': 'users'},
                      'type': 'objectid'},
            'permissions': {'nullable': True,
                            'type': 'permissions_jsonschema'}}}}
