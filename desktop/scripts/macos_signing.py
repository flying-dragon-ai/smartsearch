#!/usr/bin/env python3
"""Create maintainer-owned identities and scope macOS signing keys to one command.

Follows codex_tweaks' pinned P12 / certificate fingerprint / temporary keychain
pattern. Apple security, codesign, openssl and xcrun are macOS platform tools.
"""
from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
import getpass
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import secrets
import shlex
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
PREFIX = "SMART_SEARCH_MACOS_"
PRIVATE_VARIABLES = (PREFIX + "P12_BASE64", PREFIX + "P12_PASSWORD")
MACHO_MAGICS = {
    b"\xfe\xed\xfa\xce", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe",
    b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca", b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca",
}


def run(argv, *, env=None):
    __tracebackhide__ = True  # pytest must not render password-bearing argv.
    # Never include argv in exceptions: security import accepts its password as
    # an argument. Command output is captured, including private-key tool output.
    try:
        result = subprocess.run([str(arg) for arg in argv], env=env, capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"{Path(argv[0]).name} {argv[1]} timed out") from None
    if result.returncode:
        detail = result.stderr.decode(errors="replace").strip() if Path(argv[0]).name == "codesign" else ""
        raise RuntimeError(f"{Path(argv[0]).name} {argv[1]} failed (exit {result.returncode}): {detail}")
    return result.stdout


def fingerprint(value):
    normalized = value.replace(":", "").strip().upper()
    if not re.fullmatch(r"[0-9A-F]{64}", normalized):
        raise ValueError("A complete macOS certificate SHA-256 fingerprint is required")
    return normalized


def create_identity(directory: Path, password: str):
    """Create once; only encrypted private material survives this operation."""
    __tracebackhide__ = True  # Do not render the password if generation fails.
    if not password:
        raise ValueError("A nonempty P12 password is required")
    directory.mkdir(mode=0o700)  # Deliberately refuse to overwrite an identity.
    with tempfile.TemporaryDirectory(prefix=".generation-", dir=directory) as scratch:
        scratch = Path(scratch)
        config = scratch / "certificate.cnf"
        config.write_text("""[req]
distinguished_name = subject
x509_extensions = signing
prompt = no
[subject]
CN = Smart Search macOS Code Signing
O = Smart Search
[signing]
basicConstraints = critical,CA:FALSE
keyUsage = critical,digitalSignature
extendedKeyUsage = critical,codeSigning
subjectKeyIdentifier = hash
""")
        env = {**os.environ, "SS_CERT_PASSWORD": password}
        run(["/usr/bin/openssl", "req", "-new", "-x509", "-newkey", "rsa:3072", "-sha256",
             "-days", "3650", "-config", config, "-keyout", scratch / "key.pem",
             "-out", scratch / "certificate.pem", "-passout", "env:SS_CERT_PASSWORD"], env=env)
        run(["/usr/bin/openssl", "pkcs12", "-export", "-inkey", scratch / "key.pem",
             "-in", scratch / "certificate.pem", "-out", directory / "smart-search.p12",
             "-passin", "env:SS_CERT_PASSWORD", "-passout", "env:SS_CERT_PASSWORD"], env=env)
        run(["/usr/bin/openssl", "x509", "-in", scratch / "certificate.pem", "-outform", "DER",
             "-out", directory / "smart-search.cer"])
    (directory / "smart-search.p12").chmod(0o600)
    digest = hashlib.sha256((directory / "smart-search.cer").read_bytes()).hexdigest().upper()
    (directory / "smart-search.json").write_text(json.dumps({
        "subject": "CN=Smart Search macOS Code Signing,O=Smart Search",
        "certificate_sha256": digest, "purpose": "macOS code signing; not Sparkle EdDSA",
    }, indent=2) + "\n")
    return digest


