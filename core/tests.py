from django.test import TestCase, Client
import json

class SignalingTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_create_room(self):
        response = self.client.post('/api/create-room/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('room_id', data)
        self.assertEqual(len(data['room_id']), 6)

    def test_signaling_flow(self):
        # Create room
        res = self.client.post('/api/create-room/')
        room_id = res.json()['room_id']

        # Offerer posts offer
        offer_payload = {
            'sender': 'offerer',
            'type': 'offer',
            'offer': {'type': 'offer', 'sdp': 'v=0\r\ntest'}
        }
        res_offer = self.client.post(f'/api/signal/{room_id}/', data=json.dumps(offer_payload), content_type='application/json')
        self.assertEqual(res_offer.status_code, 200)

        # Answerer polls and receives offer
        poll_res = self.client.get(f'/api/signal/{room_id}/?sender=answerer&after=0')
        self.assertEqual(poll_res.status_code, 200)
        msgs = poll_res.json().get('messages', [])
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['type'], 'offer')

    def test_home_instructions_section(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('id="instrucciones"', content)
        self.assertIn('Instrucciones: ¿Cómo se usa?', content)
        self.assertIn('guideTabOfflineBtn', content)
        self.assertIn('guideTabLanBtn', content)
        self.assertIn('guideTabTipsBtn', content)
        self.assertIn('Modo Offline Puro', content)
        self.assertIn('Modo Aula', content)
