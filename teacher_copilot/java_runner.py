"""Bounded remote compilation/execution. Never run student code locally."""
import base64
import json
import os
import re
import time
from urllib.parse import urlparse
import requests


class RunnerUnavailable(Exception):
    pass


def endpoint():
    # Public trial explicitly uses the free demo endpoint; an empty override disables it.
    default = 'https://ce.judge0.com' if os.getenv('TEACHER_COPILOT_PUBLIC_DEMO') == '1' else ''
    return os.getenv('CSA_JAVA_RUNNER_URL', default).strip().rstrip('/')


def configured():
    return bool(endpoint())


def _request(base, path, payload=None):
    headers = {'Content-Type': 'application/json'}
    token = os.getenv('CSA_JAVA_RUNNER_KEY', '')
    if token:
        headers['X-Auth-Token'] = token
    rapid = os.getenv('CSA_JAVA_RAPIDAPI_KEY', '')
    if rapid:
        headers.update({'X-RapidAPI-Key': rapid, 'X-RapidAPI-Host': urlparse(base).hostname})
    try:
        with requests.request('POST' if payload is not None else 'GET', base + path,
                              json=payload, headers=headers, timeout=(5,10),
                              allow_redirects=False, stream=True) as response:
            if not 200 <= response.status_code < 300:
                raise RunnerUnavailable('代码运行服务暂时不可用，请稍后重试。')
            data = b''
            for chunk in response.iter_content(8192):
                data += chunk
                if len(data) > 131072:
                    raise RunnerUnavailable('检查结果过大，请减少输出。')
        return json.loads(data)
    except (requests.RequestException, TimeoutError, ValueError):
        raise RunnerUnavailable('代码运行服务暂时不可用，请稍后重试。') from None


def run_java(source):
    base = endpoint()
    if not base:
        raise RunnerUnavailable('Java 运行服务尚未配置。')
    parsed = urlparse(base)
    if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise RunnerUnavailable('Java 运行服务配置无效。')
    payload = dict(source_code=base64.b64encode(source.encode()).decode(),
                   language_id=int(os.getenv('CSA_JAVA_LANGUAGE_ID', '91')),
                   cpu_time_limit=2, wall_time_limit=5, memory_limit=262144,
                   max_file_size=64, enable_network=False, number_of_runs=1)
    data = _request(base, '/submissions?base64_encoded=true&wait=false', payload)
    token = data.get('token', '')
    if not re.fullmatch(r'[a-f0-9-]{36}', token):
        raise RunnerUnavailable('运行服务未接受本次检查。')
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        data = _request(base, '/submissions/' + token + '?base64_encoded=true')
        status = data.get('status', {}).get('id')
        if status not in (1, 2):
            if status not in range(3, 13):
                raise RunnerUnavailable('运行服务返回了无效结果。')
            for key in ('stdout', 'stderr', 'compile_output'):
                try:
                    data[key] = base64.b64decode(data.get(key) or '', validate=True).decode('utf-8', errors='replace')[:16000]
                except ValueError:
                    raise RunnerUnavailable('运行结果无法读取。') from None
            return data
        time.sleep(.8)
    raise RunnerUnavailable('检查排队超时，请稍后重试。')
