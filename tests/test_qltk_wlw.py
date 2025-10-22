# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from tests import TestCase
from .helper import locale_numeric_conv

from gi.repository import Gtk

from quodlibet.qltk.wlw import WaitLoadWindow


class TWaitLoadWindow(TestCase):

    class DummyConnector(Gtk.Window):
        count = 0

        def connect(self, *args):
            self.count += 1

        def disconnect(self, *args):
            self.count -= 1

        class Eater:
            def set_cursor(*args):
                pass

        window = Eater()

    def setUp(self):
        self.parent = self.DummyConnector()
        self.wlw = WaitLoadWindow(self.parent, 5, "a test")

    def test_none(self):
        wlw = WaitLoadWindow(None, 5, "a test")
        wlw.step()
        wlw.destroy()

    def test_plurals(self):
        with locale_numeric_conv():
            wlw = WaitLoadWindow(None, 1234, "At %(current)d of %(total)d")
            self.failUnlessEqual(wlw._label.get_text(), "At 0 of 1,234")
            while wlw.current < 1000:
                wlw.step()
            self.failUnlessEqual(wlw._label.get_text(), "At 1,000 of 1,234")

    def test_connect(self):
        self.failUnlessEqual(self.parent.count, 2)
        self.wlw.destroy()
        self.failUnlessEqual(self.parent.count, 0)

    def test_start(self):
        self.failUnlessEqual(self.wlw.current, 0)
        self.failUnlessEqual(self.wlw.count, 5)

    def test_step(self):
        self.failIf(self.wlw.step())
        self.failUnlessEqual(self.wlw.current, 1)
        self.failIf(self.wlw.step())
        self.failIf(self.wlw.step())
        self.failUnlessEqual(self.wlw.current, 3)

    def test_destroy(self):
        self.wlw.destroy()
        self.failUnlessEqual(self.parent.count, 0)

    def tearDown(self):
        self.wlw.destroy()
