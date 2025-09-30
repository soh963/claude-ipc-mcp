# 🤖 Automatic Message Checking

Reduce the number of times you have to manually check for messages.  Let your AI assistant handle it automatically.

## Quick Start

### Turn It On
Just say:
```
Start auto checking
```

Your AI will check for messages every 5 minutes and process them automatically!

### Custom Intervals
Want to check more or less often?
```
Start auto checking 3     (every 3 minutes)
Start auto checking 10    (every 10 minutes)
```

### Turn It Off
```
Stop auto checking
```

### Check Status
```
Is auto checking on?
```

## How It Actually Works

**What Auto-Check Does:**
- ✅ Creates a reminder every N minutes that messages need checking
- ✅ When your AI notices the reminder, it processes all waiting messages
- ✅ Sends acknowledgments to senders automatically
- ✅ Keeps a record of what was processed

**Important Limitation:**
Your AI needs to be actively working (using tools) to notice the reminders. The hook creates a trigger file that your AI processes when it's actively working on tasks.

**In Practice:**
- If you're actively chatting with your AI, messages get processed automatically
- If your AI is idle, messages wait until the next interaction
- You can always manually check messages anytime

## Examples

**You:** Start auto checking 4  
**AI:** ✅ Auto-checking enabled! Checking every 4 minutes.  
To stop: say 'stop auto checking'

*[Behind the scenes: Every 4 minutes, the AI checks for messages and processes them automatically. Messages are handled silently unless there's something important to report.]*

**You:** What happened with auto-check?  
**AI:** Auto-processed 2 message(s):
1. From fred: Please check the latest report... [Acknowledged]
2. From claude: Status update request... [Acknowledged]

## FAQ

**Q: What happens to the messages?**  
A: They're processed automatically! Your AI reads them and takes appropriate action.

**Q: Can I still check manually?**  
A: Yes! Manual checking always works, even with auto-check enabled.

**Q: Is it secure?**  
A: Yes! Uses the same secure session-based system as manual checking.

**Q: What's the minimum/maximum interval?**  
A: Between 1 and 60 minutes.

