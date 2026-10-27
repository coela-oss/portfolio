---
path: "/work/zix-cli"
title: "APIの仕様を、明示的な操作の入口へ。"
summary: "Rustの共通CLIが仕様の選別・照合を担い、プロバイダーが個別の通信と認証を担います。公開バイナリの実行結果から、その境界を説明します。"
kind: "page"
status: "published"
---

## 共通CLIの責務

仕様の読み込み、明示的に選択した操作、元データのhash、プロバイダーの実行契約を分離します。今回の実行ではOpenAPIの合成入力を読み、GET /inspectionの経路情報を取り出しました。

## 公開版の検証

v0.2.2でversion、api project、api routesを実行し、実際の入力と出力をexamples/zixに保持しました。認証情報、外部通信、実データ操作は使っていません。書込み可能範囲を限定したファイルだけを受け入れる動作も確認しています。

