"""Short and extended tasks for realistic 10/20-minute local homework."""
VERSION='homework-20260930-v1'
QUESTIONS=[]
FIXTURES=[]


def add(id,topic,level,minutes,title,code,task,answer,points,expected):
    QUESTIONS.append(dict(id=id,ced_topics=[topic],objectives=['ced_'+topic.replace('.','_')],
        level=level,minutes=minutes,title=title,code=code,task=task,answer=answer,
        origin='原创作业题',reasoning=points,errors=['忽略边界或使用更新前的变量值。'],
        rubric='；'.join(p+'（1 分）' for p in points)+'。',
        intervention='先逐轮记录状态，再用边界输入检查结论。',question_kind='trace',
        prerequisites='已学习本题涉及的比较、赋值与循环语法。'))
    FIXTURES.append(dict(id=id,members='',body=code,solution='',checks='',expected=expected,files={}))

add('HW_L_B1','2.7',2,5,'循环结束时的余额',
    'int balance=2,days=0;\nwhile(balance<15){balance+=4;days++;}\nSystem.out.print(balance+","+days);',
    'State the output and list the balance after each iteration. If the target were 14 instead of 15, how many days would be needed?',
    '原输出 18,4，余额依次为 6、10、14、18；目标为 14 时需要 3 天。',
    ['四次更新正确','停止时余额可以超过目标','目标 14 时为三天'],'18,4')
add('HW_L_B2','2.8',2,6,'循环步长与累积表',
    'int total=0;\nfor(int i=2;i<=10;i+=2){total+=i;}\nSystem.out.print(total);',
    'List every i and the running total. State the output. Then give the total if <=10 is changed to <10.',
    'i 为 2、4、6、8、10；累计 2、6、12、20、30；原输出 30，改成 <10 后为 20。',
    ['循环控制值正确','累计值正确','解释是否包含终点'],'30')
add('HW_L_A1','2.9',3,5,'计数与求和的区别',
    'int count=0,sum=0;\nfor(int n=1;n<=10;n++){if(n%3==1){count++;sum+=n;}}\nSystem.out.print(count+","+sum);',
    'State the output and identify all selected values. Explain why count and sum need different updates.',
    '选中 1、4、7、10，输出 4,22；count 增加次数，sum 累加数值。',
    ['筛选集合正确','计数和总和正确','解释两个更新含义'],'4,22')
add('HW_L_E1','2.8',4,2,'判断循环的等价边界',
    'int count=0;\nfor(int i=0;i<7;i+=2)count++;\nSystem.out.print(count);',
    'State the output. Is replacing i<7 with i<=6 equivalent for every iteration of this loop? Justify briefly.',
    '输出 4；本循环 i 为 0、2、4、6，两个条件均允许相同四个值，等价。',
    ['四次执行正确','按实际整数控制值解释等价'],'4')
add('HW_L_E2','2.7',4,4,'修复遗漏最后一个数位',
    'int n=305,count=0;\nwhile(n>=10){count++;n/=10;}\nSystem.out.print(count);',
    'The goal is the number of decimal digits of a nonnegative integer. State the output, explain the defect, and describe a repair that also handles zero.',
    '输出 2；循环未计入最后一位。可对零直接返回 1，对其他数以 while(n>0) 每次计数再除以 10。',
    ['识别遗漏最后一位','循环条件修复正确','单独处理零'],'2')

add('HW_A_B1','4.3',2,5,'根据数组下标执行赋值',
    'int[] a={3,0,2,1};\na[a[1]]=7;\na[2]=a[0]+a[3];\nSystem.out.print(a[0]+","+a[1]+","+a[2]+","+a[3]);',
    'State the final array. Show the index used in the first assignment and the values used in the second.',
    '最终为 [7,0,8,1]；第一次 a[1]=0，所以更新 a[0]；第二次使用更新后的 7 加 1。',
    ['求出间接索引零','正确更新 a[0]','使用新值计算 a[2]'],'7,0,8,1')
