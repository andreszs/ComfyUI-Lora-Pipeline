<h4 align="center">
  <a href="./README.md">English</a> | <a href="./README.de.md">Deutsch</a> | <a href="./README.es.md">Español</a> | <a href="./README.fr.md">Français</a> | <a href="./README.pt.md">Português</a> | <a href="./README.ru.md">Русский</a> | <a href="./README.ja.md">日本語</a> | <a href="./README.ko.md">한국어</a> | 中文 | <a href="./README.zh-TW.md">繁體中文</a>
</h4>



<p align="center">
  <img alt="Version" src="https://img.shields.io/github/v/tag/andreszs/comfyui-lora-pipeline?label=version" />
  <img alt="Last Commit" src="https://img.shields.io/github/last-commit/andreszs/comfyui-lora-pipeline" />
  <img alt="License" src="https://img.shields.io/github/license/andreszs/comfyui-lora-pipeline" />
</p>
<br />

# ComfyUI LoRA Pipeline

基于区域的 LoRA 调节包装器和 ComfyUI 的 LoRA 调度节点。

---

## 目录

- ✨ [功能](#features)
- 📦 [安装](#installation)
- ✅ [推荐设置（多区域/多主题）](#recommended-setup-multi-area--multi-subject)
- 🔧 [节点](#nodes)
  - [Conditioning Pipeline (Set Area)](#conditioning-pipeline-set-area)
  - [Conditioning Pipeline (Combine)](#conditioning-pipeline-combine)
  - [ScheduledLoRALoader](#scheduledloraloader)
- 🧩 [可选依赖项](#optional-dependencies)
- 🧭 [多区域示例工作流程](#example-workflow-multi-area-conditioning-pipeline)
- 🖼️ [图库](#gallery)
- 🚀 [更新日志](#changelog)
- 💙 [资金与支持](#funding--support)
- 📄 [许可证](#license)

---

## <a id="features"></a>特征

- 用于多主题和多区域提示的基于区域的调节管道。
- 带有曲线预览输出的单节点预定 LoRA 强度控制。
- 为了在多个领域实现一致的多主题构图，强烈建议通过 [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio) **ControlNet + OpenPose**。
- 如果没有ControlNet/OpenPose，多主体多区域构图通常会不一致，并且可能需要多次重试。
- 仅限 Python：不需要 JavaScript 或前端依赖项。

---

## <a id="installation"></a>安装

### 要求
- ComfyUI（最新版本）
- Python 3.10+
- 可选的每个节点依赖项：`matplotlib`

### 步骤

1. 将此存储库克隆到 `ComfyUI/custom_nodes/` 中。
2. 重新启动 ComfyUI。
3. 确认节点出现在 `LoRA Pipeline/` 下。

---

## <a id="recommended-setup-multi-area--multi-subject"></a>推荐设置（多区域/多主题）

- 使用 ControlNet OpenPose （推荐）：[comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio)。
- 保持全局提示最小化和通用。
- 保持 `global_strength` 较低（经验法则：低于 `0.5`）。
- 平衡单位面积强度、`global_strength` 和 LoRA 强度；不要最大化所有的力量。
- 效果良好的基线值示例：`0.75` 周围的区域强度、`0.90` 周围的 LoRA 强度。

---

## <a id="nodes"></a>节点

| Conditioning Pipeline (Combine) | Conditioning Pipeline (Set Area) | Load LoRA (Scheduled) |
|---|---|---|
| ![Conditioning Pipeline (Combine)](../assets/conditioning_pipeline_combine.png) | ![Conditioning Pipeline (Set Area)](../assets/conditioning_pipeline_set_area.png) | ![Load LoRA (Scheduled)](../assets/scheduled_lora_loader.png) |

### <a id="conditioning-pipeline-set-area"></a>Conditioning Pipeline (Set Area)

一次定义一个区域条件条目。该节点定义一个具有宽度、高度、x 和 y 的矩形区域，然后将专用的调节提示和强度作为链式调节管道的一部分应用于该区域。

**概览：**
- 每个区域/主题提示使用一个节点实例。
- 链接多个实例以构建区域调节管道。
- 在最终组合之前实现干净的多主体控制。

**输入：**
- `conditioning`（`CONDITIONING`，必需）
- `width`、`height`、`x`、`y`（`FLOAT`，标准化 `0.0-1.0`）
- `strength`（`FLOAT`，默认 `1.0`）
- `pipeline_in`（`CONDITIONING_PIPELINE`，可选）

**输出：**
- `pipeline_out` (`CONDITIONING_PIPELINE`)

**行为注意事项：**
- 如果 `pipeline_in` 未连接，则创建新管道。
- 连接 `pipeline_in` 时附加新的区域条目。
- 保持条目有序，以便您可以构建可预测的区域堆栈。
- 较低的区域强度通常会提高整体图像质量，但会降低每个区域的控制权限。
- 平衡区域强度以及 global_strength 和 Create Hook Lora 中的 LoRA 强度。

**常见错误：**
- 提供像素坐标而不是标准化的 `0.0-1.0` 值。
- 将 `width`/`height` 设置为接近 `0` 并期待可见的效果。
- 忘记将最终管道传递到 `Conditioning Pipeline (Combine)` 中。

---

### <a id="conditioning-pipeline-combine"></a>Conditioning Pipeline (Combine)

将全局正/负调节与区域管道相结合，以实现区域感知输出。与设置区域一起，这是多 LoRA 和每个主题/区域单独调节的核心路径。

**概览：**
- 将您的区域管道转换为最终的正/负输出。
- 保留全局提示上下文，同时添加本地区域控制。

**输入：**
- `global_positive`（`CONDITIONING`，必需）
- `global_negative`（`CONDITIONING`，必需）
- `pipeline`（`CONDITIONING_PIPELINE`，必需）
- `global_strength`（`FLOAT`，默认 `0.3`）
- `fast_mode`（`BOOLEAN`，默认 `false`）

**输出：**
- `positive_out` (`CONDITIONING`)
- `negative_out` (`CONDITIONING`)
- `areas_out` (`CONDITIONING_AREAS`)

**`areas_out` 详情：**

`areas_out` 将已配置的区域列表作为结构化数据输出公开。每个条目包含通过 `Conditioning Pipeline (Set Area)` 在管道中定义的归一化坐标（`x`、`y`、`width`、`height`）和 `strength`。将 `areas_out` 连接到 [ComfyUI-OpenPose-Studio](https://github.com/andreszs/comfyui-openpose-studio)，即可将您的调节区域自动镜像到 OpenPose 编辑器中——姿态放置将与您调节的确切区域对齐。此输出也可被接受区域元数据的任何其他扩展或节点使用，用于遮罩生成或区域感知的下游处理。

**行为注意事项：**
- 如果管道为空/无效，输出将回落到全局输入，且 `areas_out` 为空列表。
- 应用区域条目，然后对未覆盖区域应用默认组合通道。
- `global_strength` 控制全球背景与局部区域竞争的强度。
- 将 global_strength 推得太高会减少每个区域的调节影响并对图像质量产生负面影响。
- 好的结果通常来自于平衡全局强度与单位面积强度和 LoRA 强度，而不是最大化所有值。
- `fast_mode` 是可选功能，默认关闭，因此现有工作流会保持原有行为。
- 启用 Fast Mode 后，全局正向条件会连接到每个区域正向条件中。`global_strength` 不会被忽略；它只缩放新增的全局部分。
- 当配置的区域覆盖整个画布时，Fast Mode 会省略单独的全局正向计算。若覆盖不完整，则会保留全局 fallback，因此加速幅度会较小。
- Fast Mode 与标准路径并非数学上完全相同，可能改变提示词平衡、构图或主体保真度。在用于正式工作流之前请比较结果。

**常见错误：**
- 仅馈送一种调节流，而不是同时馈送正流和负流。
- 过度驾驶 `global_strength` 并清除区域细节。
- 构建区域条目，但忘记将组合输出连接到采样器路径。

---

### <a id="scheduledloraloader"></a>ScheduledLoRALoader

在一个干净的节点中，应用一个具有恒定强度的 LoRA 或扩散进度的预定曲线。

**概览：**
- 替换多个本机 LoRA/控制节点的混乱链。
- 将计时、插值和预览结合在一起。
- 时间 LoRA 行为的更清晰的图形连接。

**输入：**
- `model`（`MODEL`，必需）
- `clip`（`CLIP`，必需）
- `lora_name`（`STRING`，必需）
- `strength_start`、`strength_end` (`FLOAT`)
- `interpolation`（`STRING`：`linear`、`ease_in`、`ease_out`、`ease_in_out`）
- `start_percent`、`end_percent`（`FLOAT`、`0.0-1.0`）
- `keyframes_count`（`INT`，默认 `4`）
- `apply_to_conds`（`BOOLEAN`，可选）

**输出：**
- `model` (`MODEL`)
- `clip` (`CLIP`)
- `curve_preview` (`IMAGE`)

**行为注意事项：**
- 如果 `lora_name` 是 `None`，模型/剪辑将通过并且预览仍会渲染。
- 如果开始和结束强度匹配，则其行为就像常量 LoRA 应用程序。
- 曲线预览有助于在完整渲染之前快速验证时序。

**常见错误：**
- 使用 `curve_preview` 时忘记 `matplotlib`。
- 使用与采样器计时意图不匹配的计划窗口。
- 期望该节点直接输出`CONDITIONING`。

---

## <a id="optional-dependencies"></a>可选依赖项

在 ComfyUI 使用的相同 Python 环境中仅安装您需要的内容。

- `ScheduledLoRALoader` 曲线预览：`python -m pip install matplotlib`

---

## <a id="example-workflow-multi-area-conditioning-pipeline"></a>多区域示例工作流程

[![完整工作流程](../workflows/conditioninig_pipeline_area_wf.png)](../workflows/conditioninig_pipeline_area_wf.png)

您可以将此工作流程图像拖放到 ComfyUI 中以导入/加载完整图表。

#### 区域1设置

[![区域 1 调节](../assets/conditioninig_area_1.png)](../assets/conditioninig_area_1.png)

- 使用本机 `Create Hook Lora` 加载一个 LoRA 并定义区域 1 的区域提示/调节。
- 将该调节连接到 `Conditioning Pipeline (Set Area)` 并为该区域设置 `width`、`height`、`x`、`y` 和 `strength`。

#### 区域2设置

[![区域 2 调节](../assets/conditioninig_area_2.png)](../assets/conditioninig_area_2.png)

- 重复完全相同的模式：另一个 `Create Hook Lora` + 另一个 `Conditioning Pipeline (Set Area)`。
- 您可以在其他区域继续重复此模式。

#### 管道链接和组合

[![Conditioning Combine](../assets/conditioning_combine.png)](../assets/conditioning_combine.png)

- 将 `pipeline_out` 从区域 1 链接到区域 2（串联管道入口）。
- 将 `pipeline_out` 从最后一个区域发送到 `Conditioning Pipeline (Combine)`，这将区域管道与全局条件合并。
- 将组合输出直接路由到 `KSampler`，或路由到 `ControlNet`；在本例中，它被路由到 `ControlNet`。

#### OpenPose / ControlNet 指导

- OpenPose/ControlNet 通常是可选的，但对于这种特定的多主题、多区域构图工作流程，强烈建议使用它以保持构图一致。
- 请参阅同一作者的 [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio)（较新的存储库）。

#### 全球 `Styler Pipeline` 展示位置

[![带区域调节的全局 `Styler Pipeline` 放置 + ControlNet](../assets/styler_pipeline_node.png)](../assets/styler_pipeline_node.png)

全局样式意味着除了（或代替）按区域调节之外，还对整个图像应用 `Styler Pipeline` 一次。

- 一般规则：在 `KSampler` 之前连接 `Styler Pipeline`。
- 使用 ControlNet 时，可以在应用 ControlNet 之前或应用 ControlNet 之后连接 `Styler Pipeline`。
- 实际上，结果通常是等效的，因此请选择图表中更方便的位置。

#### `global_strength` 权衡

- 增加 `global_strength` 过多会降低每个区域调节的相对影响，并可能削弱每个区域的 LoRA/风格特性。
- 较高的全局强度也会对图像质量产生负面影响。
- 保持 `global_strength` 低并保持全局提示最小/一般。
- 经验法则：一般使用低于 `0.5` 的值（测试最高可达 `0.5`），并避免依赖超出一般指导的全局调节。
- 降低 LoRA 强度往往会降低 LoRA 身份或角色保真度，而降低区域强度往往会降低每个区域的控制。
- 不建议将所有内容都最大化，因为高综合强度会牺牲图像质量。当混合来自不同作者的 LoRA 时尤其如此，这可能会产生不一致的质量。
- 多字符 LoRA 的经验法则：如果可能，请使用同一作者的 LoRA 或类似的训练方法，以获得更一致的组合结果。

---

## <a id="gallery"></a>画廊

| 预览 | 描述 |
|---------|-------------|
| [![conditioning_pipeline_area](../workflows/conditioninig_pipeline_area.png)](../workflows/conditioninig_pipeline_area.png) | **Conditioning Pipeline — 使用 ControlNet OpenPose 的多区域**<br><br>使用 ControlNet OpenPose 演示具有多个 LoRA 且没有 LoRA bleeding 的多个垂直区域。<br><br>需要 [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio)。 |
| [![conditioning_pipeline_styled](../workflows/conditioninig_pipeline_styled.png)](../workflows/conditioninig_pipeline_styled.png) | **调节管道 - 具有 ControlNet 和样式的多区域**<br><br>演示多区域和多个 LoRA，并将每个区域的样式独立应用于每个区域。<br><br>需要 [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio) 和 [comfyui-styler-pipeline](https://github.com/andreszs/comfyui-styler-pipeline).<br><br>此工作流程使用每个区域的样式，这意味着每个区域都有自己单独配置的样式。通过在 ControlNet 之前连接 Styler 节点也可以实现全局样式设置。 |

查看[这篇文章](https://www.andreszsogon.com/building-a-multi-character-comfyui-workflow-with-area-conditioning-openpose-control-and-style-layering/)，了解同时使用多个 conditioning area、OpenPose、ControlNet 和 Styler 的完整 workflow。

---

## <a id="changelog"></a>更新日志

### 1.1.4

- 区域条件优化将一个双区域 SDXL 测试工作流的实测生成时间从约 144 秒降至 70 秒，渲染时间减少约 51%。
- 可选的 Fast Mode 在完整覆盖的等效测试中约 54 秒完成，与之前的实现相比最多减少约 63% 的时间。
- 性能会随 GPU、模型、分辨率、sampler、ControlNet 配置及区域覆盖情况而变化。Fast Mode 也可能产生视觉差异，因此默认关闭。

---

## <a id="funding--support"></a>资金与支持

### 为什么您的支持很重要

该插件是独立开发和维护的，定期使用**付费人工智能代理**来加快调试、测试和生活质量的提高。如果您觉得有用，财政支持有助于保持发展稳定。

您的贡献有助于：

* 资助人工智能工具以实现更快的修复和新功能
* 涵盖 ComfyUI 更新中的持续维护和兼容性工作
* 达到使用限制时防止开发速度减慢

> [!TIP]
> 不捐款？ GitHub 之星 ⭐ 通过提高可见性和帮助更多用户仍然有很大帮助

### 💙 支持这个项目

<table style="width: 100%; table-layout: fixed;">
  <tr>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">Ko-fi</h4>
        <a href="https://ko-fi.com/D1D716OLPM" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_kofi.svg" alt="Ko-fi Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="https://ko-fi.com/D1D716OLPM" target="_blank" rel="noopener noreferrer">买一杯咖啡</a></p>
      </div>
    </td>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">PayPal</h4>
        <a href="https://www.paypal.com/ncp/payment/GEEM324PDD9NC" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_paypal.svg" alt="PayPal Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="https://www.paypal.com/ncp/payment/GEEM324PDD9NC" target="_blank" rel="noopener noreferrer">打开 PayPal</a></p>
      </div>
    </td>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">USDC（仅限 Arbitrum ⚠️）</h4>
        <a href="https://arbiscan.io/address/0xe36a336fC6cc9Daae657b4A380dA492AB9601e73" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_usdc.svg" alt="USDC Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="#usdc-address">显示地址</a></p>
      </div>
    </td>
  </tr>
</table>

<details>
  <summary>更喜欢扫描？显示二维码</summary>
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
  <summary>显示USDC地址</summary>

```text
0xe36a336fC6cc9Daae657b4A380dA492AB9601e73
```

> [!WARNING]
> 仅在 Arbitrum One 上发送 USDC。在任何其他网络上发送的转账都不会到达，并可能永久丢失。
</details>

## <a id="license"></a>许可证

麻省理工学院许可证 - 请参阅 [LICENSE](../LICENSE) 了解全文。

---

**维护者：** andreszs
**状态：** 积极开发
