"""
Open-SAS: Python-based SAS interpreter

A Python package that provides SAS-like syntax and functionality
with a Python backend for data analysis and manipulation.
"""

__version__ = "0.1.2"
__author__ = "Ryan Story"
__email__ = "ryan@stryve.com"

from .interpreter import SASInterpreter

__all__ = ["SASInterpreter"]
