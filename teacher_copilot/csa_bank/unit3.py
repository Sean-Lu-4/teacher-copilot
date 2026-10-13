from . import q

q('3.1','B','抽象保留哪些信息', 'A classroom program records a Book for borrowing. Possible details: title, identifier, loan status, printing-press temperature.',
  'Which details belong in this abstraction for the stated purpose? Explain one exclusion.', '书名、编号、借出状态与借阅任务相关；印刷机温度与该用途无关，可省略。抽象依据用途选择信息。',
  ['选择与借阅相关的信息','依据用途解释省略'], '抽象就是把现实中的所有信息都存起来', kind='concept')
q('3.1','A','划分类的职责', 'A school app contains Student, Course, and an enrollment operation. A proposal stores the same editable course title separately in every student record.',
  'Identify a maintenance problem and propose where course identity and title should belong. Explain how the design reduces inconsistent copies.', '课程名修改后，多份学生记录可能不一致；把课程标识和名称集中在 Course，由选课关系关联学生与课程，减少重复编辑。',
  ['识别重复数据不一致风险','提出有清晰职责的实体','说明关联和集中更新'], '增加更多复制字段就能解决一致性', kind='concept')
q('3.1','E','为票库存量设计合约', 'A TicketPool has a fixed capacity and supports reserve(k) and remaining(). A failed reservation must not change the pool.',
  'Design private state and method contracts. Cover negative k, insufficient capacity, and successful reservation. Give a short scenario testing the invariant.',
  '保存 private int remaining，初始为容量。reserve(k) 对负数或 k>remaining 返回 false 且不改状态，成功时扣减并返回 true；remaining() 只读取。容量 5，预订 3 成功余 2，再订 4 失败仍余 2。约束 0<=remaining<=capacity。',
  ['私有状态与只读查询合理','失败不改状态且条件明确','用测试检验容量约束'], '先扣数量再检查是否允许', kind='concept')

q('3.2','B','识别受影响的人', 'A homework portal times out after 30 seconds and discards all unfinished text.',
  'Name two groups affected by this choice and one design improvement. Explain the connection between the choice and its impact.', '输入较慢的人和连接不稳定的人更容易丢失内容；可自动保存草稿并允许恢复。可接受其他有明确因果关系的群体和改进。',
  ['指出具体受影响群体','把设计选择与后果联系起来','提出对应改进'], '只评价外观而不考虑使用后果', kind='concept')
q('3.2','A','公平性与可访问性', 'A booking app can be used only with a mouse and displays availability using red and green dots with no text.',
  'Identify two accessibility barriers and propose a specific alternative for each. State how you would test the improvements.', '无法使用鼠标者缺少键盘操作；颜色识别困难者无法区分状态。支持键盘焦点与操作，用文字/图标补充颜色；做仅键盘流程测试并与目标用户验证状态识别。',
  ['分别识别输入与视觉障碍','提出可执行替代方案','给出对应验证方式'], '认为加大按钮即可解决所有可访问性问题', kind='concept')
q('3.2','E','需求冲突下的设计决策', 'A study app wants public leaderboards with real names to motivate students. Some users do not want their study performance exposed.',
  'Propose a design balancing motivation and user control. State a benefit, a remaining risk, and a measurable way to evaluate the design.', '例如默认不公开、可自愿使用昵称加入榜单，并允许退出；保留激励同时减少被迫曝光。仍可能通过昵称或成绩识别个人；评估自愿参与率、退出率和用户访谈，不只看使用时长。',
  ['提出同时考虑双方需求的设计','说明剩余风险','定义可检验的评价指标'], '只用开发者的目标判断设计好坏', kind='concept')

q('3.3','B','类中成员的角色', 'class Lamp {\n private boolean on;\n public Lamp(){on=false;}\n public void switchOn(){on=true;}\n public boolean isOn(){return on;}\n}',
  'Identify the field, constructor, mutator, and accessor.', 'on 是字段；Lamp() 是构造器；switchOn 是修改方法；isOn 是访问方法。',
  ['正确区分四种成员','说明状态和行为的区别'], '把构造器当成有返回值的普通方法', kind='concept')
