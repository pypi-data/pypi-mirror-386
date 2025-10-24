"""
Kernel Installation for Open-SAS

This module provides functions to install and uninstall
the Open-SAS Jupyter kernel.
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional


def install_kernel(user: bool = True, prefix: Optional[str] = None) -> bool:
    """
    Install the Open-SAS kernel for Jupyter.
    
    Args:
        user: Install for current user only
        prefix: Installation prefix path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Determine kernel directory
        if prefix:
            kernel_dir = Path(prefix) / 'share' / 'jupyter' / 'kernels' / 'osas'
        elif user:
            kernel_dir = Path.home() / '.local' / 'share' / 'jupyter' / 'kernels' / 'osas'
        else:
            kernel_dir = Path(sys.prefix) / 'share' / 'jupyter' / 'kernels' / 'osas'
        
        # Create kernel directory
        kernel_dir.mkdir(parents=True, exist_ok=True)
        
        # Create kernel specification
        kernel_spec = {
            "argv": [
                sys.executable, 
                "-m", 
                "open_sas.kernel", 
                "-f", 
                "{connection_file}"
            ],
            "display_name": "osas",
            "language": "osas",
            "mimetype": "text/x-sas",
            "file_extension": ".osas",
            "codemirror_mode": "sas",
            "pygments_lexer": "sas"
        }
        
        # Write kernel specification
        with open(kernel_dir / 'kernel.json', 'w') as f:
            json.dump(kernel_spec, f, indent=2)
        
        # Install kernel using jupyter
        cmd = ['jupyter', 'kernelspec', 'install', str(kernel_dir)]
        if user:
            cmd.append('--user')
        if prefix:
            cmd.extend(['--prefix', prefix])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Open-SAS kernel installed successfully!")
            print(f"   Kernel directory: {kernel_dir}")
            print("   You can now use Open-SAS in Jupyter notebooks!")
            return True
        else:
            print(f"❌ Failed to install kernel: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error installing kernel: {e}")
        return False


def uninstall_kernel() -> bool:
    """
    Uninstall the Open-SAS kernel.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Remove kernel using jupyter
        result = subprocess.run(
            ['jupyter', 'kernelspec', 'remove', 'osas', '-f'],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print("✅ Open-SAS kernel uninstalled successfully!")
            return True
        else:
            print(f"❌ Failed to uninstall kernel: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error uninstalling kernel: {e}")
        return False


def list_kernels() -> None:
    """List all installed Jupyter kernels."""
    try:
        result = subprocess.run(
            ['jupyter', 'kernelspec', 'list'],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print("Installed Jupyter kernels:")
            print(result.stdout)
        else:
            print(f"❌ Failed to list kernels: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error listing kernels: {e}")


def check_kernel_installed() -> bool:
    """
    Check if the Open-SAS kernel is installed.
    
    Returns:
        True if installed, False otherwise
    """
    try:
        result = subprocess.run(
            ['jupyter', 'kernelspec', 'list'],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            return 'osas' in result.stdout
        return False
        
    except Exception:
        return False


def main():
    """Main entry point for kernel installation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Install/Uninstall Open-SAS Jupyter kernel')
    parser.add_argument('action', choices=['install', 'uninstall', 'list', 'check'],
                       help='Action to perform')
    parser.add_argument('--user', action='store_true', default=True,
                       help='Install for current user only')
    parser.add_argument('--system', action='store_true',
                       help='Install system-wide')
    parser.add_argument('--prefix', type=str,
                       help='Installation prefix')
    
    args = parser.parse_args()
    
    if args.action == 'install':
        user = not args.system
        success = install_kernel(user=user, prefix=args.prefix)
        sys.exit(0 if success else 1)
        
    elif args.action == 'uninstall':
        success = uninstall_kernel()
        sys.exit(0 if success else 1)
        
    elif args.action == 'list':
        list_kernels()
        
    elif args.action == 'check':
        if check_kernel_installed():
            print("✅ Open-SAS kernel is installed")
            sys.exit(0)
        else:
            print("❌ Open-SAS kernel is not installed")
            sys.exit(1)


if __name__ == '__main__':
    main()
