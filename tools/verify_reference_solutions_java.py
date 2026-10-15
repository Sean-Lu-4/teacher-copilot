import json,subprocess,os,shutil,tempfile
from pathlib import Path
sol=json.loads(Path('teacher_copilot/imported_bank/reference_solutions_20261015.json').read_text(encoding='utf8'))
fields={'2':'ArrayList<ItemInfo> inventory;','4':'ArrayList<Player> playerList;','7':'String[][] grid;','8':'ArrayList<ElectricVehicle> vehicleList;','11':'ArrayList<String> wordList;','12':'Candy[][] box;','13':'TriviaQuestion[] allQuestions; int getMostDifficult(){return Arrays.stream(allQuestions).mapToInt(x->x.getDifficultyLevel()).max().getAsInt();} int getLeastDifficult(){return Arrays.stream(allQuestions).mapToInt(x->x.getDifficultyLevel()).min().getAsInt();}','14':'int[] itemsSold; double[] wages;','15':'ArrayList<Double> temperatures;','16':'String openDel="(";String closeDel=")";','17':'ArrayList<String> possibleNames; boolean isUsed(String n,String[] a){return Arrays.asList(a).contains(n);}','18':'int[][] grid;','19':'Plot[][] farmPlots;'}
stubs='''record ItemInfo(double cost,boolean available){public double getCost(){return cost;}public boolean isAvailable(){return available;}}
record Player(String id,int score){public String getID(){return id;}public int getScore(){return score;}}
record ElectricVehicle(String model,int range){public String getModelName(){return model;}public int getRange(){return range;}}
record Candy(String flavor){public String getFlavor(){return flavor;}}
record TriviaQuestion(int difficulty){public int getDifficultyLevel(){return difficulty;}}
record Location(int row,int col){public int getRow(){return row;}public int getCol(){return col;}}
record Plot(String crop,int yield){public String getCropType(){return crop;}public int getCropYield(){return yield;}}
'''
s='import java.util.*;\npublic class ReferenceCheck {\nstatic int checks=0; static void check(boolean b){checks++;if(!b)throw new AssertionError("check "+checks);}\n'+stubs
for n,v in sol.items():s+='static class '+v['name']+'{'+fields[n]+'\n'+v['code']+'\n}\n'
s+='''public static void main(String[] args){
ItemInventory a=new ItemInventory();a.inventory=new ArrayList<>(List.of(new ItemInfo(10,true),new ItemInfo(20,true),new ItemInfo(15,false),new ItemInfo(100,true)));check(a.averageWithinRange(10,20)==15);check(a.averageWithinRange(20,20)==20);
PlayerAnalysis p=new PlayerAnalysis();p.playerList=new ArrayList<>(List.of(new Player("A",10),new Player("B",20)));check(p.playerWithClosestScore(15).equals("A"));check(p.playerWithClosestScore(20).equals("B"));check(p.playerWithClosestScore(-2147483648).equals("A"));
WordGrid g=new WordGrid();g.grid=new String[][]{{"a","b"},{"aa","b"},{"a","bb"}};check(g.countOrderedRows()==2);
EVDataSet e=new EVDataSet();e.vehicleList=new ArrayList<>(List.of(new ElectricVehicle("A",100),new ElectricVehicle("A",150),new ElectricVehicle("B",100),new ElectricVehicle("C",200)));check(e.getHighRangeVehicles(100).equals(List.of("A","C")));check(e.getHighRangeVehicles(200).isEmpty());
WordChecker w=new WordChecker();w.wordList=new ArrayList<>(List.of("cat","bobcat","bobcatcat"));check(w.isWordChain());w.wordList=new ArrayList<>(List.of("catch","bobcat","cat","at"));check(!w.isWordChain());check(w.createList("cat").equals(List.of("ch","")));check(w.wordList.size()==4);
BoxOfCandy b=new BoxOfCandy();Candy c=new Candy("lime");b.box=new Candy[][]{{null,null},{c,null}};check(b.moveCandyToFirstRow(0));check(b.box[0][0]==c&&b.box[1][0]==null);check(!b.moveCandyToFirstRow(1));check(b.moveCandyToFirstRow(0));b.box[1][1]=new Candy("lime");Candy low=b.box[1][1];check(b.removeNextByFlavor("lime")==low);check(b.box[1][1]==null);check(b.removeNextByFlavor("none")==null);
TriviaGame t=new TriviaGame();t.allQuestions=new TriviaQuestion[]{new TriviaQuestion(0),new TriviaQuestion(50),new TriviaQuestion(100)};check(t.getRating().equals("Intermediate"));check(t.isDifficultyIncreasing());t.allQuestions[1]=new TriviaQuestion(70);check(t.getRating().equals("Expert"));t.allQuestions[1]=new TriviaQuestion(49);check(t.getRating().equals("Beginner"));t.allQuestions=new TriviaQuestion[]{new TriviaQuestion(80),new TriviaQuestion(80),new TriviaQuestion(80)};check(t.isDifficultyIncreasing()&&t.getRating().equals("Expert"));
Payroll r=new Payroll();r.itemsSold=new int[]{1,2,3,4};r.wages=new double[4];check(r.computeBonusThreshold()==2.5);r.computeWages(10,2);check(r.wages[0]==12&&Math.abs(r.wages[2]-17.6)<0.00001);r.itemsSold=new int[]{3,3,3};check(r.computeBonusThreshold()==3);
WeatherData h=new WeatherData();h.temperatures=new ArrayList<>(List.of(1.0,2.0,5.0,6.0,10.0,11.0));h.cleanData(5,10);check(h.temperatures.equals(List.of(5.0,6.0,10.0)));check(h.longestHeatWave(5)==2);h.temperatures=new ArrayList<>(List.of(9.0,9.0,5.0,9.0,9.0,9.0));check(h.longestHeatWave(5)==3);
Delimiters d=new Delimiters();check(d.getDelimitersList(new String[]{"(","x",")"}).equals(List.of("(",")")));check(d.isBalanced(new ArrayList<>()));check(d.isBalanced(new ArrayList<>(List.of("(","(",")",")"))));check(!d.isBalanced(new ArrayList<>(List.of(")","("))));check(!d.isBalanced(new ArrayList<>(List.of("("))));
UserName u=new UserName("john","smith");check(u.possibleNames.equals(List.of("smithj","smithjo","smithjoh","smithjohn")));u.setAvailableUserNames(new String[]{"smithj","smithjo","smithjohn"});check(u.possibleNames.equals(List.of("smithjoh")));u.setAvailableUserNames(new String[]{"smithjoh"});check(u.possibleNames.isEmpty());
GridPath path=new GridPath();path.grid=new int[][]{{1,5,9},{2,4,8},{3,6,7}};check(path.getNextLoc(0,0).equals(new Location(1,0)));check(path.getNextLoc(2,0).equals(new Location(2,1)));check(path.getNextLoc(0,2).equals(new Location(1,2)));check(path.sumPath(0,0)==19);check(path.sumPath(2,2)==7);
ExperimentalFarm f=new ExperimentalFarm();Plot corn=new Plot("corn",30);f.farmPlots=new Plot[][]{{corn,new Plot("pea",5)},{new Plot("corn",10),new Plot("wheat",8)}};check(f.getHighestYield("corn")==corn);check(f.getHighestYield("none")==null);check(f.sameCrop(0));check(!f.sameCrop(1));
System.out.println("PASS: "+checks+" checks across 13 reference solutions");}}
'''
javac=os.environ.get('JAVAC') or shutil.which('javac')
if not javac: raise SystemExit('Set JAVAC to a JDK compiler or add javac to PATH.')
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp)/'ReferenceCheck.java';p.write_text(s,encoding='utf8')
 subprocess.run([javac,str(p)],check=True)
 java=Path(javac).with_name('java.exe' if os.name=='nt' else 'java')
 subprocess.run([str(java),'-cp',temp,'ReferenceCheck'],check=True)
