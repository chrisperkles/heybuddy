#!/usr/bin/env python3
"""
Test script for German AI functionality
"""
import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.ai_client import AIClient
from core.german_ai import GermanContentFilter, GermanAIPersona

async def test_german_ai():
    """Test German AI functionality"""
    print("🇩🇪 Testing German AI functionality...")
    
    # Test German content filter
    print("\n1. Testing German Content Filter:")
    german_filter = GermanContentFilter()
    
    test_inputs = [
        "Hallo heyBuddy, wie geht es dir?",
        "Ich bin heute traurig",
        "Kannst du mir eine Geschichte erzählen?",
        "Ich habe Angst vor Monstern",
        "Was ist Gewalt?"  # Should be blocked
    ]
    
    for test_input in test_inputs:
        result = german_filter.check_content_appropriateness(test_input, age=8)
        print(f"  Input: '{test_input}'")
        print(f"  Safe: {result['safe']}, Emotional Support: {result['emotional_support_needed']}")
        if result['flagged_words']:
            print(f"  Flagged: {result['flagged_words']}")
        if result['emotional_keywords']:
            print(f"  Emotional: {result['emotional_keywords']}")
        print()
    
    # Test German prompts
    print("2. Testing German AI Prompts:")
    young_prompt = GermanAIPersona.get_german_system_prompt(age=6)
    print(f"  Young child prompt length: {len(young_prompt)} characters")
    print(f"  Contains 'Deutsch': {'Deutsch' in young_prompt}")
    
    school_prompt = GermanAIPersona.get_german_system_prompt(age=10)
    print(f"  School child prompt length: {len(school_prompt)} characters")
    print(f"  Contains 'Bundesländer': {'Bundesländer' in school_prompt}")
    
    # Test AI client with German
    print("\n3. Testing German AI Client:")
    try:
        ai_client = AIClient(language="de")
        if await ai_client.initialize():
            print("  ✅ German AI client initialized successfully")
            
            # Test a simple German conversation
            response = await ai_client.process_conversation(
                user_input="Hallo, kannst du mir helfen?",
                user_id="test_german",
                age=8
            )
            
            print(f"  Response success: {response['success']}")
            print(f"  Language: {response.get('language', 'not set')}")
            if response['success']:
                print(f"  AI Response: {response['response'][:100]}...")
            else:
                print(f"  Error: {response.get('error', 'unknown')}")
                
        else:
            print("  ❌ Failed to initialize German AI client")
            
    except Exception as e:
        print(f"  ❌ Error testing AI client: {e}")
    
    print("\n🎉 German AI testing completed!")

if __name__ == "__main__":
    asyncio.run(test_german_ai())