LAMP='static class Lamp{private boolean on;Lamp(){on=false;}void switchOn(){on=true;}boolean isOn(){return on;}}'
q('3.3','A','实例状态独立', LAMP+'\n// In main: Lamp a=new Lamp(),b=new Lamp();a.switchOn();System.out.print(a.isOn()+","+b.isOn());',
  'State the output. Explain why the private field can still be changed by switchOn.', '输出 true,false。实例方法可以访问自己类的私有字段；每个 Lamp 有独立状态。',
  ['区分两个实例的状态','说明 private 对同类方法可见'], 'private 字段完全不能修改', expected='true,false', members=LAMP, body='Lamp a=new Lamp(),b=new Lamp();a.switchOn();System.out.print(a.isOn()+","+b.isOn());')
q('3.3','E','编写有约束的类', 'Implement a BoundedCounter class. Constructor receives max>=0. Initial value is 0. advance() increments only if value<max. get() returns value. Fields must be private.',
  'Write the complete class. After new BoundedCounter(2) and three advance calls, get must return 2.', '使用两个私有字段保存值和上限，构造器初始化；advance 在未达上限时递增；get 不修改对象。',
  ['字段私有且正确初始化','递增遵守上限','查询返回当前状态'], '检查 <=max 导致多加一次', kind='write',
  solution='static class BoundedCounter{\n private int value,max;\n public BoundedCounter(int limit){max=limit;value=0;}\n public void advance(){if(value<max)value++;}\n public int get(){return value;}\n}', members='{{solution}}', body='BoundedCounter c=new BoundedCounter(2);c.advance();c.advance();c.advance();System.out.print(c.get());', expected='2', checks='for(int n=0;n<=20;n++){BoundedCounter b=new BoundedCounter(n);for(int i=0;i<25;i++)b.advance();if(b.get()!=n)throw new AssertionError();}')

q('3.4','B','构造器初始化', 'static class Point{int x;Point(int start){x=start;}}\n// In main: Point p=new Point(7);System.out.print(p.x);',
  'State the output. When does the constructor execute?', '输出 7；执行 new Point(7) 创建对象时运行构造器并初始化字段。', ['关联 new 与构造器','字段初始化为实参值'], '构造器会在每次读取字段时运行', expected='7', members='static class Point{int x;Point(int start){x=start;}}', body='Point p=new Point(7);System.out.print(p.x);')
q('3.4','A','参数遮蔽字段', 'static class Score{int points;Score(int points){points=points;}}\n// In main: Score s=new Score(8);System.out.print(s.points);',
  'State the output. Repair the constructor assignment and explain the original error.', '输出 0，实例 int 字段默认值为 0；points=points 只把参数赋给自己。用 this.points=points 初始化字段。',
  ['识别字段默认值','区分参数和字段','用 this 修正'], '右侧传入 8 就认为字段已保存', expected='0', members='static class Score{int points;Score(int points){points=points;}}', body='Score s=new Score(8);System.out.print(s.points);')
q('3.4','E','两个构造器保持一致约束', 'Implement a Range class with private int low,high. Range(int a,int b) stores the smaller as low and larger as high. Range(int x) stores x in both fields. Include getLow/getHigh.',
  'Write both constructors and the accessors. Do not assume a<=b.', '双参数构造器按大小排序；单参数把两端设为 x；访问方法返回对应字段。',
  ['逆序参数正确处理','单参数初始化两端','访问方法类型和字段正确'], '只处理已排好序的输入', kind='write',
  solution='static class Range{\n private int low,high;\n public Range(int a,int b){if(a<=b){low=a;high=b;}else{low=b;high=a;}}\n public Range(int x){low=x;high=x;}\n public int getLow(){return low;}\n public int getHigh(){return high;}\n}', members='{{solution}}', body='Range r=new Range(8,2);Range s=new Range(4);System.out.print(r.getLow()+","+r.getHigh()+";"+s.getLow()+","+s.getHigh());', expected='2,8;4,4', checks='for(int a=-3;a<=3;a++)for(int b=-3;b<=3;b++){Range r2=new Range(a,b);if(r2.getLow()!=Math.min(a,b)||r2.getHigh()!=Math.max(a,b))throw new AssertionError();}')

