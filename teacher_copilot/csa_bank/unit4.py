from . import q

q('4.1','B','收集目的与必要字段', 'A lunch-order app asks for meal choice, pickup time, home address, and national identity number.',
  'Which fields are necessary for school pickup? Identify a risk of collecting the other fields.', '餐品和取餐时间通常足够；住址和身份证号与校内取餐无直接关系，额外收集增加泄露与滥用风险。',
  ['依据目的判断必要性','解释不必要敏感数据的风险'], '能够收集就应全部保存', kind='concept')
q('4.1','A','匿名不等于无法识别', 'A public dataset removes names but retains exact birth date, postcode, and rare medical condition.',
  'Explain why removing names may not prevent re-identification. Propose two changes that reduce risk while preserving some analytical value.', '多个字段组合可能与外部信息匹配到个人。可把日期转成年龄段、扩大地理范围、合并罕见类别或限制访问；需要权衡分析精度与风险。',
  ['解释组合识别风险','提出两种对应改进','说明分析价值的权衡'], '没有姓名就保证匿名', kind='concept')
q('4.1','E','数据使用方案的取舍', 'A school wants to publish individual attendance histories to encourage punctuality. Students were told the data was collected to take attendance.',
  'Assess the proposed change of purpose. Recommend a less intrusive approach, a retention rule, and a way to address incorrect records.', '公开个人历史改变原收集目的，可能造成污名和误解；可发布汇总趋势并对个人私下反馈。只保留实现目的所需时间，设更正与申诉渠道并明确访问范围。',
  ['识别用途改变及可能伤害','提出较少暴露的替代方案','说明保留期限与纠错机制'], '只追求激励效果而忽略数据使用后果', kind='concept')

q('4.2','B','区分记录与字段', 'Dataset columns: studentCode, travelMinutes, travelMode.\nRows: A1,20,bus; A2,10,walk; A3,35,bus.',
  'How many records and fields are shown? Name one quantitative field and one categorical field.', '3 条记录、3 个字段。travelMinutes 是数量字段；travelMode 是类别字段。',
  ['区分行记录和列字段','正确判断字段类型'], '把记录条数和字段数混用', kind='concept')
q('4.2','A','清洗前先明确含义', 'Travel-minute values: 10, 20, -1, 30. The data dictionary says -1 means missing.',
  'Compute the mean of valid records. Explain why treating -1 as an actual travel time gives a misleading result and why silently replacing it with zero is also questionable.', '有效均值 (10+20+30)/3=20。-1 是缺失标志，不是时长；零代表真实零分钟，也不能无说明地代替未知值。',
  ['按字典识别缺失','使用有效分母得到 20','区分缺失与零'], '把所有数值无差别放进统计', kind='concept')
q('4.2','E','样本能支持什么结论', 'A survey of school commute time was posted only in the cycling club chat. 40 responses reported a mean of 12 minutes.',
  'Can this establish the school-wide mean? Identify a sampling limitation, a better collection plan, and metadata needed for reliable interpretation.', '不能直接代表全校；骑行社群可能在交通方式和距离上有偏。应覆盖不同年级与交通方式并记录抽样过程、时间、单位、缺失和样本量。12 分钟可描述这批回应者。',
  ['限定结论适用范围','提出更广泛的抽样方案','说明必要的数据背景'], '样本量大就自动消除抽样偏差', kind='concept')

q('4.3','B','数组默认值与索引', 'int[] a=new int[3];\na[1]=7;\nSystem.out.print(a[0]+","+a[1]+","+a.length);', 'State the output and the valid indices.', '输出 0,7,3；有效索引为 0、1、2，int 数组默认元素为 0。', ['默认值正确','区分长度和最大索引'], '最大索引就是 length', expected='0,7,3')
q('4.3','A','数组引用的别名', 'int[] a={2,4,6};\nint[] b=a;\nb[0]=9;\nSystem.out.print(a[0]+","+(a==b));',
  'State the output and explain whether a second array was created.', '输出 9,true。赋值复制引用，没有新建数组。', ['共享同一数组','引用相等和元素修改一致'], '引用赋值复制所有元素', expected='9,true')
