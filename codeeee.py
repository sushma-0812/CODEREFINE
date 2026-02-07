"""
CodeRefine: Complete AI Code Review & Execution Platform
Features: Signup/Signin, Code Execution, Error Detection, Complexity Analysis
UPDATED: Fixed Quick Results + Professional CSS
"""

import gradio as gr
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("Warning: Groq SDK not installed. Install with: pip install groq")

import json
import os
from datetime import datetime
import subprocess
import sys
import tempfile
import re

# User database
USERS_FILE = "coderefine_users.json"
users_db = {}

if os.path.exists(USERS_FILE):
    try:
        with open(USERS_FILE, 'r') as f:
            users_db = json.load(f)
    except:
        users_db = {}

# Initialize
client = None
current_user = None
analysis_history = []

def save_users():
    """Save users to file"""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users_db, f, indent=2)
    except Exception as e:
        print(f"Error saving users: {e}")

def signup(username, password, confirm_password):
    """User signup"""
    if not username or not password:
        return "❌ Username and password are required!", None
    
    if password != confirm_password:
        return "❌ Passwords do not match!", None
    
    if len(password) < 6:
        return "❌ Password must be at least 6 characters!", None
    
    if username in users_db:
        return "❌ Username already exists! Please login.", None
    
    users_db[username] = {
        "password": password,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "analyses_count": 0
    }
    save_users()
    
    return f"✅ Account created successfully! Welcome {username}!", gr.update(visible=True)

def login(username, password):
    """User login"""
    global current_user
    
    if not username or not password:
        return "❌ Username and password are required!", None, None
    
    if username not in users_db:
        return "❌ User not found! Please signup first.", None, None
    
    if users_db[username]["password"] != password:
        return "❌ Incorrect password!", None, None
    
    current_user = username
    return f"✅ Welcome back, {username}!", gr.update(visible=True), gr.update(visible=False)

def logout():
    """User logout"""
    global current_user
    current_user = None
    return gr.update(visible=False), gr.update(visible=True)