q('3.5','B','return 终止当前方法', 'static int choose(int x){if(x<0)return 0;return x+1;}\n// Calls: choose(-2), choose(2)', 'Give both return values and explain which statement executes for -2.', '返回 0、3。负数分支 return 后，当前调用结束，不再执行后面的 return。', ['负数提前返回','正数路径正确'], '认为两个 return 都会执行', expected='0,3', members='static int choose(int x){if(x<0)return 0;return x+1;}', body='System.out.print(choose(-2)+","+choose(2));')
q('3.5','A','修复覆盖不全的返回路径', 'static int sign(int x){\n if(x>0)return 1;\n if(x<0)return -1;\n // missing code\n}',
  'Add the missing statement so the method compiles and returns 0 for zero. Explain why a non-void method needs a return on every normal path.', '补 return 0;。正负以外的正常路径也必须返回一个 int。',
  ['零路径返回零','说明非 void 方法返回要求'], '只有常见路径需要返回值', kind='write', solution='static int sign(int x){if(x>0)return 1;if(x<0)return -1;return 0;}', members='{{solution}}', body='System.out.print(sign(-3)+","+sign(0)+","+sign(7));', expected='-1,0,1')
q('3.5','E','方法的前置条件与完整实现', 'static boolean increasingDigits(int n){ /* complete */ }\n// 0<=n<=2147483647. Return true if decimal digits strictly increase from left to right. Single-digit inputs return true.',
  'Complete the method. For 147, 144, 321, and 7 return true,false,false,true.', '从右向左取相邻数字；若左边数字大于等于右边则 false，否则继续；全部满足则 true。',
  ['相邻比较方向正确','相等时也失败','单数字正常返回 true'], '忽略重复数字或把比较方向反过来', kind='write', solution='static boolean increasingDigits(int n){\n while(n>=10){int right=n%10;n/=10;if(n%10>=right)return false;}\n return true;\n}', members='{{solution}}', body='System.out.print(increasingDigits(147)+","+increasingDigits(144)+","+increasingDigits(321)+","+increasingDigits(7));', expected='true,false,false,true', checks='for(int n=0;n<10000;n++){String s=""+n;boolean expected=true;for(int i=1;i<s.length();i++)if(s.charAt(i-1)>=s.charAt(i))expected=false;if(increasingDigits(n)!=expected)throw new AssertionError();}')

CELL='static class Cell{int value;Cell(int v){value=v;}}'
q('3.6','B','传入引用后修改对象', CELL+'\nstatic void bump(Cell c){c.value++;}\n// In main: Cell a=new Cell(4);bump(a);System.out.print(a.value);',
  'State the output. What is copied into the parameter c?', '输出 5。复制的是引用值，a 和参数 c 指向同一对象，因此能看到字段变化。', ['传递引用的副本','通过副本修改同一对象'], '把传对象说成自动深拷贝', expected='5', members=CELL+'static void bump(Cell c){c.value++;}', body='Cell a=new Cell(4);bump(a);System.out.print(a.value);')
