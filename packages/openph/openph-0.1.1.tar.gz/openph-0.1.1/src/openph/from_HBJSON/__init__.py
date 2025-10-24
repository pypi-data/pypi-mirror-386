"""Input processing for Open-PH models from external sources.

This module provides functions to convert external building models
(HBJSON, PHX) into Open-PH data structures.
"""

from .create_phpp import from_phx_variant

__all__ = ["from_phx_variant"]
