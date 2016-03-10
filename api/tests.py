# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from amqplib import client_0_8
from dateutil import parser
from django.contrib.gis.geos import fromstr
from django.test import TransactionTestCase
from pika import URLParameters
from rest_framework.test import APIClient

from api import middleware, models

from settings import BROKER


class Ads(TransactionTestCase):

    def setUp(self):
        self.user = middleware.mixer.blend('api.User')

        self.count = 10
        middleware.mixer.cycle(self.count).blend('api.Ad')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

    def test_a(self):
        response = self.client.get('/api/ads/', format='json')
        assert len(response.data) == self.count
        assert response.status_code == 200


class Blocks(TransactionTestCase):

    def setUp(self):
        self.user_1 = middleware.mixer.blend('api.User')
        self.user_2 = middleware.mixer.blend('api.User')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user_1.token))

    def test_a(self):
        response = self.client.get('/api/blocks/', format='json')
        assert response.data == []
        assert response.status_code == 200

        response = self.client.post(
            '/api/blocks/',
            {
                'user_destination_id': self.user_2.id,
                'report': True,
            },
            format='json',
        )
        assert response.data == {}
        assert response.status_code == 200

        response = self.client.get('/api/blocks/', format='json')
        assert len(response.data) == 1
        assert response.data[0]['user']['id'] == self.user_2.id
        assert response.status_code == 200

        response = self.client.post(
            '/api/tellcards/',
            {
                'user_destination_id': self.user_2.id,
                'location': 'Location',
                'action': 'View',
            },
            format='json',
        )
        assert response.status_code == 400

        response = self.client.post(
            '/api/messages/',
            {
                'user_destination_id': self.user_2.id,
                'type': 'Request',
                'contents': '1',
                'status': 'Unread',
            },
            format='json',
        )
        assert response.status_code == 400

        response = self.client.post(
            '/api/tellcards/',
            {
                'user_destination_id': self.user_2.id,
                'location': 'Location',
                'action': 'Save',
            },
            format='json',
        )
        assert response.status_code == 400

        response = self.client.get('/api/users/{id:d}/profile/'.format(id=self.user_2.id), format='json')
        assert response.status_code == 403

        response = self.client.post(
            '/api/blocks/delete/',
            {
                'user_destination_id': self.user_2.id,
                'report': True,
            },
            format='json',
        )
        assert response.data == {}
        assert response.status_code == 200

        response = self.client.get('/api/blocks/', format='json')
        assert response.data == []
        assert response.status_code == 200


class Categories(TransactionTestCase):

    def setUp(self):
        self.user = middleware.mixer.blend('api.User')

        for _ in range(0, 10):
            middleware.mixer.blend('api.Category', position=None)

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

    def test_a(self):
        response = self.client.get('/api/categories/', format='json')
        assert len(response.data) == 10
        assert sum([category['position'] for category in response.data]) == 55
        assert response.status_code == 200


class Deauthenticate(TransactionTestCase):

    def setUp(self):
        self.tellzone = middleware.mixer.blend('api.Tellzone')

        self.user = middleware.mixer.blend('api.User')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

    def test_a(self):
        assert self.user.is_signed_in is True

        response = self.client.post('/api/deauthenticate/', format='json')
        assert response.data == {}
        assert response.status_code == 200

        self.user = models.User.objects.get_queryset().filter(id=self.user.id).first()
        assert self.user is not None
        assert self.user.is_signed_in is False

    def test_b(self):
        dictionary = {
            'name': '1',
            'device_id': '1',
            'registration_id': '1',
        }

        response = self.client.post('/api/devices/apns/', dictionary, format='json')
        assert response.status_code == 201

        response = self.client.post('/api/devices/gcm/', dictionary, format='json')
        assert response.status_code == 201

        response = self.client.get('/api/devices/apns/', format='json')
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client.get('/api/devices/gcm/', format='json')
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client.post('/api/deauthenticate/', format='json')
        assert response.data == {}
        assert response.status_code == 200

        response = self.client.get('/api/devices/apns/', format='json')
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client.get('/api/devices/gcm/', format='json')
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client.post('/api/deauthenticate/', {}, format='json')
        assert response.data == {}
        assert response.status_code == 200

        response = self.client.get('/api/devices/apns/', format='json')
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client.get('/api/devices/gcm/', format='json')
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client.post(
            '/api/deauthenticate/',
            {
                'type': '',
                'device_id': '',
                'registration_id': '',
            },
            format='json',
        )
        assert response.data == {}
        assert response.status_code == 200

        response = self.client.get('/api/devices/apns/', format='json')
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client.get('/api/devices/gcm/', format='json')
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client.post(
            '/api/deauthenticate/',
            {
                'type': 'APNS',
                'registration_id': dictionary['registration_id'],
            },
            format='json',
        )
        assert response.data == {}
        assert response.status_code == 200

        response = self.client.post(
            '/api/deauthenticate/',
            {
                'type': 'GCM',
                'device_id': '0x{device_id:s}'.format(device_id=dictionary['device_id']),
            },
            format='json',
        )
        assert response.data == {}
        assert response.status_code == 200

        response = self.client.get('/api/devices/apns/', format='json')
        assert response.data == []
        assert response.status_code == 200

        response = self.client.get('/api/devices/gcm/', format='json')
        assert response.data == []
        assert response.status_code == 200


class DevicesAPNS(TransactionTestCase):

    def test_a(self):
        self.user = middleware.mixer.blend('api.User')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

        response = self.client.get('/api/devices/apns/', format='json')
        assert response.data == []
        assert response.status_code == 200

        dictionary = {
            'name': '1.1',
            'device_id': '1.1',
            'registration_id': '1',
        }

        response = self.client.post('/api/devices/apns/', dictionary, format='json')
        assert response.data['name'] == dictionary['name']
        assert response.data['device_id'] == dictionary['device_id']
        assert response.data['registration_id'] == dictionary['registration_id']
        assert response.status_code == 201

        id = response.data['id']

        response = self.client.get('/api/devices/apns/', format='json')
        assert len(response.data) == 1
        assert response.data[0]['id'] == id
        assert response.data[0]['name'] == dictionary['name']
        assert response.data[0]['device_id'] == dictionary['device_id']
        assert response.data[0]['registration_id'] == dictionary['registration_id']
        assert response.status_code == 200

        dictionary['name'] = '1.2'
        dictionary['device_id'] = '1.2'

        response = self.client.post('/api/devices/apns/', dictionary, format='json')
        assert response.data['id'] == id
        assert response.data['name'] == dictionary['name']
        assert response.data['device_id'] == dictionary['device_id']
        assert response.data['registration_id'] == dictionary['registration_id']
        assert response.status_code == 201

        response = self.client.get('/api/devices/apns/', format='json')
        assert len(response.data) == 1
        assert response.data[0]['id'] == id
        assert response.data[0]['name'] == dictionary['name']
        assert response.data[0]['device_id'] == dictionary['device_id']
        assert response.data[0]['registration_id'] == dictionary['registration_id']
        assert response.status_code == 200

        dictionary = {
            'name': '2.1',
            'device_id': '2.1',
            'registration_id': '2',
        }

        response = self.client.post('/api/devices/apns/', dictionary, format='json')
        assert response.data['name'] == dictionary['name']
        assert response.data['device_id'] == dictionary['device_id']
        assert response.data['registration_id'] == dictionary['registration_id']
        assert response.status_code == 201

        response = self.client.get('/api/devices/apns/', format='json')
        assert len(response.data) == 2
        assert response.status_code == 200

        response = self.client.delete('/api/devices/apns/{id:d}/'.format(id=id), format='json')
        assert response.data == {}
        assert response.status_code == 200

        response = self.client.get('/api/devices/apns/', format='json')
        assert len(response.data) == 1
        assert response.status_code == 200

    def test_b(self):
        self.user_1 = middleware.mixer.blend('api.User')
        self.client_1 = APIClient()
        self.client_1.credentials(HTTP_AUTHORIZATION=get_header(self.user_1.token))

        self.user_2 = middleware.mixer.blend('api.User')
        self.client_2 = APIClient()
        self.client_2.credentials(HTTP_AUTHORIZATION=get_header(self.user_2.token))

        response = self.client_1.get('/api/devices/apns/', format='json')
        assert response.data == []
        assert response.status_code == 200

        response = self.client_2.get('/api/devices/apns/', format='json')
        assert response.data == []
        assert response.status_code == 200

        dictionary = {
            'name': '1',
            'device_id': '1',
            'registration_id': '1',
        }

        response = self.client_1.post('/api/devices/apns/', dictionary, format='json')
        assert response.data['name'] == dictionary['name']
        assert response.data['device_id'] == dictionary['device_id']
        assert response.data['registration_id'] == dictionary['registration_id']
        assert response.status_code == 201

        id = response.data['id']

        response = self.client_1.get('/api/devices/apns/', format='json')
        assert len(response.data) == 1
        assert response.data[0]['id'] == id
        assert response.data[0]['name'] == dictionary['name']
        assert response.data[0]['device_id'] == dictionary['device_id']
        assert response.data[0]['registration_id'] == dictionary['registration_id']
        assert response.status_code == 200

        response = self.client_2.get('/api/devices/apns/', format='json')
        assert response.data == []
        assert response.status_code == 200

        response = self.client_2.post('/api/devices/apns/', dictionary, format='json')
        assert response.data['name'] == dictionary['name']
        assert response.data['device_id'] == dictionary['device_id']
        assert response.data['registration_id'] == dictionary['registration_id']
        assert response.status_code == 201

        id = response.data['id']

        response = self.client_1.get('/api/devices/apns/', format='json')
        assert response.data == []
        assert response.status_code == 200

        response = self.client_2.get('/api/devices/apns/', format='json')
        assert len(response.data) == 1
        assert response.data[0]['id'] == id
        assert response.data[0]['name'] == dictionary['name']
        assert response.data[0]['device_id'] == dictionary['device_id']
        assert response.data[0]['registration_id'] == dictionary['registration_id']
        assert response.status_code == 200