q('4.3','E','创建独立数组副本', 'static int[] copy(int[] a){ /* complete */ }\n// a is non-null, possibly empty.',
  'Return an independent array with the same contents. Changing the returned array must not change a. Do not use clone or library copying methods.', 'new 一个等长数组，逐个复制元素并返回。空数组也创建并返回长度零的新数组。',
  ['分配独立数组','正确复制所有元素','空数组不越界'], '直接 return a 造成别名', kind='write', solution='static int[] copy(int[] a){\n int[] result=new int[a.length];\n for(int i=0;i<a.length;i++)result[i]=a[i];\n return result;\n}', members='{{solution}}', body='int[] a={2,4};int[] b=copy(a);b[0]=9;System.out.print(a[0]+","+b[0]+","+copy(new int[0]).length);', expected='2,9,0', checks='int[] source={-1,0,7};int[] dest=copy(source);if(source==dest||!java.util.Arrays.equals(source,dest))throw new AssertionError();')

q('4.4','B','增强 for 读取元素', 'int[] a={3,1,4};\nint sum=0;\nfor(int x:a)sum+=x;\nSystem.out.print(sum);', 'State the output. Does x represent an index or an element value?', '输出 8；x 是当前元素值，不是索引。', ['正确累计','说明增强循环变量含义'], '把 x 作为索引再访问', expected='8')
q('4.4','A','增强 for 不能这样更新数组', 'int[] a={2,3};\nfor(int x:a)x*=2;\nSystem.out.print(a[0]+","+a[1]);',
  'State the output. Rewrite the loop so it doubles the stored array elements.', '输出 2,3；x 是基本类型元素的副本。应使用索引循环 a[i]*=2。',
  ['识别未修改数组','改用索引访问更新元素'], '修改增强循环变量就改变原数组', expected='2,3', checks='for(int i=0;i<a.length;i++)a[i]*=2;if(a[0]!=4||a[1]!=6)throw new AssertionError();')
q('4.4','E','逆序交换而非覆盖', 'static void reverse(int[] a){ /* complete */ }\n// a is non-null; reverse in place without allocating another array.',
  'Complete reverse. Handle odd, even, and zero lengths without swapping pairs twice.', '只遍历前半部分，使用临时值与对称位置 length-1-i 交换；中间元素不必交换。',
  ['计算对称索引','保存旧值避免覆盖','只交换前半部分'], '全程遍历导致又交换回原样', kind='write', solution='static void reverse(int[] a){\n for(int i=0;i<a.length/2;i++){int j=a.length-1-i;int temp=a[i];a[i]=a[j];a[j]=temp;}\n}', members='{{solution}}', body='int[] a={1,2,3};reverse(a);System.out.print(java.util.Arrays.toString(a));', expected='[3, 2, 1]', checks='for(int n=0;n<=10;n++){int[] x=new int[n];for(int i=0;i<n;i++)x[i]=i;reverse(x);for(int i=0;i<n;i++)if(x[i]!=n-1-i)throw new AssertionError();}')

q('4.5','B','求最大值的初始化', 'int[] a={-4,-2,-9};\nint best=a[0];\nfor(int x:a)if(x>best)best=x;\nSystem.out.print(best);', 'State the output. Why would initializing best to 0 be wrong here?', '输出 -2；若初始为 0，会错误保留数组中不存在的更大值。', ['正确求最大值','用全负数说明初始化问题'], '最大值总可从零开始', expected='-2')
q('4.5','A','相邻递增关系', 'int[] a={1,3,2,4,4};\nint count=0;\nfor(int i=1;i<a.length;i++)if(a[i]>a[i-1])count++;\nSystem.out.print(count);',
  'State the output and identify the counted pairs. Does this prove the entire array is sorted?', '输出 2，对应 1→3 和 2→4；仍有 3→2，不能说明全数组有序。', ['识别严格递增的相邻对','区分局部统计和整体有序'], '把相等也计作严格增加', expected='2')
q('4.5','E','最长连续相等段', 'static int longestRun(int[] a){ /* complete */ }\n// a is non-null; empty array returns 0.',
  'Return the length of the longest run of equal adjacent values. For {2,2,3,3,3,2} return 3.', '维护当前连续段长度和最大段长度；相等则递增，不等重置为 1；空数组返回 0。',
  ['初始化和空数组正确','相等与变化时更新当前长度','每轮更新最大值'], '把同值总次数当连续段长度', kind='write', solution='static int longestRun(int[] a){\n if(a.length==0)return 0;\n int run=1,best=1;\n for(int i=1;i<a.length;i++){\n  if(a[i]==a[i-1])run++;else run=1;\n  if(run>best)best=run;\n }\n return best;\n}', members='{{solution}}', body='System.out.print(longestRun(new int[]{2,2,3,3,3,2})+","+longestRun(new int[0]));', expected='3,0', checks='if(longestRun(new int[]{4})!=1||longestRun(new int[]{1,2,1})!=1||longestRun(new int[]{5,5,5,5})!=4)throw new AssertionError();')