def initialize_groq(api_key):
    """Initialize Groq client"""
    global client
    
    if not GROQ_AVAILABLE:
        return "❌ Error: Groq SDK not installed. Run: pip install groq"
    
    try:
        if not api_key or not api_key.strip():
            return "⚠️ Please enter a valid API key"
        
        client = Groq(api_key=api_key.strip())
        return "✅ API Key configured successfully!"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def run_code(code, language):
    """Execute code and return output"""
    try:
        if not code.strip():
            return "⚠️ No code to run!", ""
        
        if language == "Python":
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                output = result.stdout if result.stdout else ""
                error = result.stderr if result.stderr else ""
                
                if result.returncode == 0:
                    return f"✅ Execution Successful\n\n{output}", output
                else:
                    return f"❌ Execution Failed\n\n{error}", error
            finally:
                os.unlink(temp_file)
        
        elif language == "JavaScript":
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                result = subprocess.run(
                    ['node', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                output = result.stdout if result.stdout else ""
                error = result.stderr if result.stderr else ""
                
                if result.returncode == 0:
                    return f"✅ Execution Successful\n\n{output}", output
                else:
                    return f"❌ Execution Failed\n\n{error}", error
            except FileNotFoundError:
                return "❌ Node.js not installed! Only Python execution is available.", ""
            finally:
                os.unlink(temp_file)
        
        else:
            return f"⚠️ Code execution for {language} is not supported yet. Only Python and JavaScript are supported.", ""
    
    except subprocess.TimeoutExpired:
        return "❌ Execution timeout! Code took too long to run.", ""
    except Exception as e:
        return f"❌ Execution error: {str(e)}", ""

def analyze_code_short(code, language, api_key):
    """Quick analysis with error detection and corrected code"""
    global client, current_user
    
    if not current_user:
        return "⚠️ Please login first!", "⚠️ Login Required", "", "", "⚠️ Login Required"
    
    try:
        if not client and api_key:
            init_result = initialize_groq(api_key)
            if "❌" in init_result or "⚠️" in init_result:
                return init_result, "⚠️ API Key Required", "", "", "⚠️ Configure API Key"
        
        if not client:
            return "⚠️ Please set your Groq API key first!", "⚠️ API Key Required", "", "", "⚠️ Configure API Key"
        
        if not code.strip():
            return "⚠️ Please enter code to analyze!", "⚠️ No Code", "", "", "⚠️ Code Required"
        
        system_prompt = f"""You are CodeRefine, an expert code analyzer.
Analyze {language} code and provide a SHORT, CONCISE response with:
1. ERROR STATUS: "NO ERRORS" or "ERRORS FOUND"
2. If errors found, provide CORRECTED CODE
3. TIME COMPLEXITY (Big O)
4. SPACE COMPLEXITY (Big O)
5. Brief explanation (max 2 sentences)

Be direct and concise."""

        user_prompt = f"""Analyze this {language} code:

```{language.lower()}
{code}
```

Provide response in this EXACT format:

**ERROR STATUS:** [NO ERRORS / ERRORS FOUND]

**ISSUES:** [List issues briefly, or "None"]

**CORRECTED CODE:**
```{language.lower()}
[corrected code or "No corrections needed"]
```

**TIME COMPLEXITY:** O(?)
**SPACE COMPLEXITY:** O(?)

**EXPLANATION:** [1-2 sentences only]"""

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=1500,
        )
        
        analysis = chat_completion.choices[0].message.content
        
        # Parse error status
        if "NO ERRORS" in analysis.upper() and "ERRORS FOUND" not in analysis.upper():
            error_status = "✅ NO ERRORS DETECTED"
        else:
            error_status = "❌ ERRORS FOUND"
        
        # Extract corrected code
        corrected_code = ""
        code_match = re.search(r'```[\w]*\n(.*?)\n```', analysis, re.DOTALL)
        if code_match:
            corrected_code = code_match.group(1).strip()
            if "no correction" in corrected_code.lower():
                corrected_code = "No corrections needed - code is clean!"
        else:
            corrected_code = "No corrections needed"
        
        # Extract complexities
        time_complexity = "Not analyzed"
        space_complexity = "Not analyzed"
        
        time_match = re.search(r'TIME COMPLEXITY[:\s]+O\(([^)]+)\)', analysis, re.IGNORECASE)
        if time_match:
            time_complexity = f"O({time_match.group(1).strip()})"
        
        space_match = re.search(r'SPACE COMPLEXITY[:\s]+O\(([^)]+)\)', analysis, re.IGNORECASE)
        if space_match:
            space_complexity = f"O({space_match.group(1).strip()})"
        
        complexity_display = f"⏱️ Time: {time_complexity}  |  💾 Space: {space_complexity}"
        
        # Update user stats
        if current_user in users_db:
            users_db[current_user]["analyses_count"] = users_db[current_user].get("analyses_count", 0) + 1
            save_users()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_display = f"✅ Completed at {timestamp}"
        
        return analysis, error_status, corrected_code, complexity_display, status_display
        
    except Exception as e:
        return f"❌ Error: {str(e)}", "❌ ANALYSIS FAILED", "", "", f"❌ Failed: {str(e)}"

def run_and_analyze(code, language, api_key):
    """Run code and analyze it"""
    analysis, error_status, corrected, complexity, status = analyze_code_short(code, language, api_key)
    run_output, _ = run_code(code, language)
    
    return analysis, error_status, corrected, complexity, status, run_output

# Professional CSS
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

* {
    font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.gradio-container {
    max-width: 1600px !important;
    margin: 0 auto !important;
}

/* Header Styling */
.main-header {
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%);
    padding: 50px 30px;
    border-radius: 20px;
    text-align: center;
    color: white;
    margin-bottom: 30px;
    box-shadow: 0 20px 60px rgba(30, 60, 114, 0.3);
    position: relative;
    overflow: hidden;
}

.main-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%);
    animation: shine 3s infinite;
}

