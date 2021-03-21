"""Tests for coBib's TUI Buffer."""

import pytest

from cobib.config import config
from cobib.tui import TUI, InputBuffer, TextBuffer

from .mock_curses import MockCursesPad
from .mock_tui import MockTUI


class TestTextBuffer:
    """Tests for coBib's TextBuffer."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup."""
        # pylint: disable=attribute-defined-outside-init
        self.buffer = TextBuffer()

    @pytest.mark.parametrize(
        ["strings", "expected"],
        [
            [[""], {"lines": [], "height": 0, "width": 0, "wrapped": False, "ansi_map": None}],
            [
                ["test"],
                {"lines": ["test"], "height": 1, "width": 4, "wrapped": False, "ansi_map": None},
            ],
            [
                ["test\ntest"],
                {
                    "lines": ["test\ntest"],
                    "height": 1,
                    "width": 9,
                    "wrapped": False,
                    "ansi_map": None,
                },
            ],
            [
                ["test", "test"],
                {
                    "lines": ["test", "test"],
                    "height": 2,
                    "width": 4,
                    "wrapped": False,
                    "ansi_map": None,
                },
            ],
        ],
    )
    def test_write(self, strings, expected):
        """Test write method."""
        for string in strings:
            self.buffer.write(string)
        for key, value in expected.items():
            assert getattr(self.buffer, key) == value

    @pytest.mark.parametrize(
        ["lines", "old", "new", "expected"],
        [
            [0, "test", "tmp", ["tmp0", "test1", "test2"]],
            [[0, 1], "test", "tmp", ["tmp0", "tmp1", "test2"]],
            [[0, 2], "test", "tmp", ["tmp0", "test1", "tmp2"]],
            [[0, 1, 2], "test", "tmp", ["tmp0", "tmp1", "tmp2"]],
        ],
    )
    def test_replace(self, lines, old, new, expected):
        """Test replace method."""
        for string in ["test" + str(num) for num in range(3)]:
            self.buffer.write(string)
        self.buffer.replace(lines, old, new)
        assert self.buffer.lines == expected

    def test_clear(self):
        """Test clear method."""
        self.buffer.lines = ["test"]
        self.buffer.clear()
        assert self.buffer.lines == []
        assert self.buffer.height == 0
        assert self.buffer.width == 0
        assert self.buffer.wrapped is False

    def test_split(self):
        """Test split method."""
        self.buffer.lines = ["test\ntest"]
        self.buffer.split()
        assert self.buffer.lines == ["test", "test"]
        assert self.buffer.height == 2
        assert self.buffer.width == 4

    @pytest.mark.parametrize(
        ["width", "label_column", "expected"],
        [
            [
                20,
                False,
                [
                    "Label0  Title0 by",
                    "↪  Author0",
                    "Label1  Title1 by",
                    "↪  Author1",
                    "Label2  Title2 by",
                    "↪  Author2",
                    "Label3  Title3 by",
                    "↪  Author3",
                    "Label4  Title4 by",
                    "↪  Author4",
                ],
            ],
            [
                20,
                True,
                [
                    "Label0  Title0 by",
                    "↪       Author0",
                    "Label1  Title1 by",
                    "↪       Author1",
                    "Label2  Title2 by",
                    "↪       Author2",
                    "Label3  Title3 by",
                    "↪       Author3",
                    "Label4  Title4 by",
                    "↪       Author4",
                ],
            ],
            [
                6,
                True,
                [
                    "Label",
                    "↪ 0",
                    "↪ Tit",
                    "↪ le0",
                    "↪ by",
                    "↪ Aut",
                    "↪ hor",
                    "↪ 0",
                    "Label",
                    "↪ 1",
                    "↪ Tit",
                    "↪ le1",
                    "↪ by",
                    "↪ Aut",
                    "↪ hor",
                    "↪ 1",
                    "Label",
                    "↪ 2",
                    "↪ Tit",
                    "↪ le2",
                    "↪ by",
                    "↪ Aut",
                    "↪ hor",
                    "↪ 2",
                    "Label",
                    "↪ 3",
                    "↪ Tit",
                    "↪ le3",
                    "↪ by",
                    "↪ Aut",
                    "↪ hor",
                    "↪ 3",
                    "Label",
                    "↪ 4",
                    "↪ Tit",
                    "↪ le4",
                    "↪ by",
                    "↪ Aut",
                    "↪ hor",
                    "↪ 4",
                ],
            ],
        ],
    )
    def test_wrap(self, width, label_column, expected):
        """Test wrap method."""
        self.buffer.lines = [
            "Label0  Title0 by Author0",
            "Label1  Title1 by Author1",
            "Label2  Title2 by Author2",
            "Label3  Title3 by Author3",
            "Label4  Title4 by Author4",
        ]
        self.buffer.wrap(width, label_column)
        for line, truth in zip(self.buffer.lines, expected):
            assert line.strip() == truth

    def test_unwrap(self):
        """Test unwrapping."""
        self.buffer.wrapped = True
        self.buffer.lines = [
            "Label0  Title0 by",
            "↪  Author0",
            "Label1  Title1 by",
            "↪  Author1",
            "Label2  Title2 by",
            "↪  Author2",
            "Label3  Title3 by",
            "↪  Author3",
            "Label4  Title4 by",
            "↪  Author4",
        ]
        self.buffer.wrap(10)
        assert self.buffer.lines == [
            "Label0  Title0 by Author0",
            "Label1  Title1 by Author1",
            "Label2  Title2 by Author2",
            "Label3  Title3 by Author3",
            "Label4  Title4 by Author4",
        ]

    def test_view(self, caplog):
        """Test view method."""
        self.buffer.lines = [
            "Label0  Title0 by Author0",
            "Label1  Title1 by Author1",
            "Label2  Title2 by Author2",
            "Label3  Title3 by Author3",
            "Label4  Title4 by Author4",
        ]
        pad = MockCursesPad()
        self.buffer.view(pad, 10, 40)
        expected_log = [
            ("MockCursesPad", 10, "erase"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 40"),
            ("MockCursesPad", 10, "resize: 1 41"),
            ("MockCursesPad", 10, "addstr: 0 0 Label0  Title0 by Author0"),
            ("MockCursesPad", 10, "addstr: 1 0 Label1  Title1 by Author1"),
            ("MockCursesPad", 10, "addstr: 2 0 Label2  Title2 by Author2"),
            ("MockCursesPad", 10, "addstr: 3 0 Label3  Title3 by Author3"),
            ("MockCursesPad", 10, "addstr: 4 0 Label4  Title4 by Author4"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 40"),
        ]
        assert [
            record for record in caplog.record_tuples if record[0] == "MockCursesPad"
        ] == expected_log

    def test_view_with_box(self, caplog):
        """Test view method with box."""
        self.buffer.lines = [
            "Label0  Title0 by Author0",
            "Label1  Title1 by Author1",
            "Label2  Title2 by Author2",
            "Label3  Title3 by Author3",
            "Label4  Title4 by Author4",
        ]
        pad = MockCursesPad()
        self.buffer.view(pad, 10, 40, box=True)
        expected_log = [
            ("MockCursesPad", 10, "erase"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 40"),
            ("MockCursesPad", 10, "resize: 2 40"),
            ("MockCursesPad", 10, "addstr: 1 1 Label0  Title0 by Author0"),
            ("MockCursesPad", 10, "addstr: 2 1 Label1  Title1 by Author1"),
            ("MockCursesPad", 10, "addstr: 3 1 Label2  Title2 by Author2"),
            ("MockCursesPad", 10, "addstr: 4 1 Label3  Title3 by Author3"),
            ("MockCursesPad", 10, "addstr: 5 1 Label4  Title4 by Author4"),
            ("MockCursesPad", 10, "box"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 40"),
        ]
        assert [
            record for record in caplog.record_tuples if record[0] == "MockCursesPad"
        ] == expected_log

    def test_view_with_ansi_map(self, caplog, monkeypatch):
        """Test view method with ANSI color map."""
        monkeypatch.setattr("curses.color_pair", lambda *args: args)
        # create ANSI color map for testing purposes
        config.defaults()
        ansi_map = {}
        for attr in TUI.COLOR_NAMES:
            ansi_map[config.get_ansi_color(attr)] = TUI.COLOR_NAMES.index(attr) + 1
        # populate buffer
        self.buffer.lines = [
            "\x1b[31;40mLabel0\x1b[0m  Title0 by Author0",
            "\x1b[31;40mLabel1\x1b[0m  Title1 by Author1",
            "\x1b[31;40mLabel2\x1b[0m  Title2 by Author2",
            "\x1b[31;40mLabel3\x1b[0m  Title3 by Author3",
            "\x1b[31;40mLabel4\x1b[0m  Title4 by Author4",
        ]
        pad = MockCursesPad()
        self.buffer.view(pad, 10, 40, ansi_map=ansi_map)
        expected_log = [
            ("MockCursesPad", 10, "erase"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 40"),
            ("MockCursesPad", 10, "resize: 1 41"),
            ("MockCursesPad", 10, "addstr: 0 0 Label0  Title0 by Author0"),
            ("MockCursesPad", 10, "chgat: 0 0 6 (4,)"),
            ("MockCursesPad", 10, "addstr: 1 0 Label1  Title1 by Author1"),
            ("MockCursesPad", 10, "chgat: 1 0 6 (4,)"),
            ("MockCursesPad", 10, "addstr: 2 0 Label2  Title2 by Author2"),
            ("MockCursesPad", 10, "chgat: 2 0 6 (4,)"),
            ("MockCursesPad", 10, "addstr: 3 0 Label3  Title3 by Author3"),
            ("MockCursesPad", 10, "chgat: 3 0 6 (4,)"),
            ("MockCursesPad", 10, "addstr: 4 0 Label4  Title4 by Author4"),
            ("MockCursesPad", 10, "chgat: 4 0 6 (4,)"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 40"),
        ]
        assert [
            record for record in caplog.record_tuples if record[0] == "MockCursesPad"
        ] == expected_log
        for message in ["Interpreting ANSI color codes on the fly.", "Applying ANSI color map."]:
            assert ("cobib.tui.buffer", 10, message) in caplog.record_tuples

    def test_view_with_bkgd(self, caplog, monkeypatch):
        """Test view method with background."""
        monkeypatch.setattr("curses.color_pair", lambda *args: args)
        self.buffer.lines = [
            "Label0  Title0 by Author0",
            "Label1  Title1 by Author1",
            "Label2  Title2 by Author2",
            "Label3  Title3 by Author3",
            "Label4  Title4 by Author4",
        ]
        pad = MockCursesPad()
        self.buffer.view(pad, 10, 40, background=1)
        expected_log = [
            ("MockCursesPad", 10, "erase"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 40"),
            ("MockCursesPad", 10, "resize: 1 41"),
            ("MockCursesPad", 10, "addstr: 0 0 Label0  Title0 by Author0"),
            ("MockCursesPad", 10, "addstr: 1 0 Label1  Title1 by Author1"),
            ("MockCursesPad", 10, "addstr: 2 0 Label2  Title2 by Author2"),
            ("MockCursesPad", 10, "addstr: 3 0 Label3  Title3 by Author3"),
            ("MockCursesPad", 10, "addstr: 4 0 Label4  Title4 by Author4"),
            ("MockCursesPad", 10, "bkgd:   (2,)"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 40"),
        ]
        assert [
            record for record in caplog.record_tuples if record[0] == "MockCursesPad"
        ] == expected_log

    def test_view_with_bkgd_and_box(self, caplog, monkeypatch):
        """Test view method with background and box."""
        monkeypatch.setattr("curses.color_pair", lambda *args: args)
        self.buffer.lines = [
            "Label0  Title0 by Author0",
            "Label1  Title1 by Author1",
            "Label2  Title2 by Author2",
            "Label3  Title3 by Author3",
            "Label4  Title4 by Author4",
        ]
        pad = MockCursesPad()
        self.buffer.view(pad, 10, 40, background=1, box=True)
        expected_log = [
            ("MockCursesPad", 10, "erase"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 40"),
            ("MockCursesPad", 10, "resize: 2 40"),
            ("MockCursesPad", 10, "addstr: 1 1 Label0  Title0 by Author0"),
            ("MockCursesPad", 10, "addstr: 2 1 Label1  Title1 by Author1"),
            ("MockCursesPad", 10, "addstr: 3 1 Label2  Title2 by Author2"),
            ("MockCursesPad", 10, "addstr: 4 1 Label3  Title3 by Author3"),
            ("MockCursesPad", 10, "addstr: 5 1 Label4  Title4 by Author4"),
            ("MockCursesPad", 10, "bkgd:   (2,)"),
            ("MockCursesPad", 10, "box"),
            ("MockCursesPad", 10, "refresh: 0 0 1 0 10 40"),
        ]
        assert [
            record for record in caplog.record_tuples if record[0] == "MockCursesPad"
        ] == expected_log

    @pytest.mark.parametrize(
        ["background"],
        [
            [None],
            [1],
        ],
    )
    def test_popup(self, caplog, monkeypatch, background):
        """Test popup method."""
        monkeypatch.setattr("curses.newpad", lambda *args: MockCursesPad())
        if background is not None:
            monkeypatch.setattr("curses.color_pair", lambda *args: args)
        self.buffer.lines = [
            "Label0  Title0 by Author0",
            "Label1  Title1 by Author1",
            "Label2  Title2 by Author2",
            "Label3  Title3 by Author3",
            "Label4  Title4 by Author4",
        ]
        self.buffer.popup(MockTUI(), background=background)
        expected_log = [
            ("MockCursesPad", 10, "erase"),
            ("MockCursesPad", 10, "refresh: 0 0 16 0 19 40"),
            ("MockCursesPad", 10, "resize: 7 40"),
            ("MockCursesPad", 10, "addstr: 1 1 Label0  Title0 by Author0"),
            ("MockCursesPad", 10, "addstr: 2 1 Label1  Title1 by Author1"),
            ("MockCursesPad", 10, "addstr: 3 1 Label2  Title2 by Author2"),
            ("MockCursesPad", 10, "addstr: 4 1 Label3  Title3 by Author3"),
            ("MockCursesPad", 10, "addstr: 5 1 Label4  Title4 by Author4"),
            ("MockCursesPad", 10, "box"),
            ("MockCursesPad", 10, "refresh: 0 0 16 0 19 40"),
            ("MockCursesPad", 10, "getch"),
            ("MockCursesPad", 10, "clear"),
            ("MockTUI", 10, "resize_handler"),
        ]
        if background is not None:
            expected_log.insert(8, ("MockCursesPad", 10, "bkgd:   (2,)"))
        assert [
            record for record in caplog.record_tuples if record[0] in ("MockCursesPad", "MockTUI")
        ] == expected_log


def test_input_buffer(caplog, monkeypatch):
    """Test the InptBuffer."""
    monkeypatch.setattr("curses.newpad", lambda *args: MockCursesPad())
    buffer = InputBuffer(TextBuffer(), MockTUI())
    buffer.readline()
    expected_log = [
        ("MockCursesPad", 10, "erase"),
        ("MockCursesPad", 10, "refresh: 0 0 16 0 18 40"),
        ("MockCursesPad", 10, "resize: 2 40"),
        ("MockCursesPad", 10, "box"),
        ("MockCursesPad", 10, "refresh: 0 0 16 0 18 40"),
        ("MockTUI", 10, "prompt_handler"),
        ("MockCursesPad", 10, "clear"),
        ("MockTUI", 10, "resize_handler"),
    ]
    assert [
        record for record in caplog.record_tuples if record[0] in ("MockCursesPad", "MockTUI")
    ] == expected_log