q('4.6','B','逐项读取真实文本文件', 'java.util.Scanner in=new java.util.Scanner(new java.io.File("numbers.txt"));\nint total=0;\nwhile(in.hasNext()){total+=in.nextInt();}\nin.close();\nSystem.out.print(total);\n// File contents: 3 5 2',
  'State the output. Explain why hasNext is checked before reading. Assume the file exists and contains only integers.', '输出 10。hasNext 确认还有输入，避免到文件末尾后继续读取。', ['正确累计文件内容','解释终止读取条件'], '末尾自动读取到一个零', expected='10', files={'numbers.txt':'3 5 2'}, body='java.util.Scanner in=new java.util.Scanner(new java.io.File("numbers.txt"));int total=0;while(in.hasNext())total+=in.nextInt();in.close();System.out.print(total);')
q('4.6','A','行读取包含空行', 'java.util.Scanner in=new java.util.Scanner(new java.io.File("names.txt"));\nString a=in.nextLine();\nString b=in.nextLine();\nString c=in.nextLine();\nin.close();\nSystem.out.print(a+"|"+b+"|"+c);\n// File lines: Ada, an empty line, Bo.',
  'State the exact output and distinguish an empty line from end of file.', '输出 Ada||Bo。空行是可读取的零长度字符串，不等于文件结束。', ['保留空行位置','区分空行和无剩余输入'], '认为空行会被 nextLine 自动跳过', expected='Ada||Bo', files={'names.txt':'Ada\n\nBo\n'}, body='java.util.Scanner in=new java.util.Scanner(new java.io.File("names.txt"));String a=in.nextLine(),b=in.nextLine(),c=in.nextLine();in.close();System.out.print(a+"|"+b+"|"+c);')
q('4.6','E','读取文件并跳过缺失标志', 'static double mean(java.util.Scanner in){ /* complete */ }\n// Scanner is connected to a text file. Every token is an integer.\n// -1 means missing; all other values are nonnegative. At least one valid value exists.',
  'Complete mean. Read every token, ignore -1, and return the real mean of valid values. Do not close the caller-owned Scanner.', '分别维护有效总和与有效个数；读取值为 -1 时不加入两者；使用 double 总和避免整数除法。',
  ['遍历全部输入并忽略缺失','有效计数正确','返回实数均值'], '忽略缺失值但仍把它计入分母', kind='write', solution='static double mean(java.util.Scanner in){\n double total=0;int count=0;\n while(in.hasNext()){int x=in.nextInt();if(x!=-1){total+=x;count++;}}\n return total/count;\n}', members='{{solution}}', body='java.util.Scanner in=new java.util.Scanner(new java.io.File("scores.txt"));System.out.print(mean(in));in.close();', expected='2.5', files={'scores.txt':'-1 2 3 -1'}, checks='if(mean(new java.util.Scanner("0 -1 0"))!=0.0||mean(new java.util.Scanner("-1 7 -1"))!=7.0)throw new AssertionError();')

q('4.7','B','装箱与拆箱', 'Integer boxed=7;\nint n=boxed;\nSystem.out.print(n+2);', 'State the output and identify boxing and unboxing.', '输出 9。把 int 7 存入 Integer 引用发生装箱；赋给 int n 时拆箱。', ['识别两个转换方向','计算结果正确'], 'Integer 与 int 完全没有转换', expected='9')
q('4.7','A','包装对象与相等', 'Integer a=Integer.valueOf(1000);\nInteger b=Integer.valueOf(1000);\nSystem.out.print(a.equals(b)+","+(a.intValue()==b.intValue()));',
  'State the output. Why is a.equals(b) preferable to relying on a==b for comparing numeric contents?', '输出 true,true。equals 比较包装的数值；== 比较对象引用，不能依赖实现缓存来判断数值相等。', ['两种内容比较正确','区分引用比较和数值比较'], '包装类的 == 永远等于数值比较', expected='true,true')
