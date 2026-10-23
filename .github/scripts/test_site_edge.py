"""Pinned, non-executing edge-transform verification and rejection cases."""
import hashlib
import unittest
from subprocess import CompletedProcess, TimeoutExpired
from unittest.mock import patch
from site_release import edge_hashes, edge_script_digest, origin_html, verify_assets


class EdgeVerificationTests(unittest.TestCase):
    def setUp(self):
        self.source = b'<html><body><main>Approved content</main></body></html>'
        # Synthetic scripts exercise the algorithm without vendoring provider code.
        self.analytics = b'<script src="https://static.cloudflareinsights.com/beacon.min.js/fixture"></script>'
        self.jsd = b"<script>window.__CF$cv$params={r:'0123456789abcdef',t:'MTc5Mjc0MTE4Mw=='};fixture();</script>"
        self.pins = {'analytics': edge_script_digest(self.analytics), 'jsd': edge_script_digest(self.jsd)}

    def inserted(self, tags, source=None):
        return (source or self.source).replace(b'</body>', tags + b'</body>')

    def test_both_exact_pins_work_in_either_order(self):
        for tags in [self.analytics + b'\n' + self.jsd, self.jsd + self.analytics + b'\n']:
            self.assertEqual(origin_html(self.inserted(tags), self.pins), self.source)

    def test_only_request_ray_and_numeric_timestamp_can_vary(self):
        other = self.jsd.replace(b'0123456789abcdef', b'fedcba9876543210').replace(b'MTc5Mjc0MTE4Mw==', b'MTc5Mjc0MTE4NA==')
        self.assertEqual(edge_script_digest(other), self.pins['jsd'])
        for changed in [self.jsd.replace(b'fixture()', b'evil()'), self.jsd.replace(b'MTc5Mjc0MTE4Mw==', b'ZXZpbCgpOw==')]:
            self.assertNotEqual(origin_html(self.inserted(changed), self.pins), self.source)

    def test_unknown_provider_looking_script_is_not_removed(self):
        changed = self.analytics.replace(b'/fixture', b'/unreviewed')
        self.assertNotEqual(origin_html(self.inserted(changed), self.pins), self.source)
        self.assertNotEqual(origin_html(self.inserted(self.analytics), {}), self.source)

    def test_duplicate_and_additional_scripts_remain_a_mismatch(self):
        for tags in [self.analytics * 2, self.jsd * 2, self.analytics + self.jsd + b'<script>evil()</script>']:
            self.assertNotEqual(origin_html(self.inserted(tags), self.pins), self.source)

    def test_changed_content_is_not_concealed_by_approved_scripts(self):
        changed = self.inserted(self.analytics + self.jsd, self.source.replace(b'Approved', b'Changed'))
        self.assertNotEqual(origin_html(changed, self.pins), self.source)

    def test_approved_script_in_other_document_position_is_not_removed(self):
        changed = self.source.replace(b'<body>', b'<body>' + self.analytics)
        self.assertNotEqual(origin_html(changed, self.pins), self.source)

    def test_pins_are_explicit_distinct_hashes_for_known_roles(self):
        for invalid in [[], {'unknown': 'a' * 64}, {'analytics': '*'}, {'analytics': 'a' * 64, 'jsd': 'a' * 64}]:
            with self.assertRaises(ValueError):
                edge_hashes(invalid)

    def test_html_only_verification_still_requires_exact_origin_digest(self):
        live = self.inserted(self.analytics + self.jsd)
        digest = hashlib.sha256(self.source).hexdigest()
        with patch('site_release.subprocess.run', return_value=CompletedProcess([], 0, live)), patch('site_release.time.sleep'):
            verify_assets('https://example.org', {'index.html': digest}, self.pins)
            with self.assertRaises(ValueError):
                verify_assets('https://example.org', {'data.json': digest}, self.pins)

    def test_timeout_is_bounded_and_reported_as_failed_verification(self):
        with patch('site_release.subprocess.run', side_effect=TimeoutExpired('curl', 35)) as run, patch('site_release.time.sleep'):
            with self.assertRaises(ValueError):
                verify_assets('https://example.org', {'index.html': 'a' * 64}, self.pins)
            self.assertEqual(run.call_count, 5)


if __name__ == '__main__':
    unittest.main()
