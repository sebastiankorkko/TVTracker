import unittest
import os
import sys
import datetime
from contextlib import contextmanager
from io import StringIO
from unittest import mock
import tvTracker


TEST_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


class Test_TvTracker(unittest.TestCase):

    def test_EmptyFile(self):
        tvt = tvTracker.TvTracker(os.path.join(TEST_ROOT, "empty_tv_shows.json"))
        self.assertDictEqual(tvt.tvShows, {})

    def test_SingleShowNoEpisodesCorrupt(self):
        tvt = tvTracker.TvTracker(os.path.join(TEST_ROOT, "single_show_no_episodes_corrupt.json"))
        self.assertRaises(Exception)

    def test_SingleShowNoEpisodes(self):
        tvt = tvTracker.TvTracker(os.path.join(TEST_ROOT, "single_show_no_episodes.json"))
        with captured_output() as(out, err):
            tvt.printSchedule()
            output = out.getvalue()
        self.assertEqual(output, "")

    @mock.patch("tvTracker.input", return_value="")
    def test_DeleteOptionsPrinted(self, mock_input):
        tvt = tvTracker.TvTracker(os.path.join(TEST_ROOT, "single_show_no_episodes.json"))
        with captured_output() as(out, err):
            tvt.deleteTvShow()
            output = out.getvalue()
        self.assertIn("ID: 82", output)

    @mock.patch("tvTracker.input", return_value=82)
    @mock.patch("tvTracker.TvTracker.removeTvShow")
    def test_RemoveTvShowCalled(self, mock_input, mock_remove):
        tvt = tvTracker.TvTracker(os.path.join(TEST_ROOT, "single_show_no_episodes.json"))
        tvt.deleteTvShow()
        self.assertTrue(mock_remove.call_count, 1)

    def test_SingleShowMultipleEpisodes(self):
        tvt = tvTracker.TvTracker(os.path.join(TEST_ROOT, "single_show_multiple_episodes.json"))
        date = datetime.date.today() + datetime.timedelta(days=5)
        tvt.tvShows["329"]["nextAirdate"] = date.strftime("%Y-%m-%d")
        with captured_output() as(out, err):
            tvt.printSchedule()
            output = out.getvalue()
        self.assertIn(date.strftime("%Y-%m-%d"), output)
        self.assertIn("Shark Tank", output)

    def test_MultipleShowMultipleEpisodes(self):
        tvt = tvTracker.TvTracker(os.path.join(TEST_ROOT, "multiple_show_multiple_episodes.json"))
        date = datetime.date.today() + datetime.timedelta(days=5)
        tvt.tvShows["329"]["nextAirdate"] = date.strftime("%Y-%m-%d")
        tvt.tvShows["73"]["nextAirdate"] = date.strftime("%Y-%m-%d")
        with captured_output() as(out, err):
            tvt.printSchedule()
            output = out.getvalue()
        self.assertIn(date.strftime("%Y-%m-%d"), output)
        self.assertIn("Shark Tank", output)
        self.assertIn("The Walking Dead", output)

    def test_na_AirdateNotPrinted(self):
        tvt = tvTracker.TvTracker(os.path.join(TEST_ROOT, "single_show_multiple_episodes.json"))
        tvt.tvShows["329"]["nextAirdate"] = "n/a"
        with captured_output() as(out, err):
            tvt.printSchedule()
            output = out.getvalue()
        self.assertNotIn("Shark Tank", output)

    def test_None_AirdateNotPrinted(self):
        tvt = tvTracker.TvTracker(os.path.join(TEST_ROOT, "single_show_multiple_episodes.json"))
        tvt.tvShows["329"]["nextAirdate"] = None
        with captured_output() as(out, err):
            tvt.printSchedule()
            output = out.getvalue()
        self.assertNotIn("Shark Tank", output)

    @mock.patch("tvTracker.TvTracker.updateTvShows")
    def testUpdateNeeded_oldEpisode(self, mock_update):
        date = datetime.date.today() - datetime.timedelta(days=1)
        tvt = tvTracker.TvTracker(os.path.join(TEST_ROOT, "single_show_multiple_episodes.json"))
        tvt.tvShows["329"]["episodes"][0]["airdate"] = date.strftime("%Y-%m-%d")
        tvt.checkUpdates()
        self.assertEqual(mock_update.call_count, 1)

    @mock.patch("tvTracker.TvTracker.updateTvShows")
    def testUpdateNeeded_upcomingEpisode(self, mock_update):
        date = datetime.date.today() + datetime.timedelta(days=1)
        fetchDate = datetime.date.today() - datetime.timedelta(days=2)
        tvt = tvTracker.TvTracker(os.path.join(TEST_ROOT, "single_show_multiple_episodes.json"))
        tvt.tvShows["329"]["episodes"][0]["airdate"] = date.strftime("%Y-%m-%d")
        tvt.tvShows["329"]["lastFetch"] = fetchDate.strftime("%Y-%m-%d")
        tvt.checkUpdates()
        mock_update.assert_called_with([])

    @mock.patch("tvTracker.TvTracker.updateTvShows")
    def testUpdateNeeded_todayEpisode(self, mock_update):
        date = datetime.date.today()
        fetchDate = datetime.date.today() - datetime.timedelta(days=5)
        tvt = tvTracker.TvTracker(os.path.join(TEST_ROOT, "single_show_multiple_episodes.json"))
        tvt.tvShows["329"]["episodes"][0]["airdate"] = date.strftime("%Y-%m-%d")
        tvt.tvShows["329"]["lastFetch"] = fetchDate.strftime("%Y-%m-%d")
        tvt.checkUpdates()
        mock_update.assert_called_with([])

    @mock.patch("tvTracker.TvTracker.updateTvShows")
    def testUpdateNeeded_oldLastFetch(self, mock_update):
        date = datetime.date.today()
        fetchDate = datetime.date.today() - datetime.timedelta(days=6)
        tvt = tvTracker.TvTracker(os.path.join(TEST_ROOT, "single_show_multiple_episodes.json"))
        tvt.tvShows["329"]["episodes"][0]["airdate"] = date.strftime("%Y-%m-%d")
        tvt.tvShows["329"]["lastFetch"] = fetchDate.strftime("%Y-%m-%d")
        tvt.checkUpdates()
        mock_update.assert_called_with(["329"])





@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err
