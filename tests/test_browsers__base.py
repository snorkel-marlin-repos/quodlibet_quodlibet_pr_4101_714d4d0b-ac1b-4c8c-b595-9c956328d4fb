# Copyright 2006 Joe Wreschnig
#           2013 Christoph Reiter
#           2016 Nick Boultbee
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

import os
from gi.repository import Gtk

from quodlibet.browsers._base import FakeDisplayItem as FDI, \
    DisplayPatternMixin, FakeDisplayItem
from tests import TestCase, init_fake_app, destroy_fake_app, mkstemp
from .helper import realized, dummy_path

from quodlibet import browsers
from quodlibet.formats import AudioFile
from quodlibet import config
from quodlibet.browsers import Browser
from quodlibet.library import SongFileLibrary, SongLibrarian


SONGS = [
    AudioFile({
        "title": "one",
        "artist": "piman",
        "~filename": dummy_path(u"/dev/null"),
    }),
    AudioFile({
        "title": "two",
        "artist": "mu",
        "~filename": dummy_path(u"/dev/zero"),
    }),
    AudioFile({
        "title": "three",
        "artist": "boris",
        "~filename": dummy_path(u"/bin/ls"),
    })
]
SONGS.sort()

for song in SONGS:
    song.sanitize()


class TBrowser(TestCase):
    def setUp(self):
        self.browser = Browser()

    def test_can_filter(self):
        for key in ["foo", "title", "fake~key", "~woobar", "~#huh"]:
            self.failIf(self.browser.can_filter(key))

    def test_defaults(self):
        self.failUnless(self.browser.background)
        self.failIf(self.browser.can_reorder)
        self.failIf(self.browser.headers)

    def test_status_bar(self):
        self.assertEqual(self.browser.status_text(1, "21s"),
                         "1 song (21s)")
        self.assertEqual(self.browser.status_text(101, "2:03"),
                         "101 songs (2:03)")

    def tearDown(self):
        self.browser = None


class TBrowserBase(TestCase):
    Kind = None

    def setUp(self):
        config.init()
        init_fake_app()
        self.library = library = SongFileLibrary()
        library.librarian = SongLibrarian()
        library.add(SONGS)
        self.Kind.init(library)
        self.b = self.Kind(library)

    def tearDown(self):
        self.b.destroy()
        self.library.librarian = None
        self.library.destroy()
        config.quit()
        destroy_fake_app()


class TBrowserMixin:

    def test_menu(self):
        # FIXME: the playlist browser accesses the song list directly
        if self.b.name == "Playlists":
            return
        menu = self.b.Menu([], self.library, [])
        self.assertTrue(isinstance(menu, Gtk.Menu))

    def test_key(self):
        self.assertEqual(browsers.get(browsers.name(self.Kind)), self.Kind)

    def test_pack_unpack(self):
        to_pack = Gtk.Button()
        container = self.b.pack(to_pack)
        self.b.unpack(container, to_pack)

    def test_pack_noshow_songpane(self):
        to_pack = Gtk.Button()
        to_pack.hide()
        container = self.b.pack(to_pack)
        self.assertFalse(to_pack.get_visible())
        self.b.unpack(container, to_pack)
        self.assertFalse(to_pack.get_visible())

    def test_name(self):
        self.failIf("_" in self.b.name)
        self.failUnless("_" in self.b.accelerated_name)

    def test_init(self):
        self.Kind.init(self.library)

    def test_active_filter(self):
        with realized(self.b):
            if self.b.active_filter is not None:
                self.b.active_filter(SONGS[0])

    def test_save_restore(self):
        self.b.restore()
        self.b.finalize(True)
        try:
            self.b.save()
        except NotImplementedError:
            pass

    def test_msic(self):
        with realized(self.b):
            self.b.activate()
            self.b.status_text(1000)
            self.b.status_text(1)
            song = AudioFile({"~filename": dummy_path(u"/fake")})
            song.sanitize()
            self.b.scroll(song)

    def test_filters_caps(self):
        with realized(self.b):
            self.failUnless(isinstance(self.b.can_filter_tag("foo"), bool))
            self.failUnless(isinstance(self.b.can_filter_text(), bool))
            self.failUnless(isinstance(self.b.can_filter("foo"), bool))

    def test_filter_text(self):
        with realized(self.b):
            if self.b.can_filter_tag("foo"):
                self.b.filter("foo", ["bar"])
            if self.b.can_filter_tag("(((((##!!!!))),"):
                self.b.filter("(((((##!!!!))),", ["(((((##!!!!))),"])
            if self.b.can_filter_text():
                self.b.filter_text("foo")
                self.b.filter_text("(((((##!!!!))),,,==")

    def test_get_filter_text(self):
        with realized(self.b):
            if self.b.can_filter_text():
                self.assertEqual(self.b.get_filter_text(), u"")
                self.assertTrue(
                    isinstance(self.b.get_filter_text(), str))
                self.b.filter_text(u"foo")
                self.assertEqual(self.b.get_filter_text(), u"foo")
                self.assertTrue(
                    isinstance(self.b.get_filter_text(), str))

    def test_filter_albums(self):
        with realized(self.b):
            if self.b.can_filter_albums():
                self.b.filter_albums([])
                self.b.filter_albums([object])
                self.b.filter_albums(self.library.albums.values())

    def test_filter_other(self):
        with realized(self.b):
            self.b.unfilter()


