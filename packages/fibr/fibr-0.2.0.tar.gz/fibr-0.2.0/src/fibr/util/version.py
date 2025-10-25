# SPDX-FileCopyrightText: 2025 René de Hesselle <dehesselle@web.de>
#
# SPDX-License-Identifier: GPL-2.0-or-later

try:
    from fibr._hatch_build_hooks_vcs import version
except ImportError:
    version = "0.0.0"