q('4.7','E','拆箱前处理空值', 'static int valueOrZero(Integer value){ /* complete */ }\n// Return 0 for null; otherwise return the represented int.',
  'Complete the method without causing a null-unboxing exception. Explain why int n=value; before checking null is unsafe.', '先判断 value==null 再决定返回 0 或拆箱；若先赋给 int，空引用会在检查前就拆箱异常。',
  ['null 判断先于拆箱','非 null 正确返回数值','解释错误顺序的后果'], '认为装箱类型 null 自动表示零', kind='write', solution='static int valueOrZero(Integer value){if(value==null)return 0;return value.intValue();}', members='{{solution}}', body='System.out.print(valueOrZero(null)+","+valueOrZero(Integer.valueOf(-3)));', expected='0,-3', checks='if(valueOrZero(Integer.valueOf(0))!=0||valueOrZero(Integer.valueOf(2147483647))!=2147483647)throw new AssertionError();')

q('4.8','B','插入改变后续下标', 'java.util.ArrayList<String> a=new java.util.ArrayList<String>();\na.add("A");a.add("C");a.add(1,"B");\nSystem.out.print(a.get(2)+","+a.size());',
  'State the output and the final list order.', '顺序为 A、B、C；输出 C,3，插入使原索引 1 的 C 右移。', ['正确插入位置','size 为元素个数'], 'add(index,value) 是替换', expected='C,3')
q('4.8','A','set 与 remove 的返回值', 'java.util.ArrayList<String> a=new java.util.ArrayList<String>();\na.add("A");a.add("B");a.add("C");\nString old=a.set(1,"X");\nString removed=a.remove(0);\nSystem.out.print(old+","+removed+","+a);',
  'State the output. Which operation changes the size?', '输出 B,A,[X, C]。set 返回旧值但不改长度；remove 删除元素并使长度减 1。', ['正确解释两个返回值','跟踪列表顺序与长度'], 'set 会插入额外元素', expected='B,A,[X, C]')
q('4.8','E','整数列表 remove 的参数含义', 'java.util.ArrayList<Integer> a=new java.util.ArrayList<Integer>();\na.add(4);a.add(1);a.add(4);\na.remove(1);\nSystem.out.print(a);',
  'State the output. Using an index loop and remove(index), write statements that remove only the first value equal to 4, if present. Do not assume its index.', '原输出 [4, 4]，remove(1) 删除索引 1 的值。随后先找首个值 4 的索引，找到才按该索引删除。',
  ['识别 remove(int) 删除索引','找到首个匹配值','不存在时保持原列表'], '把 remove(1) 当作按数值删除 1', kind='write', solution='int index=-1;\nfor(int i=0;i<a.size() && index==-1;i++)if(a.get(i)==4)index=i;\nif(index!=-1)a.remove(index);', body='java.util.ArrayList<Integer> a=new java.util.ArrayList<Integer>();a.add(4);a.add(1);a.add(4);a.remove(1);System.out.print(a+" -> ");{{solution}}System.out.print(a);', expected='[4, 4] -> [4]')

q('4.9','B','按索引遍历列表', 'java.util.ArrayList<Integer> a=new java.util.ArrayList<Integer>();\na.add(2);a.add(5);a.add(1);\nint total=0;\nfor(int i=0;i<a.size();i++)total+=a.get(i);\nSystem.out.print(total);', 'State the output and the last legal index.', '输出 8，最后合法索引为 2。', ['遍历到 size-1','正确累计'], '把 size 当合法元素索引', expected='8')
q('4.9','A','删除后的跳项问题', 'java.util.ArrayList<Integer> a=new java.util.ArrayList<Integer>();\na.add(-1);a.add(-2);a.add(3);\nfor(int i=0;i<a.size();i++)if(a.get(i)<0)a.remove(i);\nSystem.out.print(a);',
  'State the output. Explain why a negative value remains.', '输出 [-2, 3]。删除 -1 后 -2 左移到索引 0，而 i 递增到 1，导致漏检。', ['跟踪删除后的移动','解释 i 自增导致跳项'], '认为 remove 不影响其他下标', expected='[-2, 3]')
