import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from teacher_copilot.accounts import Accounts
from teacher_copilot.review_app import create_server


class AccountTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.accounts = Accounts(self.tmp.name)

    def register(self, name='student_1'):
        return self.accounts.authenticate('register', {'username':name,'password':'Test-pass-1234','role':'student'}, 'local')

    def test_password_hash_session_restart_and_recovery_revocation(self):
        token, recovery = self.register()
        uid = self.accounts.user(token)['id']
        self.assertEqual(Accounts(self.tmp.name).user(token)['id'], uid)
        self.assertNotIn(b'Test-pass-1234', self.accounts.path.read_bytes())
        with self.assertRaises(ValueError):
            self.accounts.authenticate('login', {'username':'student_1','password':'Incorrect-pass'},'local')
        new_token, new_recovery = self.accounts.authenticate('reset', {
            'username':'student_1','password':'Another-password','recovery':recovery},'local')
        self.assertIsNone(self.accounts.user(token))
        self.assertEqual(self.accounts.user(new_token)['id'],uid)
        self.assertNotEqual(recovery,new_recovery)
        self.accounts.logout(new_token)
        self.assertIsNone(self.accounts.user(new_token))

    def test_progress_isolation_and_concurrent_update(self):
        a,_=self.register()
        b,_=self.register('student_2')
        uid=self.accounts.user(a)['id']
        self.accounts.progress(uid, {'revision':0,'data':{'q1':{'done':True}}})
        self.assertEqual(self.accounts.progress(self.accounts.user(b)['id'])['data'], {})
        with self.assertRaises(ValueError):
            self.accounts.progress(uid, {'revision':0,'data':{}})
        self.assertTrue(self.accounts.progress(uid)['data']['q1']['done'])

    def test_throttle_and_role_validation(self):
        for _ in range(3):
            self.accounts.throttle('test',3)
        with self.assertRaises(ValueError):
            self.accounts.throttle('test',3)
        with self.assertRaises(ValueError):
            self.accounts.authenticate('register',{'username':'admin_test','password':'Long-password','role':'admin'},'local')

    def test_http_auth_csrf_and_feedback(self):
        server=create_server(Path(self.tmp.name),0,'127.0.0.1')
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base='http://127.0.0.1:'+str(server.server_port)
        def request(path,data=None,cookie='',token=''):
            headers={'Content-Type':'application/json','Cookie':cookie,'X-Review-Token':token}
            return urlopen(Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers=headers))
        token=json.load(request('/api/account'))['token']
        with self.assertRaises(HTTPError) as err:
            request('/api/account/register',{'username':'web_test','password':'Test-password'})
        self.assertEqual(err.exception.code,403)
        response=request('/api/account/register',{'username':'web_test','password':'Test-password'},token=token)
        cookie=response.headers['Set-Cookie'].split(';')[0]
        self.assertIn('HttpOnly',response.headers['Set-Cookie'])
        self.assertEqual(json.load(request('/api/account',cookie=cookie))['user']['username'],'web_test')
        self.assertEqual(json.load(request('/api/account/progress',cookie=cookie))['data'],{})
        request('/api/account/progress',{'revision':0,'data':{'Q1':{'done':True}}},cookie,token).close()
        with self.assertRaises(HTTPError) as err:
            request('/api/account/progress')
        self.assertEqual(err.exception.code,401)
        other=request('/api/account/register',{'username':'other_web','password':'Test-password'},token=token)
        other_cookie=other.headers['Set-Cookie'].split(';')[0]
        other.close()
        self.assertEqual(json.load(request('/api/account/progress',cookie=other_cookie))['data'],{})
        self.assertTrue(json.load(request('/api/account/progress',cookie=cookie))['data']['Q1']['done'])
        result=json.load(request('/api/feedback',{'kind':'bug','comment':'Mobile test','page':'/practice','contact':'tester'},token=token))
        self.assertTrue(result['saved'])
        self.assertIn(b'/community.js',request('/practice').read())
        self.assertNotIn(b'/community.js',request('/admin').read())


if __name__=='__main__':
    unittest.main()
