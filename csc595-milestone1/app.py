import html
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
from core import answer

PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>CMDB Change-Review Assistant</title>
<style>
body { font-family: Segoe UI, Arial, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 16px; }
textarea { width: 100%; height: 80px; font-size: 16px; }
button { font-size: 16px; padding: 8px 16px; margin-top: 8px; }
.reply { white-space: pre-wrap; background: #f4f6f8; padding: 16px; border-radius: 6px; margin-top: 16px; }
</style></head>
<body>
<h1>CMDB Change-Review Assistant</h1>
<form method="post" action="/">
<textarea name="question" placeholder="Ask about a CMDB record or open change">__QUESTION__</textarea><br>
<button type="submit">Ask</button>
</form>
__REPLY__
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, body):
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send(PAGE.replace("__QUESTION__", "").replace("__REPLY__", ""))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        form = parse_qs(self.rfile.read(length).decode("utf-8"))
        question = form.get("question", [""])[0].strip()
        if not question:
            reply = "Please type a question."
        elif len(question) > 2000:
            reply = "That question is too long. Please keep it under 2,000 characters."
        else:
            try:
                result = answer(question)
                if isinstance(result, dict):
                    reply = result.get("reply") or result.get("text") or str(result)
                else:
                    reply = str(result)
            except Exception as e:
                reply = f"Something went wrong: {e}"
        page = PAGE.replace("__QUESTION__", html.escape(question))
        page = page.replace("__REPLY__", f'<div class="reply">{html.escape(reply)}</div>')
        self._send(page)


if __name__ == "__main__":
    print("Open http://127.0.0.1:8000 in your browser. Press Ctrl+C to stop.")
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()