class TFakeDisplayItem(TestCase):

    def test_call(self):
        self.assertEqual(FDI()("title"), "Title")
        self.assertEqual(FDI()("~title~artist"), "Title - Artist")
        self.assertEqual(FDI(title="foo")("title"), "foo")
        self.assertEqual(FDI(title="f")("~title~artist"), "f - Artist")
        self.assertEqual(FDI()("~#rating"), "Rating")
        self.assertEqual(FDI({"~#rating": 0.5})("~#rating"), 0.5)
        self.assertEqual(FDI()("~#rating:max"), "Rating<max>")

    def test_get(self):
        self.assertEqual(FDI().get("title"), "Title")

    def test_comma(self):
        self.assertEqual(FDI().comma("title"), "Title")
        self.assertEqual(FDI({"~#rating": 0.5}).comma("~#rating"), 0.5)
        self.assertEqual(FDI(title="a\nb").comma("title"), "a, b")


class DummyDPM(DisplayPatternMixin):
    fd, _PATTERN_FN = mkstemp()
    os.close(fd)


class TDisplayPatternMixin(TestCase):
    TEST_PATTERN = u"<~name>: <artist|<artist>|?> [b]<~length>[/b]"

    def setUp(self):
        with open(DummyDPM._PATTERN_FN, "wb") as f:
            f.write(self.TEST_PATTERN.encode("utf-8") + b"\n")

    @classmethod
    def tearDownClass(cls):
        os.unlink(DummyDPM._PATTERN_FN)

    def test_loading_pattern(self):
        dpm = DummyDPM()
        dpm.load_pattern()
        self.failUnlessEqual(dpm.display_pattern_text, self.TEST_PATTERN)

    def test_updating_pattern(self):
        dpm = DummyDPM()
        dpm.load_pattern()
        dpm.update_pattern("static")
        self.failUnlessEqual(
            dpm.display_pattern % FakeDisplayItem(),
            "static")

    def test_markup(self):
        dpm = DummyDPM()
        dpm.load_pattern()
        item = FakeDisplayItem({"~length": "2:34"})
        self.failUnlessEqual(dpm.display_pattern % item,
                             "Name: Artist <b>2:34</b>")


browsers.init()
# create a new test class for each browser
for browser in browsers.browsers:
    cls = TBrowserBase
    name = "TB" + browser.__name__
    new_test = type(name, (TBrowserBase, TBrowserMixin), {})
    new_test.Kind = browser
    globals()[name] = new_test
