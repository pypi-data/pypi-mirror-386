import unittest
from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

from recordflow.api import record_screen, recording_session


class RecordingSessionTests(unittest.TestCase):
    @patch("recordflow.api.MpdecimateOptimizer")
    @patch("recordflow.api.SegmentedRecorder")
    def test_session_starts_and_stops(self, mock_recorder_cls, mock_optimizer_cls):
        mock_recorder = mock_recorder_cls.return_value
        mock_recorder.session_dir = Path("/tmp/dummy")
        mock_optimizer = mock_optimizer_cls.return_value

        with recording_session() as recorder:
            self.assertIs(recorder, mock_recorder)

        mock_optimizer_cls.assert_called_once()
        mock_recorder_cls.assert_called_once()
        mock_recorder_cls.assert_called_with(ANY, optimizer=mock_optimizer, session_id=None)
        mock_recorder.start.assert_called_once()
        mock_recorder.stop.assert_called_once()

    @patch("recordflow.api.MpdecimateOptimizer")
    @patch("recordflow.api.SegmentedRecorder")
    def test_session_accepts_prebuilt_config(self, mock_recorder_cls, mock_optimizer_cls):
        mock_config = MagicMock()
        mock_config.optimizer_threshold = None

        with recording_session(config=mock_config, optimize=False):
            pass

        mock_optimizer_cls.assert_not_called()
        mock_recorder_cls.assert_called_once()
        _, kwargs = mock_recorder_cls.call_args
        self.assertIs(kwargs["optimizer"], None)


class RecordScreenTests(unittest.TestCase):
    @patch("recordflow.api.time.sleep", autospec=True)
    @patch("recordflow.api.SegmentedRecorder")
    def test_record_screen_returns_session_dir(self, mock_recorder_cls, mock_sleep):
        mock_recorder = mock_recorder_cls.return_value
        mock_recorder.session_dir = Path("/tmp/fake-session")

        session_dir = record_screen(1, optimize=False)

        self.assertEqual(session_dir, mock_recorder.session_dir)
        mock_recorder.start.assert_called_once()
        mock_recorder.stop.assert_called_once()
        mock_sleep.assert_called_once_with(1)

    def test_record_screen_requires_positive_duration(self):
        with self.assertRaises(ValueError):
            record_screen(0)


if __name__ == "__main__":
    unittest.main()
