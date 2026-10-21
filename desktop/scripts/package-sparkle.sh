#!/usr/bin/env bash
set -euo pipefail
# Args: App, pinned Sparkle distribution, fresh output, private key file, architecture, optional baseline.
app="$1"; tools="$2"; output="$3"; key_file="$4"; architecture="$5"; previous="${6:-}"
[[ "$architecture" == arm64 || "$architecture" == x86_64 || "$architecture" == universal ]]
[[ -d "$app" && -f "$key_file" && ! -e "$output" ]]
version="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' "$app/Contents/Info.plist")"
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
public_key="$(/usr/libexec/PlistBuddy -c 'Print :SUPublicEDKey' "$app/Contents/Info.plist")"
derived_key="$(SPARKLE_KEY_FILE="$key_file" swift - <<'SWIFT'
import Foundation
import CryptoKit
let path = ProcessInfo.processInfo.environment["SPARKLE_KEY_FILE"]!
let value = try String(contentsOfFile: path).trimmingCharacters(in: .whitespacesAndNewlines)
guard let data = Data(base64Encoded: value), data.count == 32 else { fatalError("Expected an Ed25519 seed") }
print(try Curve25519.Signing.PrivateKey(rawRepresentation: data).publicKey.rawRepresentation.base64EncodedString())
SWIFT
)"
[[ "$derived_key" == "$public_key" ]] || { echo 'Sparkle key does not match the App public key.' >&2; exit 1; }
codesign --verify --deep --strict "$app"
mkdir "$output"
staging="$(mktemp -d "$(dirname "$output")/sparkle-stage.XXXXXX")"
suffix="-$architecture"
if [[ "$architecture" == universal ]]; then suffix=""; fi
archive="SmartSearch-v$version$suffix-sparkle.zip"
ditto -c -k --sequesterRsrc --keepParent "$app" "$staging/$archive"
has_baseline=false
if [[ -n "$previous" ]]; then
  [[ -d "$previous" ]]
  shopt -s nullglob
  if [[ "$architecture" == universal ]]; then
    # Universal archives have no architecture suffix; use the exact feed reference.
    old_name="$(python3 - "$previous/appcast-macos-universal.xml" <<'PY'
import sys, xml.etree.ElementTree as ET
from pathlib import PurePosixPath
print(PurePosixPath(ET.parse(sys.argv[1]).find('./channel/item/enclosure').attrib['url']).name)
PY
)"
    old=("$previous/$old_name")
  else
    old=("$previous"/SmartSearch-v*-"$architecture"-sparkle.zip
         "$previous"/SmartSearch-*-macos-"$architecture"-sparkle.zip)
  fi
  [[ ${#old[@]} -eq 1 ]] || { echo 'Expected exactly one verified Sparkle baseline.' >&2; exit 1; }
  cp "${old[0]}" "$staging/"
  has_baseline=true
fi
prefix="https://github.com/konbakuyomu/smartsearch/releases/download/v$version/"
if [[ -n "${SMART_SEARCH_TEST_DOWNLOAD_PREFIX:-}" ]]; then
  [[ "$(/usr/libexec/PlistBuddy -c 'Print :SSUpdateTestBuild' "$app/Contents/Info.plist")" == true ]]
  [[ "$SMART_SEARCH_TEST_DOWNLOAD_PREFIX" == http://127.0.0.1:*/* ]]
  prefix="$SMART_SEARCH_TEST_DOWNLOAD_PREFIX"
fi
"$tools/bin/generate_appcast" --ed-key-file "$key_file" --download-url-prefix "$prefix" \
  --link 'https://github.com/konbakuyomu/smartsearch/releases' --versions "$version" \
  --maximum-versions 1 --maximum-deltas 1 "$staging"
feeds=("$staging"/*.xml)
[[ ${#feeds[@]} -eq 1 ]]
"$tools/bin/sign_update" --verify --ed-key-file "$key_file" "${feeds[0]}"
python3 - "$staging" "$output" "${feeds[0]}" "$version" "$architecture" "$has_baseline" "$prefix" <<'PY'
from pathlib import Path
from urllib.parse import quote, unquote
import re, shutil, sys, xml.etree.ElementTree as ET
stage, output, feed = map(Path, sys.argv[1:4])
version, architecture, baseline, prefix = sys.argv[4:]
suffix = '' if architecture == 'universal' else f'-{architecture}'
ns = 'http://www.andymatuschak.org/xml-namespaces/sparkle'
tree = ET.parse(feed)
items = tree.findall('./channel/item')
current = [i for i in items if i.findtext(f'{{{ns}}}version') == version]
assert len(current) == 1, 'Missing current appcast item'
enclosures = list(current[0].iter('enclosure'))
assert enclosures and (baseline != 'true' or len(enclosures) > 1), 'Expected delta was not generated'
for e in enclosures:
    url = e.attrib['url']
    assert url.startswith(prefix) and e.attrib.get(f'{{{ns}}}edSignature'), 'Untrusted or unsigned enclosure'
    name = unquote(url[len(prefix):])
    assert name and name not in {'.', '..'} and '/' not in name and '\\' not in name
    assert (stage / name).stat().st_size == int(e.attrib['length'])
    delta_from = e.get(f'{{{ns}}}deltaFrom')
    if delta_from is not None:
        assert re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', delta_from) and name.endswith('.delta')
        # Sparkle uses the App name for deltas; both architectures share that name.
        target = f'SmartSearch-v{version}-from-{delta_from}{suffix}.delta'
    else:
        target = f'SmartSearch-v{version}{suffix}-sparkle.zip'
        assert name == target, 'Unexpected full update archive'
    assert not (output / target).exists(), 'Duplicate update artifact'
    shutil.copy2(stage / name, output / target)
    e.set('url', prefix + quote(target))
ET.register_namespace('sparkle', ns)
tree.write(output / f'appcast-macos-{architecture}.xml', encoding='utf-8', xml_declaration=True)
PY
# Renaming delta URLs changes the feed bytes, so sign and verify the final feed.
"$tools/bin/sign_update" --ed-key-file "$key_file" "$output/appcast-macos-$architecture.xml"
"$tools/bin/sign_update" --verify --ed-key-file "$key_file" "$output/appcast-macos-$architecture.xml"
echo "Sparkle $version $architecture packaged; delta baseline=$has_baseline"
