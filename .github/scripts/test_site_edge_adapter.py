"""Local process admission and credential separation around the real provider boundary."""
import unittest
from subprocess import CompletedProcess, TimeoutExpired
from unittest.mock import patch
from site_edge import edge_hashes, origin_html


class EdgeAdapterBoundaryTests(unittest.TestCase):
    def test_cloudflare_credentials_are_not_delegated_to_the_pure_verifier(self):
        with patch.dict('os.environ', {'CLOUDFLARE_API_TOKEN': 'synthetic-not-a-credential'}), patch('site_edge.edge_run', return_value=CompletedProcess([], 0, b'{}')) as run:
            self.assertEqual(edge_hashes({}), {})
            call = run.call_args
            self.assertEqual(set(call.kwargs['env']), {'PATH'})
            self.assertEqual(call.kwargs['timeout'], 10)
            self.assertNotIn('synthetic-not-a-credential', repr((call.args, call.kwargs)))

    def test_oversize_input_is_refused_before_process_launch(self):
        with patch('site_edge.edge_run') as run:
            with self.assertRaises(ValueError):
                origin_html(b'x' * (8 * 1024 * 1024 + 1), {})
            run.assert_not_called()

    def test_provider_process_timeout_is_an_explicit_failed_verification(self):
        with patch('site_edge.edge_run', side_effect=TimeoutExpired('node', 10)):
            with self.assertRaises(ValueError):
                edge_hashes({})