class DevicesGCM(TransactionTestCase):

    def test_a(self):
        self.user = middleware.mixer.blend('api.User')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

        response = self.client.get('/api/devices/gcm/', format='json')
        assert response.data == []
        assert response.status_code == 200

        dictionary = {
            'name': '1',
            'device_id': '0x1',
            'registration_id': '1',
        }

        response = self.client.post('/api/devices/gcm/', dictionary, format='json')
        assert response.data['name'] == dictionary['name']
        assert response.data['device_id'] == dictionary['device_id']
        assert response.data['registration_id'] == dictionary['registration_id']
        assert response.status_code == 201

        id = response.data['id']

        response = self.client.get('/api/devices/gcm/', format='json')
        assert len(response.data) == 1
        assert response.data[0]['id'] == id
        assert response.data[0]['name'] == dictionary['name']
        assert response.data[0]['device_id'] == dictionary['device_id']
        assert response.data[0]['registration_id'] == dictionary['registration_id']
        assert response.status_code == 200

        dictionary['name'] = '2'
        dictionary['registration_id'] = '2'

        response = self.client.post('/api/devices/gcm/', dictionary, format='json')
        assert response.data['id'] == id
        assert response.data['name'] == dictionary['name']
        assert response.data['device_id'] == dictionary['device_id']
        assert response.data['registration_id'] == dictionary['registration_id']
        assert response.status_code == 201

        response = self.client.get('/api/devices/gcm/', format='json')
        assert len(response.data) == 1
        assert response.data[0]['id'] == id
        assert response.data[0]['name'] == dictionary['name']
        assert response.data[0]['device_id'] == dictionary['device_id']
        assert response.data[0]['registration_id'] == dictionary['registration_id']
        assert response.status_code == 200

        dictionary = {
            'name': '2',
            'device_id': '0x2',
            'registration_id': '2',
        }

        response = self.client.post('/api/devices/gcm/', dictionary, format='json')
        assert response.data['name'] == dictionary['name']
        assert response.data['device_id'] == dictionary['device_id']
        assert response.data['registration_id'] == dictionary['registration_id']
        assert response.status_code == 201

        response = self.client.get('/api/devices/gcm/', format='json')
        assert len(response.data) == 2
        assert response.status_code == 200

        response = self.client.delete('/api/devices/gcm/{id:d}/'.format(id=id), format='json')
        assert response.data == {}
        assert response.status_code == 200

        response = self.client.get('/api/devices/gcm/', format='json')
        assert len(response.data) == 1
        assert response.status_code == 200

    def test_b(self):
        self.user_1 = middleware.mixer.blend('api.User')
        self.client_1 = APIClient()
        self.client_1.credentials(HTTP_AUTHORIZATION=get_header(self.user_1.token))

        self.user_2 = middleware.mixer.blend('api.User')
        self.client_2 = APIClient()
        self.client_2.credentials(HTTP_AUTHORIZATION=get_header(self.user_2.token))

        response = self.client_1.get('/api/devices/gcm/', format='json')
        assert response.data == []
        assert response.status_code == 200

        response = self.client_2.get('/api/devices/gcm/', format='json')
        assert response.data == []
        assert response.status_code == 200

        dictionary = {
            'name': '1',
            'device_id': '0x1',
            'registration_id': '1',
        }

        response = self.client_1.post('/api/devices/gcm/', dictionary, format='json')
        assert response.data['name'] == dictionary['name']
        assert response.data['device_id'] == dictionary['device_id']
        assert response.data['registration_id'] == dictionary['registration_id']
        assert response.status_code == 201

        id = response.data['id']

        response = self.client_1.get('/api/devices/gcm/', format='json')
        assert len(response.data) == 1
        assert response.data[0]['id'] == id
        assert response.data[0]['name'] == dictionary['name']
        assert response.data[0]['device_id'] == dictionary['device_id']
        assert response.data[0]['registration_id'] == dictionary['registration_id']
        assert response.status_code == 200

        response = self.client_2.get('/api/devices/gcm/', format='json')
        assert response.data == []
        assert response.status_code == 200

        response = self.client_2.post('/api/devices/gcm/', dictionary, format='json')
        assert response.data['name'] == dictionary['name']
        assert response.data['device_id'] == dictionary['device_id']
        assert response.data['registration_id'] == dictionary['registration_id']
        assert response.status_code == 201

        id = response.data['id']

        response = self.client_1.get('/api/devices/gcm/', format='json')
        assert response.data == []
        assert response.status_code == 200

        response = self.client_2.get('/api/devices/gcm/', format='json')
        assert len(response.data) == 1
        assert response.data[0]['id'] == id
        assert response.data[0]['name'] == dictionary['name']
        assert response.data[0]['device_id'] == dictionary['device_id']
        assert response.data[0]['registration_id'] == dictionary['registration_id']
        assert response.status_code == 200


class Home(TransactionTestCase):

    def setUp(self):
        self.user = middleware.mixer.blend('api.User')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

    def test_a(self):
        category = middleware.mixer.blend('api.Category')

        network = middleware.mixer.blend('api.Network')

        tellzone = middleware.mixer.blend('api.Tellzone', user=None)
        tellzone.point = get_point()
        tellzone.save()

        network_tellzone = middleware.mixer.blend('api.NetworkTellzone', network=network, tellzone=tellzone)
        network_tellzone.save()

        with middleware.mixer.ctx(commit=False):
            for user in middleware.mixer.cycle(5).blend('api.User'):
                user.point = get_point()
                user.is_signed_in = True
                user.save()

                for master_tell in middleware.mixer.cycle(5).blend(
                    'api.MasterTell', created_by=user, owned_by=user, category=category,
                ):
                    master_tell.contents = str(user.id)
                    master_tell.save()

                client = APIClient()
                client.credentials(HTTP_AUTHORIZATION=get_header(user.token))
                response = client.post(
                    '/api/radar/',
                    {
                        'network_id': network.id,
                        'tellzone_id': tellzone.id,
                        'point': {
                            'latitude': 1.00,
                            'longitude': 1.00,
                        },
                        'accuracies_horizontal': 1.00,
                        'accuracies_vertical': 1.00,
                        'is_casting': True,
                    },
                    format='json',
                )
                assert len(response.data) == 1
                assert 'id' in response.data[0]
                assert 'name' in response.data[0]
                assert response.status_code == 200

        response = self.client.get(
            '/api/home/master-tells/',
            {
                'latitude': 1.00,
                'longitude': 1.00,
            },
            format='json',
        )
        assert len(response.data) == 25
        assert response.status_code == 200

        response = self.client.get(
            '/api/home/master-tells/',
            {
                'latitude': 1.00,
                'longitude': 1.00,
                'tellzone_id': models.Tellzone.objects.get_queryset().order_by('?').first().id,
            },
            format='json',
        )
        assert len(response.data) == 0
        assert response.status_code == 200

    def test_b(self):
        network = middleware.mixer.blend('api.Network')

        tellzone = middleware.mixer.blend('api.Tellzone', user=None)
        tellzone.point = get_point()
        tellzone.save()

        network_tellzone = middleware.mixer.blend('api.NetworkTellzone', network=network, tellzone=tellzone)
        network_tellzone.save()

        with middleware.mixer.ctx(commit=False):
            for user in middleware.mixer.cycle(5).blend('api.User'):
                user.point = get_point()
                user.is_signed_in = True
                user.save()

                client = APIClient()
                client.credentials(HTTP_AUTHORIZATION=get_header(user.token))
                response = client.post(
                    '/api/radar/',
                    {
                        'network_id': network.id,
                        'tellzone_id': tellzone.id,
                        'point': {
                            'latitude': 1.00,
                            'longitude': 1.00,
                        },
                        'accuracies_horizontal': 1.00,
                        'accuracies_vertical': 1.00,
                        'is_casting': True,
                    },
                    format='json',
                )
                assert len(response.data) == 1
                assert 'id' in response.data[0]
                assert 'name' in response.data[0]
                assert response.status_code == 200

        dictionary = {
            'latitude': 1.00,
            'longitude': 1.00,
            'dummy': 'No',
        }

        response = self.client.get('/api/home/connections/', dictionary, format='json')
        assert 'days' in response.data
        assert len(response.data['days'].keys()) == 7
        assert 'trailing_24_hours' in response.data
        assert 'users' in response.data
        assert len(response.data['users']) == 0
        assert response.status_code == 200

        response = self.client.get('/api/home/statistics/frequent/', dictionary, format='json')
        assert 'views' in response.data
        assert 'today' in response.data['views']
        assert 'total' in response.data['views']
        assert 'saves' in response.data
        assert 'today' in response.data['saves']
        assert 'total' in response.data['saves']
        assert 'users' in response.data
        assert 'area' in response.data['users']
        assert 'near' in response.data['users']
        assert response.status_code == 200

        response = self.client.get('/api/home/statistics/infrequent/', dictionary, format='json')
        assert 'views' in response.data
        assert 'days' in response.data['views']
        assert 'weeks' in response.data['views']
        assert 'months' in response.data['views']
        assert 'saves' in response.data
        assert 'days' in response.data['saves']
        assert 'weeks' in response.data['saves']
        assert 'months' in response.data['saves']
        assert response.status_code == 200

    def test_c(self):
        count = 5

        for tellzone in middleware.mixer.cycle(count).blend('api.Tellzone', user=None):
            tellzone.point = get_point()
            tellzone.save()

        response = self.client.get(
            '/api/home/tellzones/',
            {
                'latitude': 1.00,
                'longitude': 1.00,
                'dummy': 'No',
            },
            format='json',
        )
        assert len(response.data) == count
        assert response.status_code == 200


