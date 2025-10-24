"""
mhi.help

Root of embedded HTML help files
"""

import os
import re
import sys

from pathlib import Path
from typing import Optional

def package_help(pkg) -> None:
    """
    Open the help of a particular package

    Parameters:
        pkg: The
    """

    name = pkg.__package__
    path = name[4:].replace('.', '/')

    # Look for the help rooted in that package's source tree
    root1 = Path(pkg.__file__).parents[name.count('.')] / 'help'

    # Look for the help rooted in this package's tree
    root2 = Path(__file__).parent

    for root in (root1, root2):
        index = root / 'html' / path / 'index.html'
        if index.is_file():
            os.startfile(index)
            break
    else:
        raise FileNotFoundError(f'Help file "{index}" not found')


def open_help(mod: Optional[str] = None) -> None:
    """
    Open a web browser for the HTML help

    Parameters:
        mod: A module name to open the help pages at (optional)
    """

    try:
        if mod:
            if not re.fullmatch(r'\w+(\.\w+)*', mod):
                raise ValueError(f'Invalid module "{mod}"')
            if mod.startswith('mhi.'):
                mod = mod[4:]
            mod = mod.replace('.', '/')

            help_file = f'{mod}/index.html'
        else:
            help_file = 'packages.html'

        path = Path(__file__).parent / 'html' / help_file
        if not path.is_file():
            raise FileNotFoundError(f'Help file "{path}" not found')
        os.startfile(path)

    except (FileNotFoundError, ValueError) as err:
        print(err, file=sys.stderr)
        sys.exit(1)


__version__ = '1.0.0'
