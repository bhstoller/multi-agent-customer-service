from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import json

from .tools import MCP_TOOLS, process_tool_call  # you will create this

app = Flask(__name__)
CORS(app)

def create_sse_message(data):
    return f"data: {json.dumps(data)}\n\n"

@app.route("/mcp", methods=["POST"])
def mcp_endpoint():
    message = request.get_json()

    def generate():
        print(f"📥 Received: {message.get('method')}")
        response = process_mcp_message(message)
        yield create_sse_message(response)

    return Response(generate(), mimetype="text/event-stream")

@app.route("/health", methods=["GET"])
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    app.run(port=5001, debug=True)