q('4.9','E','安全删除所有负数', 'static void removeNegatives(java.util.ArrayList<Integer> a){ /* complete */ }\n// a is non-null and has no null elements.',
  'Complete the method in place. Handle consecutive negatives, all-negative lists, and empty lists.', '从最后一个索引向前遍历，删除不会影响尚未处理的更小索引。',
  ['遍历方向或索引控制正确','删除全部负数','空列表安全'], '删除后照常递增而跳过相邻负数', kind='write', solution='static void removeNegatives(java.util.ArrayList<Integer> a){\n for(int i=a.size()-1;i>=0;i--)if(a.get(i)<0)a.remove(i);\n}', members='{{solution}}', body='java.util.ArrayList<Integer> a=new java.util.ArrayList<Integer>(java.util.Arrays.asList(-1,-2,0,3,-4));removeNegatives(a);System.out.print(a);', expected='[0, 3]', checks='java.util.ArrayList<Integer> b=new java.util.ArrayList<Integer>(java.util.Arrays.asList(-2,-1));removeNegatives(b);removeNegatives(b);if(b.size()!=0)throw new AssertionError();')

q('4.10','B','条件计数', 'java.util.ArrayList<Integer> a=new java.util.ArrayList<Integer>();\na.add(3);a.add(7);a.add(7);a.add(2);\nint count=0;\nfor(int x:a)if(x>=7)count++;\nSystem.out.print(count);', 'State the output and whether duplicate values are counted separately.', '输出 2。两个 7 是不同元素，分别计数。', ['按元素而非不同值计数','>= 包含边界'], '重复数值只计一次', expected='2')
q('4.10','A','有序列表中定位插入点', 'java.util.ArrayList<Integer> a=new java.util.ArrayList<Integer>();\na.add(2);a.add(5);a.add(5);a.add(9);\nint target=5,index=0;\nwhile(index<a.size() && a.get(index)<target)index++;\na.add(index,target);\nSystem.out.print(index+":"+a);',
  'State the output and explain whether the new value is before or after existing equal values.', '输出 1:[2, 5, 5, 5, 9]；遇到第一个相等值就停止，所以插在已有 5 之前。', ['正确找到索引 1','解释严格小于的停止条件'], '忽略重复元素插入位置', expected='1:[2, 5, 5, 5, 9]')
q('4.10','E','有序列表去重', 'static void unique(java.util.ArrayList<Integer> a){ /* complete */ }\n// a is sorted in nondecreasing order, non-null, with no null elements. Keep one copy of each value, in place.',
  'Complete unique without constructing a second list. Handle runs of more than two equal values.', '从末尾向前比较相邻值，相等则删当前索引。由于有序，所有重复都相邻。',
  ['利用有序保证相邻重复','删除时不跳过重复段','空或单元素安全'], '一次跳过两个位置导致三连重复残留', kind='write', solution='static void unique(java.util.ArrayList<Integer> a){\n for(int i=a.size()-1;i>0;i--)if(a.get(i).equals(a.get(i-1)))a.remove(i);\n}', members='{{solution}}', body='java.util.ArrayList<Integer> a=new java.util.ArrayList<Integer>(java.util.Arrays.asList(1,1,1,2,4,4));unique(a);System.out.print(a);', expected='[1, 2, 4]', checks='java.util.ArrayList<Integer> b=new java.util.ArrayList<Integer>();unique(b);b.add(1000);b.add(1000);unique(b);if(b.size()!=1)throw new AssertionError();')

q('4.11','B','行列与访问次序', 'int[][] a={{1,2,3},{4,5,6}};\nSystem.out.print(a.length+","+a[0].length+","+a[1][2]);', 'State the output and identify the row and column of 6.', '输出 2,3,6。6 在行索引 1、列索引 2。', ['行数列数正确','使用先行后列下标'], '把行列顺序颠倒', expected='2,3,6')
q('4.11','A','二维数组的默认值与修改', 'int[][] a=new int[2][3];\na[1][0]=8;\na[0][2]=a[1][0]+1;\nSystem.out.print(a[0][0]+","+a[0][2]+","+a[1][0]);',
  'State the output and count how many entries are still zero.', '输出 0,9,8；6 个元素中修改两个，剩余 4 个为零。', ['追踪两个不同位置','正确统计默认零值'], '修改一行会自动修改其他行', expected='0,9,8')
