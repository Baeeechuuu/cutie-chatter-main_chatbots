#!/usr/bin/env python3
"""
Demo script to test TTS functionality independently of the main application.
"""

import os
import sys
from pathlib import Path

def demo_tts():
    """Demo the TTS functionality"""
    try:
        from tts.tts_engine import TTSEngine
        
        print("=== CutieChatter TTS Demo ===")
        print("Initializing TTS engine...")
        
        # Initialize TTS engine
        model_path = "./model-train/model_checkpoints/best_model.pt"
        tts_engine = TTSEngine(model_path)
        
        print("TTS engine initialized successfully!")
        print(f"Available speakers: {len(tts_engine.get_available_speakers())}")
        
        # Test text
        test_text = "Hello! I'm CutieChatter, your AI assistant with Genshin Impact voices!"
        
        print(f"\nConverting text to speech: '{test_text}'")
        print("Speaker: Paimon")
        
        # Generate audio
        audio_path = tts_engine.text_to_speech(test_text, speaker="paimon", output_path="demo_output.wav")
        
        if audio_path and os.path.exists(audio_path):
            print(f"✅ Audio generated successfully: {audio_path}")
            print("You can play this file with any audio player!")
            
            # Try to play with system default player
            try:
                import subprocess
                import platform
                
                system = platform.system()
                if system == "Windows":
                    os.startfile(audio_path)
                elif system == "Darwin":  # macOS
                    subprocess.run(["open", audio_path])
                else:  # Linux
                    subprocess.run(["xdg-open", audio_path])
                    
                print("🔊 Playing audio with system default player...")
            except Exception as e:
                print(f"Could not auto-play audio: {e}")
                print(f"Please manually play: {audio_path}")
        else:
            print("❌ Failed to generate audio")
            
    except ImportError as e:
        print(f"❌ TTS module not available: {e}")
        print("Make sure you have installed the TTS dependencies:")
        print("cd model-train && pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Demo failed: {e}")

def list_speakers():
    """List available speakers"""
    try:
        from tts.tts_engine import TTSEngine
        
        model_path = "./model-train/model_checkpoints/best_model.pt"
        tts_engine = TTSEngine(model_path)
        
        speakers = tts_engine.get_available_speakers()
        print(f"\n=== Available Speakers ({len(speakers)}) ===")
        
        # Group speakers for better display
        for i, speaker in enumerate(sorted(speakers)):
            if i % 4 == 0:
                print()
            print(f"{speaker:<15}", end="")
        print("\n")
        
    except Exception as e:
        print(f"Could not list speakers: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "speakers":
        list_speakers()
    else:
        demo_tts() 