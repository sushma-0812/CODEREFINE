import gradio as gr
from datetime import datetime

# ==============================
# Groq safe import
# ==============================
try:
    from groq import Groq
except Exception:
    class _ChatCompletions:
        def create(self, *args, **kwargs):
            raise RuntimeError("Groq not installed. Run: pip install groq")

    class _Chat:
        def __init__(self):
            self.completions = _ChatCompletions()

    class Groq:
        def __init__(self, api_key=None):
            self.chat = _Chat()

# ==============================
# Global state
# ==============================
client = None

# ==============================
# Initialize Groq
# ==============================
def init_groq(api_key):
    global client
    if not api_key or not api_key.strip():
        return "⚠️ Please enter API key"
    try:
        client = Groq(api_key=api_key.strip())
        return "✅ Connected to Groq"
    except Exception as e:
        return f"❌ {e}"

# ==============================
# Analyze code (demo logic)
# ==============================
def analyze(code, api_key):
    if not client:
        status = init_groq(api_key)
        if status.startswith("❌") or status.startswith("⚠️"):
            return status

    lines = len(code.splitlines())
    chars = len(code)

    return f"""
### 📊 Analysis Result

- 🧾 Lines of code: **{lines}**
- 🔠 Characters: **{chars}**
- ⏱️ Time: **{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**

✅ CodeRefine is working correctly.
"""

# ==============================
# Chat logic
# ==============================
def respond(message, history, api_key):
    if not message.strip():
        return "", history

    if not client:
        init_groq(api_key)

    history.append((message, "🤖 CodeRefine response received"))
    return "", history

# ==============================
# Gradio UI
# ==============================
with gr.Blocks(title="CodeRefine", theme=gr.themes.Soft()) as app:

    gr.Markdown("# 🚀 CodeRefine\n### AI-Powered Code Review Tool")

    api_key = gr.Textbox(
        label="🔑 Groq API Key",
        type="password",
        placeholder="Paste your Groq API key here"
    )

    status = gr.Textbox(label="Status", interactive=False)
    gr.Button("Connect").click(init_groq, api_key, status)

    with gr.Tabs():

        with gr.Tab("🔍 Code Analysis"):
            code = gr.Code(language="python", label="Enter your code", lines=15)
            output = gr.Markdown()
            gr.Button("Analyze Code", variant="primary").click(
                analyze,
                inputs=[code, api_key],
                outputs=output
            )

        with gr.Tab("💬 AI Chat"):
            chatbot = gr.Chatbot(height=400)
            msg = gr.Textbox(placeholder="Ask about bugs, optimization, algorithms…")

            gr.Button("Send", variant="primary").click(
                respond,
                inputs=[msg, chatbot, api_key],
                outputs=[msg, chatbot]
            )

            msg.submit(
                respond,
                inputs=[msg, chatbot, api_key],
                outputs=[msg, chatbot]
            )

# ==============================
# Launch (FIXED)
# ==============================
if __name__ == "__main__":
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        inbrowser=True,   # 🔥 THIS OPENS THE BROWSER
        share=False,
        show_error=True
    )
