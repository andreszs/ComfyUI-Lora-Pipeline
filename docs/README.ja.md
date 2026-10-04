<h4 align="center">
  <a href="./README.md">English</a> | <a href="./README.de.md">Deutsch</a> | <a href="./README.es.md">Español</a> | <a href="./README.fr.md">Français</a> | <a href="./README.pt.md">Português</a> | <a href="./README.ru.md">Русский</a> | 日本語 | <a href="./README.ko.md">한국어</a> | <a href="./README.zh.md">中文</a> | <a href="./README.zh-TW.md">繁體中文</a>
</h4>



<p align="center">
  <img alt="Version" src="https://img.shields.io/github/v/tag/andreszs/comfyui-lora-pipeline?label=version" />
  <img alt="Last Commit" src="https://img.shields.io/github/last-commit/andreszs/comfyui-lora-pipeline" />
  <img alt="License" src="https://img.shields.io/github/license/andreszs/comfyui-lora-pipeline" />
</p>
<br />

# ComfyUI LoRA Pipeline

エリアベースの LoRA コンディショニング ラッパーと ComfyUI の LoRA スケジューリング ノード。

---

## 目次

- ✨ [特徴](#features)
- 📦 [インストール](#installation)
- ✅ [推奨設定 (複数エリア/複数科目)](#recommended-setup-multi-area--multi-subject)
- 🔧 [ノード](#nodes)
  - [Conditioning Pipeline (Set Area)](#conditioning-pipeline-set-area)
  - [Conditioning Pipeline (Combine)](#conditioning-pipeline-combine)
  - [ScheduledLoRALoader](#scheduledloraloader)
- 🧩 [オプションの依存関係](#optional-dependencies)
- 🧭 [マルチエリアのワークフロー例](#example-workflow-multi-area-conditioning-pipeline)
- 🖼️ [ギャラリー](#gallery)
- 🚀 [変更履歴](#changelog)
- 💙 [資金とサポート](#funding--support)
- 📄 [ライセンス](#license)

---

## <a id="features"></a>特徴

- 複数の主題および複数地域のプロンプトに対するエリアベースの調整パイプライン。
- 曲線プレビュー出力を備えた 1 ノードのスケジュールされた LoRA 強度制御。
- 複数の分野にわたって一貫した複数の主題の構成を実現するには、[comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio) による **ControlNet + OpenPose を強くお勧めします**。
- ControlNet/OpenPose がないと、複数の主題、複数の領域の合成に一貫性がなくなることが多く、何度も再試行が必要になる場合があります。
- Python のみ: JavaScript やフロントエンドの依存関係は必要ありません。

---

## <a id="installation"></a>インストール

### 要件
- ComfyUI (最近のビルド)
- Python 3.10+
- オプションのノード別依存関係: `matplotlib`

### ステップ

1. このリポジトリのクローンを `ComfyUI/custom_nodes/` に作成します。
2. ComfyUI を再起動します。
3. ノードが `LoRA Pipeline/` の下に表示されることを確認します。

---

## <a id="recommended-setup-multi-area--multi-subject"></a>推奨設定（複数エリア・複数被写体）

- ControlNet OpenPose (推奨): [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio) を使用します。
- グローバル プロンプトは最小限かつ一般的なものにしてください。
- `global_strength` を低く保ちます (経験則: `0.5` 未満)。
- エリアごとの強度、`global_strength`、LoRA の強度のバランスをとります。すべての強みを最大限に発揮しないでください。
- うまく機能したベースライン値の例: `0.75` 付近のエリア強度、`0.90` 付近の LoRA 強度。

---

## <a id="nodes"></a>ノード

| Conditioning Pipeline (Combine) | Conditioning Pipeline (Set Area) | Load LoRA (Scheduled) |
|---|---|---|
| ![Conditioning Pipeline (Combine)](../assets/conditioning_pipeline_combine.png) | ![Conditioning Pipeline (Set Area)](../assets/conditioning_pipeline_set_area.png) | ![Load LoRA (Scheduled)](../assets/scheduled_lora_loader.png) |

### <a id="conditioning-pipeline-set-area"></a>Conditioning Pipeline (Set Area)

エリア条件付きエントリは一度に 1 つずつ定義します。このノードは、幅、高さ、x、y を含む長方形の領域を定義し、チェーンされたコンディショニング パイプラインの一部として、専用のコンディショニング プロンプトと強度をその領域に適用します。

**概要:**
- リージョン/件名プロンプトごとに 1 つのノード インスタンスを使用します。
- 複数のインスタンスをチェーンして、地域の調整パイプラインを構築します。
- 最終的な結合の前に、クリーンなマルチサブジェクト制御を有効にします。

**入力:**
- `conditioning` (`CONDITIONING`、必須)
- `width`、`height`、`x`、`y` (`FLOAT`、正規化された `0.0-1.0`)
- `strength` (`FLOAT`、デフォルトは `1.0`)
- `pipeline_in` (`CONDITIONING_PIPELINE`、オプション)

**出力:**
- `pipeline_out` (`CONDITIONING_PIPELINE`)

**行動メモ:**
- `pipeline_in` が接続されていない場合は、新しいパイプラインを作成します。
- `pipeline_in` が接続されているときに、新しい地域エントリを追加します。
- エントリの順序を維持することで、予測可能な地域スタックを構築できます。
- 領域強度が低いと、全体的な画質は向上しますが、領域ごとの制御権限は低下します。
- global_strength と Create Hook Lora の LoRA 強度を合わせて領域の強度のバランスをとります。

**よくある間違い:**
- 正規化された `0.0-1.0` 値の代わりにピクセル座標を指定します。
- `width`/`height` を `0` 付近に設定して目に見える効果を期待すること。
- 最終パイプラインを `Conditioning Pipeline (Combine)` に渡すのを忘れています。

---

### <a id="conditioning-pipeline-combine"></a>Conditioning Pipeline (Combine)

グローバルなポジティブ/ネガティブ コンディショニングをエリア パイプラインと組み合わせて、地域を意識した出力を実現します。これは、Set Area とともに、複数の LoRA のコア パスであり、サブジェクト/ゾーンごとに個別のコンディショニングを行います。

**概要:**
- 地域パイプラインを最終的な正/負の出力に変換します。
- ローカルの地域制御を追加しながら、グローバル プロンプト コンテキストを保持します。

**入力:**
- `global_positive` (`CONDITIONING`、必須)
- `global_negative` (`CONDITIONING`、必須)
- `pipeline` (`CONDITIONING_PIPELINE`、必須)
- `global_strength` (`FLOAT`、デフォルトは `0.3`)
- `fast_mode` (`BOOLEAN`、デフォルトは `false`)

**出力:**
- `positive_out` (`CONDITIONING`)
- `negative_out` (`CONDITIONING`)
- `areas_out` (`CONDITIONING_AREAS`)

**`areas_out` の詳細:**

`areas_out` は、設定されたエリア領域のリストを構造化データ出力として公開します。各エントリには、`Conditioning Pipeline (Set Area)` を通じてパイプラインで定義された正規化座標（`x`、`y`、`width`、`height`）と `strength` が含まれています。`areas_out` を [ComfyUI-OpenPose-Studio](https://github.com/andreszs/comfyui-openpose-studio) に接続すると、コンディショニングエリアを OpenPose エディターに自動的にミラーリングできます。ポーズの配置は、コンディショニングした正確な領域に合わせて整列されます。この出力は、マスク生成や領域認識型のダウンストリーム処理のためにエリアメタデータを受け入れる他の拡張機能やノードでも使用できます。

**行動メモ:**
- パイプラインが空または無効な場合、出力はグローバル入力にフォールバックし、`areas_out` は空のリストになります。
- 地域エントリを適用してから、カバーされていない地域のデフォルトの結合パスを適用します。
- `global_strength` は、グローバル コンテキストがローカル エリアとどの程度競合するかを制御します。
- global_strength を高くしすぎると、エリアごとのコンディショニングの影響が減少し、画質に悪影響を及ぼす可能性があります。
- 通常、良い結果は、すべての値を最大化するのではなく、全体的な強度とエリアごとの強度および LoRA の強度のバランスを取ることで得られます。
- `fast_mode` は任意で、デフォルトでは無効です。そのため、既存のワークフローは以前の動作を維持します。
- Fast Mode を有効にすると、グローバルなポジティブコンディショニングが各地域のポジティブコンディショニングに連結されます。`global_strength` は無視されず、追加されたグローバル部分だけをスケーリングします。
- 設定された地域がキャンバス全体を覆う場合、Fast Mode は独立したグローバルポジティブパスを省略します。カバーが不完全な場合はグローバルフォールバックを維持するため、速度向上は小さくなります。
- Fast Mode は標準パスと数学的に同一ではなく、プロンプトのバランス、構図、被写体の再現性が変わる可能性があります。本番ワークフローに採用する前に結果を比較してください。

**よくある間違い:**
- ポジティブとネガティブの両方ではなく、1 つのコンディショニング ストリームのみを供給します。
- `global_strength` をオーバードライブし、領域の詳細を洗い流します。
- エリアエントリを構築していますが、結合された出力をサンプラーパスに接続するのを忘れています。

---

### <a id="scheduledloraloader"></a>ScheduledLoRALoader

1 つのクリーンなノードに、一定の強度を持つ 1 つの LoRA または拡散の進行状況に対するスケジュールされたカーブを適用します。

**概要:**
- 複数のネイティブ LoRA/制御ノードの乱雑なチェーンを置き換えます。
- タイミング、補間、プレビューをまとめて維持します。
- 一時的な LoRA 動作のためのよりクリーンなグラフ配線。

**入力:**
- `model` (`MODEL`、必須)
- `clip` (`CLIP`、必須)
- `lora_name` (`STRING`、必須)
- `strength_start`、`strength_end` (`FLOAT`)
- `interpolation` (`STRING`: `linear`、`ease_in`、`ease_out`、`ease_in_out`)
- `start_percent`、`end_percent` (`FLOAT`、`0.0-1.0`)
- `keyframes_count` (`INT`、デフォルトは `4`)
- `apply_to_conds` (`BOOLEAN`、オプション)

**出力:**
- `model` (`MODEL`)
- `clip` (`CLIP`)
- `curve_preview` (`IMAGE`)

**行動メモ:**
- `lora_name` が `None` の場合、モデル/クリップはパススルーされ、プレビューはレンダリングされます。
- 開始強度と終了強度が一致する場合、定数 LoRA アプリケーションのように動作します。
- 曲線プレビューは、完全なレンダリングの前にタイミングを迅速に確認するのに役立ちます。

**よくある間違い:**
- `curve_preview` を使用するときに `matplotlib` を忘れます。
- サンプラーのタイミングの意図と一致しないスケジュール ウィンドウの使用。
- このノードは `CONDITIONING` を直接出力することが期待されます。

---

## <a id="optional-dependencies"></a>オプションの依存関係

ComfyUI が使用するのと同じ Python 環境に、必要なものだけをインストールします。

- `ScheduledLoRALoader` 曲線プレビュー: `python -m pip install matplotlib`

---

## <a id="example-workflow-multi-area-conditioning-pipeline"></a>マルチエリアのワークフロー例

[![完全なワークフロー](../workflows/conditioninig_pipeline_area_wf.png)](../workflows/conditioninig_pipeline_area_wf.png)

このワークフロー イメージを ComfyUI にドラッグ アンド ドロップして、グラフ全体をインポート/ロードできます。

#### エリア1のセットアップ

[![エリア 1 コンディショニング](../assets/conditioninig_area_1.png)](../assets/conditioninig_area_1.png)

- ネイティブ `Create Hook Lora` を使用して 1 つの LoRA をロードし、エリア 1 のエリア プロンプト/コンディショニングを定義します。
- そのコンディショニングを `Conditioning Pipeline (Set Area)` に接続し、その領域の `width`、`height`、`x`、`y`、および `strength` を設定します。

#### エリア2のセットアップ

[![エリア 2 コンディショニング](../assets/conditioninig_area_2.png)](../assets/conditioninig_area_2.png)

- まったく同じパターンを繰り返します (別の `Create Hook Lora` + 別の `Conditioning Pipeline (Set Area)`)。
- 追加の領域に対してこのパターンを繰り返し続けることができます。

#### パイプラインのチェーン化と結合

[![コンディショニングコンバイン](../assets/conditioning_combine.png)](../assets/conditioning_combine.png)

- `pipeline_out` をエリア 1 からエリア 2 にチェーンします (連結されたパイプライン エントリ)。
- 最後のエリアから `pipeline_out` を `Conditioning Pipeline (Combine)` に送信します。これにより、エリア パイプラインがグローバル コンディショニングとマージされます。
- 結合された出力を `KSampler` に直接、または `ControlNet` にルーティングします。この例では、`ControlNet` にルーティングされます。

#### OpenPose / ControlNet のガイダンス

- OpenPose/ControlNet は一般にオプションですが、この特定の複数の被写体、複数のエリアの合成ワークフローでは、一貫した合成を行うために強くお勧めします。
- 同じ作者の [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio) を参照してください (新しいリポジトリ)。

#### グローバル `Styler Pipeline` 配置

[![グローバル `Styler Pipeline` 配置（エリア コンディショニング + ControlNet）](../assets/styler_pipeline_node.png)](../assets/styler_pipeline_node.png)

グローバル スタイルとは、領域ごとのコンディショニングに加えて (またはその代わりに) `Styler Pipeline` を画像全体に 1 回適用することを意味します。

- 一般規則: `Styler Pipeline` を `KSampler` の前に接続します。
- ControlNet を使用する場合、`Styler Pipeline` は ControlNet を適用する前でも、ControlNet を適用した後でも接続できます。
- 実際には、結果は通常同等であるため、グラフ内でより使いやすい配置を選択してください。

#### `global_strength` のトレードオフ

- `global_strength` を増やしすぎると、エリアごとのコンディショニングの相対的な影響が減り、エリアごとの LoRA/スタイルのアイデンティティが弱まる可能性があります。
- グローバル強度が高いと、画質に悪影響を及ぼす可能性もあります。
- `global_strength` を低く保ち、グローバル プロンプトを最小限/一般的なものに保ちます。
- 経験則: 一般に `0.5` 未満の値を使用し (`0.5` までテスト済み)、一般的なガイダンスを超えてグローバルな条件付けに依存することは避けてください。
- LoRA の強度を下げると、LoRA のアイデンティティまたはキャラクターの忠実度が低下する傾向があり、一方、領域の強度を下げると、領域ごとの制御が低下する傾向があります。
- 総合力を高くすると画質が犠牲になる可能性があるため、すべてを最大にすることはお勧めできません。これは、異なる作成者の LoRA を混合する場合に特に当てはまり、品質に一貫性がなくなる可能性があります。
- 複数文字の LoRA の経験則: 可能な場合は、より一貫性のある結合結果を得るために、同じ作成者または同様のトレーニング アプローチによる LoRA を使用します。

---

## <a id="gallery"></a>ギャラリー

| プレビュー | 説明 |
|---------|-------------|
| [![conditioning_pipeline_area](../workflows/conditioninig_pipeline_area.png)](../workflows/conditioninig_pipeline_area.png) | **コンディショニング パイプライン — ControlNet OpenPose**<br><br>ControlNet OpenPose を使用して、LoRA ブリーディングなしで複数の LoRA を含む複数の垂直エリアを示します。<br><br>[comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio) が必要です。 |
| [![conditioning_pipeline_styled](../workflows/conditioninig_pipeline_styled.png)](../workflows/conditioninig_pipeline_styled.png) | **コンディショニング パイプライン — ControlNet とスタイリングを使用したマルチエリア**<br><br>各領域に個別に適用されるエリアごとのスタイルを使用したマルチエリアと複数の LoRA を示します。<br><br>[comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio) と[comfyui-styler-pipeline](https://github.com/andreszs/comfyui-styler-pipeline).<br><br>このワークフローはエリアごとのスタイル設定を使用します。つまり、各エリアには個別に構成された独自のスタイルがあります。 ControlNet の直前に Styler ノードを接続することで、グローバル スタイル設定も可能です。 |

複数の conditioning area、OpenPose、ControlNet、Styler をすべて同時に使用したワークフローは、[こちらの記事](https://www.andreszsogon.com/building-a-multi-character-comfyui-workflow-with-area-conditioning-openpose-control-and-style-layering/)でご覧いただけます。

---

## <a id="changelog"></a>変更履歴

### 1.1.4

- 地域コンディショニングの最適化により、2 地域の SDXL テストワークフローで、測定された生成時間が約 144 秒から 70 秒に短縮されました。レンダリング時間は約 51% 減少しました。
- 任意の Fast Mode は、全体をカバーする同等のテストを約 54 秒で完了しました。以前の実装と比べて最大約 63% の時間短縮です。
- 性能は GPU、モデル、解像度、sampler、ControlNet 設定、地域のカバー範囲によって変わります。Fast Mode は視覚的な差も生じる可能性があるため、デフォルトでは無効です。

---

## <a id="funding--support"></a>資金提供とサポート

### あなたのサポートが重要な理由

このプラグインは独自に開発および保守されており、**有料 AI エージェント**を定期的に使用して、デバッグ、テスト、および生活の質の向上を迅速化します。役に立つと思われる場合は、財政的なサポートが開発を着実に進めるのに役立ちます。

あなたの貢献は次のことに役立ちます。

* より迅速な修正と新機能のために AI ツールに資金を提供する
* ComfyUI アップデート全体にわたる継続的なメンテナンスと互換性作業をカバーします
* 使用制限に達した場合の開発速度の低下を防ぐ

> [!TIP]
> 寄付しませんか？ GitHub のスター ⭐ 可視性を向上させ、より多くのユーザーを支援することで、今でも大いに役立っています

### 💙 このプロジェクトをサポートする

<table style="width: 100%; table-layout: fixed;">
  <tr>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">Ko-fi</h4>
        <a href="https://ko-fi.com/D1D716OLPM" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_kofi.svg" alt="Ko-fi Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="https://ko-fi.com/D1D716OLPM" target="_blank" rel="noopener noreferrer">コーヒーを購入</a></p>
      </div>
    </td>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">PayPal</h4>
        <a href="https://www.paypal.com/ncp/payment/GEEM324PDD9NC" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_paypal.svg" alt="PayPal Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="https://www.paypal.com/ncp/payment/GEEM324PDD9NC" target="_blank" rel="noopener noreferrer">PayPal を開く</a></p>
      </div>
    </td>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">USDC (Arbitrum のみ ⚠️)</h4>
        <a href="https://arbiscan.io/address/0xe36a336fC6cc9Daae657b4A380dA492AB9601e73" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_usdc.svg" alt="USDC Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="#usdc-address">住所を表示</a></p>
      </div>
    </td>
  </tr>
</table>

<details>
  <summary>スキャンをご希望ですか? QR コードを表示</summary>
  <br />
  <table style="width: 100%; table-layout: fixed;">
    <tr>
      <td align="center" style="width: 33.33%; padding: 12px;">
        <strong>Ko-fi</strong><br />
        <a href="https://ko-fi.com/D1D716OLPM" target="_blank" rel="noopener noreferrer">
          <img src="../assets/qr-kofi.svg" alt="Ko-fi QR Code" width="200" />
        </a>
      </td>
      <td align="center" style="width: 33.33%; padding: 12px;">
        <strong>PayPal</strong><br />
        <a href="https://www.paypal.com/ncp/payment/GEEM324PDD9NC" target="_blank" rel="noopener noreferrer">
          <img src="../assets/qr-paypal.svg" alt="PayPal QR Code" width="200" />
        </a>
      </td>
      <td align="center" style="width: 33.33%; padding: 12px;">
        <strong>USDC (Arbitrum) ⚠️</strong><br />
        <a href="https://arbiscan.io/address/0xe36a336fC6cc9Daae657b4A380dA492AB9601e73" target="_blank" rel="noopener noreferrer">
          <img src="../assets/qr-usdc.svg" alt="USDC (Arbitrum) QR Code" width="200" />
        </a>
      </td>
    </tr>
  </table>
</details>

<a id="usdc-address"></a>
<details>
  <summary>USDC アドレスを表示</summary>

```text
0xe36a336fC6cc9Daae657b4A380dA492AB9601e73
```

> [!WARNING]
> USDC は Arbitrum One のみに送信してください。他のネットワークへの送金は届かず、永久に失われる可能性があります。
</details>

## <a id="license"></a>ライセンス

MIT ライセンス - 全文については [LICENSE](../LICENSE) を参照してください。

---

**管理者:** andreszs
**ステータス:** 活発な開発
