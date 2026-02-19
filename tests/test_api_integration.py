from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class ApiIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_and_ready(self):
        self.assertEqual(self.client.get('/health').status_code, 200)
        ready = self.client.get('/ready')
        self.assertEqual(ready.status_code, 200)
        self.assertIn('status', ready.json())

    def test_sessions_and_chat(self):
        create = self.client.post('/sessions', json={'session_id': 'itest', 'display_name': 'ITest'})
        self.assertEqual(create.status_code, 200)

        chat = self.client.post('/chat', json={'session_id': 'itest', 'text': 'Bitte antworte kurz'})
        self.assertEqual(chat.status_code, 200)
        self.assertIn('reply', chat.json())

        sessions = self.client.get('/sessions')
        self.assertEqual(sessions.status_code, 200)

    def test_jobs_and_policy(self):
        payload = {
            'name': 'itest-job',
            'cron': '0 */30 * * * *',
            'enabled': True,
            'payload': {'kind': 'heartbeat', 'channel': 'web-ui'},
        }
        created = self.client.post('/jobs', json=payload)
        self.assertEqual(created.status_code, 200)
        job_id = created.json()['job']['job_id']

        pause = self.client.post(f'/jobs/{job_id}/pause')
        self.assertEqual(pause.status_code, 200)
        resume = self.client.post(f'/jobs/{job_id}/resume')
        self.assertEqual(resume.status_code, 200)

        policy = self.client.post('/policy/shell-check', json={'command': 'ls -la'})
        self.assertEqual(policy.status_code, 200)
        self.assertTrue(policy.json()['ok'])

    def test_webhook_ingest(self):
        r = self.client.post('/webhooks/manual', json={'payload': {'text': 'Hallo vom Webhook'}})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['status'], 'accepted')


if __name__ == '__main__':
    unittest.main()
