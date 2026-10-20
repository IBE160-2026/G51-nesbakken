import unittest
from unittest.mock import MagicMock, patch

import requests

from services import fetch_duration_matrix, fetch_route_geometry


def make_mock_response(json_body, status_ok=True):
    mock_response = MagicMock()
    mock_response.json.return_value = json_body
    if status_ok:
        mock_response.raise_for_status = MagicMock()
    return mock_response


class TestFetchDurationMatrix(unittest.TestCase):
    def setUp(self):
        # Bypass the real .env file / API key lookup entirely for these tests.
        patcher = patch("services.get_api_key", return_value="test-api-key")
        self.mock_get_api_key = patcher.start()
        self.addCleanup(patcher.stop)

    def test_coordinates_sent_as_lon_lat_with_start_point_first(self):
        mock_response = make_mock_response({"durations": [[0, 100], [100, 0]]})
        with patch("services.requests.post", return_value=mock_response) as mock_post:
            points = [(-33.90, 151.18), (-33.91, 151.19)]  # (lat, lon) input
            fetch_duration_matrix(points)

            _, kwargs = mock_post.call_args
            sent_locations = kwargs["json"]["locations"]
            # Each location must be [lon, lat], not [lat, lon], and the
            # start point (index 0 of the input) must be locations[0].
            self.assertEqual(sent_locations[0], [151.18, -33.90])
            self.assertEqual(sent_locations[1], [151.19, -33.91])

    def test_uses_the_foot_walking_matrix_endpoint(self):
        mock_response = make_mock_response({"durations": [[0]]})
        with patch("services.requests.post", return_value=mock_response) as mock_post:
            fetch_duration_matrix([(-33.9, 151.18)])
            args, _ = mock_post.call_args
            self.assertEqual(
                args[0], "https://api.openrouteservice.org/v2/matrix/foot-walking"
            )

    def test_sends_authorization_header_with_the_api_key(self):
        mock_response = make_mock_response({"durations": [[0]]})
        with patch("services.requests.post", return_value=mock_response) as mock_post:
            fetch_duration_matrix([(-33.9, 151.18)])
            _, kwargs = mock_post.call_args
            self.assertEqual(kwargs["headers"]["Authorization"], "test-api-key")

    def test_requests_the_duration_metric(self):
        mock_response = make_mock_response({"durations": [[0]]})
        with patch("services.requests.post", return_value=mock_response) as mock_post:
            fetch_duration_matrix([(-33.9, 151.18)])
            _, kwargs = mock_post.call_args
            self.assertEqual(kwargs["json"]["metrics"], ["duration"])

    def test_returns_the_durations_matrix_from_the_response(self):
        mock_response = make_mock_response({"durations": [[0, 5], [5, 0]]})
        with patch("services.requests.post", return_value=mock_response):
            result = fetch_duration_matrix([(-33.9, 151.18), (-33.91, 151.19)])
            self.assertEqual(result, [[0, 5], [5, 0]])

    def test_http_failure_is_raised_not_swallowed(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500")
        with patch("services.requests.post", return_value=mock_response):
            with self.assertRaises(requests.exceptions.HTTPError):
                fetch_duration_matrix([(-33.9, 151.18)])

    def test_missing_durations_key_raises(self):
        mock_response = make_mock_response({"distances": [[0, 10], [10, 0]]})
        with patch("services.requests.post", return_value=mock_response):
            with self.assertRaises(KeyError):
                fetch_duration_matrix([(-33.9, 151.18), (-33.91, 151.19)])


def make_geojson_response(coordinates):
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "LineString", "coordinates": coordinates}}
    ]}


class TestFetchRouteGeometry(unittest.TestCase):
    """Story 1.4. The real request/response shape here was verified
    directly against the live OpenRouteService API before this function was
    written (not assumed) - see the implementation spec's Design Notes."""

    def setUp(self):
        patcher = patch("services.get_api_key", return_value="test-api-key")
        self.mock_get_api_key = patcher.start()
        self.addCleanup(patcher.stop)

    def test_coordinates_sent_as_lon_lat_in_walked_order(self):
        mock_response = make_mock_response(make_geojson_response([[151.18, -33.90]]))
        with patch("services.requests.post", return_value=mock_response) as mock_post:
            points = [(-33.90, 151.18), (-33.91, 151.19), (-33.90, 151.18)]  # start -> stop -> start
            fetch_route_geometry(points)
            _, kwargs = mock_post.call_args
            sent_coords = kwargs["json"]["coordinates"]
            self.assertEqual(sent_coords, [[151.18, -33.90], [151.19, -33.91], [151.18, -33.90]])

    def test_uses_the_geojson_directions_endpoint(self):
        mock_response = make_mock_response(make_geojson_response([[151.18, -33.90]]))
        with patch("services.requests.post", return_value=mock_response) as mock_post:
            fetch_route_geometry([(-33.9, 151.18)])
            args, _ = mock_post.call_args
            self.assertEqual(
                args[0],
                "https://api.openrouteservice.org/v2/directions/foot-walking/geojson",
            )

    def test_sends_authorization_header_with_the_api_key(self):
        mock_response = make_mock_response(make_geojson_response([[151.18, -33.90]]))
        with patch("services.requests.post", return_value=mock_response) as mock_post:
            fetch_route_geometry([(-33.9, 151.18)])
            _, kwargs = mock_post.call_args
            self.assertEqual(kwargs["headers"]["Authorization"], "test-api-key")

    def test_returns_the_linestring_coordinates_from_the_response(self):
        coords = [[151.179, -33.898], [151.180, -33.897], [151.178, -33.898]]
        mock_response = make_mock_response(make_geojson_response(coords))
        with patch("services.requests.post", return_value=mock_response):
            result = fetch_route_geometry([(-33.898, 151.179), (-33.897, 151.180)])
        self.assertEqual(result, coords)

    def test_http_failure_is_raised_not_swallowed(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500")
        with patch("services.requests.post", return_value=mock_response):
            with self.assertRaises(requests.exceptions.HTTPError):
                fetch_route_geometry([(-33.9, 151.18)])

    def test_missing_features_key_raises(self):
        mock_response = make_mock_response({"type": "FeatureCollection"})
        with patch("services.requests.post", return_value=mock_response):
            with self.assertRaises(KeyError):
                fetch_route_geometry([(-33.9, 151.18)])


if __name__ == "__main__":
    unittest.main()