q('3.6','A','参数重新绑定不会替换调用者', CELL+'\nstatic void change(Cell c){c.value++;c=new Cell(99);}\n// In main: Cell a=new Cell(4);change(a);System.out.print(a.value);',
  'State the output and explain why 99 is not printed.', '输出 5。第一次修改共享对象；c=new Cell(99) 只重新绑定局部参数，不会改变 a 的引用。', ['区分修改对象和赋值参数','调用者仍指向旧对象'], '方法内重新赋值参数会替换实参变量', expected='5', members=CELL+'static void change(Cell c){c.value++;c=new Cell(99);}', body='Cell a=new Cell(4);change(a);System.out.print(a.value);')
q('3.6','E','返回内部引用与封装', CELL+'\nstatic class Holder{private Cell data=new Cell(7);Cell get(){return data;}}\n// In main: Holder h=new Holder();Cell a=h.get();a.value=0;System.out.print(h.get().value);',
  'State the output. Change get so callers can inspect a copy without changing the stored Cell. Explain why a private field alone was insufficient.', '输出 0。原 get 暴露了内部可变对象；改为 return new Cell(data.value); 返回独立副本。private 只阻止直接字段访问，不阻止经返回引用修改对象。',
  ['识别内部引用泄露','返回新对象而非相同引用','解释 private 的边界'], '私有字段的对象永远不可能从外部修改', expected='0', members=CELL+'static class Holder{private Cell data=new Cell(7);Cell get(){return data;}}', body='Holder h=new Holder();Cell a=h.get();a.value=0;System.out.print(h.get().value);', checks='Cell original=new Cell(7);Cell copy=new Cell(original.value);copy.value=0;if(original.value!=7)throw new AssertionError();')

q('3.7','B','static 字段由类共享', 'static class Badge{static int count=0;Badge(){count++;}}\n// In main: new Badge();new Badge();System.out.print(Badge.count);',
  'State the output and whether each Badge has a separate count.', '输出 2。count 是类共享字段，不是每个实例独有。', ['两次构造使共享值增加','区分类变量和实例变量'], '每次 new 会重置 static 字段', expected='2', members='static class Badge{static int count=0;Badge(){count++;}}', body='new Badge();new Badge();System.out.print(Badge.count);')
q('3.7','A','类方法没有隐含接收者', 'class Account{\n private int balance;\n public static int getBalance(){return balance;}\n}',
  'Explain why getBalance does not compile. Give two design repairs and state which preserves a separate balance for each account.', 'static 方法不能无对象访问实例字段。可把 getBalance 改为实例方法；或接收 Account 参数并读其字段。把 balance 改为 static 会共享余额，通常不符合账户独立要求。',
  ['指出没有隐含实例','提出实例方法修复','保留每账户独立余额'], '为消除错误把所有字段都改 static', kind='concept')
q('3.7','E','分配唯一序号', 'Implement Ticket with a private static next starting at 1 and private instance id. Each constructor assigns the next id and advances next. getId returns the instance id; issued returns total created. Single-threaded use only.',
  'Write the class and show why creating a third ticket must not change the first ticket id.', '构造器把共享 next 当前值复制到实例 id 再递增。issued 返回 next-1，实例 id 不跟随 next 变化。',
  ['区分共享计数器与实例编号','构造时先取号再递增','统计已创建数量且旧编号不变'], '把 id 也声明为 static', kind='write', solution='static class Ticket{\n private static int next=1;\n private int id;\n public Ticket(){id=next;next++;}\n public int getId(){return id;}\n public static int issued(){return next-1;}\n}', members='{{solution}}', body='Ticket a=new Ticket();Ticket b=new Ticket();Ticket c=new Ticket();System.out.print(a.getId()+","+b.getId()+","+c.getId()+","+Ticket.issued());', expected='1,2,3,3')

q('3.8','B','局部变量的作用范围', 'for(int i=0;i<3;i++){System.out.print(i);}\n// Statement after the loop: System.out.print(i);',
  'Does the statement after the loop compile? Explain the scope of i.', '不编译。i 在 for 初始化处声明，作用域限于这个 for 语句，循环外不可访问。', ['定位声明位置','解释循环外作用域'], '认为执行结束后局部变量仍随处可用', kind='concept')
