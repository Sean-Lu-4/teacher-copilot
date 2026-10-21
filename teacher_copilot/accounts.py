"""Persistent accounts, opaque sessions and optional verified-email recovery."""
from contextlib import contextmanager
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import time
from pathlib import Path


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def password_hash(password, salt):
    return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()


class Accounts:
    def __init__(self, root):
        self.path = Path(root) / 'accounts.sqlite3'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
              id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, salt TEXT NOT NULL,
              password TEXT NOT NULL, recovery TEXT NOT NULL, role TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions (
              token TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS limits (
              key TEXT PRIMARY KEY, count INTEGER NOT NULL, start INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS progress (
              user_id TEXT PRIMARY KEY, data TEXT NOT NULL, revision INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS email_codes (
              id TEXT PRIMARY KEY, user_id TEXT NOT NULL, email TEXT NOT NULL,
              purpose TEXT NOT NULL, code TEXT NOT NULL, expires INTEGER NOT NULL, attempts INTEGER NOT NULL);
            """)
            if 'email' not in {r[1] for r in db.execute('PRAGMA table_info(users)')}:
                db.execute('ALTER TABLE users ADD COLUMN email TEXT')
            db.execute('CREATE UNIQUE INDEX IF NOT EXISTS user_email ON users(email)')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def throttle(self, key, maximum=15):
        now = int(time.time())
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM limits WHERE key=?', (key,)).fetchone()
            if row and now - row['start'] < 900:
                if row['count'] >= maximum:
                    raise ValueError('操作过于频繁，请在 15 分钟后重试。')
                db.execute('UPDATE limits SET count=count+1 WHERE key=?', (key,))
            else:
                db.execute('INSERT OR REPLACE INTO limits VALUES (?,1,?)', (key, now))
            db.execute('DELETE FROM limits WHERE start<?', (now - 86400,))

    def user(self, token):
        with self.connect() as db:
            row = db.execute('SELECT u.id,u.username,u.role,u.email FROM users u JOIN sessions s ON u.id=s.user_id WHERE s.token=? AND s.expires>?',
                             (digest(token), int(time.time()))).fetchone()
        return dict(row) if row else None

    def session(self, uid):
        token = secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute('DELETE FROM sessions WHERE expires<?', (int(time.time()),))
            db.execute('INSERT INTO sessions VALUES (?,?,?)', (digest(token), uid, int(time.time()) + 30*86400))
        return token

    def authenticate(self, action, payload, ip):
        self.throttle('ip:' + ip, 30)
        username = str(payload.get('username', '')).strip().lower()
        self.throttle('name:' + digest(username))
        password = str(payload.get('password', ''))
        if not re.fullmatch(r'[a-z0-9_]{3,32}', username):
            raise ValueError('用户名使用 3–32 位字母、数字或下划线。')
        if not 10 <= len(password) <= 128:
            raise ValueError('密码长度须为 10–128 位。')
        verified_uid = None
        if action == 'reset' and payload.get('challenge'):
            verified_uid = self.consume_code(str(payload['challenge']),str(payload.get('email_code','')),'reset')
        with self.connect() as db:
            row = db.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
            if action == 'register':
                if row:
                    raise ValueError('这个用户名已被使用，请换一个。')
                role = payload.get('role', 'student')
                if role not in ('student', 'teacher'):
                    raise ValueError('请选择学生或教师。')
                uid, salt, recovery = secrets.token_hex(16), secrets.token_hex(16), secrets.token_urlsafe(24)
                try:
                    db.execute('INSERT INTO users (id,username,salt,password,recovery,role) VALUES (?,?,?,?,?,?)', (uid, username, salt, password_hash(password, salt), digest(recovery), role))
                except sqlite3.IntegrityError:
                    raise ValueError('这个用户名已被使用，请换一个。')
            elif action == 'reset':
                if not row or not (verified_uid == row['id'] if verified_uid else hmac.compare_digest(row['recovery'], digest(str(payload.get('recovery', ''))))):
                    raise ValueError('用户名或恢复码不正确。')
                uid, salt, recovery = row['id'], secrets.token_hex(16), secrets.token_urlsafe(24)
                db.execute('UPDATE users SET salt=?,password=?,recovery=? WHERE id=?', (salt, password_hash(password, salt), digest(recovery), uid))
                db.execute('DELETE FROM sessions WHERE user_id=?', (uid,))
            elif action == 'login':
                salt = row['salt'] if row else '00' * 16
                valid = hmac.compare_digest(password_hash(password, salt), row['password'] if row else '00' * 64)
                if not row or not valid:
                    raise ValueError('用户名或密码不正确。')
                uid, recovery = row['id'], None
            else:
                raise ValueError('不支持的操作。')
        return self.session(uid), recovery

    def logout(self, token):
        with self.connect() as db:
            db.execute('DELETE FROM sessions WHERE token=?', (digest(token),))

    def progress(self, uid, payload=None):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM progress WHERE user_id=?', (uid,)).fetchone()
            revision = row['revision'] if row else 0
            data = json.loads(row['data']) if row else {}
            if payload is not None:
                if payload.get('revision') != revision:
                    raise ValueError('其他窗口已更新学习记录。请保留当前草稿，刷新后继续。')
                data = payload.get('data')
                if not isinstance(data, dict) or len(data) > 10000:
                    raise ValueError('学习记录格式无效。')
                serialized = json.dumps(data, ensure_ascii=False)
                if len(serialized.encode()) > 2000000:
                    raise ValueError('学习记录过大，请联系网站管理员。')
                revision += 1
                db.execute('INSERT OR REPLACE INTO progress VALUES (?,?,?)', (uid, serialized, revision))
        return {'data': data, 'revision': revision}

    def request_code(self, purpose, payload, ip, uid=None):
        from . import account_mail
        if not account_mail.available():
            raise ValueError('邮箱服务尚未启用，请使用账号恢复码。')
        self.throttle('mail-ip:'+ip, 8)
        key=secrets.token_urlsafe(24)
        with self.connect() as db:
            if purpose == 'bind':
                row=db.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
                if not row or not hmac.compare_digest(password_hash(str(payload.get('password','')),row['salt']),row['password']):
                    raise ValueError('请先确认当前密码。')
                address=str(payload.get('email','')).strip().lower()
                if len(address)>254 or not re.fullmatch(r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9.-]+\.[a-z]{2,}",address):
                    raise ValueError('请输入有效的邮箱地址。')
                if db.execute('SELECT 1 FROM users WHERE email=? AND id<>?',(address,uid)).fetchone():
                    raise ValueError('此邮箱无法绑定，请使用其他邮箱。')
            else:
                row=db.execute('SELECT * FROM users WHERE username=?',(str(payload.get('username','')).strip().lower(),)).fetchone()
                if not row or not row['email']:return {'challenge':key,'message':'如果账号已绑定邮箱，验证码将发送至该邮箱。'}
                uid=row['id'];address=row['email']
        self.throttle('mail-address:'+digest(address), 3)
        code=f'{secrets.randbelow(1000000):06d}'
        with self.connect() as db:
            db.execute('DELETE FROM email_codes WHERE expires<?',(int(time.time()),))
            db.execute('DELETE FROM email_codes WHERE user_id=? AND purpose=?',(uid,purpose))
            db.execute('INSERT INTO email_codes VALUES (?,?,?,?,?,?,0)',(key,uid,address,purpose,digest(code),int(time.time())+600))
        account_mail.send_code(address,code)
        return {'challenge':key,'message':'如果账号已绑定邮箱，验证码将发送至该邮箱。' if purpose=='reset' else '验证码已发送，请检查邮箱。'}

    def consume_code(self, challenge, code, purpose, uid=None):
        valid=False
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM email_codes WHERE id=?',(challenge,)).fetchone()
            if row and row['purpose']==purpose and row['expires']>time.time() and row['attempts']<5 and (uid is None or uid==row['user_id']):
                valid=hmac.compare_digest(row['code'],digest(code))
                if valid:
                    db.execute('DELETE FROM email_codes WHERE id=?',(challenge,))
                    if purpose=='bind':
                        try:db.execute('UPDATE users SET email=? WHERE id=?',(row['email'],uid))
                        except sqlite3.IntegrityError:raise ValueError('此邮箱无法绑定，请使用其他邮箱。') from None
                else:db.execute('UPDATE email_codes SET attempts=attempts+1 WHERE id=?',(challenge,))
        if not valid:raise ValueError('验证码无效或已过期，请重新获取。')
        return row['user_id']
