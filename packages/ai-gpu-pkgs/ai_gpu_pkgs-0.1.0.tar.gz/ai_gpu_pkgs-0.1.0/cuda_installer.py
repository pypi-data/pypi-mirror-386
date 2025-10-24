#!/usr/bin/env python3
"""
AI GPU Packages Installer
Automatically detects GPU, CUDA version, and installs appropriate PyTorch and CUDA toolkit.
"""

import argparse
import os
import sys
import subprocess
import urllib.request
import tempfile
import platform


def detect_gpu():
    """Detect if NVIDIA GPU is present and return GPU name."""
    try:
        import pynvml
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        if device_count > 0:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            name = pynvml.nvmlDeviceGetName(handle)
            return True, name.decode('utf-8') if isinstance(name, bytes) else str(name)
        else:
            return False, None
    except ImportError:
        print("pynvml not installed. Installing...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pynvml'])
        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count > 0:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                name = pynvml.nvmlDeviceGetName(handle)
                return True, name.decode('utf-8') if isinstance(name, bytes) else str(name)
        except:
            pass
    except Exception as e:
        print(f"Error detecting GPU: {e}")
    
    return False, None


def get_cuda_version():
    """Get installed CUDA version."""
    try:
        result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'release' in line.lower():
                    version = line.split('release')[1].strip().split(',')[0].strip()
                    return version
    except Exception as e:
        print(f"Error getting CUDA version: {e}")
    
    return None


def get_gpu_cuda_capability():
    """Get CUDA capability of the GPU."""
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        major, minor = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
        return f"{major}.{minor}"
    except Exception as e:
        print(f"Error getting CUDA capability: {e}")
        return None


def recommend_pytorch_version(cuda_version):
    """Recommend PyTorch version based on CUDA version."""
    # This is a simplified mapping - in reality, check PyTorch compatibility
    if cuda_version.startswith('12.'):
        return "2.1.0"  # Latest stable with CUDA 12
    elif cuda_version.startswith('11.8'):
        return "2.0.1"
    elif cuda_version.startswith('11.'):
        return "1.13.1"
    else:
        return "2.1.0"  # Default to latest


def ask_create_venv():
    """Ask user if they want to create a new virtual environment."""
    while True:
        response = input("Do you want to create a new virtual environment? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please answer 'y' or 'n'")


def create_virtual_env(env_name="ai_gpu_env"):
    """Create a new virtual environment."""
    print(f"Creating virtual environment: {env_name}")
    subprocess.check_call([sys.executable, '-m', 'venv', env_name])
    print(f"Virtual environment created. Activate it with: {env_name}\\Scripts\\activate (Windows) or source {env_name}/bin/activate (Linux/Mac)")


def install_cuda_toolkit(cuda_version):
    """Download and install CUDA toolkit."""
    print(f"Installing CUDA Toolkit {cuda_version}...")
    
    # This is a simplified version - in reality, need to handle different OS and architectures
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == "windows":
        # For Windows, CUDA installer
        base_url = "https://developer.download.nvidia.com/compute/cuda"
        installer_name = f"cuda_{cuda_version.replace('.', '_')}_windows.exe"
        url = f"{base_url}/{cuda_version}/local_installers/{installer_name}"
        
        print(f"Downloading CUDA installer from: {url}")
        with tempfile.TemporaryDirectory() as temp_dir:
            installer_path = os.path.join(temp_dir, installer_name)
            urllib.request.urlretrieve(url, installer_path)
            
            print("Running CUDA installer (silent install)...")
            # Note: This might require admin privileges
            subprocess.run([installer_path, '/silent', '/noexec', '/noreboot'], check=True)
            
    else:
        print(f"CUDA installation for {system} not implemented yet. Please install manually.")
        return False
    
    print("CUDA Toolkit installed successfully.")
    return True


def install_pytorch(cuda_version, use_venv=False):
    """Install PyTorch with CUDA support."""
    print(f"Installing PyTorch for CUDA {cuda_version}...")
    
    cuda_short = cuda_version.replace('.', '')[:3]  # e.g., 118 for 11.8
    index_url = f"https://download.pytorch.org/whl/cu{cuda_short}"
    
    packages = ["torch", "torchvision", "torchaudio"]
    
    if use_venv:
        # Assume venv is activated - in practice, need to handle activation
        pip_cmd = [sys.executable, '-m', 'pip']
    else:
        pip_cmd = [sys.executable, '-m', 'pip']
    
    try:
        subprocess.check_call(pip_cmd + ['install'] + packages + ['--index-url', index_url])
        print("PyTorch installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install PyTorch: {e}")
        return False


def verify_installation():
    """Verify that PyTorch can use CUDA."""
    print("Verifying installation...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"CUDA is available! Device count: {torch.cuda.device_count()}")
            print(f"Current device: {torch.cuda.current_device()}")
            print(f"Device name: {torch.cuda.get_device_name()}")
            return True
        else:
            print("CUDA is not available in PyTorch.")
            return False
    except ImportError:
        print("PyTorch not installed or not importable.")
        return False


def setup():
    """Main setup function."""
    print("AI GPU Packages Setup")
    print("=" * 30)
    
    # Detect GPU
    has_gpu, gpu_name = detect_gpu()
    if not has_gpu:
        print("No NVIDIA GPU detected. This tool is designed for NVIDIA GPUs.")
        return
    
    print(f"✓ GPU detected: {gpu_name}")
    
    # Get CUDA capability
    cuda_capability = get_gpu_cuda_capability()
    if cuda_capability:
        print(f"✓ CUDA capability: {cuda_capability}")
    
    # Check existing CUDA
    cuda_version = get_cuda_version()
    if cuda_version:
        print(f"✓ CUDA Toolkit {cuda_version} is already installed.")
    else:
        print("✗ CUDA Toolkit not found.")
        # For now, assume user installs manually or we can try to install
        print("Please install CUDA Toolkit manually from: https://developer.nvidia.com/cuda-downloads")
        return
    
    # Ask about virtual environment
    create_venv = ask_create_venv()
    if create_venv:
        env_name = input("Enter virtual environment name (default: ai_gpu_env): ").strip()
        if not env_name:
            env_name = "ai_gpu_env"
        create_virtual_env(env_name)
        print(f"To continue installation, activate the environment and run this command again.")
        return
    
    # Install PyTorch
    if install_pytorch(cuda_version, use_venv=create_venv):
        # Verify
        verify_installation()
    else:
        print("PyTorch installation failed.")


def main():
    parser = argparse.ArgumentParser(description="AI GPU Packages Installer")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup GPU packages')
    
    args = parser.parse_args()
    
    if args.command == 'setup':
        setup()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()