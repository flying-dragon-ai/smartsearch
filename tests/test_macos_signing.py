"""Exercise real macOS signatures with disposable identities, never maintainer keys."""
import base64
from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import plistlib
import secrets
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "desktop/scripts/macos_signing.py"
spec = importlib.util.spec_from_file_location("macos_signing", SCRIPT)
signing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(signing)
pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="Requires Apple's actual signing tools")


@dataclass(repr=False)
class DisposableIdentity:
    p12: bytes
    password: str
    digest: str

    def __iter__(self):
        return iter((self.p12, self.password, self.digest))

    def __getitem__(self, index):
        return tuple(self)[index]

    def __repr__(self):
        return f"<DisposableIdentity certificate_sha256={self.digest}>"


@pytest.fixture(scope="module")
def identity(tmp_path_factory):
    directory = tmp_path_factory.mktemp("certificates") / "identity"
    password = secrets.token_hex(24)
    digest = signing.create_identity(directory, password)
    return DisposableIdentity((directory / "smart-search.p12").read_bytes(), password, digest)


def make_app(root, version):
    app = root / "Smart Search.app"
    binaries = app / "Contents/MacOS"
    binaries.mkdir(parents=True)
    resources = app / "Contents/Resources"
    resources.mkdir()
    (app / "Contents/Info.plist").write_bytes(plistlib.dumps({
        "CFBundleIdentifier": "com.smartsearch.test.signing", "CFBundleExecutable": "Probe",
        "CFBundleVersion": str(version), "CFBundleShortVersionString": str(version),
        "CFBundlePackageType": "APPL",
    }))
    source = root / "probe.c"
    source.write_text(f"int main(void) {{ return {version}; }}")
    signing.run(["xcrun", "clang", source, "-o", binaries / "Probe"])
    shutil.copy2(binaries / "Probe", resources / "backend")
    (resources / "config.json").write_text('{"fixture":true}')
    return app


def test_identity_survives_version_change_and_relocation(identity, tmp_path):
    before = signing.run(["/usr/bin/security", "list-keychains", "-d", "user"])
    first, second = [make_app(tmp_path / label, version) for label, version in (("old", 1), ("new", 2))]
    with signing.signing_identity(*identity, kind="self-signed-test") as env:
        one = signing.sign_app(first, env=env)
        two = signing.sign_app(second, env=env)
        assert one["designated_requirement"] == two["designated_requirement"]
        signing.run(["/usr/bin/codesign", "--verify", "--test-requirement", "=" + one["designated_requirement"], second])
        assert (first / "Contents/MacOS/Probe").read_bytes() != (second / "Contents/MacOS/Probe").read_bytes()
        copied = tmp_path / "Applications/Smart Search.app"
        signing.run(["ditto", second, copied])
        assert signing.verify_app(copied, identity[2])["certificate_sha256"] == identity[2]
        keychain = Path(env[signing.PREFIX + "SIGNING_KEYCHAIN"])
        assert all(name not in env for name in signing.PRIVATE_VARIABLES)
    assert not keychain.exists()
    assert signing.run(["/usr/bin/security", "list-keychains", "-d", "user"]) == before
    # Recipients can validate the signature after the signing keychain is gone.
    signing.verify_app(copied, identity[2])


def test_rejects_tampered_resources_and_wrong_signer(identity, tmp_path):
    app = make_app(tmp_path, 1)
    with signing.signing_identity(*identity) as env:
        signing.sign_app(app, env=env)
        with pytest.raises(ValueError, match="Wrong or missing"):
            signing.verify_app(app, "0" * 64)
        (app / "Contents/Resources/config.json").write_text('{"tampered":true}')
        with pytest.raises(RuntimeError, match="codesign"):
            signing.verify_app(app, identity[2])


def test_rejects_adhoc_bundle_disguised_as_certificate_signed(identity, tmp_path):
    app = make_app(tmp_path, 1)
    signing.run(["/usr/bin/codesign", "--force", "--deep", "--sign", "-", app])
    with pytest.raises(ValueError, match="Wrong or missing"):
        signing.verify_app(app, identity[2])


