"""Open-PH: Passive House energy processing toolkit.

This package provides exact PHPP (Passive House Planning Package) calculation
replication in Python, with complete transparency and validation capabilities.
"""

from openph.from_HBJSON.create_phpp import from_phx_variant
from openph.phpp import OpPhPHPP

__version__ = "0.1.0"
__all__ = ["OpPhPHPP", "from_phx_variant"]
