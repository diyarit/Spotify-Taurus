import importlib.util
import plistlib
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('check_ipa', ROOT / 'scripts/check-safari-ipa.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class IpaVerificationTests(unittest.TestCase):
    def fixture(self, path, missing=None, extension_id='com.spotify.client.TaurusOpenSpotify'):
        base = 'Payload/Spotify.app/'
        host = {'CFBundleIdentifier': 'com.spotify.client', 'CFBundleShortVersionString': '9.1.90', 'CFBundleVersion': '123'}
        extension = dict(host, CFBundleIdentifier=extension_id, CFBundleExecutable='TaurusOpenSpotify', NSExtension={
            'NSExtensionPointIdentifier': 'com.apple.Safari.web-extension',
            'NSExtensionPrincipalClass': 'TaurusSafariWebExtensionHandler'})
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr(base + 'Info.plist', plistlib.dumps(host))
            ext = base + 'PlugIns/TaurusOpenSpotify.appex/'
            archive.writestr(ext + 'Info.plist', plistlib.dumps(extension))
            archive.writestr(ext + 'TaurusOpenSpotify', b'\xcf\xfa\xed\xfe' + b'fixture')
            for source in module.RESOURCES.rglob('*'):
                if source.is_file() and source.name != missing:
                    archive.writestr(ext + source.relative_to(module.RESOURCES).as_posix(), source.read_bytes())

    def test_valid_package_and_missing_or_misidentified_extension(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.ipa'
            self.fixture(path)
            self.assertEqual(module.verify(path)['verification'], 'passed')
            self.fixture(path, missing='content.js')
            with self.assertRaises(KeyError):
                module.verify(path)
            self.fixture(path, extension_id='wrong.bundle.id')
            with self.assertRaises(ValueError):
                module.verify(path)


class SyncTests(unittest.TestCase):
    def test_merge_keeps_extension_and_main_and_aborts_conflicts(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            def git(*args):
                return subprocess.run(['git', *args], cwd=repo, text=True, check=True, capture_output=True).stdout.strip()
            git('init', '-b', 'main')
            git('config', 'user.name', 'Test')
            git('config', 'user.email', 'test@example.invalid')
            (repo / 'shared').write_text('base\n')
            git('add', '.')
            git('commit', '-m', 'base')
            git('branch', 'upstream')
            (repo / 'extension.js').write_text('keep my extension\n')
            git('add', '.')
            git('commit', '-m', 'extension')
            main = git('rev-parse', 'main')
            git('switch', 'upstream')
            (repo / 'shared').write_text('new upstream version\n')
            git('commit', '-am', 'upstream change')
            git('switch', 'main')
            run = lambda: subprocess.run(['bash', str(ROOT / 'scripts/sync-upstream.sh'), 'upstream', 'main', 'sync'], cwd=repo, capture_output=True, text=True)
            self.assertEqual(run().returncode, 0)
            self.assertEqual((repo / 'extension.js').read_text(), 'keep my extension\n')
            self.assertEqual((repo / 'shared').read_text(), 'new upstream version\n')
            self.assertEqual(git('rev-parse', 'main'), main)
            self.assertEqual(run().returncode, 0)  # Repeated runs must also work.
            git('switch', 'main')
            (repo / 'shared').write_text('fork edit\n')
            git('commit', '-am', 'fork change')
            new_main = git('rev-parse', 'main')
            self.assertNotEqual(run().returncode, 0)
            self.assertEqual(git('rev-parse', 'main'), new_main)
            self.assertFalse((repo / '.git/MERGE_HEAD').exists())
            self.assertEqual((repo / 'extension.js').read_text(), 'keep my extension\n')
