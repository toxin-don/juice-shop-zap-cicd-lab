# リスク判断基準 たたき台

> **これはJuice Shop（練習用の脆弱アプリ）への当てはめであり、GA（あるいはどの事業会社）の実際の判断基準そのものではない。** 実際の基準は、各社が自社プロダクトの特性（扱うデータ、認証モデル、事業影響）に基づいて決めるもの。ここではその「決め方の型」を試作する。

## 問題

ZAPのようなDASTツールが出すseverity（Medium/Low等）は**技術的な脆弱性としての深刻度**であり、**そのプロダクトにとっての事業リスク**とは別物。CORS全開放は公開APIなら許容、認証Cookieが絡めば重大——同じ技術的所見でも文脈で意味が変わる。

かつ、実際に直すかどうかを決めるのは開発者・PdMであり、セキュリティ担当でもDASTツールでもない。**このドキュメント/レポートの読者は彼らである**、という前提でフォーマットを設計する必要がある。

## 判断の軸（叩き台）

技術的severityに、以下4つの事業文脈の軸を掛け合わせて「初期判断（人間が最終決定する前段階の目安）」を出す:

| 軸 | 問い |
|---|---|
| **到達性** | 認証なしで外部から到達できるか？ 社内限定か？ |
| **データ・機能への影響** | 個人情報・決済・認証情報など機微なデータ/機能に関わるか？ |
| **悪用の容易さ** | 専門知識なしで自動化ツールで大量に突けるか？ 手動の高度な技術が要るか？ |
| **事業影響** | ブランド毀損・規制対象・契約上のSLA違反につながるか？ |

## Juice Shop 8件への当てはめ（練習用・イメージ）

| 検出 | 技術的severity | 到達性 | データ影響 | 悪用容易さ | 初期判断（例） |
|---|---|---|---|---|---|
| Content Security Policy (CSP) Header Not Set | Medium | 外部到達可 | XSS経由で認証情報を含む全データに波及しうる | 中（既存XSSと組み合わせて悪用） | 直すべき。ただしCSP設計は影響範囲が広く、Report-Onlyでの段階導入を推奨（2026-07-16調査済み） |
| Cross-Domain Misconfiguration（CORS全開放） | Medium | 外部到達可 | **認証Cookieを使うエンドポイントに掛かっているかで評価が反転**（要確認） | 低〜中 | 認証系エンドポイントへの影響を確認してから判断。公開APIのみなら許容可 |
| COOP/COEP Header Missing | Low | 外部到達可 | 限定的（クロスオリジン分離の弱体化） | 低 | 多くの本番サイトも未対応。優先度は下げてよいことが多い |
| Dangerous JS Functions（1件） | Low | 該当箇所依存 | 中身次第（eval等の使用箇所を要確認） | 中 | 件数が少ないので中身を実際に読んで判断（自動判定に頼らない） |
| Deprecated Feature Policy Header Set | Low | 外部到達可 | 低（新しいPermissions-Policyへの移行漏れ） | 低 | 技術的負債。緊急ではない |
| Timestamp Disclosure - Unix | Low | 外部到達可 | 低（情報漏洩としては軽微） | 低 | 定番のノイズ寄り所見。優先度低 |

**注**: 「初期判断」列はあくまで一次的な目安。**最終的に直すかどうかは、この表を見た開発者・PdMが決める**。

## レポートフォーマットの再設計（開発者・PdM向け）