@keyframes shine {
    0%, 100% { transform: translateX(-100%); }
    50% { transform: translateX(100%); }
}

.main-header h1 {
    font-size: 3.5em;
    font-weight: 700;
    margin: 0 0 15px 0;
    text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
    letter-spacing: -1px;
}

.main-header h3 {
    font-size: 1.4em;
    font-weight: 400;
    margin: 0 0 10px 0;
    opacity: 0.95;
}

.main-header p {
    font-size: 1.1em;
    opacity: 0.9;
    margin: 0;
}

/* Auth Container */
.auth-box {
    background: white;
    border-radius: 20px;
    padding: 40px;
    box-shadow: 0 15px 50px rgba(0,0,0,0.1);
    max-width: 500px;
    margin: 50px auto;
}

/* Quick Results Cards */
.results-card {
    background: linear-gradient(135deg, #f6f8fb 0%, #e9ecef 100%);
    border-radius: 15px;
    padding: 20px;
    margin: 10px 0;
    border-left: 5px solid #1e3c72;
    box-shadow: 0 5px 15px rgba(0,0,0,0.08);
    transition: all 0.3s ease;
}

.results-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.12);
}

.status-success {
    background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
    border-left-color: #28a745;
    color: #155724;
}

.status-error {
    background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
    border-left-color: #dc3545;
    color: #721c24;
}

.status-warning {
    background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
    border-left-color: #ffc107;
    color: #856404;
}

/* Buttons */
.gr-button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    padding: 12px 24px !important;
    transition: all 0.3s ease !important;
    border: none !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-size: 0.9em !important;
}

.gr-button-primary {
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%) !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(30, 60, 114, 0.4) !important;
}

.gr-button-primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(30, 60, 114, 0.5) !important;
}

.gr-button-secondary {
    background: linear-gradient(135deg, #6c757d 0%, #495057 100%) !important;
    color: white !important;
}

/* Input Fields */
.gr-input, .gr-textbox, .gr-dropdown {
    border-radius: 10px !important;
    border: 2px solid #e0e6ed !important;
    padding: 12px !important;
    transition: all 0.3s ease !important;
}

.gr-input:focus, .gr-textbox:focus, .gr-dropdown:focus {
    border-color: #1e3c72 !important;
    box-shadow: 0 0 0 3px rgba(30, 60, 114, 0.1) !important;
}

/* Code Editor */
.gr-code {
    border-radius: 12px !important;
    border: 2px solid #e0e6ed !important;
    overflow: hidden;
    box-shadow: 0 5px 20px rgba(0,0,0,0.08) !important;
}

/* Tabs */
.gr-tab {
    border-radius: 10px 10px 0 0 !important;
    font-weight: 600 !important;
    padding: 12px 24px !important;
    transition: all 0.3s ease !important;
}

.gr-tab-selected {
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%) !important;
    color: white !important;
}

/* Cards and Panels */
.gr-panel {
    border-radius: 15px !important;
    border: none !important;
    box-shadow: 0 5px 20px rgba(0,0,0,0.08) !important;
}

