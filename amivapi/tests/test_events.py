# -*- coding: utf-8 -*-
#
# AMIVAPI test_events.py
# Copyright (C) 2015 AMIV an der ETH, see AUTHORS for more details
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime, timedelta

from amivapi.tests import util

from amivapi.settings import DATE_FORMAT

import json


class EventTest(util.WebTestNoAuth):
    """ This class contains test for events"""
    def test_additional_fields(self):
        """ Test correct validation of 'additional_fields'"""
        start = datetime.today() + timedelta(days=2)
        # Not JSON
        self.api.post("/events", data={
            'time_start': start.strftime(DATE_FORMAT),
            'is_public': True,
            'price': 0,
            'spots': 10,
            'time_register_start': datetime.now().strftime(DATE_FORMAT),
            'time_register_end': start.strftime(DATE_FORMAT),
            'additional_fields': ['This', 'is', 'not', 'JSON']
        }, status_code=422)

        # Now JSON, but not a correct schema
        self.api.post("/events", data={
            'time_start': start.strftime(DATE_FORMAT),
            'is_public': True,
            'price': 0,
            'spots': 10,
            'time_register_start': datetime.now().strftime(DATE_FORMAT),
            'time_register_end': start.strftime(DATE_FORMAT),
            'additional_fields': json.dumps({
                'department': {
                    'type': 'lol'
                }
            })
        }, status_code=422)

        # Now everything correct
        self.api.post("/events", data={
            'time_start': start.strftime(DATE_FORMAT),
            'is_public': True,
            'price': 0,
            'spots': 10,
            'time_register_start': datetime.now().strftime(DATE_FORMAT),
            'time_register_end': start.strftime(DATE_FORMAT),
            'additional_fields': json.dumps({
                'department': {
                    'type': 'string',
                }
            })
        }, status_code=201)

        # Double check that its nullable
        self.api.post("/events", data={
            'time_start': start.strftime(DATE_FORMAT),
            'is_public': True,
            'price': 0,
            'spots': 10,
            'time_register_start': datetime.now().strftime(DATE_FORMAT),
            'time_register_end': start.strftime(DATE_FORMAT)
        }, status_code=201)

    def test_price(self):
        """Test price formatting, decimals and negativ numbers forbidden"""
        start = (datetime.today() + timedelta(days=21)).strftime(DATE_FORMAT)
        end = (datetime.today() + timedelta(days=42)).strftime(DATE_FORMAT)

        self.api.post("/events", data={
            'time_start': end,
            'is_public': True,
            'price': 0,
            'spots': 10,
            'time_register_start': start,
            'time_register_end': end
        }, status_code=201)

        self.api.post("/events", data={
            'time_start': end,
            'is_public': True,
            'price': 10.5,
            'spots': 10,
            'time_register_start': start,
            'time_register_end': end
        }, status_code=422)

        self.api.post("/events", data={
            'time_start': end,
            'is_public': True,
            'price': -10,
            'spots': 10,
            'time_register_start': start,
            'time_register_end': end
        }, status_code=422)

    def test_spots_and_time(self):
        """ This test will create an event with signup. This means registration
        times are required
        """
        time_1 = datetime.today().strftime(DATE_FORMAT)
        time_2 = (datetime.today() + timedelta(days=21)).strftime(DATE_FORMAT)
        time_3 = (datetime.today() + timedelta(days=42)).strftime(DATE_FORMAT)

        # Post without registration timee
        self.api.post("/events", data={
            'time_start': time_3,
            'is_public': True,
            'spots': 10,
        }, status_code=422)

        # Post only with one time

        self.api.post("/events", data={
            'time_start': time_3,
            'is_public': True,
            'spots': 10,
            'time_register_start': time_1
        }, status_code=422)

        self.api.post("/events", data={
            'time_start': time_3,
            'is_public': True,
            'spots': 10,
            'time_register_end': time_2
        }, status_code=422)

        # Post correctly
        self.api.post("/events", data={
            'time_start': time_3,
            'is_public': True,
            'spots': 10,
            'time_register_start': time_1,
            'time_register_end': time_2
        }, status_code=201)

    def test_swapped_time(self):
        """ Tests that end times have to be later or equal start times
        """
        time_1 = datetime.today().strftime(DATE_FORMAT)
        time_2 = (datetime.today() + timedelta(days=21)).strftime(DATE_FORMAT)
        time_3 = (datetime.today() + timedelta(days=42)).strftime(DATE_FORMAT)
        time_4 = (datetime.today() + timedelta(days=63)).strftime(DATE_FORMAT)

        # End before start
        self.api.post("/events", data={
            'time_start': time_4,
            'time_end': time_3,
            'is_public': True,
            'spots': 10,
            'time_register_start': time_2,
            'time_register_end': time_1
        }, status_code=422)

        self.api.post("/events", data={
            'time_start': time_3,
            'time_end': time_4,
            'is_public': True,
            'spots': 10,
            'time_register_start': time_2,
            'time_register_end': time_1
        }, status_code=422)

        self.api.post("/events", data={
            'time_start': time_4,
            'time_end': time_3,
            'is_public': True,
            'spots': 10,
            'time_register_start': time_1,
            'time_register_end': time_2
        }, status_code=422)

        # Now correct
        self.api.post("/events", data={
            'time_start': time_3,
            'time_end': time_4,
            'is_public': True,
            'spots': 10,
            'time_register_start': time_1,
            'time_register_end': time_2
        }, status_code=201)

        # Test incomplete
        self.api.post("/events", data={
            'time_end': time_4,
            'is_public': True,
            'spots': 10,
            'time_register_start': time_1,
            'time_register_end': time_2
        }, status_code=422)

        self.api.post("/events", data={
            'time_start': time_3,
            'is_public': True,
            'spots': 10,
            'time_register_end': time_2
        }, status_code=422)
