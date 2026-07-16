# juice-shop-zap-cicd-lab

DAST（動的アプリケーションセキュリティテスト）を CI/CD パイプラインに組み込む学習用ラボ。
[OWASP Juice Shop](https://github.com/juice-shop/juice-shop)（意図的に脆弱なデモアプリ）を対象に、[OWASP ZAP](https://www.zaproxy.org/) の baseline scan をローカル → GitHub Actions の順に組み込んでいく。

## 安全境界（必読）

- **スキャン対象は常にローカルの使い捨てコンテナ、または自分が管理する検証用インスタンスに限定する**
- 外部サイト・実在の第三者ドメインへのスキャンはこのリポジトリの用途に一切含まない
- GitHub Actions 上でも target は `localhost` またはコンテナ間ネットワークの URL に固定する
- Juice Shop は意図的に脆弱なアプリケーション。学習・検証目的以外での起動、本番相当の環境への配置は行わない

## 運用ルール

**変更は Issue 起票 → 実装 → PR の順で行う**（2026-07-16〜）。Issue一覧・PR一覧に経緯と学びが残っている。過去のつまずき（バグ・設定漏れ）もIssueとして記録している。

## 構成

### Phase 1: ローカル（docker compose）

```bash
# Juice Shop単体起動確認
docker compose up -d juice-shop
curl http://localhost:3000

# ZAP baseline scan実行（レポート出力はファイル名のみ指定 — 絶対パスだと二重化するので注意）
docker compose run --rm zap zap-baseline.py \
  -t http://juice-shop:3000 \
  -r report.html -J report.json -w report.md

# レポート確認
open zap-reports/report.html

# exit codeを確認（0=クリーン, 1=FAIL, 2=WARNのみ, 3=実行失敗）
echo $?
```

`.zap/rules.tsv` でルールごとに IGNORE / WARN / FAIL を上書きできる（フォーマット: `ルールID\tアクション\tURL(任意)\t説明`）。

### Phase 2: GitHub Actions

`.github/workflows/zap-baseline.yml` — push / 手動実行で Juice Shop を起動し ZAP baseline scan を実行する。現状の設定: `allow_issue_writing: true` / `fail_action: true`。

学習ポイント:
- `fail_action` はデフォルト `false`。指摘があってもチェックは緑のまま通る — 明示的に `true` にしないとCIゲートにならない。**ただし何も triage していない生の状態でいきなり true にすると、直せる材料がないまま常に赤くなるだけになる** — 実際にtrueへ切り替えるのは、findings をtriageして`rules.tsv`で判断済みのものを抑制した後が望ましい（ラチェット原則）
- `allow_issue_writing: true` にすると `GITHUB_TOKEN` に `issues: write` 権限が必要（デフォルトでは付与されない）。**明示的な `permissions:` ブロックが無いと403で失敗する**（Issue #8で発覚。GHAS/CodeQLが `actions/missing-workflow-permissions` として事前警告していた）
- `action-baseline` が自動生成するIssueは、ルールID・URL一覧のみでseverity・対応方法が出ない固定テンプレート。開発者・PdMが読める形式への再設計案は [`docs/risk-judgment-criteria-draft.md`](docs/risk-judgment-criteria-draft.md)（Issue #11・#13で実例あり）
- レポートは artifact として自動アップロードされる（Actions タブ→該当run→Artifacts。**ダウンロードは常にzip形式**、GitHub側の固定仕様）

### Phase 3(計画): AWS上のJuice Shop x2

[Issue #4](https://github.com/toxin-don/juice-shop-zap-cicd-lab/issues/4)。AWSアカウントがプロダクトごとに分離された事業会社で、各パイプラインにスキャナを入れ込むメリット/デメリットの検証が目的。**未実行**（レビュー後にPRを起こす）。

### 番外編(計画): apple/containerへの置き換え

[Issue #5](https://github.com/toxin-don/juice-shop-zap-cicd-lab/issues/5)。DockerからApple公式の[container](https://github.com/apple/container) CLIへの置き換え調査。composeに相当する機能が無いため、ZAPとJuice Shop間のネットワーキングを個別に組む必要がある。**準備中**。

## 参考

- [ZAP Docker User Guide](https://www.zaproxy.org/docs/docker/about/)
- [ZAP Baseline Scan](https://www.zaproxy.org/docs/docker/baseline-scan/)
- [zaproxy/action-baseline](https://github.com/zaproxy/action-baseline)
- [OWASP Juice Shop](https://github.com/juice-shop/juice-shop)
- [apple/container](https://github.com/apple/container)
