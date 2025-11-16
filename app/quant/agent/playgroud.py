from trader import kimi_trader

from app.quant.prompting.builder import SystemPromptProvider

print(kimi_trader(SystemPromptProvider().load(), "你好，你是谁？"))
