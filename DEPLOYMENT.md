# Teacher Copilot 测试部署

当前项目默认只允许本机访问。要让其他老师试用，需要把网页和 Python 后端一起部署；GitHub Pages 不能承载这个后端。

## 推荐的第一次部署

使用任何支持 Docker 的小型云服务。部署时设置以下环境变量：

```text
OPENAI_API_KEY=你的服务端密钥
TEACHER_COPILOT_ENABLE_AI=1
OPENAI_MODEL=gpt-6-luna
TEACHER_COPILOT_ALLOWED_HOSTS=你的域名
TEACHER_COPILOT_ALLOWED_ORIGINS=https://你的域名
```

平台通常会注入 `PORT`；容器会自动监听该端口。若平台不提供端口变量，使用默认的 8765。

## 本机模拟公网启动

在 PowerShell 中：

```powershell
$env:TEACHER_COPILOT_HOST='0.0.0.0'
$env:TEACHER_COPILOT_ALLOWED_HOSTS='127.0.0.1:8765'
$env:TEACHER_COPILOT_ALLOWED_ORIGINS='http://127.0.0.1:8765'
py -m teacher_copilot.review_app --host 0.0.0.0 --port 8765
```

公网环境必须使用 HTTPS 反向代理，并将 `TEACHER_COPILOT_ALLOWED_HOSTS` 和 `TEACHER_COPILOT_ALLOWED_ORIGINS` 换成真实域名。不要把 `OPENAI_API_KEY` 写进前端、仓库或 Dockerfile。

## 试用阶段限制

- 当前是单机文件存储，适合小范围试用，不适合多人同时编辑同一份练习。
- API Key 在后端环境变量中保存；部署平台的日志和备份也要限制访问。
- 正式上线前还需要账号登录、每位教师的数据隔离、数据库、备份和错误监控。


## 免费补题配置

在 Render 的 Environment 中设置以下值，保存并重新部署：

- `OPENROUTER_API_KEY`：在 Render 中填写自己的密钥，勿提交到仓库。
- `OPENROUTER_MODEL`：`openrouter/free`。
- `TEACHER_COPILOT_ENABLE_AI`：`1`。
- `TEACHER_COPILOT_PUBLIC_DEMO` 保持 `1`。公开试用只允许免费模型，不会回退到付费 OpenAI。

生成页面会自动开放“题库优先，不足时用 AI 补题”。快速练习按剩余时长补题；正式试卷按剩余题数、时长和分值补题，达到题数后不会为填满时间追加题目。结构检查会检查选项、答案键、参考实现和评分点合计，不代表内容已经通过教师审核。免费服务限流或返回不合格内容时，保留已组好的题库练习并显示原因。

验收：`python -m unittest test_generation_flow test_ai_questions test_pdf_bank_regression -q`。


### 补题内容检查

继续使用环境变量配置的免费模型，不回退到付费模型。先使用 PDF 题库，缺题时才生成。每次补题先进行结构、语言、Java 语法和评分检查，再进行单独的模型内容复核；失败最多修正一次。服务错误直接停止，已有 PDF 题保留。每次生成操作最多包含四次模型调用，输出额度预留覆盖生成、复核和一次修正，未知用量保留预留额度。模型复核不能代替教师审核，不会将题目标记为人工审核通过。


2026-10-16 本地补题修复：MCQ 同样执行 Java 语法检查（明确考查编译错误且答案指出错误的题仍需内容复核）；FRQ 拒绝为已给出的方法签名单独计分。合法 JSON 换行转义可恢复，字母 n、截断代码等不猜测修补，返回模型修正。练习补题允许保留短于缺口的合格批次，第二次生成按剩余时间与缺失考点补充，并排除已接受题目；最多两次生成、每次一次复核。后续失败仍保留已验收批次和 PDF 题，显示真实剩余时长。正式试卷和换题继续执行原有严格时长、题量、分值规则。以上为本地改动，尚未部署。

2026-10-16 本地输出修复：生成接口使用 code_lines/reference_solution_lines 逐行传输 Java，程序以真实换行拼接；不猜测替换代码中的字母 n。MCQ 英文计分由答案键和分值生成；FRQ 每个评分点要求 criterion_en，与中文点数一起组成英文评分说明，仍经独立内容审核。英文答案解释不能为空，不能用自动附加的评分说明冒充解释。复核请求将 FRQ 学生骨架标为 student_skeleton，与 reference_solution 明确区分，避免把待完成代码当成答案。
