※ このディレクトリ内のドキュメントは主に日本語で記載されています。

※ The documents in this directory are primarily written in Japanese.


# memo
## how to publish
1. uv version --bump patch を実行して、バージョンを更新する。
2. コミットして、main ブランチにプッシュする。
4. GitHub のリリースページで、リリースを作成する。タグは `v{version}` とする。pyproject.toml の version と一致させる。
   - タイトルは `v{version}` とする。
   - 説明は、変更点を記載する。
   - 例: `- Update dependencies\n- Fix bugs`        
5. ワークフローが自動実行され、タグ（v0.1.51）と version（0.1.51）の一致確認後に PyPI へ公開される。