@contextmanager
def signing_identity(p12: bytes, password: str, expected: str, *, kind="self-signed"):
    __tracebackhide__ = True  # P12/password values must not appear in test reports.
    expected = fingerprint(expected)
    with tempfile.TemporaryDirectory(prefix="smartsearch-signing-") as temporary:
        directory = Path(temporary)
        keychain = directory / "signing.keychain-db"
        container = directory / "identity.p12"
        certificate = directory / "certificate.pem"
        container.write_bytes(p12)
        container.chmod(0o600)
        try:
            cert_env = {**os.environ, "SS_CERT_PASSWORD": password}
            pem = run(["/usr/bin/openssl", "pkcs12", "-in", container, "-clcerts", "-nokeys",
                       "-passin", "env:SS_CERT_PASSWORD"], env=cert_env)
            certificate.write_bytes(pem)
            der = run(["/usr/bin/openssl", "x509", "-in", certificate, "-outform", "DER"])
            if hashlib.sha256(der).hexdigest().upper() != expected:
                raise ValueError("Imported macOS certificate does not match the pinned SHA-256")
            run(["/usr/bin/openssl", "x509", "-in", certificate, "-checkend", "0", "-noout"])
            description = run(["/usr/bin/openssl", "x509", "-in", certificate, "-text", "-noout"])
            usage = re.search(rb"X509v3 Extended Key Usage:[^\n]*\n[ \t]+([^\r\n]+)", description)
            if not usage or b"Code Signing" not in usage.group(1).split(b", "):
                raise ValueError("The certificate must explicitly permit code signing")
            sha1 = hashlib.sha1(der).hexdigest().upper()
            keychain_password = secrets.token_hex(24)
            run(["/usr/bin/security", "create-keychain", "-p", keychain_password, keychain])
            run(["/usr/bin/security", "set-keychain-settings", "-lut", "21600", keychain])
            run(["/usr/bin/security", "unlock-keychain", "-p", keychain_password, keychain])
            run(["/usr/bin/security", "import", container, "-k", keychain, "-P", password,
                 "-T", "/usr/bin/codesign", "-T", "/usr/bin/security"])
            run(["/usr/bin/security", "set-key-partition-list", "-S", "apple-tool:,apple:,codesign:",
                 "-s", "-k", keychain_password, keychain])
            # Older macOS resolves certificate chains through the search list,
            # even when codesign receives --keychain for identity selection.
            keychains = shlex.split(run(["/usr/bin/security", "list-keychains", "-d", "user"]).decode())
            if str(keychain) not in keychains:
                run(["/usr/bin/security", "list-keychains", "-d", "user", "-s", keychain, *keychains])
            for attempt in range(5):
                available = run(["/usr/bin/security", "find-identity", "-p", "codesigning", keychain]).decode()
                if sha1 in available:
                    break
                if attempt == 4:
                    raise ValueError("The imported macOS signing identity has no discoverable private key")
                time.sleep(1)
            # The final codesign invocation verifies usability; no global trust
            # settings or login/system keychain identities are changed.
            container.unlink()
            env = {key: value for key, value in os.environ.items() if key not in PRIVATE_VARIABLES}
            env.update({PREFIX + "CERT_SHA256": expected, PREFIX + "SIGNING_IDENTITY": sha1,
                        PREFIX + "SIGNING_KEYCHAIN": str(keychain), PREFIX + "SIGNING_KIND": kind,
                        PREFIX + "SIGNING_MODE": "required"})
            yield env
        finally:
            if keychain.exists():
                run(["/usr/bin/security", "delete-keychain", keychain])


def signing_context(env=None):
    env = os.environ if env is None else env
    expected = fingerprint(env.get(PREFIX + "CERT_SHA256", ""))
    identity = env.get(PREFIX + "SIGNING_IDENTITY", "")
    keychain = env.get(PREFIX + "SIGNING_KEYCHAIN", "")
    if not re.fullmatch(r"[0-9A-F]{40}", identity) or not keychain or not Path(keychain).is_file():
        raise ValueError("Required macOS signing identity is missing; use the with-signing task")
    if env.get(PREFIX + "SIGNING_KIND") not in {"self-signed", "self-signed-test"}:
        raise ValueError("Unknown macOS signing identity kind")
    return expected, identity, keychain


def code_objects(app: Path):
    """Enumerate real code, including PyInstaller libraries in Resources."""
    objects = []
    for path in app.rglob("*"):
        if path.is_symlink():
            continue
        if path.is_file():
            with path.open("rb") as stream:
                if stream.read(4) in MACHO_MAGICS:
                    objects.append(path)
        elif path.suffix in {".app", ".xpc", ".framework"}:
            objects.append(path)
    return sorted(objects, key=lambda path: (-len(path.parts), str(path))) + [app]


def designated_requirement(path: Path):
    result = subprocess.run(["/usr/bin/codesign", "--display", "-r", "-", str(path)],
                            capture_output=True, text=True, check=True)
    for line in (result.stdout + result.stderr).splitlines():
        if line.startswith("designated => "):
            return line.removeprefix("designated => ")
    raise ValueError("The code has no explicit stable designated requirement")


def bundle_info(path: Path):
    location = "Resources/Info.plist" if path.suffix == ".framework" else "Contents/Info.plist"
    return plistlib.loads((path / location).read_bytes())


