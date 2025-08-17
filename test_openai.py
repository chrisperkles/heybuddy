#!/usr/bin/env python3
import os
import sys

# Clear all proxy environment variables
proxy_vars = [k for k in os.environ.keys() if 'proxy' in k.lower()]
for var in proxy_vars:
    del os.environ[var]
    print(f"Removed {var}")

try:
    from openai import OpenAI
    
    # Your API key
    api_key = "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"
    
    client = OpenAI(api_key=api_key)
    print("✓ OpenAI client created successfully")
    
    # Test Chat
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=10
    )
    print(f"✓ Chat test: {response.choices[0].message.content}")
    
    # Test TTS
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input="Hello from heyBuddy!"
    )
    print("✓ TTS test successful")
    
    print("\n🎉 All OpenAI services working!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()