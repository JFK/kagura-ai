# コントリビューションガイドライン

**Kagura AI**プロジェクトにご興味をお持ちいただきありがとうございます！このプロジェクトは、協力を通じて成長していきます。以下のガイドラインに従って、円滑に貢献してください。

---

## Kagura AIの目的とビジョン

Kagura AIは、日本の伝統芸能「神楽（Kagura）」に着想を得たオープンソースのフレームワークです。「神楽」が音楽、舞、儀式を調和させるように、Kagura AIはテクノロジー、データ、エージェントを調和させたシームレスなAIシステムを目指しています。このプロジェクトは以下を目的としています：

- **協力的かつ倫理的で持続可能なAIシステムの構築**
- **最先端のAI技術と人間性・自然との調和の架け橋となる**
- **革新を促進しつつ、調和と尊重のタイムレスな原則を守る**

Kagura AIへの貢献を通じて、技術の進歩と社会的・環境的責任を両立するフレームワークを共に作り上げましょう。

---

## Issueを作成する方法

適切なテンプレートを使用してIssueを作成してください：

- [バグ報告](https://github.com/JFK/kagura-ai/issues/new?template=bug_report.md): プロジェクト内のバグを報告します。
- [機能リクエスト](https://github.com/JFK/kagura-ai/issues/new?template=feature_request.md): 新しい機能や改善案を提案します。
- [タスク](https://github.com/JFK/kagura-ai/issues/new?template=task.md): 特定のタスクを提案または追跡します。
- [ドキュメント改善](https://github.com/JFK/kagura-ai/issues/new?template=documentation_improvement.md): ドキュメントの改善を提案します。
- [質問](https://github.com/JFK/kagura-ai/issues/new?template=question.md): プロジェクトに関する質問をします。

初心者の方は、[Good First Issues](https://github.com/JFK/kagura-ai/issues?q=is%3Aopen+is%3Aissue+label%3A"good+first+issue") を確認し、取り組みやすいタスクから始めてください。

---

## コントリビューションの方法

1. **Issueを確認または作成する**
   - [Issues](https://github.com/JFK/kagura-ai/issues) セクションを確認し、既存のIssueがないか確認します。
   - 該当するIssueがない場合、新しいIssueを作成してください。

2. **リポジトリをフォークし、クローンする**
   - リポジトリをフォークしてローカルにクローンします：
     ```bash
     git clone https://github.com/your-username/kagura-ai.git
     cd kagura-ai
     make sync
     ```

3. **新しいブランチを作成する**
   - 作業用のブランチを作成します：
     ```bash
     git checkout -b feature/your-feature-name
     ```

4. **変更を加える**
   - コードを編集し、変更をローカルで検証します：
     ```bash
     make test
     ```

5. **コミットしてプッシュする**
   - 明確なコミットメッセージを書きます：
     ```bash
     git add .
     git commit -m "Add feature: your-feature-name"
     git push origin feature/your-feature-name
     ```

6. **Pull Requestを作成する**
   - [Pull Requests](https://github.com/JFK/kagura-ai/pulls) セクションで新しいPRを作成します。
   - 変更内容とその目的を詳しく記述してください。

---

## 継続的インテグレーション

GitHub Actionsを使用して、コントリビューションの品質を確保しています。Pull Requestを作成すると、以下のチェックが自動で実行されます：

- **コードフォーマット**: プロジェクトのスタイルガイドに準拠しているか確認。
- **ユニットテスト**: 変更が正しいことを検証。
- **カバレッジレポート**: コードカバレッジが基準を満たしているか確認。

PRを送信する前に、これらのチェックをローカルで通過していることを確認してください。

---

## コーディング標準

- **スタイルガイド**:
  - [PEP 8](https://peps.python.org/pep-0008/) に従ってください。
    ```bash
    make ruff
    ```

- **型チェック**:
  - `pyright` を使用して型の正確性を確認します：
    ```bash
    make right
    ```

---

## テスト

- 新しい機能を追加する場合は、必ず関連するユニットテストを含めてください。
- テストを実行し、コードカバレッジを確認します：
  ```bash
  uv run pytest --cov=kagura
  ```

---

## ドキュメント

- 新しい機能やAPIを追加する場合、`README.md`や`docs/`ディレクトリ内のファイルを更新してください。

---

## Pull Requestのレビュー

- プロジェクトのメンテナーがPRをレビューし、フィードバックを提供します。
- コメントや提案に対応して、変更を最終調整してください。

---

## よくある質問 (FAQ)

### なぜテストが必要なのですか？
テストは、コードベースの安定性と信頼性を確保し、潜在的な問題を早期に検出するために重要です。

### どのようなIssueを作成すればよいですか？
バグ報告、新機能の提案、またはドキュメント改善の提案を歓迎します。

---

## その他のリソース

- [Code of Conduct](./CODE_OF_CONDUCT.md): このプロジェクトで期待される行動規範。
- [Contribution Guide](./CONTRIBUTING.md): 現在のガイドライン。
- [Issues](https://github.com/JFK/kagura-ai/issues): 貢献可能なIssueを確認。

---

**Kagura AI**の改善にご協力いただき、ありがとうございます！一緒に、革新的で倫理的、そして影響力のあるAIフレームワークを作り上げましょう。 😊
