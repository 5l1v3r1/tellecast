# -*- coding: utf-8 -*-

from django.test import TransactionTestCase
from rest_framework.test import APIClient

from api import middleware, models


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


class DevicesAPNS(TransactionTestCase):

    def setUp(self):
        self.user = middleware.mixer.blend('api.User')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

    def test_a(self):
        response = self.client.get('/api/devices/apns/', format='json')
        assert response.data == []
        assert response.status_code == 200

        dictionary = {
            'name': '1',
            'device_id': '1',
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

        dictionary['name'] = '2'
        dictionary['registration_id'] = '2'

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
            'name': '2',
            'device_id': '2',
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

        response = self.client.delete('/api/devices/apns/{id}/'.format(id=id), format='json')
        assert response.data == {}
        assert response.status_code == 200

        response = self.client.get('/api/devices/apns/', format='json')
        assert len(response.data) == 1
        assert response.status_code == 200


class DevicesGCM(TransactionTestCase):

    def setUp(self):
        self.user = middleware.mixer.blend('api.User')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

    def test_a(self):
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

        response = self.client.delete('/api/devices/gcm/{id}/'.format(id=id), format='json')
        assert response.data == {}
        assert response.status_code == 200

        response = self.client.get('/api/devices/gcm/', format='json')
        assert len(response.data) == 1
        assert response.status_code == 200


class Home(TransactionTestCase):

    def setUp(self):
        self.user = middleware.mixer.blend('api.User')

        middleware.mixer.cycle(5).blend('api.User')
        middleware.mixer.cycle(5).blend('api.Tellzone')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

    def test_a(self):
        dictionary = {
            'latitude': 1.00,
            'longitude': 1.00,
            'dummy': 'Yes',
        }

        response = self.client.get('/api/home/connections/', dictionary, format='json')
        assert len(response.data) == 5
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

        response = self.client.get('/api/home/tellzones/', dictionary, format='json')
        assert len(response.data) == 5
        assert response.status_code == 200


class MasterTells(TransactionTestCase):

    def setUp(self):
        self.user = middleware.mixer.blend('api.User')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

    def test_a(self):
        response = self.client.get('/api/master-tells/', format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

        dictionary = {
            'contents': '1',
        }

        response = self.client.post('/api/master-tells/', dictionary, format='json')
        assert response.data['created_by_id'] == self.user.id
        assert response.data['owned_by_id'] == self.user.id
        assert response.data['contents'] == dictionary['contents']
        assert response.data['position'] == 1
        assert response.data['is_visible'] is True
        assert response.status_code == 201

        id = response.data['id']

        response = self.client.get('/api/master-tells/', format='json')
        assert len(response.data) == 1
        assert response.status_code == 200

        dictionary = {
            'contents': '2',
        }

        response = self.client.put('/api/master-tells/{id}/'.format(id=id), dictionary, format='json')
        assert response.data['id'] == id
        assert response.data['created_by_id'] == self.user.id
        assert response.data['owned_by_id'] == self.user.id
        assert response.data['contents'] == dictionary['contents']
        assert response.data['position'] == 1
        assert response.data['is_visible'] is True
        assert response.status_code == 200

        response = self.client.delete('/api/master-tells/{id}/'.format(id=id), format='json')
        assert response.data == {}
        assert response.status_code == 200

        response = self.client.get('/api/master-tells/', format='json')
        assert len(response.data) == 0
        assert response.status_code == 200


class Messages(TransactionTestCase):
    pass


class Notifications(TransactionTestCase):
    pass


class Radar(TransactionTestCase):
    pass


class Shares(TransactionTestCase):
    pass


class SlaveTells(TransactionTestCase):

    def setUp(self):
        self.user = middleware.mixer.blend('api.User')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

    def test_a(self):
        response = self.client.get('/api/slave-tells/', format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

        response = self.client.post(
            '/api/master-tells/',
            {
                'contents': '1',
            },
            format='json',
        )
        master_tell_id = response.data['id']

        dictionary = {
            'master_tell_id': master_tell_id,
            'type': 'image/*',
            'contents': '1',
            'description': '1',
        }

        response = self.client.post('/api/slave-tells/', dictionary, format='json')
        assert response.data['master_tell_id'] == dictionary['master_tell_id']
        assert response.data['created_by_id'] == self.user.id
        assert response.data['owned_by_id'] == self.user.id
        assert response.data['type'] == dictionary['type']
        assert response.data['contents'] == dictionary['contents']
        assert response.data['description'] == dictionary['description']
        assert response.data['position'] == 1
        assert response.data['is_editable'] is True
        assert response.status_code == 201

        id = response.data['id']

        response = self.client.get('/api/slave-tells/', format='json')
        assert len(response.data) == 1
        assert response.status_code == 200

        dictionary['contents'] = '2'
        dictionary['description'] = '2'

        response = self.client.put('/api/slave-tells/{id}/'.format(id=id), dictionary, format='json')
        assert response.data['master_tell_id'] == dictionary['master_tell_id']
        assert response.data['created_by_id'] == self.user.id
        assert response.data['owned_by_id'] == self.user.id
        assert response.data['type'] == dictionary['type']
        assert response.data['contents'] == dictionary['contents']
        assert response.data['description'] == dictionary['description']
        assert response.data['position'] == 1
        assert response.data['is_editable'] is True
        assert response.status_code == 200

        response = self.client.delete('/api/slave-tells/{id}/'.format(id=id), format='json')
        assert response.data == {}
        assert response.status_code == 200

        response = self.client.get('/api/slave-tells/', format='json')
        assert len(response.data) == 0
        assert response.status_code == 200


class Tellcards(TransactionTestCase):
    pass


class Tellzones(TransactionTestCase):
    pass


class Users(TransactionTestCase):

    def setUp(self):
        self.client = APIClient()

    def test_a_deauthenticate(self):
        self.user = middleware.mixer.blend('api.User')

        assert self.user.is_signed_in is False

        self.user.is_signed_in = True
        self.user.save()

        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

        response = self.client.post('/api/deauthenticate/', format='json')
        assert response.data == {}
        assert response.status_code == 200

        self.user = models.User.objects.get_queryset().filter(id=self.user.id).first()
        assert self.user is not None
        assert self.user.is_signed_in is False

    def test_b(self):
        pass

    def test_c_tellzones(self):
        pass

    def test_d_profile(self):
        pass


def get_header(token):
        return 'Token {token}'.format(token=token)
