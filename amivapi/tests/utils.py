# -*- coding: utf-8 -*-
#
# license: AGPLv3, see LICENSE for details. In addition we strongly encourage
#          you to buy us beer if we meet and you like the software.
"""General testing utilities."""

import sys
import json
import string
import random
import unittest
from datetime import datetime, date
import os
from tempfile import mkdtemp
from itertools import count
from pymongo import MongoClient
from bson import ObjectId

from flask import g
from flask.testing import FlaskClient
from flask.wrappers import Response
from eve.methods.post import post_internal

from amivapi import bootstrap, utils
from amivapi.settings import DEFAULT_ROOT_PASSWORD, ROOT_ID
from amivapi.utils import EMAIL_REGEX
from mongo_manage import initdb

# Test Config overwrites
test_config = {
    'MONGO_DBNAME': 'test_amivapi',
    'STORAGE_DIR': '',
    'FORWARD_DIR': '',
    'ROOT_MAIL': 'nobody@example.com',
    'SMTP_SERVER': '',
    'APIKEYS': {},
    'TESTING': True,
    'DEBUG': True   # This makes eve's error messages more helpful
}


def find_by_pair(dicts, key, value):
    """Find an entry in a list of dicts, which has a pair key => value.

    If there is not exactly one result returns None

    This is useful to find an entry in the result of a get query

    Example:

    users = api.get("/users")
    root_user = find_by_pair(users, "nethz", "adietmue")

    This will find the entry in the response which corresponds to the root
    user
    """
    found = [x for x in dicts if key in x and x[key] == value]
    if len(found) != 1:
        return None
    return found[0]


def is_file_content(path, content):
    """Check file content.

    Returns true if the file at path exists and has the content in the
    second parameter
    """
    try:
        with open(path, "r") as f:
            if content != f.read():
                return False
    except IOError:
        return False

    return True


class BadTestException(Exception):
    pass


class TestClient(FlaskClient):
    """Custom test client with additional request/response checks.

    Auth header will be added if token is provided.
    Data is sent as json if nothing else is specified.
    Responses can be checked against an expected status code.
    """

    def open(self, *args, **kwargs):
        """Modified request.

        Adds token and headers and asserts status code.
        """
        # We are definetly going to add some headers
        if 'headers' not in kwargs:
            kwargs['headers'] = {}

        # Add token
        token = kwargs.pop('token', None)

        if token:
            kwargs['headers'].update({
                # We support a auth header of the form "Token <thetoken>"
                'Authorization': 'Token ' + token
            })

        # Add content-type: json header if nothing else is provided
        if (not("content-type" in kwargs['headers']) and
                ("data" in kwargs)):
            # Parse data
            kwargs['data'] = json.dumps(kwargs['data'])
            # Set header
            kwargs['content_type'] = "application/json"

        # get the actual response and assert status
        expected_code = kwargs.pop('status_code', None)

        response = super(TestClient, self).open(*args, **kwargs)

        status_code = response.status_code

        if (expected_code is not None and expected_code != status_code):
            raise AssertionError(
                "Expected a status code of %i, but got %i instead\n"
                "Response:\n%s\n%s\n%s" % (expected_code, status_code,
                                           response, response.data,
                                           response.status))

        return response


class TestResponse(Response):
    """Custom response to ease JSON handling."""

    @property
    def json(self):
        """Return data in JSON."""
        return json.loads(self.data.decode())