q('4.11','E','构造单位矩阵', 'static int[][] identity(int n){ /* complete */ }\n// 0<=n<=100. Return an n by n array with 1 on the main diagonal and 0 elsewhere.',
  'Complete identity. Explain why non-diagonal elements need no explicit assignment.', 'new int[n][n] 默认全零，只需把 [i][i] 设为 1；n=0 返回零行数组。',
  ['创建正确尺寸','对角索引正确','利用默认值并处理零尺寸'], '将一整行都赋成 1', kind='write', solution='static int[][] identity(int n){\n int[][] a=new int[n][n];\n for(int i=0;i<n;i++)a[i][i]=1;\n return a;\n}', members='{{solution}}', body='System.out.print(java.util.Arrays.deepToString(identity(3)));', expected='[[1, 0, 0], [0, 1, 0], [0, 0, 1]]', checks='for(int n=0;n<=10;n++){int[][] a=identity(n);if(a.length!=n)throw new AssertionError();for(int r=0;r<n;r++)for(int c=0;c<n;c++)if(a[r][c]!=(r==c?1:0))throw new AssertionError();}')

q('4.12','B','行优先遍历', 'int[][] a={{1,2},{3,4}};\nfor(int r=0;r<a.length;r++)for(int c=0;c<a[0].length;c++)System.out.print(a[r][c]);',
  'State the output and the order of visited positions.', '输出 1234，顺序为 [0][0]、[0][1]、[1][0]、[1][1]。', ['识别外层控制行','正确输出顺序'], '误按列优先读取', expected='1234')
q('4.12','A','列优先遍历', 'int[][] a={{1,2,3},{4,5,6}};\nfor(int c=0;c<a[0].length;c++)for(int r=0;r<a.length;r++)System.out.print(a[r][c]);',
  'State the output and explain why swapping loop order changes it.', '输出 142536。外层固定列，内层依次遍历该列的各行。', ['使用正确行列上界','解释列优先顺序'], '只交换循环顺序却仍按行输出', expected='142536')
q('4.12','E','逐行求和', 'static int[] rowTotals(int[][] a){ /* complete */ }\n// a is a non-null rectangular array; may have zero rows or zero columns.',
  'Return one sum per row without modifying a. Handle zero rows without reading a[0].', '结果长度为行数；每行从零累计该行所有列，可用 a[r].length，避免零行时访问 a[0]。',
  ['输出长度匹配行数','每行独立累加','零行和零列均安全'], '累计变量未重置导致后面行包含前面结果', kind='write', solution='static int[] rowTotals(int[][] a){\n int[] totals=new int[a.length];\n for(int r=0;r<a.length;r++)for(int c=0;c<a[r].length;c++)totals[r]+=a[r][c];\n return totals;\n}', members='{{solution}}', body='System.out.print(java.util.Arrays.toString(rowTotals(new int[][]{{1,2},{3,4}})));', expected='[3, 7]', checks='if(rowTotals(new int[0][0]).length!=0||!java.util.Arrays.equals(rowTotals(new int[2][0]),new int[]{0,0}))throw new AssertionError();')

q('4.13','B','二维数组条件计数', 'int[][] a={{-1,2},{0,3}};\nint count=0;\nfor(int[] row:a)for(int value:row)if(value>0)count++;\nSystem.out.print(count);', 'State the output. Is zero counted?', '输出 2；只统计 2 和 3，零不满足 >0。', ['遍历所有元素','严格正数条件正确'], '把零当成正数', expected='2')
q('4.13','A','计算某列的最大值', 'int[][] a={{3,8},{5,2},{4,7}};\nint col=1,best=a[0][col];\nfor(int r=1;r<a.length;r++)if(a[r][col]>best)best=a[r][col];\nSystem.out.print(best);',
  'State the output and identify which values are compared.', '比较第二列 8、2、7，输出 8；只变化行索引。', ['固定列正确','最大值初始化来自真实元素'], '把列索引也随循环改变', expected='8')
q('4.13','E','选择总分最高的行', 'static int bestRow(int[][] scores){ /* complete */ }\n// Rectangular, at least one row and one column. Values may be negative; sums fit int. Return the earliest row with the greatest sum.',
  'Complete bestRow. For {{-5,-2},{-3,-1},{-2,-2}} return 1, preserving the earliest tie.', '逐行计算和；首行作为初始最佳，只有严格更大才更新索引，避免相等时覆盖更早行。',
  ['支持负数总和','逐行计算并保存最佳索引','并列时保留最早行'], '最佳和初值为零或用 >= 覆盖并列', kind='write', solution='static int bestRow(int[][] scores){\n int best=0,bestSum=0;\n for(int r=0;r<scores.length;r++){\n  int sum=0;for(int c=0;c<scores[r].length;c++)sum+=scores[r][c];\n  if(r==0||sum>bestSum){best=r;bestSum=sum;}\n }\n return best;\n}', members='{{solution}}', body='System.out.print(bestRow(new int[][]{{-5,-2},{-3,-1},{-2,-2}}));', expected='1', checks='if(bestRow(new int[][]{{0},{0}})!=0||bestRow(new int[][]{{-8}})!=0||bestRow(new int[][]{{1},{9},{2}})!=1)throw new AssertionError();')

