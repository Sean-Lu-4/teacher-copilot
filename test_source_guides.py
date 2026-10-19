import unittest,tempfile,threading,urllib.request,urllib.error
from pathlib import Path
from teacher_copilot.source_guides import pages_for,render_page,index
from teacher_copilot.review_app import create_server
class SourceGuideTests(unittest.TestCase):
 def test_entire_email_guide_and_no_duplicate_documents(self):
  pages=pages_for('FRQ-2459373609e2732d')
  self.assertEqual([p['page'] for p in pages],list(range(1,11)))
  self.assertEqual(len({p['document'] for p in pages}),1)
 def test_all_ranges_are_valid_and_unique(self):
  docs,guides=index()
  for pages in guides.values():
   self.assertEqual(len(pages),len({(p['document'],p['page']) for p in pages}))
   self.assertTrue(all(1<=p['page']<=docs[p['document']]['pages'] for p in pages))
 def test_rejects_unknown_document_and_invalid_page(self):
  doc=pages_for('FRQ-2459373609e2732d')[0]['document']
  for d,p in [('../secrets',1),('0'*64,1),(doc,0),(doc,9999)]:
   with self.assertRaises(ValueError):render_page(d,p)
 def test_http_preview_and_path_validation(self):
  with tempfile.TemporaryDirectory() as root:
   server=create_server(Path(root),0,'127.0.0.1');t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
   try:
    base='http://127.0.0.1:'+str(server.server_port);page=pages_for('FRQ-2459373609e2732d')[0]
    with urllib.request.urlopen(base+'/scoring-page/'+page['document']+'/1.png') as r:
     self.assertEqual(r.headers.get_content_type(),'image/png');self.assertTrue(r.read().startswith(b'\x89PNG'))
    with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(base+'/scoring-page/'+page['document']+'/999.png')
    self.assertEqual(e.exception.code,404)
   finally:server.shutdown();server.server_close();t.join()
if __name__=='__main__':unittest.main()