/* Section Headers */
.section-header {
    background: linear-gradient(90deg, #1e3c72 0%, transparent 100%);
    color: white;
    padding: 15px 25px;
    border-radius: 10px;
    margin: 20px 0 15px 0;
    font-weight: 600;
    font-size: 1.2em;
}

/* Status Badges */
.status-badge {
    display: inline-block;
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.95em;
    text-align: center;
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.fade-in {
    animation: fadeIn 0.5s ease;
}

/* Footer */
.footer {
    text-align: center;
    padding: 30px;
    margin-top: 50px;
    border-top: 2px solid #e0e6ed;
    color: #6c757d;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: #f1f3f5;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
}
"""

# Build the app
with gr.Blocks(title="CodeRefine - Professional Code Analysis") as app:
    
    # Authentication Pages
    with gr.Column(visible=True) as auth_page:
        gr.HTML("""
        <div class="main-header">
            <h1>🚀 CodeRefine</h1>
            <h3>Professional AI Code Analysis & Execution Platform</h3>
            <p>Instant Error Detection • Auto-Correction • Complexity Analysis • Code Execution</p>
        </div>
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("")
            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.Tab("🔐 Login"):
                        gr.Markdown("### Welcome Back!")
                        login_username = gr.Textbox(label="Username", placeholder="Enter your username")
                        login_password = gr.Textbox(label="Password", type="password", placeholder="Enter your password")
                        login_btn = gr.Button("🚀 Login", variant="primary", size="lg")
                        login_status = gr.Textbox(label="Status", interactive=False)
                    
                    with gr.Tab("📝 Sign Up"):
                        gr.Markdown("### Create Your Account")
                        signup_username = gr.Textbox(label="Username", placeholder="Choose a unique username")
                        signup_password = gr.Textbox(label="Password", type="password", placeholder="Min 6 characters")
                        signup_confirm = gr.Textbox(label="Confirm Password", type="password", placeholder="Re-enter password")
                        signup_btn = gr.Button("✨ Create Account", variant="primary", size="lg")
                        signup_status = gr.Textbox(label="Status", interactive=False)
            with gr.Column(scale=1):
                gr.Markdown("")
    
    # Main Application
    with gr.Column(visible=False) as main_page:
        gr.HTML("""
        <div class="main-header">
            <h1>🚀 CodeRefine</h1>
            <h3>Professional Code Analysis Platform</h3>
            <p>AI-Powered Error Detection • Auto-Correction • Complexity Analysis • Live Execution</p>
        </div>
        """)
        
        with gr.Row():
            with gr.Column(scale=4):
                gr.Markdown("### 👤 Session Active")
            with gr.Column(scale=1):
                logout_btn = gr.Button("🚪 Logout", size="sm", variant="secondary")
        
        gr.Markdown("---")
        
        # API Key Section
        with gr.Row():
            with gr.Column(scale=3):
                api_key_input = gr.Textbox(
                    label="🔑 Groq API Key",
                    placeholder="Get your free API key from console.groq.com",
                    type="password"
                )
            with gr.Column(scale=2):
                api_status = gr.Textbox(label="🔌 Connection Status", value="⚪ Not Connected", interactive=False)
            with gr.Column(scale=1):
                set_api_btn = gr.Button("Connect", variant="primary", size="lg")
        
        set_api_btn.click(
            fn=initialize_groq,
            inputs=[api_key_input],
            outputs=[api_status]
        )
        
        gr.Markdown("---")
        
        # Main Interface
        with gr.Row():
            # Left: Code Input
            with gr.Column(scale=3):
                gr.Markdown("### 📝 Code Editor")
                code_input = gr.Code(
                    label="",
                    language="python",
                    lines=22
                )
                
                language_select = gr.Dropdown(
                    choices=["Python", "JavaScript", "Java", "C++", "C#", "Go", "TypeScript", "Ruby", "PHP"],
                    value="Python",
                    label="Programming Language"
                )
                
                with gr.Row():
                    analyze_btn = gr.Button("🔍 Analyze", variant="primary", size="lg", scale=1)
                    run_btn = gr.Button("▶️ Run", variant="secondary", size="lg", scale=1)
                    both_btn = gr.Button("🚀 Analyze & Run", variant="primary", size="lg", scale=2)
            
            # Right: Quick Results
            with gr.Column(scale=2):
                gr.Markdown("### 📊 Quick Results")
                
                error_status_output = gr.Textbox(
                    label="",
                    value="⚪ Waiting for analysis...",
                    interactive=False,
                    lines=2,
                    elem_classes="results-card"
                )
                
                complexity_output = gr.Textbox(
                    label="",
                    value="⏱️ Time: - | 💾 Space: -",
                    interactive=False,
                    lines=2,
                    elem_classes="results-card"
                )
                
                status_output = gr.Textbox(
                    label="",
                    value="⏳ Ready to analyze",
                    interactive=False,
                    lines=2,
                    elem_classes="results-card"
                )
        
        gr.Markdown("---")
        
        # Results Tabs
        with gr.Tabs():
            with gr.Tab("📊 Full Analysis"):
                analysis_output = gr.Markdown(value="*Analysis results will appear here...*")
            
            with gr.Tab("✅ Corrected Code"):
                corrected_output = gr.Code(
                    label="",
                    language="python",
                    lines=15,
                    value="# Corrected code will appear here after analysis"
                )
            
            with gr.Tab("▶️ Execution Output"):
                run_output = gr.Textbox(
                    label="",
                    lines=15,
                    interactive=False,
                    value="Code execution output will appear here..."
                )
        
        gr.Markdown("---")
        
        # Examples
        gr.Markdown("### 📚 Try These Examples (with intentional errors)")
        gr.Examples(
            examples=[
                ["""def factorial(n):
    if n = 1:  # Error: = should be ==
        return 1
    return n * factorial(n-1)

print(factorial(5))""", "Python"],
                ["""def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

print(bubble_sort([64, 34, 25, 12, 22]))""", "Python"],
                ["""function sum(a, b) {
    return a + b
}
console.log(sum(10, 20))""", "JavaScript"],
            ],
            inputs=[code_input, language_select]
        )
        
        # Event handlers
        analyze_btn.click(
            fn=analyze_code_short,
            inputs=[code_input, language_select, api_key_input],
            outputs=[analysis_output, error_status_output, corrected_output, complexity_output, status_output]
        )
        
        run_btn.click(
            fn=run_code,
            inputs=[code_input, language_select],
            outputs=[run_output, gr.Textbox(visible=False)]
        )
        
        both_btn.click(
            fn=run_and_analyze,
            inputs=[code_input, language_select, api_key_input],
            outputs=[analysis_output, error_status_output, corrected_output, complexity_output, status_output, run_output]
        )
        
        # Footer
        gr.HTML("""
        <div class="footer">
            <p style="font-size: 1.1em; font-weight: 600; margin-bottom: 10px;">
                Built with ❤️ using Gradio & Groq
            </p>
            <p style="margin: 5px 0;">CodeRefine v3.0 Professional Edition</p>
            <p style="color: #999;">Powered by Llama 3.3 70B Versatile</p>
        </div>
        """)
    
    # Authentication handlers
    login_btn.click(
        fn=login,
        inputs=[login_username, login_password],
        outputs=[login_status, main_page, auth_page]
    )
    
    signup_btn.click(
        fn=signup,
        inputs=[signup_username, signup_password, signup_confirm],
        outputs=[signup_status, main_page]
    )
    
    logout_btn.click(
        fn=logout,
        outputs=[main_page, auth_page]
    )

# Launch
if __name__ == "__main__":
    print("=" * 80)
    print("🚀 CodeRefine v3.0 - Professional Code Analysis Platform")
    print("=" * 80)
    print("✨ Features:")
    print("   ✅ User Authentication (Signup/Login)")
    print("   ✅ Error Detection with Auto-Correction")
    print("   ✅ Time & Space Complexity Analysis")
    print("   ✅ Live Code Execution (Python & JavaScript)")
    print("   ✅ Professional UI with Modern Design")
    print("   ✅ Quick Results Display (UPDATED)")
    print("=" * 80)
    print("📍 Server: http://127.0.0.1:7860")
    print("🔑 Get Free API Key: https://console.groq.com")
    print("=" * 80)
    
    app.launch(
        share=False,
        server_name="127.0.0.1",
        server_port=7860,
        show_error=True,
        css=custom_css
    )