q('4.14','B','顺序查找第一处', 'int[] a={7,2,7};\nint index=-1;\nfor(int i=0;i<a.length && index==-1;i++)if(a[i]==7)index=i;\nSystem.out.print(index);', 'State the output. Why does the algorithm not return index 2?', '输出 0。首次匹配后 index 不再为 -1，循环停止。', ['识别首次匹配','解释停止条件'], '总返回最后一次出现的位置', expected='0')
q('4.14','A','顺序查找的最好与最坏', 'An algorithm checks entries from index 0 upward, stopping at the first match. The array has 8 entries.',
  'How many element-to-target comparisons occur when the target is first, last, or absent? Does the array need to be sorted?', '分别为 1、8、8 次；顺序查找不要求有序。这里只计元素与目标值的比较，不计循环边界检查。',
  ['三个比较次数正确','说明无需排序'], '把循环条件也算进指定的元素比较次数', kind='concept')
q('4.14','E','查找最后一次匹配', 'static int lastIndex(int[] a,int target){ /* complete */ }\n// a is non-null and may be empty or unsorted.',
  'Return the last matching index or -1. Use a linear search and explain why the result is correct for duplicates.', '从末尾向前查找，第一次找到就是最大匹配索引；没有匹配则返回 -1。',
  ['从合法末尾索引开始','遇到首个反向匹配即返回','无匹配和空数组返回 -1'], '从前往后首次命中就返回', kind='write', solution='static int lastIndex(int[] a,int target){\n for(int i=a.length-1;i>=0;i--)if(a[i]==target)return i;\n return -1;\n}', members='{{solution}}', body='System.out.print(lastIndex(new int[]{2,7,2},2)+","+lastIndex(new int[0],2));', expected='2,-1', checks='if(lastIndex(new int[]{4},4)!=0||lastIndex(new int[]{1,2},9)!=-1)throw new AssertionError();')

q('4.15','B','选择排序的一轮', 'int[] a={4,1,3,2};\nint min=0;\nfor(int j=1;j<a.length;j++)if(a[j]<a[min])min=j;\nint temp=a[0];a[0]=a[min];a[min]=temp;\nSystem.out.print(java.util.Arrays.toString(a));',
  'State the array after this first selection-sort pass. Which position is now final?', '输出 [1, 4, 3, 2]；最小值放到索引 0，位置已经确定，其余尚未排序。', ['选择全局最小值','仅交换一次并识别已定位置'], '一轮就认为整个数组有序', expected='[1, 4, 3, 2]')
q('4.15','A','插入排序的一步', 'int[] a={2,5,7,3};\nint key=a[3],j=2;\nwhile(j>=0 && a[j]>key){a[j+1]=a[j];j--;}\na[j+1]=key;\nSystem.out.print(java.util.Arrays.toString(a));',
  'State the resulting array and list the values shifted before key is placed.', '先右移 7，再右移 5；最后把 3 放到索引 1，输出 [2, 3, 5, 7]。', ['正确跟踪右移','保存 key 避免被覆盖'], '每一步都交换而误算给定代码', expected='[2, 3, 5, 7]')
q('4.15','E','两种排序的比较次数', 'Selection sort: for each i=0..n-2, compare every later value with the current minimum.\nInsertion sort: for each i=1..n-1, compare the key with preceding values and stop at the first value <= key.\nInput: an already ascending array of 5 distinct integers.',
  'Count element-to-element comparisons for each algorithm on this input. Explain why the count differs and give each algorithm\'s general count on an already sorted array of length n.',
  '选择排序为 4+3+2+1=10，通式 n(n-1)/2；插入排序每轮首次比较即停止，共 4，通式 n-1。这里只计元素之间的比较，n>=1。',
  ['选择排序仍扫描未排序区','插入排序每轮只比较一次','正确给出精确次数与通式'], '认为输入已排序就完全没有比较', kind='concept')

