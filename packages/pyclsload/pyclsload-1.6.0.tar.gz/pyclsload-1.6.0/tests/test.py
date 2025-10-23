from pathlib import Path
from unittest import TestCase

from pyclsload import load_cls, load_dir


class TestFile(TestCase):
    def test_simple(self):
        cls = load_cls(Path("cls/simple.py"), "SimpleClass")
        self.assertEqual(cls.value, 42)

    def test_args(self):
        cls = load_cls(Path("cls/args.py"), "ArgsClass1", *("cool", 69))
        self.assertEqual(cls.something, "cool")
        self.assertEqual(cls.something_else, 69)

    def test_kwargs(self):
        cls = load_cls(Path("cls/args.py"), "ArgsClass2", *(), very="nice", cafe=0xbabe)
        self.assertEqual(cls.very, "nice")
        self.assertEqual(cls.cafe, 0xbabe)

    def test_static(self):
        cls = load_cls(Path("cls/static.py"), "StaticFunctionClass")
        self.assertEqual(cls.get_value(), 42)

    def test_directory(self):
        classes = load_dir(Path("cls"), {
            "ArgsClass1": {
                "something": "special",
                "something_else": -42,
            },
            "ArgsClass2": {
                "very": "nice",
                "cafe": 0xbabe,
            }
        })
        self.assertEqual(classes["SimpleClass"].value, 42)
        self.assertEqual(classes["ArgsClass1"].something, "special")
        self.assertEqual(classes["ArgsClass1"].something_else, -42)
        self.assertEqual(classes["ArgsClass2"].very, "nice")
        self.assertEqual(classes["ArgsClass2"].cafe, 0xbabe)
        self.assertEqual(classes["StaticFunctionClass"].get_value(), 42)