def test_verifies_every_architecture_of_a_universal_backend(identity, tmp_path):
    app = make_app(tmp_path / "app", 1)
    other = tmp_path / "other-identity"
    password = secrets.token_hex(24)
    digest = signing.create_identity(other, password)
    with signing.signing_identity(*identity) as first:
        evidence = signing.sign_app(app, env=first)
        with signing.signing_identity((other / "smart-search.p12").read_bytes(), password, digest) as second:
            slices = []
            for architecture, env in (("arm64", first), ("x86_64", second)):
                thin = tmp_path / architecture
                signing.run(["xcrun", "clang", "-arch", architecture, tmp_path / "app/probe.c", "-o", thin])
                signing.run(["codesign", "--force", "--timestamp=none", "--keychain", env[signing.PREFIX + "SIGNING_KEYCHAIN"],
                             "--sign", env[signing.PREFIX + "SIGNING_IDENTITY"], thin])
                slices.append(thin)
            signing.run(["xcrun", "lipo", "-create", *slices, "-output", app / "Contents/Resources/backend"])
        # Seal the modified Resources without repairing its second signer.
        signing.run(["codesign", "--force", "--timestamp=none", "--keychain", first[signing.PREFIX + "SIGNING_KEYCHAIN"],
                     "--sign", first[signing.PREFIX + "SIGNING_IDENTITY"],
                     "--requirements", "=designated => " + evidence["designated_requirement"], app])
        with pytest.raises(ValueError, match="Wrong or missing.*x86_64"):
            signing.verify_app(app, identity[2])


@pytest.mark.parametrize("failure", ("wrong-password", "wrong-fingerprint"))
def test_failed_import_does_not_change_keychains(identity, failure):
    p12, password, digest = identity
    before = signing.run(["/usr/bin/security", "list-keychains", "-d", "user"])
    if failure == "wrong-password":
        password = "wrong"
    else:
        digest = "0" * 64
    with pytest.raises((ValueError, RuntimeError)):
        with signing.signing_identity(p12, password, digest):
            pytest.fail("Invalid identity was imported")
    assert signing.run(["/usr/bin/security", "list-keychains", "-d", "user"]) == before


def test_certificate_name_cannot_replace_the_code_signing_usage(tmp_path):
    password = secrets.token_hex(24)
    env = {**os.environ, "SS_CERT_PASSWORD": password}
    signing.run(["/usr/bin/openssl", "req", "-new", "-x509", "-newkey", "rsa:2048", "-sha256",
                 "-days", "1", "-subj", "/CN=Smart Search macOS Code Signing",
                 "-keyout", tmp_path / "key.pem", "-out", tmp_path / "certificate.pem",
                 "-passout", "env:SS_CERT_PASSWORD"], env=env)
    signing.run(["/usr/bin/openssl", "pkcs12", "-export", "-inkey", tmp_path / "key.pem",
                 "-in", tmp_path / "certificate.pem", "-out", tmp_path / "identity.p12",
                 "-passin", "env:SS_CERT_PASSWORD", "-passout", "env:SS_CERT_PASSWORD"], env=env)
    der = signing.run(["/usr/bin/openssl", "x509", "-in", tmp_path / "certificate.pem", "-outform", "DER"])
    digest = signing.hashlib.sha256(der).hexdigest()
    with pytest.raises(ValueError, match="explicitly permit code signing"):
        with signing.signing_identity((tmp_path / "identity.p12").read_bytes(), password, digest):
            pytest.fail("A display name was accepted as a certificate purpose")


def test_required_mode_never_falls_back_to_generated_identity(tmp_path):
    env = {key: value for key, value in os.environ.items() if not key.startswith(signing.PREFIX)}
    marker = tmp_path / "executed"
    result = subprocess.run([sys.executable, SCRIPT, "run", "--mode", "required", "--", sys.executable,
                             "-c", "from pathlib import Path; Path('" + str(marker) + "').touch()"],
                            env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert not marker.exists()


def test_command_failure_cleans_up_identity_and_hides_secrets(identity):
    before = signing.run(["/usr/bin/security", "list-keychains", "-d", "user"])
    p12, password, digest = identity
    env = {**os.environ, signing.PREFIX + "P12_BASE64": base64.b64encode(p12).decode(),
           signing.PREFIX + "P12_PASSWORD": password, signing.PREFIX + "CERT_SHA256": digest}
    result = subprocess.run([sys.executable, SCRIPT, "run", "--mode", "required", "--", sys.executable,
                             "-c", "import os,sys; assert 'SMART_SEARCH_MACOS_P12_PASSWORD' not in os.environ; sys.exit(7)"],
                            env=env, capture_output=True, text=True)
    assert result.returncode == 7
    assert password not in result.stdout + result.stderr
    assert signing.run(["/usr/bin/security", "list-keychains", "-d", "user"]) == before


def test_certificate_generation_refuses_to_replace_existing_identity(tmp_path):
    directory = tmp_path / "identity"
    directory.mkdir()
    marker = directory / "keep"
    marker.write_text("existing identity")
    with pytest.raises(FileExistsError):
        signing.create_identity(directory, "password")
    assert marker.read_text() == "existing identity"
