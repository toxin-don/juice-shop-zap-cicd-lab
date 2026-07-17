#!/usr/bin/env python3
"""ZAPのreport.jsonを開発者・PdMが読めるMarkdown形式に整形するスクリプト。

Issue #11 対応: 現状の`zaproxy/action-baseline`が自動生成するIssue（Issue #10参照）は
ルールID・URL一覧のみでseverity・対応方法が無い固定テンプレート。
report.jsonには実際には riskdesc（重要度）・desc（事象）・solution（対応方法）が
含まれているため、これらを使って docs/risk-judgment-criteria-draft.md の
Afterフォーマットに沿ったMarkdownを自動生成する。

使い方:
    python3 scripts/format_report.py [report.jsonのパス]

    パスを省略した場合は `zap-reports/report.json` を読む。

標準ライブラリのみを使用（外部依存なし）。
"""
import html
import json
import re
import sys

# riskcode: ZAPの数値表現による技術的重要度（Issue #11の仕様）
RISKCODE_LABELS = {
    "3": "High",
    "2": "Medium",
    "1": "Low",
    "0": "Informational",
}

DEFAULT_REPORT_PATH = "zap-reports/report.json"


def strip_html(raw: str) -> str:
    """report.json内のHTML断片（desc/solution等）をプレーンテキスト化する。

    - <p>や<br>は段落・改行として扱う
    - それ以外のタグは除去
    - HTMLエンティティ（&amp;等）はデコードする
    - 連続する空行は1行にまとめる
    """
    if not raw:
        return ""

    text = raw
    # 段落・改行タグを改行に変換（タグ除去前に処理しないと構造が失われる）
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\s*>", "\n\n", text)
    text = re.sub(r"(?i)<li\s*>", "- ", text)
    text = re.sub(r"(?i)</li\s*>", "\n", text)
    # 残りのタグをすべて除去
    text = re.sub(r"<[^>]+>", "", text)
    # HTMLエンティティをデコード
    text = html.unescape(text)
    # 行末の余分な空白を除去しつつ、3行以上の空行を2行に圧縮
    lines = [line.rstrip() for line in text.splitlines()]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def severity_label(riskcode: str) -> str:
    return RISKCODE_LABELS.get(str(riskcode), f"Unknown({riskcode})")


def format_alert(alert: dict) -> str:
    name = alert.get("name") or alert.get("alert", "(名称不明)")
    riskcode = alert.get("riskcode", "")
    riskdesc = alert.get("riskdesc", "")
    desc = strip_html(alert.get("desc", ""))
    solution = strip_html(alert.get("solution", ""))
    instances = alert.get("instances", [])
    uris = [i.get("uri", "") for i in instances if i.get("uri")]

    lines = [f"## [{severity_label(riskcode)}] {name}", ""]
    lines.append(f"**リスク評価**: {riskdesc}")
    lines.append("")
    lines.append("**事象**:")
    lines.append(desc if desc else "(記載なし)")
    lines.append("")
    lines.append(f"**影響箇所**（該当URL全件・{len(uris)}件）:")
    if uris:
        for uri in uris:
            lines.append(f"- {uri}")
    else:
        lines.append("- (記載なし)")
    lines.append("")
    lines.append("**対応方法**:")
    lines.append(solution if solution else "(記載なし)")
    lines.append("")

    return "\n".join(lines)


def load_alerts(report_path: str) -> list:
    with open(report_path, encoding="utf-8") as f:
        data = json.load(f)

    alerts = []
    for site in data.get("site", []):
        alerts.extend(site.get("alerts", []))
    return alerts


def main() -> int:
    report_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_REPORT_PATH

    try:
        alerts = load_alerts(report_path)
    except FileNotFoundError:
        print(f"エラー: {report_path} が見つかりません。", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"エラー: {report_path} のJSONパースに失敗しました: {e}", file=sys.stderr)
        return 1

    if not alerts:
        print("# ZAP Scan結果\n\n検出されたアラートはありませんでした。")
        return 0

    # riskcodeの高い順（3=High → 0=Informational）にソート
    alerts.sort(key=lambda a: int(a.get("riskcode", 0)), reverse=True)

    print("# ZAP Scan結果（開発者・PdM向け）")
    print()
    print(f"検出件数: {len(alerts)}件（重要度の高い順）")
    print()
    print(
        "> severityはZAPの汎用判定であり、実際の優先度・対応要否は開発者・PdMが"
        "事業文脈を踏まえて最終判断する（詳細: `docs/risk-judgment-criteria-draft.md`）。"
    )
    print()

    for alert in alerts:
        print(format_alert(alert))
        print("---")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
