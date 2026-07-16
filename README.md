# juice-shop-zap-cicd-lab

DAST（動的アプリケーションセキュリティテスト）を CI/CD パイプラインに組み込む学習用ラボ。
[OWASP Juice Shop](https://github.com/juice-shop/juice-shop)（意図的に脆弱なデモアプリ）を対象に、[OWASP ZAP](https://www.zaproxy.org/) の baseline scan をローカル → GitHub Actions の順に組み込んでいく。

## 安全境界（必読）

- **スキャン対象は常にローカルの使い捨てコンテナ、または自分が管理する検証用インスタンスに限定する**
- 外部サイト・実在の第三者ドメインへのスキャンはこのリポジトリの用途に一切含まない
- GitHub Actions 上でも target は `localhost` またはコンテナ間ネットワークの URL に固定する
- Juice Shop は意図的に脆弱なアプリケーション。学習・検証目的以外での起動、本番相当の環境への配置は行わない

## 構成

### Phase 1: ローカル（docker compose）

```bash
# Juice Shop単体起動確認
docker compose up -d juice-shop
curl http://localhost:3000

# ZAP baseline scan実行
docker compose run --rm zap zap-baseline.py \
  -t http://juice-shop:3000 \
  -r /zap/wrk/report.html -J /zap/wrk/report.json -w /zap/wrk/report.md

# レポート確認
open zap-reports/report.html

# exit codeを確認（0=クリーン, 1=FAIL, 2=WARNのみ, 3=実行失敗）
echo $?
```

`.zap/rules.tsv` でルールごとに IGNORE / WARN / FAIL を上書きできる（フォーマット: `ルールID\tアクション\tURL(任意)\t説明`）。

### Phase 2: GitHub Actions

`.github/workflows/zap-baseline.yml` — push / 手動実行で Juice Shop を起動し ZAP baseline scan を実行する。

学習ポイント:
- `zaproxy/action-baseline` の `fail_action` はデフォルト `false`。指摘があってもチェックは緑のまま通る — 明示的に `true` にしないとCIゲートにならない
- `allow_issue_writing` はデフォルト `true`。練習中は issue が積み上がるので `false` 推奨
- レポートは artifact として自動アップロードされる（Actions タブ→該当run→Artifacts）

### Phase 3: クラウド上のインスタンスへのスキャン（設計中）

詳細は個人ノート側で管理。**このリポジトリのワークフローとしては含めない**（対象がクラウド上の固定インスタンスになるため、GitHub Actions の secrets でエンドポイントを管理する形に分離する想定）。

## 参考

- [ZAP Docker User Guide](https://www.zaproxy.org/docs/docker/about/)
- [ZAP Baseline Scan](https://www.zaproxy.org/docs/docker/baseline-scan/)
- [zaproxy/action-baseline](https://github.com/zaproxy/action-baseline)
- [OWASP Juice Shop](https://github.com/juice-shop/juice-shop)