q('3.8','A','局部遮蔽与字段', 'static class Sample{int x=2;int read(){int x=7;return x+this.x;}}\n// In main: System.out.print(new Sample().read());',
  'State the output. Identify which x each reference denotes.', '输出 9。普通 x 是局部变量 7，this.x 是实例字段 2。', ['识别同名变量的绑定','正确相加'], '同名变量就是同一个存储位置', expected='9', members='static class Sample{int x=2;int read(){int x=7;return x+this.x;}}', body='System.out.print(new Sample().read());')
q('3.8','E','访问权限与设计修复', 'class Vault{private int value=9;public int read(){return value;}}\n// In an unrelated client class: System.out.print(v.value);\n// v refers to a Vault.',
  'Explain the access error. Repair the client while keeping the field private. Why is exposing the field a weaker design?', '客户端应调用 v.read()；不相关类不能直接访问 private value。保持私有可以让类控制读写规则；公开字段会允许任意赋值绕开规则。',
  ['解释类边界上的 private','通过公开访问方法修复','说明封装价值'], '把 private 全部改 public 作为默认修复', kind='concept')

q('3.9','B','this 指当前对象', 'static class Item{int n;Item(int n){this.n=n;}}\n// In main: System.out.print(new Item(6).n);',
  'State the output. Explain this.n versus n in the constructor.', '输出 6。this.n 指当前对象字段，右侧 n 为参数。', ['区分字段与参数','正确初始化'], 'this 是另一个新对象', expected='6', members='static class Item{int n;Item(int n){this.n=n;}}', body='System.out.print(new Item(6).n);')
q('3.9','A','比较当前对象与另一个对象', 'static class Mark{int n;Mark(int n){this.n=n;}boolean higher(Mark other){return this.n>other.n;}}\n// In main: Mark a=new Mark(8),b=new Mark(3);System.out.print(a.higher(b)+","+b.higher(a));',
  'State the output and identify this in each call.', '输出 true,false。第一次 this 是 a，第二次是 b；other 分别是 b、a。', ['调用决定当前接收者','区分两个对象字段'], 'this 固定指第一个创建的对象', expected='true,false', members='static class Mark{int n;Mark(int n){this.n=n;}boolean higher(Mark other){return this.n>other.n;}}', body='Mark a=new Mark(8),b=new Mark(3);System.out.print(a.higher(b)+","+b.higher(a));')
q('3.9','E','使用 this 实现状态转移', 'Implement Wallet with private int coins; constructor takes nonnegative coins. transferTo(Wallet other,int amount) returns false and changes neither wallet if amount<0 or amount>this.coins; otherwise transfer and return true. other is non-null; the sum of both balances fits int. Transferring to itself leaves its balance unchanged.',
  'Write the class, including getCoins. Handle transferTo(this, amount) without losing coins.', '先验证数量，再从 this.coins 扣除并加到 other.coins。若两引用相同，同一字段先减后加恢复原值；失败路径不修改。',
  ['失败不改变任一余额','正确区分接收者与参数对象','自转账不改变总量'], '修改后才检查余额或误读另一个对象', kind='write', solution='static class Wallet{\n private int coins;\n public Wallet(int coins){this.coins=coins;}\n public int getCoins(){return coins;}\n public boolean transferTo(Wallet other,int amount){\n  if(amount<0||amount>this.coins)return false;\n  this.coins-=amount;other.coins+=amount;return true;\n }\n}', members='{{solution}}', body='Wallet a=new Wallet(8),b=new Wallet(2);a.transferTo(b,3);a.transferTo(a,2);System.out.print(a.getCoins()+","+b.getCoins());', expected='5,5', checks='Wallet c=new Wallet(4),d=new Wallet(1);if(c.transferTo(d,5)||c.transferTo(d,-1)||c.getCoins()!=4||d.getCoins()!=1)throw new AssertionError();')
