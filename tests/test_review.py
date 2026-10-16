import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer
from core import Store, Invalid, Conflict, parse_srt, validate_candidate, view
from server import make_handler

SAMPLE = (Path(__file__).resolve().parents[1] / 'demo' / 'studio-demo.srt').read_text()


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'test.sqlite3'
        self.store = Store(self.path)
        self.doc = self.store.create(SAMPLE, 'test.srt', ['Solara', 'Riverside'])

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def draft(self, index=2):
        return self.store.propose(self.doc['id'], self.doc['revision'], index,
            lambda *_: {'text': 'Press the green button on the Solara panel.', 'model': 'test-adapter', 'elapsed_seconds': 0})

    def test_bom_crlf_and_exact_times_roundtrip(self):
        parsed = parse_srt('\ufeff' + SAMPLE.replace('\n', '\r\n'))
        exported = self.store.export(self.doc['id'], 1)
        self.assertEqual(SAMPLE.strip(), exported['srt'].strip())
        self.assertEqual([(c['start'], c['end']) for c in parsed],
                         [(c['start'], c['end']) for c in parse_srt(exported['srt'])])

    def test_bad_srt_is_rejected(self):
        for text in ['', '1\n00:00:00,000 --> 00:00:00,000\nNo',
                     SAMPLE.replace('00:00:05,500', '00:99:05,500'),
                     SAMPLE.replace('\n2\n', '\n1\n'),
                     SAMPLE.replace('Welcome', '<script>Welcome'),
                     SAMPLE.replace('00:00:13,000', '00:00:02,000')]:
            with self.subTest(text=text[:50]):
                with self.assertRaises(Invalid):
                    parse_srt(text)

    def test_diagnostics_include_overlap_and_speed(self):
        self.assertIn('reading_speed', self.doc['cues'][1]['before']['issues'])
        self.assertIn('long_line', self.doc['cues'][1]['before']['issues'])
        self.assertIn('overlap', self.doc['cues'][3]['before']['issues'])
        self.assertIn('short_duration', self.doc['cues'][3]['before']['issues'])

    def test_proposal_never_exports_until_approved(self):
        draft = self.draft()
        self.assertEqual(SAMPLE.strip(), self.store.export(draft['id'], draft['revision'])['srt'].strip())
        cue = draft['cues'][1]
        approved = self.store.decide(draft['id'], draft['revision'], 2, 'approve', cue['proposal']['text'])
        result = self.store.export(approved['id'], approved['revision'])
        self.assertIn('Press the green button', result['srt'])
        self.assertNotIn('In order to get started', result['srt'])
        self.assertEqual(approved['cues'][1]['original'], self.doc['cues'][1]['original'])
        self.assertEqual(result['audit']['cues'][1]['history'][-1]['action'], 'approved')

    def test_rejection_restore_and_persistence(self):
        draft = self.draft()
        rejected = self.store.decide(draft['id'], draft['revision'], 2, 'reject')
        self.assertIsNone(rejected['cues'][1]['proposal'])
        self.assertEqual(draft['cues'][1]['proposal'], rejected['cues'][1]['history'][0]['proposal'])
        self.assertEqual(SAMPLE.strip(), self.store.export(rejected['id'], rejected['revision'])['srt'].strip())
        draft = self.store.propose(rejected['id'], rejected['revision'], 2,
            lambda *_: {'text': 'Press the green button on the Solara panel.'})
        approved = self.store.decide(draft['id'], draft['revision'], 2, 'approve', draft['cues'][1]['proposal']['text'])
        self.store.close()
        self.store = Store(self.path)
        self.assertEqual(approved['revision'], self.store.get(draft['id'])['revision'])
        restored = self.store.decide(draft['id'], approved['revision'], 2, 'restore')
        self.assertEqual(SAMPLE.strip(), self.store.export(restored['id'], restored['revision'])['srt'].strip())

    def test_stale_revision_and_no_proposal_fail(self):
        draft = self.draft()
        with self.assertRaises(Conflict):
            self.store.decide(draft['id'], 1, 2, 'approve', 'Press Solara.')
        with self.assertRaises(Conflict):
            self.store.export(draft['id'], 1)
        with self.assertRaises(Invalid):
            self.store.decide(draft['id'], draft['revision'], 1, 'approve', 'Hello')

    def test_model_failure_does_not_mutate_review(self):
        def broken(*_):
            raise Invalid('Unavailable model')
        with self.assertRaises(Invalid):
            self.store.propose(self.doc['id'], 1, 2, broken)
        self.assertEqual(1, self.store.get(self.doc['id'])['revision'])
        self.assertIsNone(self.store.get(self.doc['id'])['cues'][1]['proposal'])

    def test_model_returning_after_another_edit_is_stale(self):
        def racing(*_):
            self.store.decide(self.doc['id'], 1, 1, 'reject')
            return {'text': 'Press the green button on the Solara panel.'}
        with self.assertRaises(Conflict):
            self.store.propose(self.doc['id'], 1, 2, racing)
        self.assertIsNone(self.store.get(self.doc['id'])['cues'][1]['proposal'])

    def test_guard_rejects_changed_numbers_terms_or_markup(self):
        for original, candidate, glossary in [
            ('Wait 10 seconds.', 'Wait 1 second.', []),
            ('10 then 20', '20 then 10', []),
            ('Press Solara.', 'Press solar.', ['Solara']),
            ('Hi.', '<img src=x>', []),
            ('Hi.', 'New\n\n1\n00:00:00,000 --> 00:00:01,000\ncue', [])]:
            with self.subTest(candidate=candidate):
                with self.assertRaises(Invalid):
                    validate_candidate(original, candidate, glossary)

    def test_invalid_profile_and_glossary(self):
        for cps in [True, float('nan'), 0, 100]:
            with self.assertRaises(Invalid):
                self.store.create(SAMPLE, 'x', [], cps)
        with self.assertRaises(Invalid):
            self.store.create(SAMPLE, 'x', [''])


class HTTPTests(unittest.TestCase):
    def test_real_http_import_ledger_export_and_origin_guards(self):
        with tempfile.TemporaryDirectory() as temp:
            store = Store(Path(temp) / 'db.sqlite3')
            server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(store))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f'http://127.0.0.1:{server.server_port}'
            def post(path, data, headers=None):
                req = urllib.request.Request(base + path, data=json.dumps(data).encode(),
                    headers={'Content-Type': 'application/json', **(headers or {})})
                return json.load(urllib.request.urlopen(req))
            try:
                doc = post('/api/import', {'source': SAMPLE, 'name': 'http.srt'})
                with urllib.request.urlopen(base + '/api/review?id=' + doc['id']) as response:
                    self.assertIn("frame-ancestors 'none'", response.headers['Content-Security-Policy'])
                    self.assertEqual(doc['id'], json.load(response)['id'])
                self.assertEqual(SAMPLE.strip(), post('/api/export', {'id': doc['id'], 'revision': 1})['srt'].strip())
                for headers in [{'Origin': 'https://evil.example'}, {'Host': 'evil.example'}, {'Sec-Fetch-Site': 'cross-site'}]:
                    with self.assertRaises(urllib.error.HTTPError) as caught:
                        post('/api/import', {'source': SAMPLE}, headers)
                    self.assertEqual(403, caught.exception.code)
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    post('/api/export', {'id': doc['id'], 'revision': 0})
                self.assertEqual(409, caught.exception.code)
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    post('/api/import', {'source': '<script>'})
                self.assertEqual(400, caught.exception.code)
            finally:
                server.shutdown()
                server.server_close()
                store.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
