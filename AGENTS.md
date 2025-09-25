# Claude IPC MCP Agent Communication Guide

## 🌐 Inter-Instance Communication System

This document provides comprehensive guidance for communication between Claude, Codex, LM, and other AI instances using the IPC (Inter-Process Communication) system. The system supports natural language messaging, automatic responses, and collaborative workflows.

## 📋 Table of Contents
- [Quick Start](#quick-start)
- [Instance Roles](#instance-roles)
- [Natural Language Commands](#natural-language-commands)
- [Message Patterns](#message-patterns)
- [Auto-Response System](#auto-response-system)
- [Monitoring & Debugging](#monitoring--debugging)
- [Advanced Features](#advanced-features)

## 🚀 Quick Start

### Starting the System
```bash
# Start 4-panel monitoring
start_monitor_fixed.bat

# Or start individual windows
start_4windows.bat
```

### Basic Messaging
```bash
# Send message from one instance to another
python tools/ipc_manager.py send codex claude "안녕하세요"
python tools/ipc_manager.py send lm gemini "파일 리스트를 보여주세요"
```

## 🤖 Instance Roles

### Claude (Master Coordinator)
- **Role**: Primary orchestrator and intelligent responder
- **Auto-Response**: Active with `tools/auto_responder.py`
- **Capabilities**:
  - File list management
  - System status monitoring
  - Task coordination
  - Intelligent request handling

### Codex (Code Specialist)
- **Role**: Code analysis, generation, and review
- **Natural Language Understanding**:
  - "코드를 분석해줘" → Code analysis
  - "버그를 찾아줘" → Bug detection
  - "리팩토링해줘" → Code refactoring
  - "테스트 코드 생성" → Test generation

### LM (Language Model)
- **Role**: Documentation, translation, and content generation
- **Natural Language Understanding**:
  - "문서를 작성해줘" → Documentation creation
  - "번역해줘" → Translation services
  - "요약해줘" → Summarization
  - "설명해줘" → Explanations

### Gemini (Multi-Modal Assistant)
- **Role**: Visual analysis, creative tasks, and research
- **Natural Language Understanding**:
  - "이미지를 분석해줘" → Image analysis
  - "다이어그램 생성" → Diagram creation
  - "리서치해줘" → Research tasks
  - "아이디어 제안" → Creative suggestions

## 💬 Natural Language Commands

### File Operations (자연어 파일 작업)

#### Request File List
```text
Natural Language Inputs:
- "파일 리스트를 보여줘"
- "프로젝트 파일 목록 요청"
- "현재 디렉토리 파일들"
- "Show me the file list"
- "List project files"

Auto-Response:
📁 프로젝트 주요 파일:
- file1.py
- file2.md
- ...
```

#### Request Specific File Content
```text
Natural Language Inputs:
- "README.md 파일 내용 보여줘"
- "설정 파일 확인해줘"
- "Show me the config file"
- "Read the documentation"

Auto-Response:
📄 [filename] 내용:
[file content]
```

### Status Checks (상태 확인)

#### System Status
```text
Natural Language Inputs:
- "시스템 상태 확인"
- "현재 상태 어때?"
- "정상 작동중이야?"
- "Check system status"
- "How are you doing?"

Auto-Response:
✅ [Instance] 인스턴스 정상 작동 중
- 자동 응답: 활성화
- 메시지 큐: N개
- 마지막 활동: HH:MM:SS
```

#### Performance Status
```text
Natural Language Inputs:
- "성능 상태 보고"
- "리소스 사용량"
- "메모리 상태"
- "Check performance"

Auto-Response:
📊 성능 상태:
- CPU: XX%
- Memory: XX MB
- Messages: N/sec
```

### Task Requests (작업 요청)

#### Code-Related Tasks (Codex)
```text
Natural Language to Codex:
- "이 코드 리뷰해줘" → Code review request
- "버그 찾아줘" → Bug finding
- "최적화 제안해줘" → Optimization suggestions
- "테스트 작성해줘" → Test generation

Expected Codex Response:
🔍 코드 분석 결과:
- Issue 1: ...
- Issue 2: ...
- Suggestions: ...
```

#### Documentation Tasks (LM)
```text
Natural Language to LM:
- "README 업데이트해줘" → Update README
- "API 문서 작성" → API documentation
- "주석 추가해줘" → Add comments
- "사용 가이드 작성" → Usage guide

Expected LM Response:
📝 문서 작업 완료:
- Updated: ...
- Added: ...
- Format: Markdown
```

#### Analysis Tasks (Gemini)
```text
Natural Language to Gemini:
- "프로젝트 구조 분석" → Project structure analysis
- "의존성 확인" → Dependency check
- "보안 취약점 검사" → Security audit
- "성능 분석" → Performance analysis

Expected Gemini Response:
🔎 분석 결과:
- Structure: ...
- Dependencies: N packages
- Issues found: ...
```

### Collaborative Workflows (협업 워크플로우)

#### Chain Messages
```text
Example Workflow:
1. User → Claude: "전체 시스템 점검해줘"
2. Claude → Codex: "코드 품질 확인 요청"
3. Claude → LM: "문서 상태 확인"
4. Claude → Gemini: "시각적 자료 검토"
5. All → Claude: [Reports]
6. Claude → User: "종합 보고서"
```

#### Broadcast Messages
```text
Natural Language Broadcast:
- "모든 인스턴스 상태 확인"
- "전체 시스템 재시작 알림"
- "긴급 작업 요청"
- "Broadcast to all instances"

Response Pattern:
각 인스턴스가 개별적으로 응답
```

## 🔄 Auto-Response System

### Activation
```bash
# Start auto-responder for Claude
cd D:/claude-ipc-mcp
python tools/auto_responder.py
```

### Response Patterns

#### Pattern Matching Rules
```python
# Keywords → Response Type
파일 + (리스트|목록) → File list response
상태 | status → Status check response
테스트 | test → Test response
도움 | help → Help message
시스템 | system → System info
안녕 | hello | hi → Greeting
감사 | 고마 | thanks → Thanks response
```

#### Custom Pattern Addition
```python
# In auto_responder.py, add to generate_response():
elif "your_keyword" in content:
    return "Your custom response"
```

### Response Examples

#### File List Request → Auto Response
```text
Input: "파일 목록 좀 보여줘"
Auto-Response:
📁 프로젝트 주요 파일:
- README.md
- auto_responder.py
- ipc_manager.py
- [more files...]
```

#### Status Check → Auto Response
```text
Input: "지금 상태 어때?"
Auto-Response:
✅ Claude 인스턴스 정상 작동 중
자동 응답 시스템 활성화됨
현재 시간: 14:30:45
```

## 📊 Monitoring & Debugging

### Real-time Monitoring
```bash
# Monitor specific instance
python tools/fixed_monitor.py claude
python tools/fixed_monitor.py codex
python tools/fixed_monitor.py lm
python tools/fixed_monitor.py gemini
```

### Check Message History
```bash
# Check messages for specific instance
python tools/ipc_manager.py check codex
python tools/ipc_manager.py check lm
```

### Debug Auto-Responder
```python
# Check auto-responder logs
# The script prints:
📥 받은 메시지 [sender]: content
📤 응답 전송 [receiver]: response
✅ 자동 응답 완료!
```

## 🎯 Advanced Features

### Smart Response Chaining
```text
Natural Language Chain:
User: "프로젝트 전체 분석하고 보고서 작성해"

Automatic Chain:
1. Claude → Codex: "코드 분석"
2. Claude → LM: "문서 검토"
3. Claude → Gemini: "구조 분석"
4. Claude: [종합 및 보고서 생성]
5. Claude → User: "완료된 보고서"
```

### Conditional Responses
```text
If message contains "긴급":
  - Priority: HIGH
  - Response time: < 1s
  - Alert all instances

If message contains "천천히":
  - Priority: LOW
  - Batch processing
  - Delayed response OK
```

### Multi-Language Support
```text
Supported Languages:
- Korean: "안녕", "도움말", "파일"
- English: "hello", "help", "files"
- Mixed: "파일 list 보여줘"

Auto-detection and response in same language
```

### Error Handling
```text
Natural Language Error Requests:
- "오류 발생" → Error report generation
- "디버그 모드" → Enable debug mode
- "로그 확인" → Show recent logs
- "문제 해결" → Troubleshooting guide
```

## 🛠️ Custom Agent Development

### Creating Custom Response Agent
```python
# custom_agent.py
class CustomAgent:
    def __init__(self, instance_id):
        self.instance_id = instance_id
        self.patterns = {
            "custom_task": self.handle_custom_task,
            "special_request": self.handle_special
        }

    def process_message(self, content, from_id):
        for pattern, handler in self.patterns.items():
            if pattern in content.lower():
                return handler(content, from_id)
        return None

    def handle_custom_task(self, content, from_id):
        # Your custom logic
        return f"Custom response for {from_id}"
```

### Natural Language Processing Enhancement
```python
# Enhanced NLP for better understanding
import re

def enhanced_nlp_response(content):
    # Remove particles (조사) for Korean
    content_clean = re.sub(r'[을를이가은는도]', ' ', content)

    # Synonym mapping
    synonyms = {
        '파일': ['file', 'files', '화일', '문서'],
        '상태': ['status', 'state', '상황', 'condition'],
        '도움': ['help', 'assistance', '도움말', '헬프']
    }

    # Match against synonyms
    for key, values in synonyms.items():
        if any(v in content_clean.lower() for v in values):
            return generate_response_for(key)
```

## 📝 Best Practices

### Message Format Guidelines
1. **Clear Intent**: Start with action verb
2. **Specific Target**: Mention target instance if needed
3. **Context Inclusion**: Provide necessary context
4. **Language Consistency**: Use consistent language

### Examples of Good Messages
```text
✅ Good:
- "Codex야, 이 코드 리뷰해줘"
- "LM에게 문서 작성 요청"
- "모든 인스턴스 상태 확인"

❌ Avoid:
- "아무나 해줘"
- "그거 좀..."
- [No context messages]
```

### Performance Optimization
```text
For better response time:
- Use specific keywords
- Avoid ambiguous requests
- Include instance names
- Use structured queries when possible
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Messages Not Received
```bash
# Check database connection
python tools/ipc_manager.py init

# Verify instance registration
python tools/ipc_manager.py list

# Re-register if needed
python tools/ipc_manager.py register codex
```

#### Auto-Responder Not Working
```bash
# Check if running
ps aux | grep auto_responder

# Restart if needed
pkill -f auto_responder.py
python tools/auto_responder.py
```

#### Message Queue Full
```bash
# Clear old messages
python tools/ipc_manager.py clear --days 7

# Increase polling frequency
# Edit auto_responder.py: time.sleep(1)  # from 2
```

## 📚 References

- [IPC Manager Documentation](./README.md)
- [Auto Responder Source](./tools/auto_responder.py)
- [Monitoring Tools Guide](./README_IPC_MONITORING.md)
- [Quick Start Guide](./QUICK_START.md)

---

**Note**: This system supports fully natural language communication. You can communicate with any instance using everyday language, and the system will understand and respond appropriately. The auto-response system ensures continuous availability and instant responses to common requests.