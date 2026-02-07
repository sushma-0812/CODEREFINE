"""
CodeRefine: Generative AI-Powered Code Review & Optimization Engine
A professional debugging and code optimization tool powered by Groq Llama 3.3 70B
"""

import gradio as gr
from groq import Groq
import os
import json
from datetime import datetime

# Initialize Groq client
# Set your API key as environment variable: export GROQ_API_KEY="your_key_here"
# Or you can set it directly in the interface
client = None

# Debugging workflow templates
DEBUGGING_WORKFLOWS = {
    "Quick Debug": """Analyze this code for common issues:
1. Syntax errors
2. Logic errors
3. Runtime exceptions
4. Performance bottlenecks
5. Security vulnerabilities

Provide specific fixes with line numbers.""",
    
    "Deep Analysis": """Perform comprehensive code analysis:
1. Code structure and architecture
2. Design patterns usage
3. Error handling mechanisms
4. Memory management
5. Scalability concerns
6. Best practices violations
7. Optimization opportunities

Provide detailed recommendations.""",
    
    "Performance Optimization": """Focus on performance optimization:
1. Identify slow operations
2. Algorithm efficiency (Big O analysis)
3. Memory usage optimization
4. Database query optimization
5. Caching opportunities
6. Parallelization possibilities

Suggest specific optimizations with code examples.""",
    
    "Security Audit": """Conduct security-focused review:
1. Input validation vulnerabilities
2. SQL injection risks
3. XSS vulnerabilities
4. Authentication/authorization issues
5. Sensitive data exposure
6. Dependency vulnerabilities
7. OWASP Top 10 compliance

Provide security fixes and best practices.""",
    
    "Bug Hunt": """Systematic bug detection:
1. Logical errors and edge cases
2. Null/undefined handling
3. Type mismatches
4. Resource leaks
5. Race conditions
6. Infinite loops
7. Exception handling gaps

List all potential bugs with severity levels.""",
    
    "Code Refactoring": """Suggest refactoring improvements:
1. Code duplication (DRY principle)
2. Function/class decomposition
3. Naming conventions
4. Code readability
5. Maintainability improvements
6. SOLID principles application

Provide refactored code examples."""
}

def initialize_groq(api_key):
    """Initialize Groq client with API key"""
    global client
    try:
        client = Groq(api_key=api_key)
        return "✅ API Key configured successfully!"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def analyze_code(code, workflow_type, language, custom_prompt, api_key):
    """Main function to analyze code using Groq API"""
    global client
    
    # Initialize client if not already done
    if not client and api_key:
        initialize_groq(api_key)
    
    if not client:
        return "⚠️ Please set your Groq API key first!", "", ""
    
    if not code.strip():
        return "⚠️ Please enter code to analyze!", "", ""
    
    # Build the analysis prompt
    workflow_prompt = DEBUGGING_WORKFLOWS.get(workflow_type, DEBUGGING_WORKFLOWS["Quick Debug"])
    
    system_prompt = f"""You are CodeRefine, an expert code reviewer and debugging assistant.
You specialize in {language} code analysis and optimization.
Provide clear, actionable feedback with code examples when relevant.
Be thorough but concise. Focus on practical improvements."""

    user_prompt = f"""Language: {language}

Code to analyze:
```{language.lower()}
{code}
```

Analysis Type: {workflow_type}

{workflow_prompt}

{f'Additional Instructions: {custom_prompt}' if custom_prompt else ''}

Provide your analysis in a structured format with clear sections."""

    try:
        # Call Groq API
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=2048,
        )
        
        analysis = chat_completion.choices[0].message.content
        
        # Generate summary
        summary = generate_summary(analysis)
        
        # Format timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return analysis, summary, f"Analysis completed at {timestamp}"
        
    except Exception as e:
        return f"❌ Error during analysis: {str(e)}", "", ""

def generate_summary(analysis):
    """Generate a quick summary of the analysis"""
    lines = analysis.split('\n')
    summary_lines = []
    
    for line in lines[:10]:  # First 10 lines
        if line.strip() and not line.strip().startswith('```'):
            summary_lines.append(line)
            if len(summary_lines) >= 5:
                break
    
    return '\n'.join(summary_lines) + '\n\n...(See full analysis above)'

