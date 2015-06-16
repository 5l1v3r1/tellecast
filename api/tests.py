# -*- coding: utf-8 -*-

from django.contrib.gis.geos import fromstr
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
            '/api/tellcards/',
            {
                'user_destination_id': self.user_2.id,
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
                'action': 'Save',
            },
            format='json',
        )
        assert response.status_code == 400

        response = self.client.get('/api/users/{id}/profile/'.format(id=self.user_2.id), format='json')
        assert response.status_code == 400

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

    def setUp(self):
        self.user_1 = middleware.mixer.blend('api.User')
        self.client_1 = APIClient()
        self.client_1.credentials(HTTP_AUTHORIZATION=get_header(self.user_1.token))

        self.user_2 = middleware.mixer.blend('api.User')
        self.client_2 = APIClient()
        self.client_2.credentials(HTTP_AUTHORIZATION=get_header(self.user_2.token))

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
        assert response.data['type'] == dictionary['type']
        assert response.data['contents'] == dictionary['contents']
        assert response.data['status'] == dictionary['status']
        assert response.data['attachments'] == []
        assert response.status_code == 201

        id = response.data['id']

        dictionary['status'] = 'Read'

        response = self.client_1.patch('/api/messages/{id}/'.format(id=id), dictionary, format='json')
        assert response.data['id'] == id
        assert response.data['contents'] == dictionary['contents']
        assert response.status_code == 200

        dictionary = {
            'user_destination_id': self.user_1.id,
            'type': 'Response - Accepted',
            'contents': '1',
            'status': 'Unread',
        }

        response = self.client_2.post('/api/messages/', dictionary, format='json')
        assert response.data['user_source']['id'] == self.user_2.id
        assert response.data['user_source_is_hidden'] is False
        assert response.data['user_destination']['id'] == dictionary['user_destination_id']
        assert response.data['user_destination_is_hidden'] is False
        assert response.data['user_status'] is None
        assert response.data['master_tell'] is None
        assert response.data['type'] == dictionary['type']
        assert response.data['contents'] == dictionary['contents']
        assert response.data['status'] == dictionary['status']
        assert response.data['attachments'] == []
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
        assert len(response.data) == 1
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

        response = self.client_1.delete('/api/messages/{id}/'.format(id=id), format='json')
        assert response.data == {}
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

        response = self.client_2.post(
            '/api/messages/',
            {
                'user_destination_id': self.user_1.id,
                'type': 'Request',
                'contents': '1',
                'status': 'Unread',
            },
            format='json',
        )
        assert response.status_code == 201

        response = self.client_1.get('/api/notifications/', format='json')
        assert len(response.data) == 3
        assert response.data[0]['type'] == 'G'
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


class Radar(TransactionTestCase):

    def setUp(self):
        self.user = middleware.mixer.blend('api.User')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

        with middleware.mixer.ctx(commit=False):
            for tellzone in middleware.mixer.cycle(5).blend('api.Tellzone'):
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
                        'bearing': 180,
                        'is_casting': True,
                    },
                    format='json',
                )
                assert len(response.data) == 5
                assert 'id' in response.data[0]
                assert 'name' in response.data[0]
                assert response.status_code == 200

            for email in [
                'bradotts@gmail.com',
                'callmejerms@aol.com',
                'fl@fernandoleal.me',
                'kevin@tellecast.com',
                'mbatchelder13@yahoo.com',
            ]:
                user = middleware.mixer.blend('api.User', email=email)
                user.point = get_point()
                user.is_signed_in = True
                user.save()

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
                'bearing': 180,
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
        assert 'users' in response.data
        assert len(response.data['users']) > 1
        assert 'degrees' in response.data['users'][0]
        assert 'radius' in response.data['users'][0]
        assert 'items' in response.data['users'][0]
        assert len(response.data['users'][0]['items']) > 1
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

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

        with middleware.mixer.ctx(commit=False):
            for tellzone in middleware.mixer.cycle(5).blend('api.Tellzone'):
                tellzone.point = get_point()
                tellzone.save()
            for user in middleware.mixer.cycle(5).blend('api.User'):
                user.point = get_point()
                user.is_signed_in = True
                user.save()
                for index in range(0, 5):
                    models.MasterTell.objects.create(created_by_id=user.id, owned_by_id=user.id, contents=str(id))
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
                        'bearing': 180,
                        'is_casting': True,
                    },
                    format='json',
                )
                assert len(response.data) == 5
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
        assert len(response.data) == 5
        assert response.status_code == 200

        response = self.client.get(
            '/api/tellzones/{id}/master-tells/'.format(id=models.Tellzone.objects.get_queryset().first().id),
            {
                'latitude': 1.00,
                'longitude': 1.00,
                'radius': 300,
            },
            format='json',
        )
        assert len(response.data) == 25
        assert response.status_code == 200


class Users(TransactionTestCase):

    def setUp(self):
        self.tellzone = middleware.mixer.blend('api.Tellzone')

        self.user = middleware.mixer.blend('api.User')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=get_header(self.user.token))

    def test_a(self):
        assert self.user.is_signed_in is False

        self.user.is_signed_in = True
        self.user.save()

        response = self.client.post('/api/deauthenticate/', format='json')
        assert response.data == {}
        assert response.status_code == 200

        self.user = models.User.objects.get_queryset().filter(id=self.user.id).first()
        assert self.user is not None
        assert self.user.is_signed_in is False

        response = self.client.get('/api/users/0/', format='json')
        assert response.status_code == 400

        response = self.client.get('/api/users/{id}/'.format(id=self.user.id), format='json')
        assert response.data['id'] == self.user.id
        assert response.status_code == 200

        dictionary = {
            'email': self.user.email,
            'first_name': '1',
            'last_name': '1',
        }

        response = self.client.put('/api/users/{id}/'.format(id=self.user.id), dictionary, format='json')
        assert response.data['id'] == self.user.id
        assert response.data['first_name'] == dictionary['first_name']
        assert response.data['last_name'] == dictionary['last_name']
        assert response.status_code == 200

        response = self.client.get('/api/users/{id}/profile/'.format(id=self.user.id), format='json')
        assert response.data['id'] == self.user.id
        assert response.status_code == 200

        response = self.client.get('/api/users/{id}/tellzones/'.format(id=self.user.id), format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

        response = self.client.post(
            '/api/users/{id}/tellzones/'.format(id=self.user.id),
            {
                'tellzone_id': self.tellzone.id,
                'action': 'Favorite',
            },
            format='json',
        )
        assert response.data['tellzone_id'] == self.tellzone.id
        assert response.status_code == 201

        response = self.client.get('/api/users/{id}/tellzones/'.format(id=self.user.id), format='json')
        assert len(response.data) == 1
        assert response.status_code == 200

        response = self.client.post(
            '/api/users/{id}/tellzones/delete/'.format(id=self.user.id),
            {
                'tellzone_id': self.tellzone.id,
                'action': 'Favorite',
            },
            format='json',
        )
        assert response.data == {}
        assert response.status_code == 200

        response = self.client.get('/api/users/{id}/tellzones/'.format(id=self.user.id), format='json')
        assert len(response.data) == 0
        assert response.status_code == 200

        response = self.client.delete('/api/users/{id}/'.format(id=self.user.id), format='json')
        assert response.status_code == 200


def get_header(token):
    return 'Token {token}'.format(token=token)


def get_point():
    return fromstr('POINT(1.00 1.00)')