class WebTest(unittest.TestCase):
    """Base test class for tests against the full WSGI stack.

    Inspired by eve standard testing class.
    """

    def setUp(self):
        """Set up the testing client and database connection.

        self.api will be a flask TestClient to make requests
        self.db will be a MongoDB database
        """
        super(WebTest, self).setUp()

        # In 3.2, assertItemsEqual was replaced by assertCountEqual
        # Make assertItemsEqual work in tests for py3 as well
        if sys.version_info >= (3, 2):
            self.assertItemsEqual = self.assertCountEqual

        config = utils.get_config()

        # create temporary directories
        test_config['STORAGE_DIR'] = mkdtemp(prefix='amivapi_storage')
        test_config['FORWARD_DIR'] = mkdtemp(prefix='amivapi_forwards')

        # connect to Mongo
        self.connection = MongoClient(config['MONGO_HOST'],
                                      config['MONGO_PORT'])

        # create eve app
        self.app = bootstrap.create_app(**test_config)
        self.app.response_class = TestResponse
        self.app.test_client_class = TestClient

        # connect to testing database and create user
        self.db = self.connection[test_config['MONGO_DBNAME']]

        # Assert that database is empty before starting tests.
        self.assertFalse(
            self.db.collection_names(),
            "The database already exists!")

        # init database
        initdb(self.app)

        # create test client
        self.api = self.app.test_client()

    def tearDown(self):
        """Tear down after testing."""
        # delete testing database
        self.connection.drop_database(test_config['MONGO_DBNAME'])
        # close database connection
        self.connection.close()

        # delete all uploaded files
        self.file_cleanup()

        # remove temporary folders
        os.rmdir(test_config['STORAGE_DIR'])
        os.rmdir(test_config['FORWARD_DIR'])

    def file_cleanup(self):
        """Remove all remaining files."""
        for f in os.listdir(self.app.config['STORAGE_DIR']):
            try:
                os.remove(os.path.join(self.app.config['STORAGE_DIR'], f))
            except:
                # The tests seem to be to fast sometimes, cleanup in the end
                # works fine, in between tests deletion sometimes doesn't work.
                # Hack-like solution: Just ignore that and be happy that all
                # files are deleted in the end.
                # TODO: Find out whats wrong
                # (To reproduce remove the try-except block and run the
                # file access test)
                pass
        for f in os.listdir(self.app.config['FORWARD_DIR']):
            try:
                os.unlink(os.path.join(self.app.config['FORWARD_DIR'], f))
            except Exception as e:
                print(e)

    def create_random_value(self, definition):
        """Create a random value for the given cerberus field description"""
        # If there is a list of allowed values, just pick one
        if 'allowed' in definition:
            return random.choice(definition['allowed'])

        if definition['type'] == 'string':
            minimum_length = 0 if definition.get('empty', True) else 1
            length = random.randint(minimum_length,
                                    definition.get('maxlength', 100))

            if 'regex' in definition:
                if definition['regex'] == EMAIL_REGEX:
                    return "%s@%s.%s" % (
                        ''.join(random.choice(string.ascii_letters
                                              + string.digits)
                                for _ in range(max(1, length - 27))),
                        ''.join(random.choice(string.ascii_letters
                                              + string.digits)
                                for _ in range(20)),
                        ''.join(random.choice(string.ascii_letters
                                              + string.digits)
                                for _ in range(5)))
                raise NotImplementedError

            return ''.join(random.choice(string.ascii_letters + string.digits)
                           for _ in range(length))

        elif definition['type'] == 'boolean':
            return random.choice([True, False])

        elif definition['type'] == 'date':
            return datetime.date.fromordinal(
                random.randint(0, date.max.toordinal()))

        elif definition['type'] == 'datetime':
            return datetime.fromtimestamp(random.randint(0, 2**32))

        elif definition['type'] == 'float':
            return random.rand() * random.randint(0, 2**32)

        elif definition['type'] == 'number' or definition['type'] == 'integer':
            return random.randint(0, 2**32)

        elif definition['type'] == 'objectid':
            if 'data_relation' in definition:
                related_res = definition['data_relation']['resource']
                return random.choice(list(self.db[related_res].find({})))['_id']
            return ObjectId(''.join(random.choice(string.hexdigits)
                                    for _ in range(24)))

        raise NotImplementedError

    def preprocess_fixture_object(self, resource, schema, obj, fixture):
        """Fills in missing fields in a fixture's objects"""

        if resource == 'users':
            if 'password' not in obj:
                # Fill in a password, althought it is not required to enable
                # login without ldap in tests
                obj['password'] = ''.join(
                    random.choice(string.ascii_letters + string.digits)
                    for _ in range(30))

        if resource == 'sessions':
            # We need to fill correct usernames and passwords for sessions, so
            # they are special
            if 'username' not in obj:
                # No username, make a random session
                obj['username'] = str(random.choice(
                    list(self.db['users'].find({})))['_id'])

            if 'password' not in obj:
                if (obj['username'] == u'root'
                        or obj['username'] == str(ROOT_ID)):
                    obj['password'] = DEFAULT_ROOT_PASSWORD
                else:
                    # find the user in the fixture and insert his password
                    for user in fixture['users']:
                        if (user.get('nethz') == obj['username']
                                or user.get('email') == obj['username']
                                or user.get('_id') == obj['username']):
                            obj['password'] = user['password']

            if 'password' not in obj:
                raise BadTestException("Could not determine password for user"
                                       " %s in fixture with unspecified "
                                       " password for session %s"
                                       % (obj['username'], obj))

            return

        # We iterate over the schema to fix missing fields with random values
        for field, field_def in schema.items():
            if (field not in obj
                    and not field_def.get('nullable', False)
                    and not field_def.get('readonly', False)):
                # We need to add a value for the field to create a valid
                # object
                if 'default' in field_def:
                    obj[field] = field_def['default']
                else:
                    # Create a random value
                    obj[field] = self.create_random_value(field_def)

    def load_fixture(self, fixture):
        """Takes a dictionary, describing an initial database, and applies it.
        Missing fields are filled in using defaults, or if not available with
        random values. Note that this describes post requests, so for example
        a session will need username and password, not user and token.

        Returns:
            A list of all created objects

        Example:
        self.load_fixture({
            'users': [
                {
                    'nethz': 'pablo',
                    'rfid': '132432'
                }
            ],
            'events': [
                {
                    'title': 'mytestevent'
                }
            ]
        })
        """
        added_objects = []

        # We need to sort in the order of dependencies. It is for example
        # not possible to add sessions before we have users, as we need valid
        # object IDs for the relations.
        for resource, obj in self.sorted_by_dependencies(fixture):
            schema = self.app.config['DOMAIN'][resource]['schema']

            # Note that we pass the current state of the fixture to resolve
            # fields, which depend on already inserted content
            self.preprocess_fixture_object(resource, schema, obj, fixture)

            # Add it to the database
            with self.app.test_request_context("/%s" % resource, method='POST'):
                response, _, _, return_code = post_internal(resource, obj)
                if return_code != 201:
                    raise BadTestException("Fixture could not be loaded:\n%s\n"
                                           "Problem was caused by:\n%s"
                                           % (response.__repr__(), obj))
            added_objects.append(response)

        # Check that everything went fine
        if len(added_objects) < sum([len(v) for v in fixture.values()]):
            raise BadTestException("Not all objects in the fixture could be "
                                   "added! Check your dictionary!")

        return added_objects

    def sorted_by_dependencies(self, fixture):
        """Generator to yield a fixture in an order, which can be added to the
        database. It is not possible to add objects, which reference other
        objects, before those have been added to the database. Therefore we
        build a dependency map and yield only objects, which have their
        dependencies resolved.

        Yields (resource, object) pairs"""
        deps = {}
        for resource, resource_def in self.app.config['DOMAIN'].items():
            deps[resource] = set([
                field_def.get('data_relation', {}).get('resource')
                for field_def in resource_def['schema'].values()
                if 'data_relation' in field_def])

        # Try yielding until all resources have been yielded.
        while len(deps) > 0:
            # Search for something, which has no more dependencies
            for resource in deps:
                if len(deps[resource]) == 0:
                    break
            # Yield all elements of that resource
            for item in fixture.get(resource, []):
                yield (resource, item)
            # Remove it from the list of resources left
            deps.pop(resource)
            # Remove it from dependencies of other resources
            for dep in deps.values():
                try:
                    dep.remove(resource)
                except KeyError:
                    pass

    def new_object(self, resource, **kwargs):
        return self.load_fixture({resource: [kwargs]})[0]

    # Shortcuts to get a token
    counter = count()

    def get_user_token(self, user_id):
        """Create session for a user and return a token.

        Args:
            user_id (str): user_id as string.

        Returns:
            str: Token that can be used to authenticate user.
        """
        token = "test_token_" + str(next(self.counter))
        self.db['sessions'].insert({u'user': ObjectId(user_id),
                                    u'token': token})
        return token

    def get_root_token(self):
        """Create session for root user and return token.

        Returns:
            str: Token for the root user
        """
        return self.get_user_token(24 * "0")


class WebTestNoAuth(WebTest):
    """WebTest without authentification."""

    def setUp(self):
        """Use auth hook to always authenticate as root for every request."""
        super(WebTestNoAuth, self).setUp()

        def authenticate_root(resource):
            g.current_user = str(self.app.config['ROOT_ID'])
            g.resource_admin = True

        self.app.after_auth += authenticate_root
