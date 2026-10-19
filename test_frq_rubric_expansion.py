import unittest
from teacher_copilot.java_score_evidence import evidence, RULES
from teacher_copilot.java_grading import PROFILES

class RubricExpansionTests(unittest.TestCase):
    def rows(self,q,code,states,part=None):
        return evidence(q,code,dict(status='passed' if all(s=='passed' for s in states) else 'failed',cases=[dict(status=s) for s in states]),[dict(id=str(i),description='criterion',points=1) for i in range(12)],part)
    def test_helper_extraction_preserves_api_point(self):
        q='AP-FRQe12b4823e927b30fS1'
        rows=self.rows(q,'private int years(GameAccount item){return item.getAge();} public double avgTeenAccounts(){return years(allPlayers.get(0));}', ['passed']*3)
        self.assertEqual(rows[1]['status'],'earned')
    def test_comments_and_uncalled_helpers_do_not_count(self):
        q='AP-FRQe12b4823e927b30fS1'
        for body in ['// getAge()\nreturn 16;', 'return 16;']:
            rows=self.rows(q,'private int unused(GameAccount item){return item.getAge();} public double avgTeenAccounts(){'+body+'}', ['passed']*3)
            self.assertEqual(rows[1]['status'],'unverified')
    def test_failed_boundary_withholds_related_points(self):
        q='AP-FRQe12b4823e927b30fS1'
        rows=self.rows(q,'public double avgTeenAccounts(){return allPlayers.get(0).getAge();}',['failed','passed','passed'])
        self.assertTrue(all(rows[i]['status']=='unverified' for i in range(5)))
    def test_independent_method_keeps_points(self):
        q='AP-FRQ69fc5af861bea528S10'
        rows=self.rows(q,'public int findFreeBlock(int p,int d){return -1;} public boolean makeAppointment(int a,int b,int d){int start=findFreeBlock(a,d);reserveBlock(a,start,d);return true;}', ['failed','failed','passed'])
        self.assertEqual(rows[4]['status'],'unverified')
        self.assertEqual(rows[6]['status'],'earned')
        self.assertEqual(rows[8]['status'],'earned')
    def test_selected_part_does_not_show_other_parts_pending(self):
        rows=self.rows('AP-FRQ69fc5af861bea528S3','System.out.print(songInfo);',['passed']*2,1)
        self.assertEqual([r['id'] for r in rows if r.get('applicable')],['3','4','5'])
        self.assertTrue(all(rows[i]['status']=='earned' for i in [3,4,5]))
    def test_missing_results_never_award(self):
        rows=self.rows('AP-FRQ69fc5af861bea528S3','System.out.print(songInfo);',[],1)
        self.assertTrue(all(r['status']=='unverified' for r in rows))
    def test_email_accepts_variable_names_but_not_randomness_from_output(self):
        rows=self.rows('AP-FRQ2459373609e2732d','String anyName=email.substring(0,1);',['passed']*3)
        self.assertTrue(all(rows[i]['status']=='earned' for i in [1,2,3,4]))
        self.assertTrue(all(rows[i]['status']=='unverified' for i in [0,5,6,7,8]))
    def test_syntax_errors_do_not_create_evidence(self):
        rows=self.rows('AP-FRQe12b4823e927b30fS1','public double avgTeenAccounts( { return 1; }',['passed']*3)
        self.assertTrue(all(r['status']=='unverified' for r in rows))
    def test_all_rule_test_indices_exist(self):
        for q,rules in RULES.items():
            count=len(PROFILES[q]['cases'])
            for rule in rules:
                self.assertTrue(rule['cases'],q)
                self.assertTrue(all(type(i) is int and 0<=i<count for i in rule['cases']),q)
    def test_accumulation_accepts_increment_and_expanded_assignment(self):
        q='AP-FRQe12b4823e927b30fS2'
        for update in ['count++','count+=1','count=count+1','count=1+count']:
            code='public int getLongestHomeWinStreak(){int count=0;while(true){if(true){'+update+';}break;}return count;}'
            self.assertEqual(self.rows(q,code,['passed']*3)[3]['status'],'earned')
    def test_accumulation_does_not_accept_reset_on_every_iteration(self):
        q='AP-FRQe12b4823e927b30fS2'
        code='public int getLongestHomeWinStreak(){while(true){int count=0;if(true)count++;break;}return 0;}'
        self.assertEqual(self.rows(q,code,['passed']*3)[3]['status'],'unverified')
    def test_mixed_gates_require_both_null_check_and_equals(self):
        q='AP-FRQ764c3eaaeb638f9fS12'
        code='public Candy removeNextByFlavor(String flavor){if(box[0][0]!=null)return box[0][0];return null;}'
        self.assertEqual(self.rows(q,code,['passed']*len(PROFILES[q]['cases']))[6]['status'],'unverified')
    def test_random_distribution_and_written_design_stay_unverified(self):
        rows=self.rows('AP-FRQ69fc5af861bea528S6','public void simulateOneDay(int n){currentFood=0;}public int simulateManyDays(int n,int d){return 0;}',['passed']*3)
        self.assertTrue(all(rows[i]['status']=='unverified' for i in range(4)))

if __name__=='__main__':unittest.main()
