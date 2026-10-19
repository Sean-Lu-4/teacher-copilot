import tempfile, threading, unittest, urllib.request
from teacher_copilot.review_app import create_server
from teacher_copilot.worksheets import bank_data
class PortalTests(unittest.TestCase):
 def test_routes_and_old_teacher_links(self):
  with tempfile.TemporaryDirectory() as root:
   from pathlib import Path
   server=create_server(Path(root),0,'127.0.0.1')
   worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
   try:
    base='http://127.0.0.1:'+str(server.server_port)
    for path,expected in [('/', '我是学生'),('/teacher','设置练习'),('/?picked=Q1','设置练习'),('/practice','我的单元进度'),('/practice?view=mistakes','mistake-list'),('/progress.js','wasWrong'),('/practice.js','localStorage'),('/learn.css','.unit-grid')]:
     with urllib.request.urlopen(base+path) as r:self.assertIn(expected,r.read().decode())
   finally:server.shutdown();server.server_close();worker.join()
 def test_student_pool_has_valid_mcq_keys_and_units(self):
  rows=[q for q in bank_data()['questions'] if q.get('source_item_id')]
  self.assertEqual(len(rows),len({q['id'] for q in rows}))
  for q in rows:
   self.assertTrue(q['units'])
   if q['question_kind']=='concept':self.assertIn(q['answer_key'],q['options'])
