#!/usr/bin/env python3
"""
Open-SAS Jupyter Kernel Entry Point
"""

import sys
from .osas_kernel import OSASKernel
from ipykernel.kernelapp import IPKernelApp

def main():
    """Main entry point for the kernel."""
    IPKernelApp.launch_instance(kernel_class=OSASKernel)

if __name__ == '__main__':
    main()
