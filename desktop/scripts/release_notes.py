#!/usr/bin/env python3
"""Prepend verified desktop downloads while preserving the existing release notes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from update_artifacts import REPOSITORY, macos_stem, version_tuple, windows_installer

START = "<!-- smart-search-downloads:start -->"
END = "<!-- smart-search-downloads:end -->"


def with_downloads(body: str, version: str, directory: Path, repository: str = REPOSITORY) -> str:
    version_tuple(version)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Invalid release repository")
    entries = [
        ("macOS 13+ 通用版（推荐） / Universal", macos_stem(version, "universal") + ".dmg", "Apple Silicon + Intel"),
        ("macOS 13+ Apple Silicon", macos_stem(version, "arm64") + ".dmg", "M 系列 / Apple M-series"),
        ("macOS 13+ Intel", macos_stem(version, "x86_64") + ".dmg", "Intel Mac"),
        ("Windows x64", windows_installer(version, "x64"), "Intel / AMD 64-bit"),
        ("Windows ARM64", windows_installer(version, "arm64"), "Snapdragon / ARM64"),
    ]
    cli_entries = [(f"{platform} {architecture}", f"smart-search-cli-{version}-{platform}-{architecture}.zip")
                   for platform, architectures in (("macos", ("arm64", "x86_64")), ("windows", ("arm64", "x64")))
                   for architecture in architectures]
    for name in [entry[1] for entry in entries + cli_entries] + ["SHA256SUMS.txt"]:
        if not (directory / name).is_file() or (directory / name).stat().st_size == 0:
            raise ValueError(f"Download asset is missing or empty: {name}")
    signing = [json.loads((directory / f"macos-signing-{arch}.json").read_text())
               for arch in ("universal", "arm64", "x86_64")]
    kinds = {item.get("kind") for item in signing}
    labels = {"self-signed": ("维护者持有的固定自签名证书", "the maintainer's fixed self-signed certificate"),
              "self-signed-test": ("一次性测试证书", "a disposable test certificate"),
              "ad-hoc-test": ("ad-hoc 签名", "ad-hoc signing")}
    if len(kinds) != 1 or next(iter(kinds)) not in labels:
        raise ValueError("Missing or inconsistent macOS signing status")
    kind = next(iter(kinds))
    if kind == "self-signed":
        fingerprints = {item.get("certificate_sha256", "") for item in signing}
        if len(fingerprints) != 1 or not re.fullmatch(r"[0-9A-Fa-f]{64}", next(iter(fingerprints))):
            raise ValueError("macOS release certificates must match")
    signing_zh, signing_en = labels[kind]
    if body.count(START) != body.count(END) or body.count(START) > 1:
        raise ValueError("Release notes contain malformed download markers")
    if START in body:
        start, end = body.index(START), body.index(END)
        if start > end:
            raise ValueError("Release download markers are out of order")
        body = body[:start] + body[end + len(END):]
    base = f"https://github.com/{repository}/releases/download/v{version}/"
    rows = [START, "## 下载 / Downloads", "",
            "| 系统 / System | 下载文件 / Download | 适用设备 / Devices |",
            "| --- | --- | --- |"]
    rows.extend(f"| {system} | [{name}]({base}{name}) | {devices} |" for system, name, devices in entries)
    rows += ["", "### 独立 CLI / Standalone CLI", "",
             "App 通过系统 npm 安装和管理 CLI；以下独立包也可直接用于命令行。App 与 CLI 分别更新。",
             "The App installs and manages the CLI through system npm. These standalone archives also work directly in a terminal.", "",
             "| 系统 / System | CLI |", "| --- | --- |"]
    rows.extend(f"| {system} | [{name}]({base}{name}) |" for system, name in cli_entries)
    rows += ["", "选择与系统对应的安装包；Mac 不确定芯片型号时可选通用版。",
             "Choose the installer for your system; the universal Mac app supports both chip families.", "",
             "### macOS 安装与首次打开", "",
             "1. 下载 DMG 并打开，将 **Smart Search** 拖入 **Applications（应用程序）**，等待复制完成。",
             "2. 从“应用程序”中双击 **Smart Search**，先尝试打开一次。",
             "3. 如果提示无法验证开发者或 Apple 无法检查此 App，在确认文件来自本项目发行页后，打开 **苹果菜单 → 系统设置 → 隐私与安全性**，向下滚动到“安全性”，找到 Smart Search 的拦截提示并点击 **仍要打开**。",
             "4. 按系统要求完成身份验证，在再次出现的提示中点击 **打开**；以后可直接从“应用程序”启动。", "",
             "若未看到“仍要打开”，先再尝试启动 App，然后返回该设置页面。若提示“已损坏”或“将损坏你的电脑”，请先查看[macOS 排障说明](https://github.com/konbakuyomu/smartsearch/blob/main/docs/guide/zh-CN/troubleshooting.md#macos-提示已损坏或无法验证开发者)。", "",
             "### macOS installation and first launch", "",
             "1. Open the downloaded DMG, drag **Smart Search** to **Applications**, and wait for the copy to finish.",
             "2. Double-click **Smart Search** in Applications once to attempt the first launch.",
             "3. If macOS cannot verify the developer or check the app, confirm it came from this project's release page, then open **Apple menu → System Settings → Privacy & Security**. Scroll to Security and click **Open Anyway** beside the Smart Search message.",
             "4. Authenticate if requested, then click **Open** in the confirmation dialog. Future launches can use Applications directly.", "",
             "If Open Anyway is missing, try launching the app again before returning to Settings. For a damaged-app or will-damage-your-computer warning, consult the [macOS troubleshooting guide](https://github.com/konbakuyomu/smartsearch/blob/main/docs/guide/en/troubleshooting.md#macos-says-the-app-is-damaged-or-the-developer-cannot-be-verified) first.", "",
             "[Apple 首次打开说明 / Apple's instructions](https://support.apple.com/102445)", "",
             "Windows：运行对应架构的 Setup。 / Run Setup for your Windows architecture.", "",
             f"Windows 安装包使用项目自签名证书，仍可能显示 SmartScreen 提示；macOS 使用{signing_zh}，尚无 Developer ID 签名或 Apple 公证。",
             f"Windows uses a self-signed certificate and may show SmartScreen prompts. macOS uses {signing_en} without Developer ID or notarization.", "",
             f"文件校验 / Checksums: [SHA256SUMS.txt]({base}SHA256SUMS.txt)。",
             "Sparkle ZIP、NUPKG、XML/JSON 清单和差分包供 App 更新器使用，无需手动下载。",
             "Sparkle ZIPs, NUPKGs, XML/JSON feeds and delta packages are for the in-app updaters.", END]
    return "\n".join(rows) + "\n\n" + body.strip() + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--existing", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repository", default=REPOSITORY)
    args = parser.parse_args()
    args.output.write_text(with_downloads(args.existing.read_text(encoding="utf-8"), args.version,
                                         args.directory, args.repository), encoding="utf-8")