class MasterTells(TransactionTestCase):

    def setUp(self):
        self.user_1 = middleware.mixer.blend('api.User')
        self.client_1 = APIClient()
        self.client_1.credentials(HTTP_AUTHORIZATION=get_header(self.user_1.token))

        self.user_2 = middleware.mixer.blend('api.User')
        self.client_2 = APIClient()
        self.client_2.credentials(HTTP_AUTHORIZATION=get_header(self.user_2.token))

        self.category = middleware.mixer.blend('api.Category')
        self.tellzone = middleware.mixer.blend('api.Tellzone')

    def test_a(self):
        dictionary = {
            'user_id': self.user_1.id,
            'tellzone_id': 0,
        }
        response = self.client_1.get('/api/master-tells/all/', dictionary, format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

        dictionary = {
            'user_id': self.user_1.id,
            'tellzone_id': self.tellzone.id,
        }
        response = self.client_1.get('/api/master-tells/all/', dictionary, format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

        response = self.client_1.post(
            '/api/users/{id:d}/tellzones/'.format(id=self.user_1.id),
            {
                'tellzone_id': self.tellzone.id,
                'action': 'Pin',
            },
            format='json',
        )
        assert response.data['tellzone_id'] == self.tellzone.id
        assert response.status_code == 201

        dictionary = {
            'category_id': self.category.id,
            'contents': '1',
            'description': '1',
            'position': 1,
            'tellzones': [
                self.tellzone.id,
            ],
        }
        response = self.client_2.post('/api/master-tells/', dictionary, format='json')
        assert response.data['created_by_id'] == self.user_2.id
        assert response.data['owned_by_id'] == self.user_2.id
        assert response.data['category']['id'] == dictionary['category_id']
        assert response.data['contents'] == dictionary['contents']
        assert response.data['description'] == dictionary['description']
        assert response.data['position'] == 1
        assert response.data['is_visible'] is True
        assert len(response.data['tellzones']) == 1
        assert response.data['tellzones'][0]['id'] == dictionary['tellzones'][0]
        assert response.status_code == 201

        dictionary = {
            'user_id': self.user_1.id,
            'tellzone_id': 0,
        }
        response = self.client_1.get('/api/master-tells/all/', dictionary, format='json')
        assert len(response.data) == 1
        assert response.status_code == 200

        dictionary = {
            'user_id': self.user_1.id,
            'tellzone_id': self.tellzone.id,
        }
        response = self.client_1.get('/api/master-tells/all/', dictionary, format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

        response = self.client_1.delete(
            '/api/users/{id:d}/tellzones/'.format(id=self.user_1.id),
            {
                'tellzone_id': self.tellzone.id,
                'action': 'Pin',
            },
            format='json',
        )
        assert response.status_code == 200

        dictionary = {
            'user_id': self.user_1.id,
            'tellzone_id': 0,
        }
        response = self.client_1.get('/api/master-tells/all/', dictionary, format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

        dictionary = {
            'user_id': self.user_1.id,
            'tellzone_id': self.tellzone.id,
        }
        response = self.client_1.get('/api/master-tells/all/', dictionary, format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

        dictionary = {
            'category_id': self.category.id,
            'contents': '1',
            'description': '1',
            'position': 1,
            'tellzones': [
                self.tellzone.id,
            ],
        }
        response = self.client_1.post('/api/master-tells/', dictionary, format='json')
        assert response.data['created_by_id'] == self.user_1.id
        assert response.data['owned_by_id'] == self.user_1.id
        assert response.data['category']['id'] == dictionary['category_id']
        assert response.data['contents'] == dictionary['contents']
        assert response.data['description'] == dictionary['description']
        assert response.data['position'] == 1
        assert response.data['is_visible'] is True
        assert len(response.data['tellzones']) == 1
        assert response.data['tellzones'][0]['id'] == dictionary['tellzones'][0]
        assert response.status_code == 201

        dictionary = {
            'user_id': self.user_1.id,
            'tellzone_id': 0,
        }
        response = self.client_1.get('/api/master-tells/all/', dictionary, format='json')
        assert len(response.data) == 1
        assert response.status_code == 200

        dictionary = {
            'user_id': self.user_1.id,
            'tellzone_id': self.tellzone.id,
        }
        response = self.client_1.get('/api/master-tells/all/', dictionary, format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

    def test_b(self):
        response = self.client_1.get('/api/master-tells/', format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

        dictionary = {
            'category_id': self.category.id,
            'contents': '1',
            'description': '1',
            'position': 1,
            'tellzones': [
                self.tellzone.id,
            ],
        }

        response = self.client_1.post('/api/master-tells/', dictionary, format='json')
        assert response.data['created_by_id'] == self.user_1.id
        assert response.data['owned_by_id'] == self.user_1.id
        assert response.data['category']['id'] == dictionary['category_id']
        assert response.data['contents'] == dictionary['contents']
        assert response.data['description'] == dictionary['description']
        assert response.data['position'] == 1
        assert response.data['is_visible'] is True
        assert len(response.data['tellzones']) == 1
        assert response.data['tellzones'][0]['id'] == dictionary['tellzones'][0]
        assert response.status_code == 201

        del dictionary['position']

        response = self.client_1.post('/api/master-tells/', dictionary, format='json')
        assert response.data['created_by_id'] == self.user_1.id
        assert response.data['owned_by_id'] == self.user_1.id
        assert response.data['category']['id'] == dictionary['category_id']
        assert response.data['contents'] == dictionary['contents']
        assert response.data['description'] == dictionary['description']
        assert response.data['position'] == 2
        assert response.data['is_visible'] is True
        assert len(response.data['tellzones']) == 1
        assert response.data['tellzones'][0]['id'] == dictionary['tellzones'][0]
        assert response.status_code == 201

        id = response.data['id']

        inserted_at = parser.parse(response.data['inserted_at'])
        updated_at = parser.parse(response.data['updated_at'])

        response = self.client_1.get('/api/master-tells/', format='json')
        assert len(response.data) == 2
        assert response.status_code == 200

        response = self.client_1.get(
            '/api/master-tells/',
            {
                'inserted_at': inserted_at - timedelta(seconds=10),
            },
            format='json',
        )
        assert len(response.data) == 2
        assert response.status_code == 200

        list_ = [{
            'id': id,
            'position': 1,
        }]

        response = self.client_1.post('/api/master-tells/positions/', list_, format='json')
        assert response.data[0]['created_by_id'] == self.user_1.id
        assert response.data[0]['owned_by_id'] == self.user_1.id
        assert response.data[0]['category']['id'] == dictionary['category_id']
        assert response.data[0]['position'] == list_[0]['position']
        assert response.data[0]['is_visible'] is True
        assert len(response.data[0]['tellzones']) == 1
        assert response.data[0]['tellzones'][0]['id'] == dictionary['tellzones'][0]
        assert response.status_code == 200

        response = self.client_1.get(
            '/api/master-tells/',
            {
                'inserted_at': inserted_at + timedelta(seconds=10),
            },
            format='json',
        )
        assert response.data == []
        assert response.status_code == 200

        response = self.client_1.get(
            '/api/master-tells/',
            {
                'updated_at': updated_at - timedelta(seconds=10),
            },
            format='json',
        )
        assert len(response.data) == 2
        assert response.status_code == 200

        response = self.client_1.get(
            '/api/master-tells/',
            {
                'updated_at': updated_at + timedelta(seconds=10),
            },
            format='json',
        )
        assert response.data == []
        assert response.status_code == 200

        dictionary = {
            'category_id': self.category.id,
            'contents': '2',
            'description': '2',
            'position': 2,
            'tellzones': [],
        }

        response = self.client_1.put('/api/master-tells/{id:d}/'.format(id=id), dictionary, format='json')
        assert response.data['id'] == id
        assert response.data['created_by_id'] == self.user_1.id
        assert response.data['owned_by_id'] == self.user_1.id
        assert response.data['category']['id'] == dictionary['category_id']
        assert response.data['contents'] == dictionary['contents']
        assert response.data['description'] == dictionary['description']
        assert response.data['position'] == dictionary['position']
        assert response.data['is_visible'] is True
        assert len(response.data['tellzones']) == 0
        assert response.status_code == 200

        del dictionary['position']

        response = self.client_1.put('/api/master-tells/{id:d}/'.format(id=id), dictionary, format='json')
        assert response.data['id'] == id
        assert response.data['created_by_id'] == self.user_1.id
        assert response.data['owned_by_id'] == self.user_1.id
        assert response.data['category']['id'] == dictionary['category_id']
        assert response.data['contents'] == dictionary['contents']
        assert response.data['description'] == dictionary['description']
        assert response.data['position'] == 2
        assert response.data['is_visible'] is True
        assert len(response.data['tellzones']) == 0
        assert response.status_code == 200

        dictionary = {
            'category_id': self.category.id,
            'contents': '3',
            'description': '3',
            'position': 3,
            'tellzones': [
                self.tellzone.id,
            ],
        }

        response = self.client_1.patch('/api/master-tells/{id:d}/'.format(id=id), dictionary, format='json')
        assert response.data['id'] == id
        assert response.data['created_by_id'] == self.user_1.id
        assert response.data['owned_by_id'] == self.user_1.id
        assert response.data['category']['id'] == dictionary['category_id']
        assert response.data['contents'] == dictionary['contents']
        assert response.data['description'] == dictionary['description']
        assert response.data['position'] == dictionary['position']
        assert response.data['is_visible'] is True
        assert len(response.data['tellzones']) == 1
        assert response.data['tellzones'][0]['id'] == dictionary['tellzones'][0]
        assert response.status_code == 200

        del dictionary['position']

        response = self.client_1.patch('/api/master-tells/{id:d}/'.format(id=id), dictionary, format='json')
        assert response.data['id'] == id
        assert response.data['created_by_id'] == self.user_1.id
        assert response.data['owned_by_id'] == self.user_1.id
        assert response.data['category']['id'] == dictionary['category_id']
        assert response.data['contents'] == dictionary['contents']
        assert response.data['description'] == dictionary['description']
        assert response.data['position'] == 3
        assert response.data['is_visible'] is True
        assert len(response.data['tellzones']) == 1
        assert response.data['tellzones'][0]['id'] == dictionary['tellzones'][0]
        assert response.status_code == 200

        response = self.client_1.get('/api/master-tells/ids/', format='json')
        assert len(response.data) == 2
        assert response.data[1] == id
        assert response.status_code == 200

        response = self.client_1.delete('/api/master-tells/{id:d}/'.format(id=id), format='json')
        assert response.data == {}
        assert response.status_code == 200

        response = self.client_1.get('/api/master-tells/', format='json')
        assert len(response.data) == 1
        assert response.status_code == 200


class Messages(TransactionTestCase):

    def setUp(self):
        self.user_1 = middleware.mixer.blend('api.User')
        self.client_1 = APIClient()
        self.client_1.credentials(HTTP_AUTHORIZATION=get_header(self.user_1.token))

        self.user_2 = middleware.mixer.blend('api.User')
        self.client_2 = APIClient()
        self.client_2.credentials(HTTP_AUTHORIZATION=get_header(self.user_2.token))

        self.category = middleware.mixer.blend('api.Category')

        self.user_status = middleware.mixer.blend('api.UserStatus', user=self.user_1)
        self.master_tell = middleware.mixer.blend(
            'api.MasterTell', created_by=self.user_1, owned_by=self.user_1, category=self.category,
        )
        self.post = middleware.mixer.blend('api.Post', user=self.user_1)

    def test_a(self):
        response = self.client_1.get(
            '/api/messages/',
            {
                'recent': 'True',
            },
            format='json',
        )
        assert len(response.data) == 0
        assert response.status_code == 200

        response = self.client_1.get(
            '/api/messages/',
            {
                'user_id': self.user_2.id,
            },
            format='json',
        )
        assert len(response.data) == 0
        assert response.status_code == 200

        dictionary = {
            'user_destination_id': self.user_2.id,
            'type': 'Message',
            'contents': '1',
            'status': 'Unread',
        }

        response = self.client_1.post('/api/messages/', dictionary, format='json')
        assert response.status_code == 403

        dictionary['type'] = 'Request'

        response = self.client_1.post('/api/messages/', dictionary, format='json')
        assert response.data['user_source']['id'] == self.user_1.id
        assert response.data['user_source_is_hidden'] is False
        assert response.data['user_destination']['id'] == dictionary['user_destination_id']
        assert response.data['user_destination_is_hidden'] is False
        assert response.data['user_status'] is None
        assert response.data['master_tell'] is None
        assert response.data['post_id'] is None
        assert response.data['type'] == dictionary['type']
        assert response.data['contents'] == dictionary['contents']
        assert response.data['status'] == dictionary['status']
        assert response.data['attachments'] == []
        assert response.status_code == 201

        id = response.data['id']

        response = self.client_1.post('/api/messages/', dictionary, format='json')
        assert response.status_code == 409

        dictionary['status'] = 'Read'

        response = self.client_1.patch('/api/messages/{id:d}/'.format(id=id), dictionary, format='json')
        assert response.data['id'] == id
        assert response.data['contents'] == dictionary['contents']
        assert response.status_code == 200

        dictionary = {
            'user_destination_id': self.user_1.id,
            'type': 'Response - Accepted',
            'contents': '1',
            'status': 'Unread',
            'attachments': [
                {
                    'string': '1',
                    'position': 1,
                },
            ],
        }

        response = self.client_2.post('/api/messages/', dictionary, format='json')
        assert response.data['user_source']['id'] == self.user_2.id
        assert response.data['user_source_is_hidden'] is False
        assert response.data['user_destination']['id'] == dictionary['user_destination_id']
        assert response.data['user_destination_is_hidden'] is False
        assert response.data['user_status'] is None
        assert response.data['master_tell'] is None
        assert response.data['post_id'] is None
        assert response.data['type'] == dictionary['type']
        assert response.data['contents'] == dictionary['contents']
        assert response.data['status'] == dictionary['status']
        assert len(response.data['attachments']) == 1
        assert response.data['attachments'][0]['position'] == 1
        assert response.status_code == 201

        dictionary['post_id'] = self.post.id
        dictionary['user_destination_id'] = self.user_2.id
        dictionary['type'] = 'Message'
        dictionary['status'] = 'Unread'

        response = self.client_1.post('/api/messages/', dictionary, format='json')
        assert response.data['user_source']['id'] == self.user_1.id
        assert response.data['user_source_is_hidden'] is False
        assert response.data['user_destination']['id'] == dictionary['user_destination_id']
        assert response.data['user_destination_is_hidden'] is False
        assert response.data['user_status'] is None
        assert response.data['master_tell'] is None
        assert response.data['post_id'] == dictionary['post_id']
        assert response.data['type'] == dictionary['type']
        assert response.data['contents'] == dictionary['contents']
        assert response.data['status'] == dictionary['status']
        assert len(response.data['attachments']) == 1
        assert response.data['attachments'][0]['position'] == 1
        assert response.status_code == 201

        response = self.client_1.get(
            '/api/messages/',
            {
                'recent': 'True',
            },
            format='json',
        )
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client_1.get(
            '/api/messages/',
            {
                'user_id': self.user_2.id,
            },
            format='json',
        )
        assert len(response.data) == 3
        assert response.status_code == 200

        response = self.client_1.post(
            '/api/messages/bulk/is_hidden/',
            {
                'user_id': self.user_2.id,
            },
            format='json',
        )
        for message in response.data:
            assert message['user_source']['id'] in [self.user_1.id, self.user_2.id]
            assert message['user_destination']['id'] in [self.user_1.id, self.user_2.id]
            assert (
                (message['user_source']['id'] == self.user_1.id and message['user_source_is_hidden'] is True) or
                (message['user_destination']['id'] == self.user_1.id and message['user_destination_is_hidden'] is True)
            )
        assert response.status_code == 200

        response = self.client_1.post(
            '/api/messages/bulk/status/',
            {
                'user_id': self.user_2.id,
            },
            format='json',
        )
        for message in response.data:
            assert message['user_source']['id'] == self.user_2.id
            assert message['user_destination']['id'] == self.user_1.id
            assert message['status'] == 'Read'
        assert response.status_code == 200

        response = self.client_1.delete('/api/messages/{id:d}/'.format(id=id), format='json')
        assert response.data == {}
        assert response.status_code == 200

    def test_b(self):
        self.message_1 = middleware.mixer.blend(
            'api.Message',
            user_source=self.user_1,
            user_destination=self.user_2,
            type='Message'
        )
        self.message_2 = middleware.mixer.blend(
            'api.Message',
            user_source=self.user_1,
            user_destination=self.user_2,
            type='Message'
        )
        self.message_3 = middleware.mixer.blend(
            'api.Message',
            user_source=self.user_1,
            user_destination=self.user_2,
            type='Message'
        )
        self.message_4 = middleware.mixer.blend(
            'api.Message',
            user_source=self.user_1,
            user_destination=self.user_2,
            user_status_id=self.user_status.id,
            type='Message'
        )
        self.message_5 = middleware.mixer.blend(
            'api.Message',
            user_source=self.user_1,
            user_destination=self.user_2,
            master_tell_id=self.master_tell.id,
            type='Message'
        )
        self.message_6 = middleware.mixer.blend(
            'api.Message',
            user_source=self.user_1,
            user_destination=self.user_2,
            post_id=self.post.id,
            type='Message'
        )

        response = self.client_1.get('/api/messages/?recent=True', format='json')
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client_1.get('/api/messages/?recent=False', format='json')
        assert len(response.data) == 6
        assert response.status_code == 200

        response = self.client_1.get(
            '/api/messages/?recent=False&user_id={user_id:d}'.format(user_id=self.user_2.id),
            format='json',
        )
        assert len(response.data) == 6
        assert response.status_code == 200

        response = self.client_1.get(
            '/api/messages/?recent=False&user_id=0',
            format='json',
        )
        assert len(response.data) == 6
        assert response.status_code == 200

        response = self.client_1.get(
            '/api/messages/?recent=False&user_status_id={user_status_id:d}'.format(user_status_id=self.user_status.id),
            format='json',
        )
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client_1.get(
            '/api/messages/?recent=False&master_tell_id={master_tell_id:d}'.format(master_tell_id=self.master_tell.id),
            format='json',
        )
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client_1.get(
            '/api/messages/?recent=False&post_id={post_id:d}'.format(post_id=self.post.id),
            format='json',
        )
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client_1.get(
            '/api/messages/?recent=False&since_id={message_id:d}'.format(message_id=self.message_2.id),
            format='json',
        )
        assert len(response.data) == 4
        assert response.status_code == 200

        response = self.client_1.get(
            '/api/messages/?recent=False&max_id={message_id:d}'.format(message_id=self.message_2.id),
            format='json',
        )
        assert len(response.data) == 1
        assert response.status_code == 200

    def test_c(self):
        response = self.client_1.get('/api/users/{id:d}/profile/'.format(id=self.user_2.id), format='json')
        assert response.data['messages'] == 0

        dictionary = {
            'user_destination_id': self.user_2.id,
            'type': 'Request',
            'contents': '1',
            'status': 'Unread',
        }

        response = self.client_1.post('/api/messages/', dictionary, format='json')
        assert response.status_code == 201

        response = self.client_1.get('/api/users/{id:d}/profile/'.format(id=self.user_2.id), format='json')
        assert response.data['messages'] == 1

        dictionary = {
            'user_destination_id': self.user_1.id,
            'type': 'Response - Blocked',
            'contents': '1',
            'status': 'Unread',
        }

        response = self.client_2.post('/api/messages/', dictionary, format='json')
        assert response.status_code == 201

        dictionary = {
            'user_destination_id': self.user_1.id,
            'type': 'Message',
            'contents': '1',
            'status': 'Unread',
        }

        response = self.client_2.post('/api/messages/', dictionary, format='json')
        assert response.status_code == 400

        dictionary = {
            'user_destination_id': self.user_2.id,
            'type': 'Message',
            'contents': '1',
            'status': 'Unread',
        }

        response = self.client_1.post('/api/messages/', dictionary, format='json')
        assert response.status_code == 400

        dictionary = {
            'user_destination_id': self.user_2.id,
            'type': 'Request',
            'contents': '1',
            'status': 'Unread',
        }

        response = self.client_1.post('/api/messages/', dictionary, format='json')
        assert response.status_code == 400

    def test_d(self):
        dictionary = {
            'user_destination_id': self.user_2.id,
            'type': 'Request',
            'contents': '1',
            'status': 'Unread',
        }

        response = self.client_1.post('/api/messages/', dictionary, format='json')
        assert response.status_code == 201

        response = self.client_1.get('/api/users/{id:d}/profile/'.format(id=self.user_2.id), format='json')
        assert response.data['messages'] == 1

        dictionary = {
            'user_destination_id': self.user_1.id,
            'type': 'Response - Rejected',
            'contents': '1',
            'status': 'Unread',
        }

        response = self.client_2.post('/api/messages/', dictionary, format='json')
        assert response.status_code == 201

        response = self.client_1.get('/api/users/{id:d}/profile/'.format(id=self.user_2.id), format='json')
        assert response.data['messages'] == 0

        dictionary = {
            'user_destination_id': self.user_2.id,
            'type': 'Request',
            'contents': '1',
            'status': 'Unread',
        }

        response = self.client_1.post('/api/messages/', dictionary, format='json')
        assert response.status_code == 201

        response = self.client_1.get('/api/users/{id:d}/profile/'.format(id=self.user_2.id), format='json')
        assert response.data['messages'] == 1

        dictionary = {
            'user_destination_id': self.user_1.id,
            'type': 'Response - Accepted',
            'contents': '1',
            'status': 'Unread',
        }

        response = self.client_2.post('/api/messages/', dictionary, format='json')
        assert response.status_code == 201

        response = self.client_1.get('/api/users/{id:d}/profile/'.format(id=self.user_2.id), format='json')
        assert response.data['messages'] == 2

        dictionary = {
            'user_destination_id': self.user_1.id,
            'type': 'Message',
            'contents': '1',
            'status': 'Unread',
        }

        response = self.client_2.post('/api/messages/', dictionary, format='json')
        assert response.status_code == 201

        response = self.client_1.get('/api/users/{id:d}/profile/'.format(id=self.user_2.id), format='json')
        assert response.data['messages'] == 2

        dictionary = {
            'user_destination_id': self.user_2.id,
            'type': 'Message',
            'contents': '1',
            'status': 'Unread',
        }

        response = self.client_1.post('/api/messages/', dictionary, format='json')
        assert response.status_code == 201

        response = self.client_1.get('/api/users/{id:d}/profile/'.format(id=self.user_2.id), format='json')
        assert response.data['messages'] == 2


class Networks(TransactionTestCase):

    def test_a(self):
        user = middleware.mixer.blend('api.User', type='Root')

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=get_header(user.token))

        tellzone = middleware.mixer.blend('api.Tellzone', user=None)

        response = client.get('/api/networks/', format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

        dictionary = {
            'name': '1',
            'tellzones': [
                tellzone.id,
            ],
        }

        response = client.post('/api/networks/', dictionary, format='json')
        assert response.data['name'] == dictionary['name']
        assert len(response.data['tellzones']) == 0
        assert response.status_code == 201

        id = response.data['id']

        tellzone = middleware.mixer.blend('api.Tellzone', user=user)

        dictionary = {
            'name': '2',
            'tellzones': [
                tellzone.id,
            ],
        }

        response = client.put('/api/networks/{id:d}/'.format(id=id), dictionary, format='json')
        assert response.data['name'] == dictionary['name']
        assert len(response.data['tellzones']) == 1
        assert response.status_code == 200

        dictionary = {
            'name': '3',
        }

        response = client.patch('/api/networks/{id:d}/'.format(id=id), dictionary, format='json')
        assert response.data['name'] == dictionary['name']
        assert len(response.data['tellzones']) == 1
        assert response.status_code == 200

        dictionary = {
            'name': '3',
            'tellzones': [],
        }

        response = client.patch('/api/networks/{id:d}/'.format(id=id), dictionary, format='json')
        assert response.data['name'] == dictionary['name']
        assert len(response.data['tellzones']) == 0
        assert response.status_code == 200

        response = client.delete('/api/networks/{id:d}/'.format(id=id), format='json')
        assert response.data == {}
        assert response.status_code == 200

    def test_b(self):
        category = middleware.mixer.blend('api.Category')

        network = middleware.mixer.blend('api.Network', user=None)

        with middleware.mixer.ctx(commit=False):
            for index, user in enumerate(middleware.mixer.cycle(5).blend('api.User')):
                user.point = fromstr('POINT({index} {index})'.format(index=index + 1))
                user.is_signed_in = True
                user.save()

                for master_tell in middleware.mixer.cycle(5).blend(
                    'api.MasterTell', created_by=user, owned_by=user, category=category,
                ):
                    master_tell.contents = str(user.id)
                    master_tell.save()

                tellzone = middleware.mixer.blend('api.Tellzone', user=None)
                tellzone.point = fromstr('POINT({index} {index})'.format(index=index + 1))
                tellzone.save()

                network_tellzone = middleware.mixer.blend('api.NetworkTellzone', network=network, tellzone=tellzone)
                network_tellzone.save()

                client = APIClient()
                client.credentials(HTTP_AUTHORIZATION=get_header(user.token))
                response = client.post(
                    '/api/radar/',
                    {
                        'tellzone_id': tellzone.id,
                        'network_id': network.id,
                        'point': {
                            'latitude': index + 1,
                            'longitude': index + 1,
                        },
                        'accuracies_horizontal': 1.00,
                        'accuracies_vertical': 1.00,
                        'is_casting': True,
                    },
                    format='json',
                )
                assert len(response.data) == 1
                assert response.status_code == 200

        user = middleware.mixer.blend('api.User', type='Root')

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=get_header(user.token))
        response = client.get(
            '/api/networks/{id:d}/master-tells/'.format(id=network.id),
            format='json',
        )
        assert len(response.data) == 25
        assert response.status_code == 200

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=get_header(user.token))
        response = client.get(
            '/api/networks/{id:d}/master-tells/'.format(id=network.id),
            {
                'tellzone_id': models.Tellzone.objects.get_queryset().order_by('?').first().id,
            },
            format='json',
        )
        assert len(response.data) == 20
        assert response.status_code == 200


class Notifications(TransactionTestCase):

    def setUp(self):
        self.user_1 = middleware.mixer.blend('api.User')
        self.client_1 = APIClient()
        self.client_1.credentials(HTTP_AUTHORIZATION=get_header(self.user_1.token))

        self.user_2 = middleware.mixer.blend('api.User')
        self.client_2 = APIClient()
        self.client_2.credentials(HTTP_AUTHORIZATION=get_header(self.user_2.token))

    def test_a(self):
        response = self.client_1.get('/api/notifications/', format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

        data = []

        response = self.client_2.post(
            '/api/tellcards/',
            {
                'user_destination_id': self.user_1.id,
                'location': 'Location',
                'action': 'Save',
            },
            format='json',
        )
        assert response.status_code == 201

        response = self.client_1.get('/api/notifications/', format='json')
        assert len(response.data) == 1
        assert response.data[0]['type'] == 'A'
        assert response.data[0]['status'] == 'Unread'
        assert response.status_code == 200

        data.append({
            'id': response.data[0]['id'],
            'status': 'Read',
        })

        response = self.client_2.post(
            '/api/shares/users/',
            {
                'user_destination_id': self.user_1.id,
                'object_id': self.user_1.id,
            },
            format='json',
        )
        assert response.status_code == 201

        response = self.client_1.get('/api/notifications/', format='json')
        assert len(response.data) == 2
        assert response.data[0]['type'] == 'B'
        assert response.data[0]['status'] == 'Unread'
        assert response.status_code == 200

        data.append({
            'id': response.data[0]['id'],
            'status': 'Read',
        })

        response = self.client_1.post('/api/notifications/', data, format='json')
        for notification in response.data:
            assert notification['status'] == 'Read'
        assert response.status_code == 200

        response = self.client_1.get(
            '/api/notifications/',
            {
                'since_id': data[0]['id'],
            },
            format='json',
        )
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client_1.get(
            '/api/notifications/',
            {
                'max_id': data[1]['id'],
            },
            format='json',
        )
        assert len(response.data) == 1
        assert response.status_code == 200

    def test_b(self):
        self.notification_1 = middleware.mixer.blend(
            'api.Notification', user=self.user_1, contents={}, status='Unread',
        )
        self.notification_2 = middleware.mixer.blend(
            'api.Notification', user=self.user_1, contents={}, status='Unread',
        )
        self.notification_3 = middleware.mixer.blend(
            'api.Notification', user=self.user_1, contents={}, status='Unread',
        )

        response = self.client_1.get('/api/notifications/', format='json')
        assert len(response.data) == 3
        assert response.status_code == 200

        response = self.client_1.get(
            '/api/notifications/?since_id={since_id:d}'.format(since_id=self.notification_1.id), format='json',
        )
        assert len(response.data) == 2
        assert response.status_code == 200

        response = self.client_1.get(
            '/api/notifications/?max_id={max_id:d}'.format(max_id=self.notification_2.id), format='json',
        )
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client_1.get('/api/notifications/?limit=2', format='json')
        assert len(response.data) == 2
        assert response.status_code == 200


class Posts(TransactionTestCase):

    def setUp(self):
        self.user_1 = middleware.mixer.blend('api.User')
        self.client_1 = APIClient()
        self.client_1.credentials(HTTP_AUTHORIZATION=get_header(self.user_1.token))

        self.user_2 = middleware.mixer.blend('api.User')
        self.client_2 = APIClient()
        self.client_2.credentials(HTTP_AUTHORIZATION=get_header(self.user_2.token))

        self.category = middleware.mixer.blend('api.Category')
        self.tellzone = middleware.mixer.blend('api.Tellzone')

    def test_a(self):
        response = self.client_1.get('/api/posts/', format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

        response = self.client_1.get('/api/posts/search/', format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

        response = self.client_1.get(
            '/api/posts/search/',
            {
                'user_ids': [
                    self.user_1.id,
                ],
            },
            format='json',
        )
        assert len(response.data) == 0
        assert response.status_code == 200

        response = self.client_2.get(
            '/api/posts/search/',
            {
                'user_ids': [
                    self.user_2.id,
                ],
            },
            format='json',
        )
        assert len(response.data) == 0
        assert response.status_code == 200

        dictionary = {
            'category_id': self.category.id,
            'contents': '1',
            'title': '1',
            'tellzones': [
                self.tellzone.id,
            ],
            'attachments': [
                {
                    'type': 'image/*',
                    'string_original': '1',
                    'string_preview': '1',
                    'position': 1,
                },
                {
                    'type': 'image/*',
                    'string_original': '2',
                    'string_preview': '2',
                    'position': 2,
                },
                {
                    'type': 'image/*',
                    'string_original': '3',
                    'string_preview': '3',
                    'position': 3,
                },
            ],
        }

        response = self.client_1.post('/api/posts/', dictionary, format='json')
        assert response.data['category']['id'] == dictionary['category_id']
        assert response.data['contents'] == dictionary['contents']
        assert response.data['title'] == dictionary['title']
        assert response.data['attachments'][0]['position'] == 1
        assert response.data['attachments'][1]['position'] == 2
        assert response.data['attachments'][2]['position'] == 3
        assert len(response.data['tellzones']) == 1
        assert response.data['tellzones'][0]['id'] == dictionary['tellzones'][0]
        assert (
            datetime.strptime(response.data['inserted_at'], '%Y-%m-%dT%H:%M:%S.%f') +
            timedelta(days=365)
        ).date() == datetime.strptime(response.data['expired_at'], '%Y-%m-%dT%H:%M:%S.%f').date()
        assert response.status_code == 201

        id = response.data['id']

        response = self.client_1.get(
            '/api/tellzones/',
            {
                'latitude': 1.00,
                'longitude': 1.00,
                'radius': 300,
            },
            format='json',
        )
        assert len(response.data[0]['posts']) == 1
        assert response.data[0]['posts'][0]['id'] == id
        assert response.data[0]['posts'][0]['title'] == dictionary['title']
        assert response.data[0]['posts'][0]['contents'] == dictionary['contents']

        dictionary = {
            'category_id': self.category.id,
            'contents': '2',
            'title': '2',
            'tellzones': [],
            'attachments': [
                {
                    'type': 'image/*',
                    'string_original': '1',
                    'string_preview': '1',
                    'position': 1,
                },
                {
                    'type': 'image/*',
                    'string_original': '2',
                    'string_preview': '2',
                    'position': 2,
                },
                {
                    'type': 'image/*',
                    'string_original': '3',
                    'string_preview': '3',
                    'position': 3,
                },
            ],
        }

        response = self.client_1.put('/api/posts/{id:d}/'.format(id=id), dictionary, format='json')
        assert response.data['id'] == id
        assert response.data['category']['id'] == dictionary['category_id']
        assert response.data['title'] == dictionary['title']
        assert response.data['contents'] == dictionary['contents']
        assert len(response.data['attachments']) == 3
        assert response.data['attachments'][0]['position'] == 1
        assert response.data['attachments'][1]['position'] == 2
        assert response.data['attachments'][2]['position'] == 3
        assert len(response.data['tellzones']) == 0
        assert response.status_code == 200

        dictionary = {
            'category_id': self.category.id,
            'contents': '3',
            'title': '3',
            'tellzones': [
                self.tellzone.id,
            ],
            'attachments': [
                {
                    'type': 'image/*',
                    'string_original': '1',
                    'string_preview': '1',
                    'position': 1,
                },
                {
                    'type': 'image/*',
                    'string_original': '2',
                    'string_preview': '2',
                    'position': 2,
                },
                {
                    'type': 'image/*',
                    'string_original': '3',
                    'string_preview': '3',
                    'position': 3,
                },
            ],
        }

        response = self.client_1.patch('/api/posts/{id:d}/'.format(id=id), dictionary, format='json')
        assert response.data['id'] == id
        assert response.data['category']['id'] == dictionary['category_id']
        assert response.data['title'] == dictionary['title']
        assert response.data['contents'] == dictionary['contents']
        assert len(response.data['attachments']) == 3
        assert response.data['attachments'][0]['position'] == 1
        assert response.data['attachments'][1]['position'] == 2
        assert response.data['attachments'][2]['position'] == 3
        assert len(response.data['tellzones']) == 1
        assert response.data['tellzones'][0]['id'] == dictionary['tellzones'][0]
        assert response.status_code == 200

        response = self.client_1.delete('/api/posts/{id:d}/'.format(id=id), format='json')
        assert response.data == {}
        assert response.status_code == 200


class Profiles(TransactionTestCase):

    def setUp(self):
        self.user_1 = middleware.mixer.blend('api.User')
        self.client_1 = APIClient()
        self.client_1.credentials(HTTP_AUTHORIZATION=get_header(self.user_1.token))

        self.user_2 = middleware.mixer.blend('api.User')
        self.client_2 = APIClient()
        self.client_2.credentials(HTTP_AUTHORIZATION=get_header(self.user_2.token))

        self.user_3 = middleware.mixer.blend('api.User')
        self.client_3 = APIClient()
        self.client_3.credentials(HTTP_AUTHORIZATION=get_header(self.user_3.token))

    def test_a(self):
        dictionary = {
            'ids': [
                self.user_1.id,
                self.user_2.id,
                self.user_3.id,
            ],
        }

        response = self.client_1.post('/api/profiles/', dictionary, format='json')
        assert response.data[0]['id'] == dictionary['ids'][0]
        assert response.data[1]['id'] == dictionary['ids'][1]
        assert response.data[2]['id'] == dictionary['ids'][2]
        assert response.status_code == 200

        response = self.client_1.post(
            '/api/blocks/',
            {
                'user_destination_id': self.user_2.id,
                'report': True,
            },
            format='json',
        )
        assert response.data == {}
        assert response.status_code == 200

        response = self.client_1.post(
            '/api/profiles/',
            {
                'ids': [
                    self.user_2.id,
                    self.user_3.id,
                ],
            },
            format='json'
        )
        assert response.data[0]['id'] == self.user_3.id
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client_2.post(
            '/api/profiles/',
            {
                'ids': [
                    self.user_1.id,
                    self.user_3.id,
                ],
            },
            format='json'
        )
        assert response.data[0]['id'] == self.user_3.id
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client_3.post(
            '/api/profiles/',
            {
                'ids': [
                    self.user_1.id,
                    self.user_2.id,
                ],
            },
            format='json'
        )
        assert len(response.data) == 2
        assert response.data[0]['id'] == dictionary['ids'][0]
        assert response.data[1]['id'] == dictionary['ids'][1]
        assert response.status_code == 200


class Radar(TransactionTestCase):

    def setUp(self):
        self.user = middleware.mixer.blend('api.User')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

        with middleware.mixer.ctx(commit=False):
            for tellzone in middleware.mixer.cycle(5).blend('api.Tellzone', user=None):
                tellzone.point = get_point()
                tellzone.save()
            for user in middleware.mixer.cycle(5).blend('api.User'):
                user.point = get_point()
                user.is_signed_in = True
                user.save()
                client = APIClient()
                client.credentials(HTTP_AUTHORIZATION=get_header(user.token))
                response = client.post(
                    '/api/radar/',
                    {
                        'tellzone_id': models.Tellzone.objects.get_queryset().order_by('?').first().id,
                        'point': {
                            'latitude': 1.00,
                            'longitude': 1.00,
                        },
                        'accuracies_horizontal': 1.00,
                        'accuracies_vertical': 1.00,
                        'is_casting': True,
                    },
                    format='json',
                )
                assert len(response.data) == 5
                assert 'id' in response.data[0]
                assert 'name' in response.data[0]
                assert response.status_code == 200

    def test_a(self):
        response = self.client.post(
            '/api/radar/',
            {
                'tellzone_id': models.Tellzone.objects.get_queryset().order_by('?').first().id,
                'point': {
                    'latitude': 1.00,
                    'longitude': 1.00,
                },
                'accuracies_horizontal': 1.00,
                'accuracies_vertical': 1.00,
                'is_casting': True,
            },
            format='json',
        )
        assert len(response.data) == 5
        assert 'id' in response.data[0]
        assert 'name' in response.data[0]
        assert response.status_code == 200

        response = self.client.get(
            '/api/radar/',
            {
                'latitude': 1.00,
                'longitude': 1.00,
                'radius': 300,
                'widths_radar': 1,
                'widths_group': 1,
            },
            format='json',
        )
        assert len(response.data) == 6
        for index in range(5):
            assert 'hash' in response.data[index]
            assert len(response.data[index]['hash'].split('-')) == len(response.data[index]['items'])
            assert 'items' in response.data[index]
            assert len(response.data[index]['items']) > 0
            assert 'position' in response.data[index]
            assert response.data[index]['position'] == index + 1
        assert response.status_code == 200


class RecommendedTells(TransactionTestCase):

    def setUp(self):
        self.types = [
            'Hobby',
            'Mind',
            'Passion',
        ]
        self.count = 10

        for type in self.types:
            middleware.mixer.cycle(self.count).blend('api.RecommendedTell', type=type)

    def test_a(self):
        self.client = APIClient()

        response = self.client.get('/api/recommended-tells/TYPE/', format='json')
        assert response.status_code == 400

        for type in self.types:
            response = self.client.get('/api/recommended-tells/{type:s}/'.format(type=type), format='json')
            assert len(response.data) == self.count
            assert response.status_code == 200


class SharesUsers(TransactionTestCase):

    def setUp(self):
        self.user_1 = middleware.mixer.blend('api.User')
        self.client_1 = APIClient()
        self.client_1.credentials(HTTP_AUTHORIZATION=get_header(self.user_1.token))

        self.user_2 = middleware.mixer.blend('api.User')
        self.client_2 = APIClient()
        self.client_2.credentials(HTTP_AUTHORIZATION=get_header(self.user_2.token))

    def test_a(self):
        self.get(self.client_1, 0)
        self.get(self.client_2, 0)

        response = self.client_1.post(
            '/api/shares/users/',
            {
                'user_destination_id': self.user_2.id,
                'object_id': self.user_2.id,
            },
            format='json',
        )
        assert 'email' in response.data
        assert 'subject' in response.data['email']
        assert 'body' in response.data['email']
        assert 'sms' in response.data
        assert 'facebook_com' in response.data
        assert 'twitter_com' in response.data
        assert response.status_code == 201

        response = self.client_2.post(
            '/api/shares/users/',
            {
                'user_destination_id': self.user_1.id,
                'object_id': self.user_1.id,
            },
            format='json',
        )
        assert 'email' in response.data
        assert 'subject' in response.data['email']
        assert 'body' in response.data['email']
        assert 'sms' in response.data
        assert 'facebook_com' in response.data
        assert 'twitter_com' in response.data
        assert response.status_code == 201

        self.get(self.client_1, 1)
        self.get(self.client_2, 1)

    def get(self, client, count):
        response = client.get(
            '/api/shares/users/',
            {
                'type': 'Source',
            },
            format='json',
        )
        assert len(response.data) == count
        assert response.status_code == 200

        response = client.get(
            '/api/shares/users/',
            {
                'type': 'Destination',
            },
            format='json',
        )
        assert len(response.data) == count
        assert response.status_code == 200


class Signals(TransactionTestCase):

    def get_celery_connection(self):
        parameters = URLParameters(BROKER)
        return client_0_8.Connection(
            host='{hostname:s}:{port:d}'.format(hostname=parameters.host, port=parameters.port),
            userid=parameters.credentials.username,
            password=parameters.credentials.password,
            virtual_host=parameters.virtual_host,
            insist=False,
        ).channel()

    def get_celery_tasks(self):
        _, backlog, _ = self.get_celery_connection().queue_declare(
            queue='api.management.commands.websockets',
            passive=True,
        )
        return backlog

    def reset_celery_tasks(self):
        self.get_celery_connection().queue_purge('api.management.commands.websockets')

    def setUp(self):
        self.user_1 = middleware.mixer.blend('api.User')
        self.client_1 = APIClient()
        self.client_1.credentials(HTTP_AUTHORIZATION=get_header(self.user_1.token))

        self.user_2 = middleware.mixer.blend('api.User')
        self.client_2 = APIClient()
        self.client_2.credentials(HTTP_AUTHORIZATION=get_header(self.user_2.token))

        self.category = middleware.mixer.blend('api.Category')

        self.tellzone = middleware.mixer.blend('api.Tellzone')

        self.reset_celery_tasks()

    def test_a(self):
        response = self.client_1.post(
            '/api/blocks/',
            {
                'user_destination_id': self.user_2.id,
                'report': True,
            },
            format='json',
        )
        assert response.data == {}
        assert response.status_code == 200

        assert self.get_celery_tasks() == 1
        self.reset_celery_tasks()

    def test_b(self):
        dictionary = {
            'category_id': self.category.id,
            'contents': '1',
            'position': 1,
        }

        response = self.client_1.post('/api/master-tells/', dictionary, format='json')
        assert response.data['created_by_id'] == self.user_1.id
        assert response.data['owned_by_id'] == self.user_1.id
        assert response.data['category']['id'] == dictionary['category_id']
        assert response.data['contents'] == dictionary['contents']
        assert response.data['position'] == dictionary['position']
        assert response.data['position'] == 1
        assert response.data['is_visible'] is True
        assert response.status_code == 201

        assert self.get_celery_tasks() == 1
        self.reset_celery_tasks()

    def test_c(self):
        dictionary = {
            'user_destination_id': self.user_2.id,
            'type': 'Request',
            'contents': '1',
            'status': 'Unread',
        }

        response = self.client_1.post('/api/messages/', dictionary, format='json')
        assert response.status_code == 201

        response = self.client_1.get('/api/users/{id:d}/profile/'.format(id=self.user_2.id), format='json')
        assert response.data['messages'] == 1

        dictionary = {
            'user_destination_id': self.user_1.id,
            'type': 'Response - Accepted',
            'contents': '1',
            'status': 'Unread',
        }

        response = self.client_2.post('/api/messages/', dictionary, format='json')
        assert response.status_code == 201

        response = self.client_1.get('/api/users/{id:d}/profile/'.format(id=self.user_2.id), format='json')
        assert response.data['messages'] == 2

        dictionary = {
            'user_destination_id': self.user_1.id,
            'type': 'Message',
            'contents': '1',
            'status': 'Unread',
        }

        response = self.client_2.post('/api/messages/', dictionary, format='json')
        assert response.status_code == 201

        response = self.client_1.get('/api/users/{id:d}/profile/'.format(id=self.user_2.id), format='json')
        assert response.data['messages'] == 2

        assert self.get_celery_tasks() == 3
        self.reset_celery_tasks()

    def test_d(self):
        response = self.client_2.post(
            '/api/tellcards/',
            {
                'user_destination_id': self.user_1.id,
                'location': 'Location',
                'action': 'Save',
            },
            format='json',
        )
        assert response.status_code == 201

        response = self.client_1.get('/api/notifications/', format='json')
        assert len(response.data) == 1
        assert response.data[0]['type'] == 'A'
        assert response.data[0]['status'] == 'Unread'
        assert response.status_code == 200

        assert self.get_celery_tasks() == 1
        self.reset_celery_tasks()

    def test_f(self):
        response = self.client_1.post(
            '/api/master-tells/',
            {
                'category_id': self.category.id,
                'contents': '1',
            },
            format='json',
        )
        master_tell_id = response.data['id']

        dictionary = {
            'master_tell_id': master_tell_id,
            'type': 'image/*',
            'contents_original': '1',
            'description': '1',
            'position': 1,
        }

        response = self.client_1.post('/api/slave-tells/', dictionary, format='json')
        assert response.data['master_tell_id'] == dictionary['master_tell_id']
        assert response.data['created_by_id'] == self.user_1.id
        assert response.data['owned_by_id'] == self.user_1.id
        assert response.data['type'] == dictionary['type']
        assert response.data['contents_original'] == dictionary['contents_original']
        assert response.data['description'] == dictionary['description']
        assert response.data['position'] == dictionary['position']
        assert response.data['position'] == 1
        assert response.data['is_editable'] is True
        assert response.status_code == 201

        assert self.get_celery_tasks() == 2
        self.reset_celery_tasks()

    def test_g(self):
        response = self.client_1.get('/api/users/{id:d}/'.format(id=self.user_1.id), format='json')
        assert response.data['id'] == self.user_1.id
        assert response.status_code == 200

        dictionary = {
            'email': self.user_1.email,
            'first_name': '1',
            'last_name': '1',
            'social_profiles': [
                {
                    'netloc': 'linkedin.com',
                    'url': '1',
                },
                {
                    'netloc': 'twitter.com',
                    'url': '1',
                },
            ],
            'urls': [
                {
                    'position': 1,
                    'string': 'http://tellecast.com',
                },
            ],
            'photos': [
                {
                    'description': '1',
                    'position': 1,
                    'string_original': '1',
                    'string_preview': '1',
                },
            ],
            'status': {
                'string': '1',
                'title': '1',
                'attachments': [
                    {
                        'string_original': '1',
                        'position': 1,
                    },
                ],
            },
        }

        response = self.client_1.put('/api/users/{id:d}/'.format(id=self.user_1.id), dictionary, format='json')
        assert len(response.data['settings']) == len(models.UserSetting.dictionary.keys())
        assert len(response.data['social_profiles']) == 2
        assert len(response.data['status']['attachments']) == 1
        assert len(response.data['urls']) == 1
        assert response.data['first_name'] == dictionary['first_name']
        assert response.data['id'] == self.user_1.id
        assert response.data['last_name'] == dictionary['last_name']
        assert response.data['photos'][0]['position'] == 1
        assert response.data['status']['attachments'][0]['position'] == 1
        assert response.data['urls'][0]['is_visible'] is True
        assert response.data['urls'][0]['position'] == 1
        assert response.status_code == 200

        assert self.get_celery_tasks() == 1
        self.reset_celery_tasks()

    def test_h(self):
        response = self.client_1.post(
            '/api/radar/',
            {
                'tellzone_id': models.Tellzone.objects.get_queryset().first().id,
                'point': {
                    'latitude': 1.00,
                    'longitude': 1.00,
                },
                'accuracies_horizontal': 0.00,
                'accuracies_vertical': 0.00,
                'bearing': 0,
                'is_casting': False,
            },
            format='json',
        )
        assert len(response.data) == 1
        assert 'id' in response.data[0]
        assert 'name' in response.data[0]
        assert response.status_code == 200

        assert self.get_celery_tasks() == 1
        self.reset_celery_tasks()


class SlaveTells(TransactionTestCase):

    def setUp(self):
        self.user = middleware.mixer.blend('api.User')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

    def test_a(self):
        category = middleware.mixer.blend('api.Category')

        response = self.client.get('/api/slave-tells/', format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

        response = self.client.post(
            '/api/master-tells/',
            {
                'category_id': category.id,
                'contents': '1',
            },
            format='json',
        )
        master_tell_id = response.data['id']

        dictionary = {
            'master_tell_id': master_tell_id,
            'type': 'image/*',
            'contents_original': '1',
            'description': '1',
            'position': 1,
        }

        response = self.client.post('/api/slave-tells/', dictionary, format='json')
        assert response.data['master_tell_id'] == dictionary['master_tell_id']
        assert response.data['created_by_id'] == self.user.id
        assert response.data['owned_by_id'] == self.user.id
        assert response.data['type'] == dictionary['type']
        assert response.data['contents_original'] == dictionary['contents_original']
        assert response.data['description'] == dictionary['description']
        assert response.data['position'] == dictionary['position']
        assert response.data['position'] == 1
        assert response.data['is_editable'] is True
        assert response.status_code == 201

        del dictionary['position']

        response = self.client.post('/api/slave-tells/', dictionary, format='json')
        assert response.data['master_tell_id'] == dictionary['master_tell_id']
        assert response.data['created_by_id'] == self.user.id
        assert response.data['owned_by_id'] == self.user.id
        assert response.data['type'] == dictionary['type']
        assert response.data['contents_original'] == dictionary['contents_original']
        assert response.data['description'] == dictionary['description']
        assert response.data['position'] == 2
        assert response.data['is_editable'] is True
        assert response.status_code == 201

        id = response.data['id']

        inserted_at = parser.parse(response.data['inserted_at'])
        updated_at = parser.parse(response.data['updated_at'])

        response = self.client.get('/api/slave-tells/', format='json')
        assert len(response.data) == 2
        assert response.status_code == 200

        response = self.client.get(
            '/api/slave-tells/',
            {
                'inserted_at': inserted_at - timedelta(seconds=10),
            },
            format='json',
        )
        assert len(response.data) == 2
        assert response.status_code == 200

        list_ = [{
            'id': id,
            'position': 1,
        }]

        response = self.client.post('/api/slave-tells/positions/', list_, format='json')
        assert response.data[0]['created_by_id'] == self.user.id
        assert response.data[0]['owned_by_id'] == self.user.id
        assert response.data[0]['position'] == list_[0]['position']
        assert response.data[0]['is_editable'] is True
        assert response.status_code == 200

        response = self.client.get(
            '/api/slave-tells/',
            {
                'inserted_at': inserted_at + timedelta(seconds=10),
            },
            format='json',
        )
        assert response.data == []
        assert response.status_code == 200

        response = self.client.get(
            '/api/slave-tells/',
            {
                'updated_at': updated_at - timedelta(seconds=10),
            },
            format='json',
        )
        assert len(response.data) == 2
        assert response.status_code == 200

        response = self.client.get(
            '/api/slave-tells/',
            {
                'updated_at': updated_at + timedelta(seconds=10),
            },
            format='json',
        )
        assert response.data == []
        assert response.status_code == 200

        dictionary['contents_original'] = '2'
        dictionary['description'] = '2'
        dictionary['position'] = 2

        response = self.client.put('/api/slave-tells/{id:d}/'.format(id=id), dictionary, format='json')
        assert response.data['master_tell_id'] == dictionary['master_tell_id']
        assert response.data['created_by_id'] == self.user.id
        assert response.data['owned_by_id'] == self.user.id
        assert response.data['type'] == dictionary['type']
        assert response.data['contents_original'] == dictionary['contents_original']
        assert response.data['description'] == dictionary['description']
        assert response.data['position'] == dictionary['position']
        assert response.data['position'] == 2
        assert response.data['is_editable'] is True
        assert response.status_code == 200

        del dictionary['position']

        response = self.client.put('/api/slave-tells/{id:d}/'.format(id=id), dictionary, format='json')
        assert response.data['master_tell_id'] == dictionary['master_tell_id']
        assert response.data['created_by_id'] == self.user.id
        assert response.data['owned_by_id'] == self.user.id
        assert response.data['type'] == dictionary['type']
        assert response.data['contents_original'] == dictionary['contents_original']
        assert response.data['description'] == dictionary['description']
        assert response.data['position'] == 2
        assert response.data['is_editable'] is True
        assert response.status_code == 200

        dictionary['contents_original'] = '3'
        dictionary['description'] = '3'
        dictionary['position'] = 3

        response = self.client.patch('/api/slave-tells/{id:d}/'.format(id=id), dictionary, format='json')
        assert response.data['master_tell_id'] == dictionary['master_tell_id']
        assert response.data['created_by_id'] == self.user.id
        assert response.data['owned_by_id'] == self.user.id
        assert response.data['type'] == dictionary['type']
        assert response.data['contents_original'] == dictionary['contents_original']
        assert response.data['description'] == dictionary['description']
        assert response.data['position'] == dictionary['position']
        assert response.data['position'] == 3
        assert response.data['is_editable'] is True
        assert response.status_code == 200

        del dictionary['position']

        response = self.client.patch('/api/slave-tells/{id:d}/'.format(id=id), dictionary, format='json')
        assert response.data['master_tell_id'] == dictionary['master_tell_id']
        assert response.data['created_by_id'] == self.user.id
        assert response.data['owned_by_id'] == self.user.id
        assert response.data['type'] == dictionary['type']
        assert response.data['contents_original'] == dictionary['contents_original']
        assert response.data['description'] == dictionary['description']
        assert response.data['position'] == 3
        assert response.data['is_editable'] is True
        assert response.status_code == 200

        response = self.client.get('/api/slave-tells/ids/', format='json')
        assert len(response.data) == 2
        assert response.data[1] == id
        assert response.status_code == 200

        response = self.client.delete('/api/slave-tells/{id:d}/'.format(id=id), format='json')
        assert response.data == {}
        assert response.status_code == 200

        response = self.client.get('/api/slave-tells/', format='json')
        assert len(response.data) == 1
        assert response.status_code == 200


class Tellcards(TransactionTestCase):

    def setUp(self):
        self.user_1 = middleware.mixer.blend('api.User')
        self.client_1 = APIClient()
        self.client_1.credentials(HTTP_AUTHORIZATION=get_header(self.user_1.token))

        self.user_2 = middleware.mixer.blend('api.User')
        self.client_2 = APIClient()
        self.client_2.credentials(HTTP_AUTHORIZATION=get_header(self.user_2.token))

    def test_a(self):
        self.get(self.client_1, 0, 0)
        self.get(self.client_2, 0, 0)

        response = self.client_1.get('/api/users/{id:d}/profile/'.format(id=self.user_2.id), format='json')
        assert response.data['is_tellcard'] is False

        response = self.client_2.get('/api/users/{id:d}/profile/'.format(id=self.user_1.id), format='json')
        assert response.data['is_tellcard'] is False

        response = self.client_2.post(
            '/api/tellcards/',
            {
                'user_destination_id': self.user_1.id,
                'location': 'Location',
                'action': 'Unsave',
            },
            format='json',
        )
        assert response.status_code == 400

        response = self.client_1.post(
            '/api/tellcards/',
            {
                'user_destination_id': self.user_2.id,
                'action': 'Save',
            },
            format='json',
        )
        assert response.data == {}
        assert response.status_code == 201

        response = self.client_2.post(
            '/api/tellcards/',
            {
                'user_destination_id': self.user_1.id,
                'action': 'Save',
            },
            format='json',
        )
        assert response.data == {}
        assert response.status_code == 201

        self.get(self.client_1, 1, 1)
        self.get(self.client_2, 1, 1)

        response = self.client_1.get('/api/users/{id:d}/profile/'.format(id=self.user_2.id), format='json')
        assert response.data['is_tellcard'] is True

        response = self.client_2.get('/api/users/{id:d}/profile/'.format(id=self.user_1.id), format='json')
        assert response.data['is_tellcard'] is True

        response = self.client_1.post(
            '/api/tellcards/delete/',
            {
                'user_destination_id': self.user_2.id,
                'action': 'Save',
            },
            format='json',
        )
        assert response.data == {}
        assert response.status_code == 200

        response = self.client_2.post(
            '/api/tellcards/delete/',
            {
                'user_destination_id': self.user_1.id,
                'action': 'Save',
            },
            format='json',
        )
        assert response.data == {}
        assert response.status_code == 200

        self.get(self.client_1, 0, 0)
        self.get(self.client_2, 0, 0)

        response = self.client_1.get('/api/users/{id:d}/profile/'.format(id=self.user_2.id), format='json')
        assert response.data['is_tellcard'] is False

        response = self.client_2.get('/api/users/{id:d}/profile/'.format(id=self.user_1.id), format='json')
        assert response.data['is_tellcard'] is False

    def get(self, client, count_1, count_2):
        response = client.get(
            '/api/tellcards/',
            {
                'type': 'Source',
            },
            format='json',
        )
        assert len(response.data) == count_1
        assert response.status_code == 200

        response = client.get(
            '/api/tellcards/',
            {
                'type': 'Destination',
            },
            format='json',
        )
        assert len(response.data) == count_2
        assert response.status_code == 200


class Tellzones(TransactionTestCase):

    def setUp(self):
        self.user = middleware.mixer.blend('api.User')

        self.category = middleware.mixer.blend('api.Category')

        self.network = middleware.mixer.blend('api.Network', user=self.user)

        self.master_tell = middleware.mixer.blend(
            'api.MasterTell', created_by=self.user, owned_by=self.user, category=self.category,
        )
        self.post = middleware.mixer.blend('api.Post')

        self.tellzone = middleware.mixer.blend('api.Tellzone')
        self.tellzone.point = get_point()
        self.tellzone.save()

        for netloc in [
            'facebook.com',
            'google.com',
            'instagram.com',
            'linkedin.com',
            'twitter.com',
        ]:
            middleware.mixer.blend('api.TellzoneSocialProfile', tellzone=self.tellzone, netloc=netloc)

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

        with middleware.mixer.ctx(commit=False):
            for user in middleware.mixer.cycle(5).blend('api.User'):
                user.point = get_point()
                user.is_signed_in = True
                user.save()

                for master_tell in middleware.mixer.cycle(5).blend(
                    'api.MasterTell', created_by=user, owned_by=user, category=self.category,
                ):
                    master_tell.contents = str(user.id)
                    master_tell.save()

                client = APIClient()
                client.credentials(HTTP_AUTHORIZATION=get_header(user.token))
                response = client.post(
                    '/api/radar/',
                    {
                        'tellzone_id': models.Tellzone.objects.get_queryset().first().id,
                        'point': {
                            'latitude': 1.00,
                            'longitude': 1.00,
                        },
                        'accuracies_horizontal': 1.00,
                        'accuracies_vertical': 1.00,
                        'is_casting': True,
                    },
                    format='json',
                )
                assert len(response.data) == 1
                assert 'id' in response.data[0]
                assert 'name' in response.data[0]
                assert response.status_code == 200

    def test_a(self):
        response = self.client.get(
            '/api/tellzones/',
            {
                'latitude': 1.00,
                'longitude': 1.00,
                'radius': 300,
            },
            format='json',
        )
        assert len(response.data) == 1
        assert len(response.data[0]['social_profiles']) == 5
        assert response.status_code == 200

        response = self.client.get(
            '/api/tellzones/{id:d}/'.format(id=models.Tellzone.objects.get_queryset().first().id), format='json',
        )
        assert len(response.data['social_profiles']) == 5
        assert response.status_code == 200

        dictionary = {
            'type': '1',
            'name': '1',
            'photo': '1',
            'location': '1',
            'phone': '1',
            'url': '1',
            'hours': {
                'Mon': '09:00 am - 05:00 pm',
                'Tue': '09:00 am - 05:00 pm',
                'Wed': '09:00 am - 05:00 pm',
                'Thu': '09:00 am - 05:00 pm',
                'Fri': '09:00 am - 05:00 pm',
                'Sat': '09:00 am - 05:00 pm',
                'Sun': '09:00 pm - 05:00 pm',
            },
            'point': {
                'latitude': 1.00,
                'longitude': 1.00,
            },
            'status': 'Public',
            'started_at': '1111-11-11T11:11:11.111111',
            'ended_at': '1111-11-11T11:11:11.111111',
            'social_profiles': [
                {
                    'netloc': 'linkedin.com',
                    'url': '1',
                },
            ],
            'master_tells': [
                self.master_tell.id,
            ],
            'networks': [
                self.network.id,
            ],
            'posts': [
                self.post.id,
            ],
        }

        response = self.client.post('/api/tellzones/', dictionary, format='json')
        assert response.data['type'] == dictionary['type']
        assert response.data['name'] == dictionary['name']
        assert response.data['photo'] == dictionary['photo']
        assert response.data['location'] == dictionary['location']
        assert response.data['phone'] == dictionary['phone']
        assert response.data['url'] == dictionary['url']
        assert response.data['hours'] == dictionary['hours']
        assert float(response.data['point']['latitude']) == dictionary['point']['latitude']
        assert float(response.data['point']['longitude']) == dictionary['point']['longitude']
        assert response.data['status'] == dictionary['status']
        assert response.data['started_at'] == dictionary['started_at']
        assert response.data['ended_at'] == dictionary['ended_at']
        assert len(response.data['social_profiles']) == len(dictionary['social_profiles'])
        assert response.data['social_profiles'][0]['netloc'] == dictionary['social_profiles'][0]['netloc']
        assert response.data['social_profiles'][0]['url'] == dictionary['social_profiles'][0]['url']
        assert len(response.data['master_tells']) == len(dictionary['master_tells'])
        assert response.data['master_tells'][0]['id'] == dictionary['master_tells'][0]
        assert len(response.data['networks']) == len(dictionary['networks'])
        assert response.data['networks'][0]['id'] == dictionary['networks'][0]
        assert len(response.data['posts']) == len(dictionary['posts'])
        assert response.data['posts'][0]['id'] == dictionary['posts'][0]
        assert response.status_code == 201

        id = response.data['id']

        dictionary = {
            'type': '2',
            'name': '2',
            'photo': '2',
            'location': '2',
            'phone': '2',
            'url': '2',
            'hours': {
                'Mon': '09:00 am - 05:00 pm',
                'Tue': '09:00 am - 05:00 pm',
                'Wed': '09:00 am - 05:00 pm',
                'Thu': '09:00 am - 05:00 pm',
                'Fri': '09:00 am - 05:00 pm',
                'Sat': '09:00 am - 05:00 pm',
                'Sun': '09:00 pm - 05:00 pm',
            },
            'point': {
                'latitude': 2.00,
                'longitude': 2.00,
            },
            'status': 'Public',
            'started_at': '1111-11-11T11:11:11.111111',
            'ended_at': '1111-11-11T11:11:11.111111',
            'social_profiles': [],
            'master_tells': [],
            'networks': [],
            'posts': [],
        }

        response = self.client.put('/api/tellzones/{id:d}/'.format(id=id), dictionary, format='json')
        assert response.data['type'] == dictionary['type']
        assert response.data['name'] == dictionary['name']
        assert response.data['photo'] == dictionary['photo']
        assert response.data['location'] == dictionary['location']
        assert response.data['phone'] == dictionary['phone']
        assert response.data['url'] == dictionary['url']
        assert response.data['hours'] == dictionary['hours']
        assert float(response.data['point']['latitude']) == dictionary['point']['latitude']
        assert float(response.data['point']['longitude']) == dictionary['point']['longitude']
        assert response.data['status'] == dictionary['status']
        assert response.data['started_at'] == dictionary['started_at']
        assert response.data['ended_at'] == dictionary['ended_at']
        assert len(response.data['social_profiles']) == len(dictionary['social_profiles'])
        assert len(response.data['master_tells']) == len(dictionary['master_tells'])
        assert len(response.data['networks']) == len(dictionary['networks'])
        assert len(response.data['posts']) == len(dictionary['posts'])
        assert response.status_code == 200

        dictionary = {
            'type': '3',
            'name': '3',
            'photo': '3',
            'location': '3',
            'phone': '3',
            'url': '3',
            'hours': {
                'Mon': '09:00 am - 05:00 pm',
                'Tue': '09:00 am - 05:00 pm',
                'Wed': '09:00 am - 05:00 pm',
                'Thu': '09:00 am - 05:00 pm',
                'Fri': '09:00 am - 05:00 pm',
                'Sat': '09:00 am - 05:00 pm',
                'Sun': '09:00 pm - 05:00 pm',
            },
            'point': {
                'latitude': 3.00,
                'longitude': 3.00,
            },
            'status': 'Public',
            'started_at': '1111-11-11T11:11:11.111111',
            'ended_at': '1111-11-11T11:11:11.111111',
            'social_profiles': [
                {
                    'netloc': 'linkedin.com',
                    'url': '3',
                },
            ],
            'master_tells': [
                self.master_tell.id,
            ],
            'networks': [
                self.network.id,
            ],
            'posts': [
                self.post.id,
            ],
        }

        response = self.client.patch('/api/tellzones/{id:d}/'.format(id=id), dictionary, format='json')
        assert response.data['type'] == dictionary['type']
        assert response.data['name'] == dictionary['name']
        assert response.data['photo'] == dictionary['photo']
        assert response.data['location'] == dictionary['location']
        assert response.data['phone'] == dictionary['phone']
        assert response.data['url'] == dictionary['url']
        assert response.data['hours'] == dictionary['hours']
        assert float(response.data['point']['latitude']) == dictionary['point']['latitude']
        assert float(response.data['point']['longitude']) == dictionary['point']['longitude']
        assert response.data['status'] == dictionary['status']
        assert response.data['started_at'] == dictionary['started_at']
        assert response.data['ended_at'] == dictionary['ended_at']
        assert len(response.data['social_profiles']) == len(dictionary['social_profiles'])
        assert response.data['social_profiles'][0]['netloc'] == dictionary['social_profiles'][0]['netloc']
        assert response.data['social_profiles'][0]['url'] == dictionary['social_profiles'][0]['url']
        assert len(response.data['master_tells']) == len(dictionary['master_tells'])
        assert response.data['master_tells'][0]['id'] == dictionary['master_tells'][0]
        assert len(response.data['networks']) == len(dictionary['networks'])
        assert response.data['networks'][0]['id'] == dictionary['networks'][0]
        assert len(response.data['posts']) == len(dictionary['posts'])
        assert response.data['posts'][0]['id'] == dictionary['posts'][0]
        assert response.status_code == 200

        response = self.client.delete('/api/tellzones/{id:d}/'.format(id=id), format='json')
        assert response.data == {}
        assert response.status_code == 200

    def test_b(self):
        response = self.client.get(
            '/api/tellzones/{id:d}/master-tells/'.format(id=models.Tellzone.objects.get_queryset().first().id),
            format='json',
        )
        assert len(response.data) == 25
        assert response.status_code == 200

    def test_c(self):
        response = self.client.post(
            '/api/users/{id:d}/tellzones/'.format(id=self.user.id),
            {
                'tellzone_id': self.tellzone.id,
                'action': 'Favorite',
            },
            format='json',
        )
        assert response.data['tellzone_id'] == self.tellzone.id
        assert response.status_code == 201

        response = self.client.post(
            '/api/users/{id:d}/tellzones/'.format(id=self.user.id),
            {
                'tellzone_id': self.tellzone.id,
                'action': 'Pin',
            },
            format='json',
        )
        assert response.data['tellzone_id'] == self.tellzone.id
        assert response.status_code == 201

        response = self.client.post(
            '/api/users/{id:d}/tellzones/'.format(id=self.user.id),
            {
                'tellzone_id': self.tellzone.id,
                'action': 'View',
            },
            format='json',
        )
        assert response.data['tellzone_id'] == self.tellzone.id
        assert response.status_code == 201

        response = self.client.get('/api/users/{id:d}/tellzones/'.format(id=self.user.id), format='json')
        assert response.status_code == 200
        assert response.data[0]['tellecasters'] == 5
        assert response.data[0]['favorites'] == 1
        assert response.data[0]['pins'] == 1
        assert response.data[0]['views'] == 1
        assert response.data[0]['is_favorited']
        assert response.data[0]['is_pinned']
        assert response.data[0]['is_viewed']


class Users(TransactionTestCase):

    def setUp(self):
        self.tellzone = middleware.mixer.blend('api.Tellzone')

        self.user = middleware.mixer.blend('api.User')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

    def test_a(self):
        response = self.client.get('/api/users/0/', format='json')
        assert response.status_code == 400

        response = self.client.get('/api/users/{id:d}/'.format(id=self.user.id), format='json')
        assert response.data['id'] == self.user.id
        assert response.status_code == 200

        dictionary = {
            'email': self.user.email,
            'first_name': '1',
            'last_name': '1',
            'social_profiles': [
                {
                    'netloc': 'linkedin.com',
                    'url': '1',
                },
                {
                    'netloc': 'twitter.com',
                    'url': '1',
                },
            ],
            'urls': [
                {
                    'position': 1,
                    'string': 'http://tellecast.com',
                },
            ],
            'photos': [
                {
                    'description': '1',
                    'position': 1,
                    'string_original': '1',
                    'string_preview': '1',
                },
            ],
            'status': {
                'string': '1',
                'title': '1',
                'attachments': [
                    {
                        'string_original': '1',
                        'position': 1,
                    },
                ],
            },
        }

        response = self.client.put('/api/users/{id:d}/'.format(id=self.user.id), dictionary, format='json')
        assert len(response.data['settings']) == len(models.UserSetting.dictionary.keys())
        assert len(response.data['social_profiles']) == 2
        assert len(response.data['status']['attachments']) == 1
        assert len(response.data['urls']) == 1
        assert response.data['first_name'] == dictionary['first_name']
        assert response.data['id'] == self.user.id
        assert response.data['last_name'] == dictionary['last_name']
        assert response.data['photos'][0]['position'] == 1
        assert response.data['status']['attachments'][0]['position'] == 1
        assert response.data['urls'][0]['is_visible'] is True
        assert response.data['urls'][0]['position'] == 1
        assert response.status_code == 200

        dictionary['urls'][0]['is_visible'] = False

        del dictionary['photos'][0]['position']
        del dictionary['social_profiles'][0]['url']
        del dictionary['status']['attachments'][0]['position']
        del dictionary['urls'][0]['position']

        response = self.client.put('/api/users/{id:d}/'.format(id=self.user.id), dictionary, format='json')
        assert len(response.data['social_profiles']) == 1
        assert response.data['first_name'] == dictionary['first_name']
        assert response.data['id'] == self.user.id
        assert response.data['last_name'] == dictionary['last_name']
        assert response.data['photos'][0]['position'] == 1
        assert response.data['status']['attachments'][0]['position'] == 1
        assert response.data['urls'][0]['is_visible'] is False
        assert response.data['urls'][0]['position'] == 1
        assert response.status_code == 200

        response = self.client.get('/api/users/{id:d}/profile/'.format(id=self.user.id), format='json')
        assert response.data['id'] == self.user.id
        assert response.status_code == 200

        response = self.client.get('/api/users/{id:d}/tellzones/'.format(id=self.user.id), format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

        response = self.client.post(
            '/api/users/{id:d}/tellzones/'.format(id=self.user.id),
            {
                'tellzone_id': self.tellzone.id,
                'action': 'Favorite',
            },
            format='json',
        )
        assert response.data['tellzone_id'] == self.tellzone.id
        assert response.status_code == 201

        response = self.client.post(
            '/api/users/{id:d}/tellzones/'.format(id=self.user.id),
            {
                'tellzone_id': self.tellzone.id,
                'action': 'Pin',
            },
            format='json',
        )
        assert response.data['tellzone_id'] == self.tellzone.id
        assert response.status_code == 201

        response = self.client.post(
            '/api/users/{id:d}/tellzones/'.format(id=self.user.id),
            {
                'tellzone_id': self.tellzone.id,
                'action': 'View',
            },
            format='json',
        )
        assert response.data['tellzone_id'] == self.tellzone.id
        assert response.status_code == 201

        response = self.client.get('/api/users/{id:d}/tellzones/'.format(id=self.user.id), format='json')
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client.post(
            '/api/users/{id:d}/tellzones/delete/'.format(id=self.user.id),
            {
                'tellzone_id': self.tellzone.id,
                'action': 'Favorite',
            },
            format='json',
        )
        assert response.data == {}
        assert response.status_code == 200

        response = self.client.get('/api/users/{id:d}/tellzones/'.format(id=self.user.id), format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

        response = self.client.delete('/api/users/{id:d}/'.format(id=self.user.id), format='json')
        assert response.status_code == 200

    def test_b(self):
        user_ids = [1, 2, 3, 4, 5]
        response = self.client.post('/api/users/{id:d}/messages/'.format(id=self.user.id), user_ids, format='json')
        assert len(response.data) == len(user_ids)
        assert response.status_code == 200

    def test_c(self):
        response = self.client.get('/api/users/{id:d}/tellzones/all/'.format(id=self.user.id), format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

        response = self.client.post(
            '/api/users/{id:d}/tellzones/'.format(id=self.user.id),
            {
                'tellzone_id': self.tellzone.id,
                'action': 'Favorite',
            },
            format='json',
        )
        assert response.data['tellzone_id'] == self.tellzone.id
        assert response.status_code == 201

        response = self.client.get('/api/users/{id:d}/tellzones/all/'.format(id=self.user.id), format='json')
        assert len(response.data) == 1
        assert response.data[0]['id'] == self.tellzone.id
        assert response.data[0]['name'] == self.tellzone.name
        assert response.data[0]['source'] == 3
        assert response.status_code == 200

    def test_d(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token 0.0')
        response = self.client.get('/api/ads/', format='json')
        assert response.data['detail'] == 'Invalid Token - #2'
        assert response.status_code == 403

        self.client.credentials(HTTP_AUTHORIZATION='Token {id:d}.0'.format(id=self.user.id))
        response = self.client.get('/api/ads/', format='json')
        assert response.data['detail'] == 'Invalid Token - #3'
        assert response.status_code == 403


class UsersSettings(TransactionTestCase):

    def setUp(self):
        self.user_1 = middleware.mixer.blend(
            'api.User',
            last_name=middleware.mixer.faker.last_name(),
            photo_original=middleware.mixer.faker.word(),
            photo_preview=middleware.mixer.faker.word(),
            phone=middleware.mixer.faker.phone_number(),
        )
        models.UserSetting.objects.get_queryset().filter(user_id=self.user_1.id, key__contains='show_').update(
            value=True,
        )

        self.client_1 = APIClient()
        self.client_1.credentials(HTTP_AUTHORIZATION=get_header(self.user_1.token))

        self.user_2 = middleware.mixer.blend(
            'api.User',
            last_name=middleware.mixer.faker.last_name(),
            photo_original=middleware.mixer.faker.word(),
            photo_preview=middleware.mixer.faker.word(),
            phone=middleware.mixer.faker.phone_number(),
        )
        models.UserSetting.objects.get_queryset().filter(user_id=self.user_2.id, key__contains='show_').update(
            value=False,
        )

        self.client_2 = APIClient()
        self.client_2.credentials(HTTP_AUTHORIZATION=get_header(self.user_2.token))

    def test_a(self):
        response = self.client_1.get('/api/users/{id:d}/profile/'.format(id=self.user_2.id), format='json')
        assert response.data['email'] is None
        assert response.data['last_name'] is None
        assert response.data['photo_original'] is None
        assert response.data['photo_preview'] is None
        assert response.data['phone'] is None
        assert response.status_code == 200

        response = self.client_2.get('/api/users/{id:d}/profile/'.format(id=self.user_1.id), format='json')
        assert response.data['email'] is not None
        assert response.data['last_name'] is not None
        assert response.data['photo_original'] is not None
        assert response.data['photo_preview'] is not None
        assert response.data['phone'] is not None
        assert response.status_code == 200


def get_header(token):
    return 'Token {token:s}'.format(token=token)


def get_point():
    return fromstr('POINT(1.00 1.00)')
