"""coBib's Search command.

This command allows you to search your database for a regex-interpreted query.
While doing so, it uses the `config.commands.search.grep` tool to search associated files, too.

As a simple example, you can query for a simple author name like so:
```
cobib search Einstein
```
You can make the search case *in*sensitive in two ways:
1. By enabling `config.commands.search.ignore_case`.
2. By providing the `--ignore-case` command-line argument:
```
cobib search --ignore-case Einstein
```

By default, the search command will provide you with 1 line of context above and below the actual
matches. You can change this number of lines by setting the `--context` option:
```
cobib search --context 4 Einstein
```

Finally, you can also combine the search with coBib's filtering mechanism to narrow your search down
to a subset of your database:
```
cobib search Einstein -- ++year 2020
```
Note, that we use the auxiliary `--` argument to separate the filters from the actual arguments.
While this is not strictly necessary it helps to disambiguate the origin of the arguments.

You can also trigger this command from the `cobib.ui.tui.TUI`.
By default, it is bound to the `/` key.
"""

from __future__ import annotations

import logging
from typing import List

from rich.console import ConsoleRenderable
from rich.text import Text
from rich.tree import Tree as RichTree
from textual.widgets import Tree as TextualTree

from cobib import __version__
from cobib.config import Event, config
from cobib.database import Entry

from .base_command import ArgumentParser, Command
from .list import ListCommand

LOGGER = logging.getLogger(__name__)


class SearchCommand(Command):
    """The Search Command."""

    name = "search"

    def __init__(self, args: List[str]) -> None:
        """TODO."""
        super().__init__(args)

        self.entries: List[Entry] = []
        self.matches: List[List[List[str]]] = []
        self.hits: int = 0

    @classmethod
    def init_argparser(cls) -> None:
        """TODO."""
        parser = ArgumentParser(prog="search", description="Search subcommand parser.")
        parser.add_argument("query", type=str, help="text to search for")
        parser.add_argument(
            "-i", "--ignore-case", action="store_true", help="ignore case for searching"
        )
        parser.add_argument(
            "-c",
            "--context",
            type=int,
            default=1,
            help="number of context lines to provide for each match",
        )
        parser.add_argument(
            "filter",
            nargs="*",
            help="You can specify filters as used by the `list` command in order to select a "
            "subset of labels to be modified. To ensure this works as expected you should add the "
            "pseudo-argument '--' before the list of filters. See also `list --help` for more "
            "information.",
        )
        cls.argparser = parser

    def execute(self) -> None:
        """Searches in the database.

        This command searches the database for a regex-interpreted query.
        It leverages `cobib.database.Entry.search` to perform the actual search.

        You can configure the search-tool which searches through associated files via
        `config.commands.search.grep`.

        Args:
            args: a sequence of additional arguments used for the execution. The following values
                are allowed for this command:
                    * `query`: the required positional argument corresponds to the regex-interpreted
                      text which will be searched for.
                    * `-i`, `--ignore-case`: if specified, the search will be case *in*sensitive.
                      You can enable this setting permanently with
                      `config.commands.search.ignore_case`.
                    * `-c`, `--context`: you can specify the number of lines of "context" which
                      is the number of lines before and after the actual match to be included in the
                      output. This is similar to `grep`s `-C` option.
                    * in addition to the above, you can add `filters` to narrow the search down to a
                      subset of your database. For more information refer to `cobib.commands.list`.
            out: the output IO stream. This defaults to `None`.

        Returns:
            A tuple containing the number of hits and matching labels.
        """
        LOGGER.debug("Starting Search command.")

        Event.PreSearchCommand.fire(self)

        self.entries, _ = ListCommand(self.largs.filter).filter_entries()

        ignore_case = config.commands.search.ignore_case or self.largs.ignore_case
        LOGGER.debug("The search will be performed case %ssensitive", "in" if ignore_case else "")

        for entry in self.entries.copy():
            matches = entry.search(self.largs.query, self.largs.context, ignore_case)
            if not matches:
                self.entries.remove(entry)
                continue

            self.matches.append(matches)
            self.hits += len(matches)

            LOGGER.debug('Entry "%s" includes %d hits.', entry.label, len(matches))

        Event.PostSearchCommand.fire(self)

    def render_rich(self) -> ConsoleRenderable:
        """TODO."""
        ignore_case = config.commands.search.ignore_case or self.largs.ignore_case

        tree = RichTree(".", hide_root=True)
        for entry, matches in zip(self.entries, self.matches):
            subtree = tree.add(
                Text.assemble(
                    (entry.label, config.commands.search.highlights.label),
                    f" - {len(matches)} match" + ("es" if len(matches) > 1 else ""),
                )
            )

            for idx, match in enumerate(matches):
                matchtree = subtree.add(str(idx + 1))
                for line in match:
                    line_text = Text(line)
                    line_text.highlight_words(
                        [self.largs.query],
                        config.commands.search.highlights.query,
                        case_sensitive=ignore_case,
                    )
                    matchtree.add(line_text)

        return tree

    def render_textual(self) -> TextualTree[Text]:
        """TODO."""
        ignore_case = config.commands.search.ignore_case or self.largs.ignore_case

        # TODO: figure out how to deal with multi-line tree node contents
        tree: TextualTree[Text] = TextualTree(".")
        tree.show_root = False
        for entry, matches in zip(self.entries, self.matches):
            subtree = tree.root.add(
                Text.assemble(
                    (entry.label, config.commands.search.highlights.label),
                    f" - {len(matches)} match" + ("es" if len(matches) > 1 else ""),
                ),
                # TODO: make configurable
                expand=False,
            )

            for idx, match in enumerate(matches):
                matchtree = subtree.add(
                    str(idx + 1),
                    # TODO: make configurable
                    expand=True,
                )
                for line in match:
                    line_text = Text(line)
                    line_text.highlight_words(
                        [self.largs.query],
                        config.commands.search.highlights.query,
                        case_sensitive=ignore_case,
                    )
                    matchtree.add_leaf(line_text)

        return tree

    def render_porcelain(self) -> List[str]:
        """TODO."""
        output = []
        for entry, matches in zip(self.entries, self.matches):
            title = f"{entry.label}::{len(matches)}"
            output.append(title)

            for idx, match in enumerate(matches):
                for line in match:
                    output.append(f"{idx+1}::" + line.strip())

        return output
