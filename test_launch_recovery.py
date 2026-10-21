import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from teacher_copilot.accounts import Accounts
from teacher_copilot.review_app import create_server
from teacher_copilot import exam

class LaunchRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.accounts=Accounts(self.tmp.name)
    def register(self,name):
        token,_=self.accounts.authenticate('register',{'username':name,'password':'Test-password-2026'},'test')
        return token,self.accounts.user(token)
    def test_verified_email_reset_replay_and_session_revocation(self):
        token,user=self.register('mail_test')
        with patch('teacher_copilot.account_mail.available',return_value=True),patch('teacher_copilot.account_mail.send_code') as send:
            c=self.accounts.request_code('bind',{'email':'learner@example.com','password':'Test-password-2026'},'test',user['id'])
            code=send.call_args.args[1]
            self.assertIsNone(self.accounts.user(token)['email'])
            self.accounts.consume_code(c['challenge'],code,'bind',user['id'])
            self.assertEqual(self.accounts.user(token)['email'],'learner@example.com')
            with self.assertRaises(ValueError):self.accounts.consume_code(c['challenge'],code,'bind',user['id'])
            c=self.accounts.request_code('reset',{'username':'mail_test'},'test')
            code=send.call_args.args[1]
            new,recovery=self.accounts.authenticate('reset',{'username':'mail_test','password':'New-password-2026','challenge':c['challenge'],'email_code':code},'test')
            self.assertIsNone(self.accounts.user(token));self.assertEqual(self.accounts.user(new)['id'],user['id'])
            with self.assertRaises(ValueError):self.accounts.consume_code(c['challenge'],code,'reset')
    def test_email_bruteforce_expiry_owner_and_unconfigured(self):
        token,user=self.register('owner_one');_,other=self.register('owner_two')
        with patch('teacher_copilot.account_mail.available',return_value=False):
            with self.assertRaises(ValueError):self.accounts.request_code('reset',{'username':'owner_one'},'test')
        with patch('teacher_copilot.account_mail.available',return_value=True),patch('teacher_copilot.account_mail.send_code') as send:
            c=self.accounts.request_code('bind',{'email':'learner@example.com','password':'Test-password-2026'},'test',user['id']);code=send.call_args.args[1]
            with self.assertRaises(ValueError):self.accounts.consume_code(c['challenge'],code,'bind',other['id'])
            for _ in range(5):
                with self.assertRaises(ValueError):self.accounts.consume_code(c['challenge'],'wrong','bind',user['id'])
            with self.assertRaises(ValueError):self.accounts.consume_code(c['challenge'],code,'bind',user['id'])
            c=self.accounts.request_code('bind',{'email':'learner@example.com','password':'Test-password-2026'},'test',user['id']);code=send.call_args.args[1]
            with self.accounts.connect() as db:db.execute('UPDATE email_codes SET expires=0')
            with self.assertRaises(ValueError):self.accounts.consume_code(c['challenge'],code,'bind',user['id'])
    def test_latest_exam_restart_isolation_deadline_and_stale_drafts(self):
        a=Path(self.tmp.name)/'a';b=Path(self.tmp.name)/'b'
        first=exam.action(a,{'action':'start'},now=1000);qid=first['questions'][0]['id']
        exam.action(a,{'action':'save','id':first['id'],'revision':0,'drafts':{qid:'local answer'}},now=1001)
        latest=exam.action(a,{'action':'latest'},now=1002)['session']
        self.assertEqual(latest['drafts'][qid],'local answer');self.assertEqual(latest['deadline'],6400)
        self.assertIsNone(exam.action(b,{'action':'latest'},now=1002)['session'])
        with self.assertRaises(ValueError):exam.action(b,{'action':'get','id':first['id']},now=1002)
        with self.assertRaises(ValueError):exam.action(a,{'action':'save','id':first['id'],'revision':0,'drafts':{qid:'stale'}},now=1002)
        ended=exam.action(a,{'action':'latest'},now=6500)['session']
        self.assertEqual(ended['drafts'][qid],'local answer');self.assertEqual(ended['status'],'submitted')
    def test_http_changed_account_cannot_write_old_tab_and_device_resume(self):
        server=create_server(Path(self.tmp.name),0,'127.0.0.1');threading.Thread(target=server.serve_forever,daemon=True).start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        base='http://127.0.0.1:'+str(server.server_port)
        def req(path,data=None,cookie='',owner=None):
            headers={'Content-Type':'application/json','Cookie':cookie,'X-Review-Token':csrf}
            if owner is not None:headers['X-Account-ID']=owner
            with urlopen(Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=headers)) as r:return json.load(r)
        csrf=json.load(urlopen(base+'/api/account'))['token']
        a,ua=self.register('web_a');b,ub=self.register('web_b')
        s=req('/api/exam',{'action':'start'},'csa_account='+a,ua['id']);qid=s['questions'][0]['id']
        req('/api/exam',{'action':'save','id':s['id'],'revision':0,'drafts':{qid:'answer a'}},'csa_account='+a,ua['id'])
        for path,payload in [('/api/exam',{'action':'save','id':s['id'],'revision':1,'drafts':{qid:'wrong owner'}}),('/api/account/progress',{'revision':0,'data':{'secret':'wrong owner'}})]:
            with self.assertRaises(HTTPError) as err:req(path,payload,'csa_account='+b,ua['id'])
            self.assertEqual(err.exception.code,409)
        self.assertIsNone(req('/api/exam',{'action':'latest'},'csa_account='+b,ub['id'])['session'])
        new_token,_=self.accounts.authenticate('login',{'username':'web_a','password':'Test-password-2026'},'device2')
        restored=req('/api/exam',{'action':'latest'},'csa_account='+new_token,ua['id'])['session']
        self.assertEqual(restored['drafts'][qid],'answer a');self.assertEqual(restored['deadline'],s['deadline'])
        self.accounts.logout(a)
        with self.assertRaises(HTTPError) as err:req('/api/exam',{'action':'latest'},'csa_account='+a,ua['id'])
        self.assertEqual(err.exception.code,409)

if __name__=='__main__':unittest.main()
