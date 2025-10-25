# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

import sys


def main():
    from dongle.util.commands import cli

    cli()



if __name__ == '__main__':
    import dongle

    try:
        module = dongle.init_from(__name__)

    except dongle.DongleReady as e:
        module = e.reload()

    finally:
        module.main()

__signature__ = "MGQCME4+KdkDvPlSKBSiH8Jml3DlmwL5MwjuRk7Rr2P4buC+AkJb4TMHqZSYk0fFKkwELgIwJRTnZ2jiN9WL4cG8T9KwwUXF2Lqv9GwxaDs0VbtFR5dXQK4SKZARrvDwUuiR+vQE"
