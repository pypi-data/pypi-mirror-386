# provide/foundation/process/defaults.py
#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

"""Process defaults for Foundation configuration."""

# =================================
# Process Execution Defaults
# =================================
DEFAULT_PROCESS_READLINE_TIMEOUT = 2.0
DEFAULT_PROCESS_READCHAR_TIMEOUT = 1.0
DEFAULT_PROCESS_TERMINATE_TIMEOUT = 7.0
DEFAULT_PROCESS_WAIT_TIMEOUT = 10.0

# =================================
# Shell Safety Defaults
# =================================
DEFAULT_SHELL_ALLOW_FEATURES = False

# =================================
# Environment Scrubbing Defaults
# =================================
DEFAULT_ENV_SCRUBBING_ENABLED = True

__all__ = [
    "DEFAULT_ENV_SCRUBBING_ENABLED",
    "DEFAULT_PROCESS_READCHAR_TIMEOUT",
    "DEFAULT_PROCESS_READLINE_TIMEOUT",
    "DEFAULT_PROCESS_TERMINATE_TIMEOUT",
    "DEFAULT_PROCESS_WAIT_TIMEOUT",
    "DEFAULT_SHELL_ALLOW_FEATURES",
]


# <3 🧱🤝🏃🪄
