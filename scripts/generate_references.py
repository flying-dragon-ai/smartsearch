"""Refresh both handbook references from the public parser and config metadata."""
from __future__ import annotations

import argparse
from pathlib import Path

from smart_search.cli import build_parser
from smart_search.i18n import use_language
from smart_search.ui_metadata import CONFIG_FIELDS, SECTIONS

ROOT = Path(__file__).resolve().parents[1]


def command_pages(parser):
    yield parser, []
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            visited = set()
            for child in action.choices.values():
                if id(child) not in visited:
                    visited.add(id(child))
                    aliases = [name for name, value in action.choices.items() if value is child][1:]
                    for nested, names in command_pages(child):
                        yield nested, aliases if nested is child else names


def reference_pages(language):
    zh = language == "zh"
    folder, other = ("zh-CN", "en") if zh else ("en", "zh-CN")
    def navigation(page):
        return (f"[手册目录](../README.md) · [English](../{other}/{page}.md)" if zh else
                f"[Guide](../README.md) · [简体中文](../{other}/{page}.md)")

    with use_language(language):
        parts = [navigation("cli-reference"), "# 完整命令参考" if zh else "# Complete command reference",
                 ("由当前命令解析器生成。用法示例和退出码见 [CLI 使用指南](cli.md)。`--lang` 可放在命令前或子命令后；`--` 后面的文字按原始参数处理。" if zh else
                  "Generated from the current command parser. See the [CLI guide](cli.md) for examples and exit codes. Put `--lang` before or after the command; text following `--` remains a literal argument.")]
        for parser, aliases in command_pages(build_parser()):
            parts.append(f"## `{parser.prog}`")
            if aliases:
                parts.append(("别名：" if zh else "Aliases: ") + ", ".join(f"`{name}`" for name in aliases))
            parts.append("```text\n" + parser.format_help().rstrip() + "\n```")
            defaults = [f"`{' / '.join(action.option_strings)}` = `{action.default}`"
                        for action in parser._actions if action.option_strings and action.default not in (None, argparse.SUPPRESS)
                        and action.dest not in {"help", "version"} and action.help != argparse.SUPPRESS]
            if defaults:
                parts.append(("解析器默认值：" if zh else "Parser defaults: ") + "; ".join(defaults) + ".")
        yield ROOT / "docs/guide" / folder / "cli-reference.md", "\n\n".join(parts) + "\n"

    parts = [navigation("configuration-reference"), "# 当前配置项" if zh else "# Active configuration keys",
             ("由当前配置元数据生成。下表列出当前使用的配置键；旧向量/分类字段仍可保存但已退役，不参与执行。申请 Key、配置优先级、运行环境变量及最低能力要求见[配置指南](configuration.md)。未设置的密钥必须由用户提供；可选服务未配置时不会自动启用。" if zh else
              "Generated from current configuration metadata. Active keys appear below. Retired embedding/classifier fields remain storable but are not executed. See the [configuration guide](configuration.md) for key registration, precedence, runtime environment variables, and the minimum capability profile. Supply your own credentials; unconfigured optional providers are not enabled automatically.")]
    for section in SECTIONS:
        fields = [item for item in CONFIG_FIELDS if item.section == section.id]
        if not fields:
            continue
        parts.append("## " + getattr(section, f"label_{language}"))
        rows = ["| 配置键 | 用途及条件 | 类型 / 取值 | 默认值 |\n| --- | --- | --- | --- |" if zh else
                "| Key | Purpose and conditions | Type / values | Default |\n| --- | --- | --- | --- |"]
        for item in fields:
            help_text = getattr(item, f"help_{language}") or getattr(item, f"label_{language}")
            help_text = help_text.replace("|", "\\|").replace("\n", " ")
            kind = ", ".join(item.choices) if item.choices else item.kind
            default = f"`{item.default}`" if item.default != "" else ("未设置" if zh else "Not set")
            rows.append(f"| `{item.key}` | {help_text} | `{kind}` | {default} |")
        parts.append("\n".join(rows))
    yield ROOT / "docs/guide" / folder / "configuration-reference.md", "\n\n".join(parts) + "\n"


if __name__ == "__main__":
    for language in ("en", "zh"):
        for path, text in reference_pages(language):
            path.write_text(text, encoding="utf-8")
            print(path.relative_to(ROOT))