add('HW_A_B2','4.4',2,6,'两种遍历是否同样修改元素',
    'int[] a={1,2,3};\nfor(int value:a)value+=5;\nfor(int i=0;i<a.length;i++)a[i]+=i;\nSystem.out.print(a[0]+","+a[1]+","+a[2]);',
    'State the array after each loop and explain why their effects differ. Give the sum of the final elements.',
    '第一轮后仍为 [1,2,3]，第二轮后为 [1,3,5]；基本类型循环变量是副本，索引赋值才修改原元素；最终总和 9。',
    ['区分副本与原元素','三个最终值正确','最终和为九'],'1,3,5')
add('HW_A_A1','4.5',3,5,'统计严格局部峰值',
    'int[] a={1,4,2,5,3};\nint peaks=0;\nfor(int i=1;i<a.length-1;i++)\n if(a[i]>a[i-1] && a[i]>a[i+1])peaks++;\nSystem.out.print(peaks);',
    'State the output and the peak indices. Explain the loop bounds and whether an equal neighbor qualifies.',
    '输出 2，峰值索引 1、3；两端没有两个邻居不参加比较；相等不满足严格大于。',
    ['两个峰值索引正确','解释两端排除','相等不算严格峰值'],'2')
add('HW_A_E1','4.4',4,2,'反向遍历的首个访问',
    'int[] a={2,5,8};\nint result=0;\nfor(int i=a.length-1;i>=0;i--)result=result*10+a[i];\nSystem.out.print(result);',
    'State the output. Explain why initializing i to a.length would fail before the first update to result.',
    '输出 852；a.length 为 3，但最大合法索引为 2，使用 a[3] 会越界。',
    ['按逆序累积得到 852','指出首个索引越界'],'852')
add('HW_A_E2','4.5',4,4,'先修改再比较造成的信息损失',
    'int[] a={1,2,3,4};\nfor(int i=1;i<a.length;i++)a[i]=a[i-1];\nSystem.out.print(a[0]+","+a[1]+","+a[2]+","+a[3]);',
    'State the output. The intended task was shifting every original element one position right, leaving index 0 unchanged. Describe a corrected loop and its resulting array.',
    '原输出 1,1,1,1，因为前面的值被连续覆盖。应从 i=a.length-1 向下到 1 赋值 a[i]=a[i-1]；结果为 [1,1,2,3]。',
    ['跟踪连锁覆盖','改成逆向循环','修正结果正确'],'1,1,1,1')
add('HW_C_B1','2.3',2,2,'先匹配的分支',
    'int score=80;\nif(score>=80)System.out.print("A");\nelse if(score>=60)System.out.print("B");\nelse System.out.print("C");',
    'State the output and explain whether the second condition is evaluated.',
    '输出 A。首个条件为真，后面的 else if 条件不再求值。',
    ['边界八十包含在首分支','后续条件被跳过'],'A')

add('HW_L_B3','2.9',2,4,'筛选与更新顺序',
    'int total=0;\nfor(int i=1;i<=5;i++){if(i%2!=0)total+=i;}\nSystem.out.print(total);',
    'List the selected values and state the output. What changes if the condition becomes i%2==0?',
    '原来选中 1、3、5，输出 9；改后选中 2、4，总和为 6。',
    ['奇数筛选正确','总和正确','偶数条件下结果正确'],'9')
add('HW_A_B3','4.5',2,4,'统计与边界值',
    'int[] a={0,5,6,5};\nint count=0;\nfor(int x:a)if(x>=5)count++;\nSystem.out.print(count);',
    'State the output and identify the matching elements. What is the count if >=5 becomes >5?',
    '输出 3，匹配两个 5 和一个 6；改为 >5 时只有 6，计数 1。',
    ['包含两个边界值','按元素个数计数','严格比较结果为一'],'3')
add('HW_C_B2','2.2',2,4,'边界比较的两种结果',
    'int age=16;\nSystem.out.print((age>16)+","+(age>=16));',
    'State the output. Give both results again for ages 15 and 17, and identify the only tested age that distinguishes the comparisons.',
    '16 时 false,true；15 时 false,false；17 时 true,true；只有 16 区分两条件。',
    ['等于边界时结果正确','两侧测试结果正确','指出区分输入'],'false,true')
