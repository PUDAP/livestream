import unittest
from unittest.mock import patch, MagicMock
import cv2

RTSP_URL = "rtsp://100.125.227.14:8554/livestream"


def capture_snapshot(url, output_name="snapshot.jpg"):
    cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        print("Error: Could not open stream.")
        return False

    ret, frame = cap.read()

    if ret:
        cv2.imwrite(output_name, frame)
        print(f"Snapshot saved as {output_name}")
        cap.release()
        return True
    else:
        print("Error: Could not read frame.")
        cap.release()
        return False


class TestCaptureSnapshot(unittest.TestCase):

    @patch("cv2.imwrite")
    @patch("cv2.VideoCapture")
    def test_successful_capture(self, mock_video_capture, mock_imwrite):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, MagicMock())
        mock_video_capture.return_value = mock_cap

        result = capture_snapshot(RTSP_URL, "snapshot.jpg")

        self.assertTrue(result)
        mock_video_capture.assert_called_once_with(RTSP_URL)
        mock_imwrite.assert_called_once()
        mock_cap.release.assert_called_once()

    @patch("cv2.VideoCapture")
    def test_stream_not_opened(self, mock_video_capture):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap

        result = capture_snapshot(RTSP_URL)

        self.assertFalse(result)
        mock_cap.read.assert_not_called()

    @patch("cv2.imwrite")
    @patch("cv2.VideoCapture")
    def test_frame_read_failure(self, mock_video_capture, mock_imwrite):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (False, None)
        mock_video_capture.return_value = mock_cap

        result = capture_snapshot(RTSP_URL)

        self.assertFalse(result)
        mock_imwrite.assert_not_called()
        mock_cap.release.assert_called_once()

    @patch("cv2.imwrite")
    @patch("cv2.VideoCapture")
    def test_custom_output_name(self, mock_video_capture, mock_imwrite):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, MagicMock())
        mock_video_capture.return_value = mock_cap

        result = capture_snapshot(RTSP_URL, "custom_output.jpg")

        self.assertTrue(result)
        args, _ = mock_imwrite.call_args
        self.assertEqual(args[0], "custom_output.jpg")


if __name__ == "__main__":
    unittest.main()
