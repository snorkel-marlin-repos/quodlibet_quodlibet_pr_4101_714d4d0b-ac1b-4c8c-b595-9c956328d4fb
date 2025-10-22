# Copyright 2017 Christoph Reiter
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

import os

from gi.repository import Gtk
from senf import fsnative

from quodlibet.qltk.chooser import choose_files, get_current_dir, \
    set_current_dir, choose_folders, create_chooser_filter, \
    choose_target_file, choose_target_folder, with_response
from quodlibet.qltk import gtk_version
from quodlibet.util import is_osx, is_wine

from . import TestCase, skipIf


@skipIf(is_wine(), "hangs under wine")
@skipIf(gtk_version < (3, 16, 0) or is_osx(), "crashy on older gtk+ and macOS")
class Tchooser(TestCase):

    def test_choose_files(self):
        w = Gtk.Window()
        with with_response(Gtk.ResponseType.CANCEL):
            assert choose_files(w, u"title", u"action") == []

    def test_choose_folders(self):
        w = Gtk.Window()
        with with_response(Gtk.ResponseType.CANCEL):
            assert choose_folders(w, u"title", u"action") == []

    def test_choose_filter(self):
        cf = create_chooser_filter(u"filter", ["*.txt"])
        assert isinstance(cf, Gtk.FileFilter)
        assert cf.get_name() == u"filter"

        w = Gtk.Window()
        with with_response(Gtk.ResponseType.CANCEL):
            assert choose_files(w, u"title", u"action", cf) == []

    def test_choose_target_file(self):
        w = Gtk.Window()
        with with_response(Gtk.ResponseType.CANCEL):
            assert choose_target_file(w, u"title", u"action") is None
        with with_response(Gtk.ResponseType.CANCEL):
            assert choose_target_file(
                w, u"title", u"action", u"example") is None

    def test_choose_target_folder(self):
        w = Gtk.Window()
        with with_response(Gtk.ResponseType.CANCEL):
            assert choose_target_folder(w, u"title", u"action") is None
        with with_response(Gtk.ResponseType.CANCEL):
            assert choose_target_folder(
                w, u"title", u"action", u"example") is None

    def test_get_current_dir(self):
        path = get_current_dir()
        assert isinstance(path, fsnative)

    def test_set_current_dir(self):
        set_current_dir(fsnative(u"."))
        assert get_current_dir() == os.getcwd()
