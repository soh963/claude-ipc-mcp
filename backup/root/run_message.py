# Simulate sending "안녕" to Claude via MCP
from pathlib import Path
msg_path = Path('message_to_lm.txt')
msg_path.write_text('안녕', encoding='utf-8')
print('Message sent: 안녕')