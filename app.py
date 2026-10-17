from flask import Flask, request, jsonify
from flask_cors import CORS
import time, json, secrets, base64, uuid, requests

app = Flask(__name__)
CORS(app)

class TokenGenerator:
    @staticmethod
    def uuid4(): return str(uuid.uuid4())
    @staticmethod
    def csrf_token(length=32):
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return "".join(secrets.choice(alphabet) for _ in range(length))
    @staticmethod
    def device_id(length=43):
        raw = secrets.token_bytes(32)
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")[:length]
    @staticmethod
    def twpid():
        ts = int(time.time() * 1000)
        return f"tw.{ts}.{''.join(secrets.choice('0123456789') for _ in range(17))}"
    @staticmethod
    def fbp():
        ts = int(time.time() * 1000)
        return f"fb.1.{ts}.{''.join(secrets.choice('0123456789') for _ in range(18))}"
    @staticmethod
    def ttp():
        ts = int(time.time() * 1000)
        upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return f"{''.join(secrets.choice(upper) for _ in range(26))}_.tt.1.{ts}"
    @staticmethod
    def ttcsid():
        ts = int(time.time() * 1000)
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return f"{ts}::{''.join(secrets.choice(alphabet) for _ in range(20))}.6.{ts+30}.0::1.-{secrets.randbelow(9000)+1000}.0::{secrets.randbelow(30000)+1000}.3.331.{ts}.::{secrets.randbelow(30000)+1000}.2.1"
    @staticmethod
    def stripe_mid():
        return f"{str(uuid.uuid4())}{''.join(secrets.choice('0123456789') for _ in range(6))}"

class DeepAISession:
    def __init__(self, api_key="tryit-49513026295-390839c60e8cea5ec86b17b7ae319cd6"):
        self.session = requests.Session()
        self.tg = TokenGenerator()
        self.session_uuid = self.tg.uuid4()
        self.sensitivity_request_id = self.tg.uuid4()
        self._setup_headers(api_key)
        self._generate_cookies()
        self.refresh_tokens()

    def _setup_headers(self, api_key):
        self.session.headers.update({
            "host": "api.deepai.org",
            "api-key": api_key,
            "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
            "origin": "https://deepai.org",
            "referer": "https://deepai.org/",
        })

    def _generate_cookies(self):
        now_ms = int(time.time() * 1000)
        self.session.cookies.update({
            "deepai_device_id": self.tg.device_id(),
            "_twpid": self.tg.twpid(),
            "csrftoken": self.tg.csrf_token(),
            "__stripe_mid": self.tg.stripe_mid(),
            "_fbp": self.tg.fbp(),
            "_ttp": self.tg.ttp(),
            "ttcsid": self.tg.ttcsid(),
        })

    def refresh_tokens(self):
        self.session_uuid = self.tg.uuid4()
        self.sensitivity_request_id = self.tg.uuid4()
        self.session.cookies.set("csrftoken", self.tg.csrf_token())

    def send_chat(self, chat_history):
        self.refresh_tokens()
        payload = {
            "chat_style": "chat",
            "language": "ar",
            "web_access_enabled": "true",
            "sandbox_enabled": "false",
            "chatHistory": json.dumps(chat_history, ensure_ascii=False),
            "model": "standard",
            "session_uuid": self.session_uuid,
            "sensitivity_request_id": self.sensitivity_request_id,
            "tool_activity_support": "1",
            "thinking_image_tool_support": "1",
            "hacker_is_stinky": "very_stinky",
            "enabled_tools": json.dumps(["image_generator"], ensure_ascii=False),
        }
        return self.session.post("https://api.deepai.org/hacking_is_a_serious_crime", files={k: (None, v) for k, v in payload.items()}, timeout=60)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    messages = data.get('messages', [])
    chat_history = [{"role": m['role'], "content": m['content']} for m in messages]
    client = DeepAISession()
    try:
        response = client.send_chat(chat_history)
        content = response.text
        try:
            parsed = json.loads(content)
            content = parsed.get("output", content)
        except: pass
        return jsonify({"choices": [{"message": {"content": content.strip()}}]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
