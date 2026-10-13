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
