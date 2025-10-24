#!/usr/bin/env python3
"""
Standalone kernel launcher for Open-SAS
"""

import sys
from .osas_kernel import OSASKernel
from ipykernel.kernelapp import IPKernelApp

if __name__ == '__main__':
    IPKernelApp.launch_instance(kernel_class=OSASKernel)
