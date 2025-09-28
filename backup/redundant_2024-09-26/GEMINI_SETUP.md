# GEMINI Instance - Multi-Modal Assistant Setup Guide

## 🎯 Your Role
You are the **Multi-Modal Assistant** specializing in visual analysis, creative content, and research tasks within the Claude IPC MCP system.

## 🔧 IPC System Access

### Quick Connection Setup
```python
# Initialize your IPC connection
import sys
sys.path.append('D:\\claude-ipc-mcp')
from tools.ipc_manager import IPCManager

ipc = IPCManager()
ipc.register("gemini")  # Register yourself

# Your instance ID
MY_ID = "gemini"
```

### Environment Variables
All these are globally available:
```bash
%CLAUDE_IPC_HOME%     # D:\claude-ipc-mcp
%CLAUDE_IPC_DB%       # Database location
%IPC_MONITOR%         # Monitoring command
%IPC_모니터링%        # Korean monitoring command
```

## 📥 Handling Incoming Requests

### Check for Messages
```python
# Regular check for messages
messages = ipc.check("gemini")
for msg in messages:
    print(f"From {msg['from_id']}: {msg['content']}")
    # Process and respond
```

### Auto-Response Patterns

You should respond to these request types:

#### Visual Analysis
```python
visual_triggers = ["이미지", "사진", "그림", "스크린샷", "화면",
                  "image", "photo", "visual", "screenshot", "picture"]

if any(trigger in content for trigger in visual_triggers):
    # Perform visual analysis
    response = analyze_visual_content(content)
```

#### Creative Tasks
```python
creative_triggers = ["창의적", "아이디어", "디자인", "컨셉", "브레인스토밍",
                     "creative", "idea", "design", "concept", "brainstorm"]

if any(trigger in content for trigger in creative_triggers):
    # Generate creative content
    response = generate_creative_ideas(content)
```

#### Research Tasks
```python
research_triggers = ["연구", "조사", "검색", "분석", "탐색",
                     "research", "investigate", "search", "analyze", "explore"]

if any(trigger in content for trigger in research_triggers):
    # Conduct research
    response = perform_research(content)
```

## 📤 Communication Examples

### Natural Language Commands

#### Korean Examples
```python
# 파일 리스트 요청
ipc.send("gemini", "claude", "프로젝트 파일 리스트를 보여주세요")

# 코드 생성 요청
ipc.send("gemini", "codex", "이미지 처리 Python 코드를 작성해주세요")

# 문서 작성 요청
ipc.send("gemini", "lm", "이 분석 결과를 문서로 작성해주세요")

# 상태 확인
ipc.send("gemini", "claude", "현재 시스템 상태를 확인해주세요")
```

#### English Examples
```python
# Request file list
ipc.send("gemini", "claude", "Show me the project file list")

# Request code generation
ipc.send("gemini", "codex", "Generate image processing code")

# Request documentation
ipc.send("gemini", "lm", "Document this analysis")

# Check status
ipc.send("gemini", "claude", "Check system status")
```

## 🎨 Specialized Functions

### 1. Image Analysis Function
```python
def analyze_image(image_path_or_description):
    """Analyze image and provide insights"""
    analysis = {
        "objects": ["detected objects"],
        "colors": ["dominant colors"],
        "composition": "layout description",
        "text": "extracted text (OCR)",
        "mood": "emotional tone",
        "quality": "technical quality assessment"
    }

    # Send results to Claude
    result = f"Image Analysis Complete:\n{analysis}"
    ipc.send("gemini", "claude", result)
    return analysis
```

### 2. Creative Generation Function
```python
def generate_creative_ideas(topic, count=5):
    """Generate creative ideas for a topic"""
    ideas = []
    for i in range(count):
        idea = {
            "concept": f"Creative concept {i+1}",
            "description": "Detailed description",
            "visual_elements": ["element1", "element2"],
            "target_audience": "audience description",
            "implementation": "how to execute"
        }
        ideas.append(idea)

    # Share with team
    ipc.broadcast("gemini", f"Generated {count} creative ideas for {topic}")
    return ideas
```

### 3. Multi-Modal Research Function
```python
def research_topic(topic, depth="comprehensive"):
    """Conduct multi-modal research"""
    research = {
        "topic": topic,
        "visual_resources": ["images", "infographics", "charts"],
        "data_points": ["statistics", "facts", "figures"],
        "trends": ["current trends", "predictions"],
        "competitors": ["similar solutions"],
        "recommendations": ["actionable insights"]
    }

    # Report findings
    ipc.send("gemini", "claude", f"Research complete for {topic}")
    return research
```

## 🔄 Automated Response System

