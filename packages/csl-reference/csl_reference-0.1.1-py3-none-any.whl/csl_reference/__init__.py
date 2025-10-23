# SPDX-FileCopyrightText: 2025-present The CSL-Reference Team <https://github.com/Fusion-Power-Plant-Framework/csl-reference>
#
# SPDX-License-Identifier: MIT
"""Package to represent references."""

import logging

from csl_reference._reference import DateVariable, NameVariable, Reference, ReferenceType

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

__all__ = [
    "DateVariable",
    "NameVariable",
    "Reference",
    "ReferenceType",
]