def chat_with_coderefine(message, history, api_key):
    """Interactive chatbot for code-related questions"""
    global client
    
    if not client and api_key:
        initialize_groq(api_key)
    
    if not client:
        return "⚠️ Please set your Groq API key first!"
    
    try:
        # Build conversation history
        messages = [
            {"role": "system", "content": """You are CodeRefine Assistant, a helpful AI that answers 
            questions about coding, debugging, and software development. Provide clear, practical 
            advice with code examples when helpful."""}
        ]
        
        # Add chat history
        for user_msg, assistant_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": assistant_msg})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Get response
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1024,
        )
        
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Custom CSS for professional appearance
custom_css = """
.gradio-container {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.header {
    text-align: center;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    margin-bottom: 20px;
}

.workflow-card {
    border: 2px solid #667eea;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
}

footer {
    text-align: center;
    margin-top: 30px;
    color: #666;
}
"""

# Build Gradio Interface
with gr.Blocks(css=custom_css, title="CodeRefine - AI Code Review Engine") as app:
    
    # Header
    gr.HTML("""
    <div class="header">
        <h1>🚀 CodeRefine</h1>
        <h3>Generative AI-Powered Code Review & Optimization Engine</h3>
        <p>Powered by Groq Llama 3.3 70B Versatile</p>
    </div>
    """)
    
    # API Key Section
    with gr.Row():
        with gr.Column():
            api_key_input = gr.Textbox(
                label="🔑 Groq API Key",
                placeholder="Enter your Groq API key here...",
                type="password",
                info="Get your free API key from https://console.groq.com"
            )
            api_status = gr.Textbox(label="Status", interactive=False)
            set_api_btn = gr.Button("Set API Key", variant="primary")
    
    set_api_btn.click(
        fn=initialize_groq,
        inputs=[api_key_input],
        outputs=[api_status]
    )
    
    # Main Tabs
    with gr.Tabs():
        
        # Tab 1: Code Analysis
        with gr.Tab("🔍 Code Analysis"):
            with gr.Row():
                with gr.Column(scale=2):
                    code_input = gr.Code(
                        label="📝 Enter Your Code (Paste your code here for analysis)",
                        language="python",
                        lines=15
                    )
                    
                    with gr.Row():
                        language_select = gr.Dropdown(
                            choices=["Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust", "TypeScript", "Ruby", "PHP"],
                            value="Python",
                            label="Programming Language"
                        )
                        
                        workflow_select = gr.Dropdown(
                            choices=list(DEBUGGING_WORKFLOWS.keys()),
                            value="Quick Debug",
                            label="Analysis Workflow"
                        )
                    
                    custom_prompt = gr.Textbox(
                        label="Custom Instructions (Optional)",
                        placeholder="Add any specific requirements or areas to focus on...",
                        lines=2
                    )
                    
                    analyze_btn = gr.Button("🔎 Analyze Code", variant="primary", size="lg")
                
                with gr.Column(scale=1):
                    gr.Markdown("### 📋 Workflow Descriptions")
                    gr.Markdown("""
                    **Quick Debug**: Fast analysis for common issues
                    
                    **Deep Analysis**: Comprehensive code review
                    
                    **Performance Optimization**: Speed & efficiency focus
                    
                    **Security Audit**: Security vulnerabilities check
                    
                    **Bug Hunt**: Systematic bug detection
                    
                    **Code Refactoring**: Improvement suggestions
                    """)
            
            with gr.Row():
                with gr.Column():
                    analysis_output = gr.Markdown(label="Full Analysis")
                    
            with gr.Row():
                with gr.Column():
                    summary_output = gr.Textbox(label="Quick Summary", lines=5)
                with gr.Column():
                    status_output = gr.Textbox(label="Status", interactive=False)
            
            analyze_btn.click(
                fn=analyze_code,
                inputs=[code_input, workflow_select, language_select, custom_prompt, api_key_input],
                outputs=[analysis_output, summary_output, status_output]
            )
        
        # Tab 2: AI Chatbot
        with gr.Tab("💬 AI Assistant"):
            gr.Markdown("### Ask CodeRefine anything about coding, debugging, or development!")
            
            chatbot = gr.Chatbot(
                height=500,
                label="CodeRefine Assistant",
                show_copy_button=True
            )
            
            with gr.Row():
                msg_input = gr.Textbox(
                    label="Your Question",
                    placeholder="Ask me anything about code, bugs, best practices...",
                    scale=4
                )
                send_btn = gr.Button("Send", variant="primary", scale=1)
            
            gr.Examples(
                examples=[
                    "How do I debug a memory leak in Python?",
                    "What are common SQL injection vulnerabilities?",
                    "Explain the difference between async and sync programming",
                    "How can I optimize this slow database query?",
                    "What are SOLID principles in software design?"
                ],
                inputs=msg_input
            )
            
            def respond(message, chat_history, api_key):
                bot_response = chat_with_coderefine(message, chat_history, api_key)
                chat_history.append((message, bot_response))
                return "", chat_history
            
            send_btn.click(
                fn=respond,
                inputs=[msg_input, chatbot, api_key_input],
                outputs=[msg_input, chatbot]
            )
            
            msg_input.submit(
                fn=respond,
                inputs=[msg_input, chatbot, api_key_input],
                outputs=[msg_input, chatbot]
            )
        
        # Tab 3: Workflow Guide
        with gr.Tab("📚 Workflow Guide"):
            gr.Markdown("""
            # 🎯 Complete Debugging Workflows Guide
            
            ## Quick Debug Workflow
            **Best for**: Daily code reviews, PR checks, quick fixes
            
            **Steps**:
            1. Paste your code
            2. Select "Quick Debug"
            3. Review common issues
            4. Apply fixes
            
            ---
            
            ## Deep Analysis Workflow
            **Best for**: Architecture review, major refactoring, complex systems
            
            **Steps**:
            1. Submit full module/class
            2. Select "Deep Analysis"
            3. Review comprehensive report
            4. Plan improvements
            5. Refactor incrementally
            
            ---
            
            ## Performance Optimization Workflow
            **Best for**: Slow functions, bottlenecks, scaling issues
            
            **Steps**:
            1. Identify slow code section
            2. Select "Performance Optimization"
            3. Review Big O analysis
            4. Implement suggested optimizations
            5. Benchmark improvements
            
            ---
            
            ## Security Audit Workflow
            **Best for**: Production code, API endpoints, authentication
            
            **Steps**:
            1. Submit security-critical code
            2. Select "Security Audit"
            3. Review vulnerabilities
            4. Apply security fixes
            5. Re-audit after changes
            
            ---
            
            ## Bug Hunt Workflow
            **Best for**: QA testing, edge cases, pre-release checks
            
            **Steps**:
            1. Submit suspicious code
            2. Select "Bug Hunt"
            3. Review potential bugs by severity
            4. Test edge cases
            5. Fix high-priority issues first
            
            ---
            
            ## Code Refactoring Workflow
            **Best for**: Legacy code, maintainability, readability
            
            **Steps**:
            1. Submit code to refactor
            2. Select "Code Refactoring"
            3. Review suggestions
            4. Apply SOLID principles
            5. Update tests
            
            ---
            
            ## 💡 Pro Tips
            
            - **Use Custom Instructions**: Add specific context about your codebase
            - **Iterate**: Start with Quick Debug, then Deep Analysis for complex issues
            - **Language Selection**: Always select the correct language for better results
            - **Chat Assistant**: Use for follow-up questions and clarifications
            - **Save Results**: Copy analysis for documentation and team reviews
            
            ---
            
            ## 🚀 Getting Started
            
            1. **Get API Key**: Visit [Groq Console](https://console.groq.com) and create a free account
            2. **Set API Key**: Enter your key in the field above
            3. **Start Analyzing**: Paste code and select a workflow
            4. **Iterate**: Refine based on feedback
            
            ---
            
            ## ⚡ Best Practices
            
            - Run Quick Debug on every commit
            - Use Security Audit before production deploys
            - Perform Deep Analysis on complex modules
            - Leverage Bug Hunt during QA cycles
            - Apply Performance Optimization to critical paths
            
            """)
    
    # Footer
    gr.HTML("""
    <footer>
        <p>Built with ❤️ using Gradio and Groq | CodeRefine v1.0</p>
        <p>Powered by Llama 3.3 70B Versatile Model</p>
    </footer>
    """)

# Launch the app
if __name__ == "__main__":
    app.launch(
        share=False,
        server_name="127.0.0.1",
        server_port=7860,
        show_error=True
    )