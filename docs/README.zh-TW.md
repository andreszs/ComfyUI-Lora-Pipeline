<h4 align="center">
  <a href="./README.md">English</a> | <a href="./README.de.md">Deutsch</a> | <a href="./README.es.md">Español</a> | <a href="./README.fr.md">Français</a> | <a href="./README.pt.md">Português</a> | <a href="./README.ru.md">Русский</a> | <a href="./README.ja.md">日本語</a> | <a href="./README.ko.md">한국어</a> | <a href="./README.zh.md">中文</a> | 繁體中文
</h4>




<p align="center">
  <img alt="Version" src="https://img.shields.io/github/v/tag/andreszs/comfyui-lora-pipeline?label=version" />
  <img alt="Last Commit" src="https://img.shields.io/github/last-commit/andreszs/comfyui-lora-pipeline" />
  <img alt="License" src="https://img.shields.io/github/license/andreszs/comfyui-lora-pipeline" />
</p>
<br />

# ComfyUI LoRA Pipeline

基於區域的 LoRA 調節包裝器和 ComfyUI 的 LoRA 調度節點。

---

## 目錄

- ✨ [功能](#features)
- 📦 [安裝](#installation)
- ✅ [建議設定（多區域/多主題）](#recommended-setup-multi-area--multi-subject)
- 🔧 [節點](#nodes)
  - [Conditioning Pipeline (Set Area)](#conditioning-pipeline-set-area)
  - [Conditioning Pipeline (Combine)](#conditioning-pipeline-combine)
  - [ScheduledLoRALoader](#scheduledloraloader)
- 🧩 [可選依賴項](#optional-dependencies)
- 🧭 [多區域範例工作流程](#example-workflow-multi-area-conditioning-pipeline)
- 🖼️ [圖庫](#gallery)
- 💙 [資金與支持](#funding--support)
- 📄 [許可證](#license)

---

## <a id="features"></a>特徵

- 用於多主題和多區域提示的基於區域的調節管道。
- 帶有曲線預覽輸出的單節點預定 LoRA 強度控制。
- 為了在多個領域實現一致的多主題構圖，強烈建議透過 [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio) **ControlNet + OpenPose**。
- 如果沒有ControlNet/OpenPose，多主體多區域構圖通常會不一致，並且可能需要多次重試。
- 僅限 Python：不需要 JavaScript 或前端相依性。

---

## <a id="installation"></a>安裝

### 要求
- ComfyUI（最新版本）
- Python 3.10+
- 可選的每個節點依賴項：`matplotlib`

### 步驟

1. 將此儲存庫克隆到 `ComfyUI/custom_nodes/` 中。
2. 重新啟動 ComfyUI。
3. 確認節點出現在 `LoRA Pipeline/` 下。

---

## <a id="recommended-setup-multi-area--multi-subject"></a>建議設定（多區域/多主題）

- 使用 ControlNet OpenPose （建議）：[comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio)。
- 保持全域提示最小化和通用。
- 保持 `global_strength` 較低（經驗法則：低於 `0.5`）。
- 平衡單位面積強度、`global_strength` 和 LoRA 強度；不要最大化所有的力量。
- 效果良好的基線值範例：`0.75` 周圍的區域強度、`0.90` 周圍的 LoRA 強度。

---

## <a id="nodes"></a>節點

| Conditioning Pipeline (Combine) | Conditioning Pipeline (Set Area) | Load LoRA (Scheduled) |
|---|---|---|
| ![Conditioning Pipeline (Combine)](../assets/conditioning_pipeline_combine.png) | ![Conditioning Pipeline (Set Area)](../assets/conditioning_pipeline_set_area.png) | ![Load LoRA (Scheduled)](../assets/scheduled_lora_loader.png) |

### <a id="conditioning-pipeline-set-area"></a>Conditioning Pipeline (Set Area)

一次定義一個區域條件條目。此節點定義一個具有寬度、高度、x 和 y 的矩形區域，然後將專用的調節提示和強度作為鍊式調節管道的一部分應用於該區域。

**概覽：**
- 每個區域/主題提示使用一個節點實例。
- 連結多個實例以建立區域調節管道。
- 在最終組合之前實現乾淨的多主體控制。

**輸入：**
- `conditioning`（`CONDITIONING`，必填）
- `width`、`height`、`x`、`y`（`FLOAT`，標準化 `0.0-1.0`）
- `strength`（`FLOAT`，預設 `1.0`）
- `pipeline_in`（`CONDITIONING_PIPELINE`，可選）

**輸出：**
- `pipeline_out` (`CONDITIONING_PIPELINE`)

**行為注意事項：**
- 如果 `pipeline_in` 未連接，則建立新管道。
- 連接 `pipeline_in` 時附加新的區域條目。
- 保持條目有序，以便您可以建立可預測的區域堆疊。
- 較低的區域強度通常會提高整體影像質量，但會降低每個區域的控制權限。
- 平衡區域強度以及 global_strength 和 Create Hook Lora 中的 LoRA 強度。

**常見錯誤：**
- 提供像素座標而不是標準化的 `0.0-1.0` 值。
- 將 `width`/`height` 設定為接近 `0` 並期待可見的效果。
- 忘記將最終管道傳遞到 `Conditioning Pipeline (Combine)` 中。

---

### <a id="conditioning-pipeline-combine"></a>Conditioning Pipeline (Combine)

將全局正/負調節與區域管道結合，以實現區域感知輸出。與設定區域一起，這是多 LoRA 和每個主題/區域單獨調節的核心路徑。

**概覽：**
- 將您的區域管道轉換為最終的正/負輸出。
- 保留全域提示上下文，同時新增本機區域控制。

**輸入：**
- `global_positive`（`CONDITIONING`，必填）
- `global_negative`（`CONDITIONING`，必填）
- `pipeline`（`CONDITIONING_PIPELINE`，必填）
- `global_strength`（`FLOAT`，預設 `0.3`）

**輸出：**
- `positive_out` (`CONDITIONING`)
- `negative_out` (`CONDITIONING`)
- `areas_out` (`CONDITIONING_AREAS`)

**`areas_out` 詳情：**

`areas_out` 將已配置的區域清單作為結構化資料輸出公開。每個條目包含透過 `Conditioning Pipeline (Set Area)` 在管道中定義的歸一化座標（`x`、`y`、`width`、`height`）和 `strength`。將 `areas_out` 連接到 [ComfyUI-OpenPose-Studio](https://github.com/andreszs/comfyui-openpose-studio)，即可將您的調節區域自動鏡像到 OpenPose 編輯器中——姿態放置將與您調節的確切區域對齊。此輸出也可被接受區域元資料的任何其他擴充功能或節點使用，用於遮罩生成或區域感知的下游處理。

**行為注意事項：**
- 如果管道為空/無效，輸出將回落到全域輸入，且 `areas_out` 為空清單。
- 套用區域條目，然後對未覆蓋區域套用預設組合通道。
- `global_strength` 控制全球背景與局部區域競爭的強度。
- 將 global_strength 推得太高會減少每個區域的調節效果並對影像品質產生負面影響。
- 好的結果通常來自於平衡全局強度與單位面積強度和 LoRA 強度，而不是最大化所有值。

**常見錯誤：**
- 僅饋送一種調節流，而不是同時饋送正流和負流。
- 過度駕駛 `global_strength` 並清除區域細節。
- 建置區域條目，但忘記將組合輸出連接到取樣器路徑。

---

### <a id="scheduledloraloader"></a>ScheduledLoRALoader

在一個乾淨的節點中，應用一個具有恆定強度的 LoRA 或擴散進度的預定曲線。

**概覽：**
- 取代多個本機 LoRA/控制節點的混亂鏈。
- 將計時、插值和預覽結合在一起。
- 時間 LoRA 行為的更清晰的圖形連接。

**輸入：**
- `model`（`MODEL`，必填）
- `clip`（`CLIP`，必填）
- `lora_name`（`STRING`，必填）
- `strength_start`、`strength_end` (`FLOAT`)
- `interpolation`（`STRING`：`linear`、`ease_in`、`ease_out`、`ease_in_out`）
- `start_percent`、`end_percent`（`FLOAT`、`0.0-1.0`）
- `keyframes_count`（`INT`，預設 `4`）
- `apply_to_conds`（`BOOLEAN`，可選）

**輸出：**
- `model` (`MODEL`)
- `clip` (`CLIP`)
- `curve_preview` (`IMAGE`)

**行為注意事項：**
- 如果 `lora_name` 是 `None`，模型/剪輯將通過且預覽仍會渲染。
- 如果開始和結束強度匹配，則其行為就像常數 LoRA 應用程式。
- 曲線預覽有助於在完整渲染之前快速驗證時序。

**常見錯誤：**
- 使用 `curve_preview` 時忘記 `matplotlib`。
- 使用與採樣器計時意圖不符的計劃視窗。
- 期望該節點直接輸出`CONDITIONING`。

---

## <a id="optional-dependencies"></a>可選依賴項

在 ComfyUI 使用的相同 Python 環境中僅安裝您需要的內容。

- `ScheduledLoRALoader` 曲線預覽：`python -m pip install matplotlib`

---

## <a id="example-workflow-multi-area-conditioning-pipeline"></a>多區域範例工作流程

[![完整工作流程](../workflows/conditioninig_pipeline_area_wf.png)](../workflows/conditioninig_pipeline_area_wf.png)

您可以將此工作流程圖像拖曳到 ComfyUI 中以匯入/載入完整圖表。

#### 區域1設置

[![區域 1 調節](../assets/conditioninig_area_1.png)](../assets/conditioninig_area_1.png)

- 使用本機 `Create Hook Lora` 載入一個 LoRA 並定義區域 1 的區域提示/調節。
- 將此調節連接到 `Conditioning Pipeline (Set Area)` 並為該區域設定 `width`、`height`、`x`、`y` 和 `strength`。

#### 區域2設置

[![區域 2 調節](../assets/conditioninig_area_2.png)](../assets/conditioninig_area_2.png)

- 重複完全相同的模式：另一個 `Create Hook Lora` + 另一個 `Conditioning Pipeline (Set Area)`。
- 您可以在其他區域繼續重複此模式。

#### 管道連結和組合

[![Conditioning Combine](../assets/conditioning_combine.png)](../assets/conditioning_combine.png)

- 將 `pipeline_out` 從區域 1 連結到區域 2（串聯管道入口）。
- 將 `pipeline_out` 從最後一個區域傳送到 `Conditioning Pipeline (Combine)`，這會將區域管道與全域條件合併。
- 將組合輸出直接路由到 `KSampler`，或路由到 `ControlNet`；在此範例中，它被路由到 `ControlNet`。

#### OpenPose / ControlNet 指導

- OpenPose/ControlNet 通常是可選的，但對於這種特定的多主題、多區域構圖工作流程，強烈建議使用它以保持構圖一致。
- 請參閱同一作者的 [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio)（較新的儲存庫）。

#### 全球 `Styler Pipeline` 展示位置

[![帶區域調節的全域 `Styler Pipeline` 放置 + ControlNet](../assets/styler_pipeline_node.png)](../assets/styler_pipeline_node.png)

全域樣式表示除了（或取代）按區域調整之外，還對整個影像套用 `Styler Pipeline` 一次。

- 一般規則：在 `KSampler` 之前連接 `Styler Pipeline`。
- 使用 ControlNet 時，可以在套用 ControlNet 之前或套用 ControlNet 之後連接 `Styler Pipeline`。
- 實際上，結果通常是等效的，因此請選擇圖表中更方便的位置。

#### `global_strength` 權衡

- 增加 `global_strength` 過多會降低每個區域調節的相對影響，並可能削弱每個區域的 LoRA/風格特性。
- 較高的全局強度也會對影像品質產生負面影響。
- 保持 `global_strength` 低並保持全域提示最小/一般。
- 經驗法則：一般使用低於 `0.5` 的值（測試最高可達 `0.5`），並避免依賴超出一般指導的全局調節。
- 降低 LoRA 強度往往會降低 LoRA 身份或角色保真度，而降低區域強度往往會降低每個區域的控制。
- 不建議將所有內容都最大化，因為高綜合強度會犧牲影像品質。當混合來自不同作者的 LoRA 時尤其如此，這可能會產生不一致的品質。
- 多重字元 LoRA 的經驗法則：如果可能，請使用同一作者的 LoRA 或類似的訓練方法，以獲得更一致的組合結果。

---

## <a id="gallery"></a>畫廊

| 預覽 | 描述 |
|---------|-------------|
| [![調節_管道_區域](../workflows/conditioninig_pipeline_area.png)](../workflows/conditioninig_pipeline_area.png) | **調節管道 — 具有 ControlNet OpenPose 的多個區域**<br><br>使用 ControlNet OpenPose 演示具有多個 LoRA 且沒有 LoRA 出血的多個垂直區域。<br><br>需要 [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio)。 |
| [![conditioning_pipeline_styled](../workflows/conditioninig_pipeline_styled.png)](../workflows/conditioninig_pipeline_styled.png) | **調節管道 - 具有 ControlNet 和樣式的多區域**<br><br>演示多區域和多個 LoRA，並將每個區域的樣式獨立應用於每個區域。 <br><br>需要 [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio) 和 [comfyui-styler-pipeline](https://github.com/andreszs/comfyui-styler-pipeline).<br><br>此工作流程使用每個區域的樣式，這表示每個區域都有自己單獨配置的樣式。透過在 ControlNet 之前連接 Styler 節點也可以實現全域樣式設定。 |

查看[這篇文章](https://www.andreszsogon.com/building-a-multi-character-comfyui-workflow-with-area-conditioning-openpose-control-and-style-layering/)，了解同時使用多個 conditioning area、OpenPose、ControlNet 和 Styler 的完整 workflow。

---

## <a id="funding--support"></a>資金與支持

### 為什麼您的支持很重要

該插件是獨立開發和維護的，定期使用**付費人工智慧代理**來加快調試、測試和生活品質的提高。如果您覺得有用，財政支持有助於維持發展穩定。

您的貢獻有助於：

* 資助人工智慧工具以實現更快的修復和新功能
* 涵蓋 ComfyUI 更新中的持續維護和相容性工作
* 達到使用限制時防止開發速度減慢

> [!TIP]
> 不捐款？ GitHub 之星 ⭐ 透過提高可見性和幫助更多用戶仍然有很大幫助

### 💙 支持這個項目

<table style="width: 100%; table-layout: fixed;">
  <tr>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">Ko-fi</h4>
        <a href="https://ko-fi.com/D1D716OLPM" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_kofi.svg" alt="Ko-fi Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="https://ko-fi.com/D1D716OLPM" target="_blank" rel="noopener noreferrer">買一杯咖啡</a></p>
      </div>
    </td>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">PayPal</h4>
        <a href="https://www.paypal.com/ncp/payment/GEEM324PDD9NC" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_paypal.svg" alt="PayPal Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="https://www.paypal.com/ncp/payment/GEEM324PDD9NC" target="_blank" rel="noopener noreferrer">開啟 PayPal</a></p>
      </div>
    </td>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">USDC（僅限 Arbitrum ⚠️）</h4>
        <a href="https://arbiscan.io/address/0xe36a336fC6cc9Daae657b4A380dA492AB9601e73" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_usdc.svg" alt="USDC Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="#usdc-address">顯示位址</a></p>
      </div>
    </td>
  </tr>
</table>

<details>
  <summary>比較喜歡掃描？顯示二維碼</summary>
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
  <summary>顯示USDC位址</summary>

```text
0xe36a336fC6cc9Daae657b4A380dA492AB9601e73
```

> [!WARNING]
> 僅在 Arbitrum One 上發送 USDC。在任何其他網路上發送的轉帳都不會到達，並可能永久丟失。
</details>

## <a id="license"></a>授權條款

麻省理工學院許可證 - 請參閱 [LICENSE](../LICENSE) 以了解全文。

---

**維護者：** andreszs
**狀態：** 積極開發