REC='static int sum(int n){if(n==0)return 0;return n+sum(n-1);}'
q('4.16','B','递归的基本情况', REC+'\n// Call: sum(3)', 'Determine the returned value and identify the base case. Do not write a new recursive method.', '返回 6；sum(0)=0 是基本情况，回溯为 1、3、6。', ['识别基本情况','正确回溯求和'], '遇到基本情况就忽略等待中的调用', expected='6', members=REC, body='System.out.print(sum(3));')
q('4.16','A','递归前后的输出', 'static void show(int n){\n if(n==0)return;\n System.out.print(n);show(n-1);System.out.print(n);\n}\n// Call: show(3)',
  'State the exact output and distinguish the descent from the return phase.', '输出 321123。递归下降时打印 3、2、1，回溯时打印 1、2、3。', ['下降输出顺序正确','回溯输出顺序正确'], '认为 return 会跳过所有调用的后半部分', expected='321123', members='static void show(int n){if(n==0)return;System.out.print(n);show(n-1);System.out.print(n);}', body='show(3);')
q('4.16','E','递归调用树与局部参数', 'static int f(int n){\n if(n<=1)return 1;\n return f(n-1)+f(n-2);\n}\n// Call: f(4)',
  'Determine the result and total number of method calls, including the initial call and base cases. Explain why two calls with n=2 have separate local parameters. Do not implement recursion.',
  '结果 5，总调用 9 次。调用次数满足 C(0)=C(1)=1，C(n)=1+C(n-1)+C(n-2)。每次调用有自己的参数和返回位置，重复参数值不表示共享同一次调用。',
  ['正确求得返回值','包含根和叶子计算 9 次','区分独立调用帧'], '把相同参数的重复调用只计一次', expected='5,9', members='static int calls=0;static int f(int n){calls++;if(n<=1)return 1;return f(n-1)+f(n-2);}', body='int result=f(4);System.out.print(result+","+calls);')

BINARY='static int search(int[] a,int target,int low,int high){if(low>high)return -1;int mid=(low+high)/2;if(a[mid]==target)return mid;if(target<a[mid])return search(a,target,low,mid-1);return search(a,target,mid+1,high);}'
q('4.17','B','递归二分查找路径', BINARY+'\n// a={1,3,5,7,9,11,13}; call search(a,11,0,6)',
  'Give the inspected middle indices in order and the returned index. State the required array ordering.', '检查索引 3（7），然后 5（11），返回 5；数组必须按升序排列。', ['两个中点正确','返回索引而非值','说明有序前提'], '在未排序数组中也直接二分', expected='5', members=BINARY, body='System.out.print(search(new int[]{1,3,5,7,9,11,13},11,0,6));')
q('4.17','A','归并时比较两个有序部分', 'Merge sorted halves [2,6,9] and [1,6,8]. Repeatedly take the smaller front value; on a tie, take from the left half first.',
  'Give the merged sequence and identify from which half each 6 is taken. Why is simply concatenating the halves incorrect?', '合并为 [1,2,6,6,8,9]，第一个 6 来自左半，第二个来自右半。直接拼接会把 1 放在 9 后，破坏有序。',
  ['完整合并顺序正确','遵守相等时左边优先','解释合并而非拼接'], '两个部分有序就认为拼接后有序', kind='concept')
q('4.17','E','二分失败边界与归并层次', BINARY+'\n// a={2,4,6,8,10}; call search(a,5,0,4)\n// Separately, merge sort splits [8,3,6,1] into equal halves until singletons.',
  'Give every inspected middle index for the search and its result. Then list the two sorted length-2 halves and final merge result for the merge sort. Do not write recursive code.',
  '二分中点依次为 2、0、1，然后 low=2、high=1，返回 -1。归并的两个长度 2 子数组为 [3,8] 与 [1,6]，最终为 [1,3,6,8]。',
  ['二分区间更新和失败边界正确','两个子数组排序正确','最终合并正确'], '未找到时返回最后一个中点或漏掉空区间终止', expected='-1', members=BINARY, body='System.out.print(search(new int[]{2,4,6,8,10},5,0,4));', checks='if(search(new int[0],5,0,-1)!=-1||search(new int[]{5},5,0,0)!=0)throw new AssertionError();')
