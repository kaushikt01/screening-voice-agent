#!/usr/bin/env python3
"""
Setup script for QnA Voice Agent
"""

import subprocess
import sys
import os
from pathlib import Path

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

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def setup_virtual_environment():
    """Create and activate virtual environment."""
    venv_path = Path(".venv")
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    return run_command("python3 -m venv .venv", "Creating virtual environment")

def install_dependencies():
    """Install Python dependencies."""
    # Determine the correct pip command based on OS
    if os.name == 'nt':  # Windows
        pip_cmd = ".venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        pip_cmd = ".venv/bin/pip"
    
    # Upgrade pip first
    run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip")
    
    # Install requirements
    return run_command(f"{pip_cmd} install -r requirements.txt", "Installing Python dependencies")

def setup_spacy():
    """Download spaCy model."""
    if os.name == 'nt':  # Windows
        python_cmd = ".venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        python_cmd = ".venv/bin/python"
    
    return run_command(f"{python_cmd} -m spacy download en_core_web_sm", "Downloading spaCy model")

def setup_tts():
    """Setup TTS components."""
    print("🔧 Setting up TTS components...")
    
    # Create audio directory
    audio_dir = Path("static/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    print("✅ Created audio directory")
    
    # Check if piper models exist
    piper_dir = Path("piper_models")
    if piper_dir.exists() and list(piper_dir.glob("*.onnx")):
        print("✅ Piper models found")
    else:
        print("⚠️  Piper models not found. You may need to download them manually.")
        print("   See TTS_SETUP.md for instructions")
    
    return True

def main():
    """Main setup function."""
    print("🚀 Setting up QnA Voice Agent...")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Setup virtual environment
    if not setup_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Setup spaCy
    if not setup_spacy():
        sys.exit(1)
    
    # Setup TTS
    if not setup_tts():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Copy .env.example to .env and configure your settings")
    print("2. Install and start MongoDB")
    print("3. Run: python run.py")
    print("\n📚 For detailed setup instructions, see README.md")

if __name__ == "__main__":
    main()
