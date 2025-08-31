#!/usr/bin/env python3
"""
Quick fix script for common dependency issues
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def fix_whisper():
    """Fix the whisper package issue."""
    print("🔧 Fixing Whisper package...")
    
    # Uninstall the wrong whisper package
    run_command("pip uninstall -y whisper", "Uninstalling wrong whisper package")
    
    # Install the correct openai-whisper package
    success = run_command("pip install openai-whisper", "Installing openai-whisper")
    
    if success:
        # Test whisper import
        try:
            import whisper
            model = whisper.load_model("base")
            print("✅ Whisper is working correctly!")
            return True
        except Exception as e:
            print(f"❌ Whisper test failed: {e}")
            return False
    return False

def fix_spacy():
    """Fix the spaCy model issue."""
    print("🔧 Fixing spaCy model...")
    
    # Install spaCy with English model
    success = run_command("pip install spacy[en_core_web_sm]", "Installing spaCy with English model")
    
    if success:
        # Download the English model
        success = run_command("python -m spacy download en_core_web_sm", "Downloading spaCy English model")
        
        if success:
            # Test spaCy import
            try:
                import spacy
                nlp = spacy.load("en_core_web_sm")
                print("✅ spaCy is working correctly!")
                return True
            except Exception as e:
                print(f"❌ spaCy test failed: {e}")
                return False
    return False

def main():
    """Main fix function."""
    print("🚀 Fixing dependency issues...")
    print("=" * 50)
    
    # Fix Whisper
    if not fix_whisper():
        print("❌ Failed to fix Whisper")
        sys.exit(1)
    
    # Fix spaCy
    if not fix_spacy():
        print("❌ Failed to fix spaCy")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ All dependency issues fixed!")
    print("\n📋 You can now run: python run.py")

if __name__ == "__main__":
    main()