def sign_app(app: Path, *, env=None):
    env = os.environ if env is None else env
    expected, identity, keychain = signing_context(env)
    bundle_id = bundle_info(app)["CFBundleIdentifier"]
    for path in code_objects(app):
        identifier = bundle_info(path)["CFBundleIdentifier"] if path.is_dir() else bundle_id + "." + path.relative_to(app).as_posix()
        # A certificate-based DR stays stable when code or version changes.
        requirement = f'designated => identifier {json.dumps(identifier)} and certificate leaf = H"{identity}"'
        run(["/usr/bin/codesign", "--force", "--timestamp=none", "--keychain", keychain,
             "--sign", identity, "--identifier", identifier, "--requirements", "=" + requirement, path], env=env)
    result = verify_app(app, expected)
    result["kind"] = env[PREFIX + "SIGNING_KIND"]
    return result


def verify_app(app: Path, expected: str):
    expected = fingerprint(expected)
    run(["/usr/bin/codesign", "--verify", "--deep", "--strict", "--all-architectures", app])
    objects = code_objects(app)
    with tempfile.TemporaryDirectory(prefix="smartsearch-public-cert-") as temporary:
        for index, path in enumerate(objects):
            run(["/usr/bin/codesign", "--verify", "--strict", "--all-architectures", path])
            binary = path
            if path.is_dir():
                executable = bundle_info(path)["CFBundleExecutable"]
                binary = path / executable if path.suffix == ".framework" else path / "Contents/MacOS" / executable
            architectures = run(["xcrun", "lipo", "-archs", binary]).decode().split()
            for architecture in architectures:
                prefix = Path(temporary) / f"{index}-{architecture}-"
                run(["/usr/bin/codesign", "--display", "--arch", architecture, f"--extract-certificates={prefix}", path])
                certificate = Path(str(prefix) + "0")
                if not certificate.is_file() or hashlib.sha256(certificate.read_bytes()).hexdigest().upper() != expected:
                    raise ValueError(f"Wrong or missing macOS signing certificate: {path.name} ({architecture})")
    requirement = designated_requirement(app)
    if "cdhash" in requirement or "certificate leaf" not in requirement:
        raise ValueError("The App must have a stable certificate-based designated requirement")
    return {"certificate_sha256": expected, "designated_requirement": requirement,
            "verified_code_objects": len(objects)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    create = commands.add_parser("create", help="Generate the maintainer's identity once, outside the repository")
    create.add_argument("directory", type=Path)
    execute = commands.add_parser("run", help="Run a command with a scoped signing identity")
    execute.add_argument("--mode", choices=("required", "test"), required=True)
    execute.add_argument("command", nargs=argparse.REMAINDER)
    sign = commands.add_parser("sign")
    sign.add_argument("app", type=Path)
    sign.add_argument("--result", type=Path, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("app", type=Path)
    verify.add_argument("--certificate-sha256", required=True)
    commands.add_parser("preflight")
    args = parser.parse_args()
    if sys.platform != "darwin":
        parser.error("macOS signing requires macOS and its command-line tools")
    if args.action == "create":
        directory = args.directory.expanduser().resolve()
        if directory == ROOT or ROOT in directory.parents:
            parser.error("Keep the signing identity outside the repository")
        password = os.environ.get(PREFIX + "P12_PASSWORD") or getpass.getpass("New P12 password: ")
        digest = create_identity(directory, password)
        print(f"Identity created at {directory}\nCertificate SHA-256: {digest}\nBack up the P12 and password separately.")
    elif args.action == "run":
        command = args.command[1:] if args.command[:1] == ["--"] else args.command
        if not command:
            parser.error("A command is required after --")
        with tempfile.TemporaryDirectory(prefix="smartsearch-test-identity-") as temporary:
            if args.mode == "test":
                directory = Path(temporary) / "identity"
                password = secrets.token_hex(32)
                digest = create_identity(directory, password)
                container = (directory / "smart-search.p12").read_bytes()
            else:
                password = os.environ.get(PREFIX + "P12_PASSWORD", "")
                encoded = os.environ.get(PREFIX + "P12_BASE64", "")
                digest = os.environ.get(PREFIX + "CERT_SHA256", "")
                if not password or not encoded or not digest:
                    parser.error("Formal signing requires P12_BASE64, P12_PASSWORD and CERT_SHA256; see docs/macos-signing.md")
                container = base64.b64decode("".join(encoded.split()), validate=True)
            with signing_identity(container, password, digest,
                                  kind="self-signed-test" if args.mode == "test" else "self-signed") as env:
                result = subprocess.run(command, env=env)
            return result.returncode
    elif args.action == "sign":
        args.result.write_text(json.dumps(sign_app(args.app), indent=2) + "\n")
    elif args.action == "verify":
        print(json.dumps(verify_app(args.app, args.certificate_sha256), indent=2))
    else:
        signing_context()
    return 0


def interrupt(signum, _frame):
    # Ensure the keychain context also unwinds on CI/terminal termination.
    raise SystemExit(128 + signum)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, interrupt)
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"macOS signing failed: {error}", file=sys.stderr)
        sys.exit(1)