現状の `zaproxy/action-baseline` が自動生成するIssueは、ルールID・URL一覧のみでseverityも対応方法も出ない（[Issue #10の実例](https://github.com/toxin-don/juice-shop-zap-cicd-lab/issues/10)参照）。`report.json` には実は `riskdesc`（severity）と `solution`（対応方法）が含まれているため、これを使って再構成すれば改善できる。

**標準の裏付け（OWASP WSTG v4.2「Reporting」）**: 脆弱性1件ごとの記載項目として「参照ID / タイトル / 尤度・悪用可能性 / システムへの影響 / リスク評価(Info〜Critical) / 詳細な説明 / 修復手順 / 追加リソース」を規定。「エンジニアが行動できるほど十分な情報を」と明記されている。

### Before（現状のIssue）
```
Content Security Policy (CSP) Header Not Set [10038] total: 5
- http://localhost:3000
- http://localhost:3000/
...
```

### After（案・開発者/PdMが読める形。2026-07-17改訂: 曖昧表現・断定・雑な1行を廃止）

```
## Content Security Policy (CSP) Header Not Set

**リスク評価**: Medium（ZAPの汎用判定。ただし下記「注記」参照）

**事象（何が起きるか）**:
CSP（Content-Security-Policy）ヘッダーが設定されていない。CSPはXSS（クロスサイトスクリプティング）が
発生した場合に、どのドメインのスクリプト・スタイル・画像等の読み込みを許可するかをブラウザに指示する
仕組み。これが無いこと自体が直接の侵入経路になるわけではない。**もしこのアプリの他の場所にXSSの
脆弱性が存在した場合、CSPがあれば被害（悪意あるスクリプトの実行）を軽減・阻止できたはずだが、
無いため軽減されない**、という「保険が掛かっていない」状態。

**注記（severityについて正直に）**: ZAPの「Medium」判定はこのアプリの実際の攻撃対象面を考慮しない
汎用ルールに基づく。CSP単体は「守りの層が1つ足りない」状態であり、それ自体が悪用可能な脆弱性ではない。
実際の深刻度は「このアプリに現に悪用可能なXSSが存在するか」に依存するため、CSP未設定を見つけたら
併せてXSS脆弱性の有無も確認するのが筋。XSSが見つからない前提では、Medium表示より優先度を下げて
判断してよい可能性がある。

**影響箇所**（該当URL全件）:
- http://localhost:3000
- http://localhost:3000/
- http://localhost:3000/ftp
- http://localhost:3000/ftp/eastere.gg
- http://localhost:3000/sitemap.xml

**対応方法**:
1. まずは `Content-Security-Policy-Report-Only` ヘッダーで導入し、実際にどのリソース読み込みが
   ポリシー違反として検知されるかを本番トラフィックで観測する（いきなり `Content-Security-Policy`
   で強制適用すると、既存の正当な機能が壊れるリスクがある）
2. 違反レポートを一定期間（数週間〜）収集し、正当な読み込み元をすべて許可リストに反映する
3. 違反が収束したら `Content-Security-Policy`（enforcing）に切り替える
4. 最小構成の例: `default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:;`
   （実際のアプリが使う外部リソース・インラインスクリプトの有無によって調整が必要）

**参考**:
- [OWASP CSP Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)
- [MDN: Content-Security-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP)
- [ZAP Alert詳細 (10038)](https://www.zaproxy.org/docs/alerts/10038/)

このまま様子見でよいか、対応が必要かはチームで判断してください。
```

**変更点（本人指摘への対応）**:
1. 「5箇所（トップページ含む）」という曖昧な要約をやめ、**該当URL全件を列挙**
2. 「XSS攻撃の被害範囲が広がる」という煽り気味の一文をやめ、**CSPは"保険の層"であり単体では悪用可能な脆弱性ではないこと・severityが汎用ルールに基づく点を正直に注記**（「本当にMediumなのか」への回答: 文脈次第で下がりうる、と明記）
3. 「ヘッダーを設定する」という雑な1行をやめ、**Report-Only段階導入の手順・ポリシー例・参考リンクまで含めた実行可能な内容に拡張**（1行に収めることにはこだわらない）

## 次のアクション（叩き台）

- [x] `report.json` を読んで上記Afterフォーマットで整形するスクリプト（Issue自動作成 or PRコメント）を作る → `scripts/format_report.py`（Issue #11）
- [ ] 4つの判断軸を、実際のプロダクト特性に合わせてGA（または任意の事業会社）向けに再定義する ← **ここは本人が決める領域**