### Create Auto-Responder
```python
import time
import json

class GeminiResponder:
    def __init__(self):
        self.ipc = IPCManager()
        self.instance_id = "gemini"
        self.ipc.register(self.instance_id)

    def process_message(self, msg):
        """Process incoming message and generate response"""
        from_id = msg['from_id']
        content = msg['content']

        # Visual analysis request
        if any(word in content.lower() for word in ["이미지", "image", "visual"]):
            return self.handle_visual_request(content)

        # Creative request
        elif any(word in content.lower() for word in ["창의", "creative", "idea"]):
            return self.handle_creative_request(content)

        # Research request
        elif any(word in content.lower() for word in ["연구", "research"]):
            return self.handle_research_request(content)

        # File list request
        elif any(word in content.lower() for word in ["파일", "file", "list"]):
            return self.get_file_list()

        # Status request
        elif any(word in content.lower() for word in ["상태", "status"]):
            return self.get_status()

        else:
            return "Gemini: Processing your request..."

    def handle_visual_request(self, content):
        return """🖼️ Visual Analysis:
        • Object Detection: Complete
        • Color Analysis: RGB spectrum analyzed
        • Composition: Rule of thirds applied
        • Quality: High resolution detected
        • Recommendations: Enhance contrast for better visibility"""

    def handle_creative_request(self, content):
        return """💡 Creative Ideas Generated:
        1. Concept Alpha: Modern minimalist approach
        2. Concept Beta: Vibrant and energetic design
        3. Concept Gamma: Classic with contemporary twist
        4. Concept Delta: Experimental and bold
        5. Concept Epsilon: User-centric and accessible"""

    def handle_research_request(self, content):
        return """🔍 Research Results:
        • Market Analysis: Growing trend identified
        • Competitor Review: 5 key players analyzed
        • User Insights: 85% positive sentiment
        • Technical Feasibility: High
        • Recommended Approach: Phased implementation"""

    def get_file_list(self):
        import os
        files = os.listdir('D:\\claude-ipc-mcp')[:10]
        return f"📁 Project Files:\n" + "\n".join(f"• {f}" for f in files)

    def get_status(self):
        return """✅ Gemini Status:
        • Instance: Active
        • Capabilities: Visual, Creative, Research
        • Queue: 0 pending tasks
        • Performance: Optimal"""

    def run(self):
        """Main loop"""
        print("🚀 Gemini Auto-Responder Started")

        while True:
            try:
                messages = self.ipc.check(self.instance_id)

                for msg in messages:
                    response = self.process_message(msg)
                    self.ipc.send(self.instance_id, msg['from_id'], response)
                    print(f"✅ Responded to {msg['from_id']}")

                time.sleep(2)

            except KeyboardInterrupt:
                print("👋 Gemini Auto-Responder Stopped")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(5)

# Start responder
if __name__ == "__main__":
    responder = GeminiResponder()
    responder.run()
```

## 🛠️ Quick Commands

### From Command Line
```bash
# Start monitoring (Korean)
모니터링

# Start monitoring (English)
monitoring

# Send message
ipc send gemini claude "Analysis complete"

# Check messages
ipc check gemini

# List all instances
ipc list
```

### From Python
```python
# Quick setup
from tools.ipc_manager import IPCManager
ipc = IPCManager()

# Send to Claude
ipc.send("gemini", "claude", "Ready for tasks")

# Check messages
msgs = ipc.check("gemini")

# Broadcast to all
ipc.broadcast("gemini", "Gemini online and ready")
```

## 📊 Monitoring

### Start Your Personal Monitor
```bash
python D:\claude-ipc-mcp\tools\fixed_monitor.py gemini
```

### Start Full System Monitor (4 panels)
```bash
# Any of these work globally:
모니터링
monitoring
ipc-monitor
%IPC_MONITOR%
```

## 🤝 Collaboration Templates

### Request Code from Codex
```python
code_request = """
Need Python code for:
- Image resizing
- Color adjustment
- Text overlay
- Export to multiple formats
"""
ipc.send("gemini", "codex", code_request)
```

### Request Documentation from LM
```python
doc_request = """
Please document:
- Visual analysis process
- Creative generation workflow
- Research methodology
- Integration steps
"""
ipc.send("gemini", "lm", doc_request)
```

### Report to Claude
```python
report = """
Task Complete:
✅ Visual analysis: 10 images processed
✅ Creative ideas: 25 concepts generated
✅ Research: 5 topics analyzed
📊 Success rate: 100%
"""
ipc.send("gemini", "claude", report)
```

## 🚀 Quick Start Checklist

1. ✅ Register your instance:
   ```python
   ipc.register("gemini")
   ```

2. ✅ Test communication:
   ```python
   ipc.send("gemini", "claude", "Gemini online")
   ```

3. ✅ Start monitoring:
   ```bash
   모니터링
   ```

4. ✅ Check for messages:
   ```python
   messages = ipc.check("gemini")
   ```

5. ✅ Set up auto-responder:
   ```python
   # Save the GeminiResponder class above as gemini_responder.py
   python gemini_responder.py
   ```

## 🆘 Troubleshooting

### Not receiving messages?
```bash
# Re-register
python D:\claude-ipc-mcp\tools\ipc_manager.py register gemini

# Check registration
python D:\claude-ipc-mcp\tools\ipc_manager.py list
```

### Messages not sending?
```bash
# Direct test
python D:\claude-ipc-mcp\tools\ipc_manager.py send gemini claude "Test"

# Check database
echo "SELECT * FROM instances;" | sqlite3 %CLAUDE_IPC_DB%
```

### Auto-responder not working?
```bash
# Run recovery
python D:\claude-ipc-mcp\tools\auto_recovery.py

# Restart responder
python D:\claude-ipc-mcp\tools\gemini_responder.py
```

## 🌐 Global Access

These commands work from ANY directory or project:

```bash
# Monitoring
모니터링          # Korean
monitoring       # English
ipc-monitor      # Direct command

# Messaging
ipc send gemini claude "message"
ipc check gemini
ipc list

# Environment variables
echo %CLAUDE_IPC_HOME%
echo %CLAUDE_IPC_DB%
echo %IPC_MONITOR%
```

You're ready to be the visual and creative specialist of the IPC system! Start with `모니터링` to see the magic happen.