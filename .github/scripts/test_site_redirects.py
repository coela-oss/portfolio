import unittest
from site_redirects import parse_rules, verify_redirects


class RedirectTests(unittest.TestCase):
    def test_localized_local_and_external_rules_are_verified_without_following(self):
        text = '/old /work 301\n/ja/old /ja/work 301\n/product https://example.org/ 301\n'
        expected = {'/old': '/work', '/ja/old': '/ja/work', '/product': 'https://example.org/'}
        self.assertEqual(verify_redirects('https://portfolio.example', text, lambda source: (301, expected[source])), 3)

    def test_wrong_location_status_and_missing_redirect_are_not_success(self):
        for response in [(200, '/work'), (302, '/work'), (301, '/other'), (404, None)]:
            with self.assertRaises(ValueError):
                verify_redirects('https://portfolio.example', '/old /work 301', lambda source: response)

    def test_open_redirects_chains_duplicates_and_unbounded_rules_are_refused(self):
        for text in ['/old //example.org 301', '/old http://example.org 301',
                     '/old https://user:secret@example.org 301', '/a /b 301\n/b /c 301',
                     '/old /work 301\n/old /about 301', '/old /old 301',
                     '/old /work 200', '/old* /work 301', '/old /work 301\n' * 129]:
            with self.assertRaises(ValueError):
                parse_rules(text)


if __name__ == '__main__':
    unittest.main()
