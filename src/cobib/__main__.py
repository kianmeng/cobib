#!/usr/bin/env python3
"""coBib main body."""

import asyncio
import sys

from cobib.ui.cli import CLI
from cobib.ui.shell_helper import ShellHelper


async def async_main() -> None:
    """Main async executable.

    coBib's main function used to parse optional keyword arguments and subcommands.
    """
    if len(sys.argv) > 1 and any(a[0] == "_" for a in sys.argv):
        # shell helper function called
        ShellHelper()
    else:
        await CLI().run()


def main() -> None:
    """The main method wrapping the async method with `asyncio.run`."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()  # pragma: no cover
