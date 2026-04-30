<h4 align="center">
  <a href="./README.md">English</a> | <a href="./README.de.md">Deutsch</a> | <a href="./README.es.md">Español</a> | <a href="./README.fr.md">Français</a> | <a href="./README.pt.md">Português</a> | <a href="./README.ru.md">Русский</a> | <a href="./README.ja.md">日本語</a> | 한국어 | <a href="./README.zh.md">中文</a> | <a href="./README.zh-TW.md">繁體中文</a>
</h4>



<p align="center">
  <img alt="Version" src="https://img.shields.io/github/v/tag/andreszs/comfyui-lora-pipeline?label=version" />
  <img alt="Last Commit" src="https://img.shields.io/github/last-commit/andreszs/comfyui-lora-pipeline" />
  <img alt="License" src="https://img.shields.io/github/license/andreszs/comfyui-lora-pipeline" />
</p>
<br />

# ComfyUI LoRA Pipeline

ComfyUI에 대한 영역 기반 LoRA 조절 래퍼 및 LoRA 예약 노드.

---

## 목차

- ✨ [특징](#features)
- 📦 [설치](#installation)
- ✅ [권장 설정(다영역/다주제)](#recommended-setup-multi-area--multi-subject)
- 🔧 [노드](#nodes)
  - [Conditioning Pipeline (Set Area)](#conditioning-pipeline-set-area)
  - [Conditioning Pipeline (Combine)](#conditioning-pipeline-combine)
  - [ScheduledLoRALoader](#scheduledloraloader)
- 🧩 [선택적 종속성](#optional-dependencies)
- 🧭 [다중 영역 예시 워크플로](#example-workflow-multi-area-conditioning-pipeline)
- 🖼️ [갤러리](#gallery)
- 💙 [자금 및 지원](#funding--support)
- 📄 [라이센스](#license)

---

## <a id="features"></a>특징

- 다중 주제 및 다중 지역 프롬프트를 위한 영역 기반 컨디셔닝 파이프라인입니다.
- 곡선 미리보기 출력을 통해 1노드 예약 LoRA 강도 제어.
- 여러 영역에 걸쳐 일관된 다중 주제 구성을 위해서는 [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio)를 통해 **ControlNet + OpenPose을 강력히 권장합니다**.
- ControlNet/OpenPose이 없으면 다중 주제 다중 영역 구성이 종종 일관성이 없으며 많은 재시도가 필요할 수 있습니다.
- Python 전용: JavaScript 또는 프런트엔드 종속성이 필요하지 않습니다.

---

## <a id="installation"></a>설치

### 요구사항
- ComfyUI (최근 빌드)
- Python 3.10+
- 선택적 노드별 deps: `matplotlib`

### 단계

1. 이 저장소를 `ComfyUI/custom_nodes/`에 복제하세요.
2. ComfyUI을(를) 다시 시작하세요.
3. `LoRA Pipeline/` 아래에 노드가 나타나는지 확인합니다.

---

## <a id="recommended-setup-multi-area--multi-subject"></a>권장 설정(다중 영역/다중 피사체)

- ControlNet OpenPose 사용(권장): [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio).
- 전역 프롬프트를 최소화하고 일반화하세요.
- `global_strength`을 낮게 유지하십시오(경험 법칙: `0.5` 미만).
- 영역별 강도, `global_strength` 및 LoRA 강도의 균형을 맞춥니다. 모든 강점을 최대화하지 마십시오.
- 잘 작동한 기준선 값의 예: `0.75` 주변의 영역 강도, `0.90` 주변의 LoRA 강도.

---

## <a id="nodes"></a>노드

| Conditioning Pipeline (Combine) | Conditioning Pipeline (Set Area) | Load LoRA (Scheduled) |
|---|---|---|
| ![Conditioning Pipeline (Combine)](../assets/conditioning_pipeline_combine.png) | ![Conditioning Pipeline (Set Area)](../assets/conditioning_pipeline_set_area.png) | ![Load LoRA (Scheduled)](../assets/scheduled_lora_loader.png) |

### <a id="conditioning-pipeline-set-area"></a>Conditioning Pipeline (Set Area)

한 번에 하나의 영역 조건 항목을 정의하십시오. 이 노드는 너비, 높이, x, y가 있는 직사각형 영역을 정의한 다음 연결된 조절 파이프라인의 일부로 해당 영역에 전용 조절 프롬프트와 강도를 적용합니다.

**한눈에 보기:**
- 지역/주제 프롬프트당 하나의 노드 인스턴스를 사용합니다.
- 여러 인스턴스를 연결하여 지역 조절 파이프라인을 구축합니다.
- 최종 결합 전에 다중 피사체를 깔끔하게 제어할 수 있습니다.

**입력:**
- `conditioning`(`CONDITIONING`, 필수)
- `width`, `height`, `x`, `y`(`FLOAT`, 정규화된 `0.0-1.0`)
- `strength`(`FLOAT`, 기본값 `1.0`)
- `pipeline_in`(`CONDITIONING_PIPELINE`, 선택사항)

**출력:**
- `pipeline_out` (`CONDITIONING_PIPELINE`)

**행동 참고사항:**
- `pipeline_in`이 연결되지 않은 경우 새 파이프라인을 생성합니다.
- `pipeline_in`이 연결되면 새 지역 항목을 추가합니다.
- 예측 가능한 지역 스택을 구축할 수 있도록 항목 순서를 유지합니다.
- 영역 강도가 낮을수록 전반적인 이미지 품질이 향상되는 경우가 많지만 영역별 제어 권한이 줄어듭니다.
- global_strength 및 Create Hook Lora의 LoRA 강도와 함께 영역 강도의 균형을 맞춥니다.

**일반적인 실수:**
- 정규화된 `0.0-1.0` 값 대신 픽셀 좌표를 제공합니다.
- `0` 근처에 `width`/`height`을(를) 설정하고 눈에 띄는 효과를 기대합니다.
- 최종 파이프라인을 `Conditioning Pipeline (Combine)`에 전달하는 것을 잊어버렸습니다.

---

### <a id="conditioning-pipeline-combine"></a>Conditioning Pipeline (Combine)

지역 인식 출력을 위해 전역 포지티브/네거티브 조건을 영역 파이프라인과 결합합니다. Set Area와 함께 이는 다중 LoRAs 및 주제/구역별 별도의 조건을 위한 핵심 경로입니다.

**한눈에 보기:**
- 지역 파이프라인을 최종 긍정적/부정적 출력으로 변환합니다.
- 로컬 지역 제어를 추가하는 동안 전역 프롬프트 컨텍스트를 유지합니다.

**입력:**
- `global_positive`(`CONDITIONING`, 필수)
- `global_negative`(`CONDITIONING`, 필수)
- `pipeline`(`CONDITIONING_PIPELINE`, 필수)
- `global_strength`(`FLOAT`, 기본값 `0.3`)

**출력:**
- `positive_out` (`CONDITIONING`)
- `negative_out` (`CONDITIONING`)
- `areas_out` (`CONDITIONING_AREAS`)

**`areas_out` 세부사항:**

`areas_out`은 구성된 영역 목록을 구조화된 데이터 출력으로 노출합니다. 각 항목에는 `Conditioning Pipeline (Set Area)`를 통해 파이프라인에서 정의된 정규화된 좌표(`x`, `y`, `width`, `height`)와 `strength`가 포함됩니다. `areas_out`을 [ComfyUI-OpenPose-Studio](https://github.com/andreszs/comfyui-openpose-studio)에 연결하면 조건화 영역을 OpenPose 편집기에 자동으로 미러링할 수 있습니다. 포즈 배치는 조건화한 정확한 영역에 맞게 정렬됩니다. 이 출력은 마스크 생성 또는 영역 인식 다운스트림 처리를 위한 영역 메타데이터를 허용하는 다른 확장 또는 노드에서도 사용할 수 있습니다.

**행동 참고사항:**
- 파이프라인이 비어 있거나 유효하지 않은 경우 출력은 전역 입력으로 대체되고 `areas_out`은 빈 목록이 됩니다.
- 지역 항목을 적용한 다음, 발견되지 않은 지역에 대한 기본 통합 패스를 적용합니다.
- `global_strength`은 글로벌 컨텍스트가 로컬 영역과 얼마나 강력하게 경쟁하는지 제어합니다.
- global_strength을(를) 너무 높이면 영역별 조정 영향이 줄어들고 이미지 품질에 부정적인 영향을 미칠 수 있습니다.
- 좋은 결과는 일반적으로 모든 값을 최대화하기보다는 글로벌 강점과 지역별 강점 및 LoRA 강점의 균형을 맞추는 것에서 나옵니다.

**일반적인 실수:**
- 양성 및 음성 둘 다 대신 하나의 조건화 스트림만 공급합니다.
- `global_strength`을 과도하게 구동하고 영역 세부 사항을 유실합니다.
- 영역 항목을 작성했지만 결합된 출력을 샘플러 경로에 연결하는 것을 잊어버렸습니다.

---

### <a id="scheduledloraloader"></a>ScheduledLoRALoader

하나의 깨끗한 노드에서 일정한 강도 또는 확산 진행에 대한 예정된 곡선으로 하나의 LoRA을 적용합니다.

**한눈에 보기:**
- 여러 네이티브 LoRA/control 노드의 지저분한 체인을 대체합니다.
- 타이밍, 보간 및 미리보기를 함께 유지합니다.
- 일시적인 LoRA 동작에 대한 더욱 깔끔한 그래프 연결.

**입력:**
- `model`(`MODEL`, 필수)
- `clip`(`CLIP`, 필수)
- `lora_name`(`STRING`, 필수)
- `strength_start`, `strength_end`(`FLOAT`)
- `interpolation` (`STRING`: `linear`, `ease_in`, `ease_out`, `ease_in_out`)
- `start_percent`, `end_percent` (`FLOAT`, `0.0-1.0`)
- `keyframes_count`(`INT`, 기본값 `4`)
- `apply_to_conds`(`BOOLEAN`, 선택사항)

**출력:**
- `model` (`MODEL`)
- `clip` (`CLIP`)
- `curve_preview` (`IMAGE`)

**행동 참고사항:**
- `lora_name`이 `None`인 경우 모델/클립 패스스루 및 미리 보기는 계속 렌더링됩니다.
- 시작 강도와 끝 강도가 일치하면 상수 LoRA 애플리케이션처럼 작동합니다.
- 곡선 미리보기는 전체 렌더링 전에 타이밍을 빠르게 확인하는 데 도움이 됩니다.

**일반적인 실수:**
- `curve_preview`을(를) 사용할 때 `matplotlib`을(를) 잊어버리는 중입니다.
- 샘플러 타이밍 의도와 일치하지 않는 일정 창을 사용합니다.
- 이 노드가 `CONDITIONING`을(를) 직접 출력할 것으로 예상됩니다.

---

## <a id="optional-dependencies"></a>선택적 종속성

ComfyUI에서 사용하는 것과 동일한 Python 환경에 필요한 것만 설치하세요.

- `ScheduledLoRALoader` 곡선 미리보기: `python -m pip install matplotlib`

---

## <a id="example-workflow-multi-area-conditioning-pipeline"></a>다중 영역 예시 워크플로

[![전체 워크플로](../workflows/conditioninig_pipeline_area_wf.png)](../workflows/conditioninig_pipeline_area_wf.png)

이 워크플로 이미지를 ComfyUI에 끌어다 놓아 전체 그래프를 가져오거나 로드할 수 있습니다.

#### 영역 1 설정

[![영역 1 조건화](../assets/conditioninig_area_1.png)](../assets/conditioninig_area_1.png)

- 기본 `Create Hook Lora`을 사용하여 하나의 LoRA을 로드하고 영역 1에 대한 영역 프롬프트/조건을 정의합니다.
- 해당 조건을 `Conditioning Pipeline (Set Area)`에 연결하고 해당 지역에 대해 `width`, `height`, `x`, `y` 및 `strength`를 설정합니다.

#### 영역 2 설정

[![영역 2 조건화](../assets/conditioninig_area_2.png)](../assets/conditioninig_area_2.png)

- 똑같은 패턴을 반복하세요. 또 다른 `Create Hook Lora` + 또 다른 `Conditioning Pipeline (Set Area)`.
- 추가 영역에 대해 이 패턴을 계속 반복할 수 있습니다.

#### 파이프라인 연결 및 결합

[![컨디셔닝 결합](../assets/conditioning_combine.png)](../assets/conditioning_combine.png)

- 영역 1에서 영역 2로 `pipeline_out`을 연결합니다(연결된 파이프라인 항목).
- 마지막 영역의 `pipeline_out`을(를) `Conditioning Pipeline (Combine)`로 보내면 영역 파이프라인을 전역 조건과 병합합니다.
- 결합된 출력을 `KSampler`로 직접 라우팅하거나 `ControlNet`로 라우팅합니다. 이 예에서는 `ControlNet`로 라우팅됩니다.

#### OpenPose / ControlNet 안내

- OpenPose/ControlNet은 일반적으로 선택 사항이지만 이 특정 다중 주제, 다중 영역 구성 작업 흐름의 경우 일관된 구성을 위해 적극 권장됩니다.
- 동일한 작성자(최신 저장소)의 [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio)을 참조하세요.

#### 전역 `Styler Pipeline` 배치

[![지역 조절을 사용한 전역 `Styler Pipeline` 배치 + ControlNet](../assets/styler_pipeline_node.png)](../assets/styler_pipeline_node.png)

전역 스타일링은 영역별 조절에 추가로(또는 대신) 전체 이미지에 `Styler Pipeline`을 한 번 적용하는 것을 의미합니다.

- 일반 규칙: `KSampler` 앞에 `Styler Pipeline`을 연결합니다.
- ControlNet을 사용하는 경우 `Styler Pipeline`은(는) ControlNet을 적용하기 전이나 ControlNet을 적용한 후에 연결할 수 있습니다.
- 실제로 결과는 일반적으로 동일하므로 그래프에서 더 편리한 배치를 선택하십시오.

#### `global_strength` 장단점

- `global_strength`을 너무 많이 늘리면 영역별 조절의 상대적 영향이 줄어들고 영역별 LoRA/스타일 정체성이 약화될 수 있습니다.
- 전역 강도가 높을수록 이미지 품질에 부정적인 영향을 미칠 수도 있습니다.
- `global_strength`을 낮게 유지하고 전역 프롬프트를 최소/일반으로 유지하세요.
- 경험 법칙: 일반적으로 `0.5` 미만의 값을 사용하고(최대 `0.5`까지 테스트됨) 일반 지침 이상의 전역 조건에 의존하지 마십시오.
- LoRA 강도를 낮추면 LoRA 정체성이나 문자 충실도가 감소하는 경향이 있는 반면, 영역 강도를 낮추면 영역별 제어가 감소하는 경향이 있습니다.
- 결합된 강도가 높으면 이미지 품질이 저하될 수 있으므로 모든 것을 최대로 설정하는 것은 권장되지 않습니다. 이는 서로 다른 작성자의 LoRA을 혼합할 때 특히 그렇습니다. 이로 인해 일관되지 않은 품질이 생성될 수 있습니다.
- 다중 문자 LoRA에 대한 경험 법칙: 가능하면 동일한 작성자의 LoRA을 사용하거나 보다 일관된 결합 결과를 위해 유사한 교육 접근 방식을 사용하십시오.

---

## <a id="gallery"></a>갤러리

| 미리보기 | 설명 |
|---------|-------------|
| [![conditioning_pipeline_area](../workflows/conditioninig_pipeline_area.png)](../workflows/conditioninig_pipeline_area.png) | **Conditioning Pipeline — ControlNet OpenPose를 사용한 다중 영역**<br><br>ControlNet OpenPose를 사용하여 LoRA bleeding 없이 여러 LoRA가 있는 다중 수직 영역을 보여줍니다.<br><br>[comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio)이 필요합니다. |
| [![conditioning_pipeline_styled](../workflows/conditioninig_pipeline_styled.png)](../workflows/conditioninig_pipeline_styled.png) | **컨디셔닝 파이프라인 — ControlNet 및 스타일링을 사용한 다중 영역**<br><br>각 영역에 독립적으로 적용되는 영역별 스타일을 사용하여 다중 영역 및 다중 LoRA을 보여줍니다.<br><br>[comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio) 및 [comfyui-styler-pipeline](https://github.com/andreszs/comfyui-styler-pipeline)이 필요합니다.<br><br>이 워크플로에서는 다음을 사용합니다. 영역별 스타일링. 즉, 각 영역에는 개별적으로 구성된 고유한 스타일이 있습니다. ControlNet 바로 앞에 Styler 노드를 연결하면 전역 스타일링도 가능합니다. |

여러 conditioning area, OpenPose, ControlNet, Styler를 모두 동시에 사용하는 workflow는 [이 포스트](https://www.andreszsogon.com/building-a-multi-character-comfyui-workflow-with-area-conditioning-openpose-control-and-style-layering/)에서 확인할 수 있습니다.

---

## <a id="funding--support"></a>자금 및 지원

### 귀하의 지원이 중요한 이유

이 플러그인은 디버깅, 테스트 및 삶의 질 향상 속도를 높이기 위해 **유료 AI 에이전트**를 정기적으로 사용하여 독립적으로 개발 및 유지 관리됩니다. 유용하다고 판단되면 재정 지원을 통해 개발이 꾸준히 진행되도록 돕습니다.

귀하의 기여가 도움이 됩니다:

* 더 빠른 수정과 새로운 기능을 위해 AI 도구에 자금을 지원하세요
* ComfyUI 업데이트 전반에 걸쳐 지속적인 유지 관리 및 호환성 작업을 다룹니다.
* 사용 제한에 도달할 때 개발 속도 저하 방지

> [!TIP]
> 기부하지 않나요? GitHub 스타 ⭐는 여전히 가시성을 향상하고 더 많은 사용자를 지원함으로써 많은 도움을 줍니다.

### 💙 이 프로젝트를 지원하세요

<table style="width: 100%; table-layout: fixed;">
  <tr>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">Ko-fi</h4>
        <a href="https://ko-fi.com/D1D716OLPM" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_kofi.svg" alt="Ko-fi Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="https://ko-fi.com/D1D716OLPM" target="_blank" rel="noopener noreferrer">커피 구입</a></p>
      </div>
    </td>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">PayPal</h4>
        <a href="https://www.paypal.com/ncp/payment/GEEM324PDD9NC" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_paypal.svg" alt="PayPal Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="https://www.paypal.com/ncp/payment/GEEM324PDD9NC" target="_blank" rel="noopener noreferrer">PayPal 열기</a></p>
      </div>
    </td>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">USDC (Arbitrum만 ⚠️)</h4>
        <a href="https://arbiscan.io/address/0xe36a336fC6cc9Daae657b4A380dA492AB9601e73" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_usdc.svg" alt="USDC Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="#usdc-address">주소 표시</a></p>
      </div>
    </td>
  </tr>
</table>

<details>
  <summary>스캔을 선호하시나요? QR 코드 표시</summary>
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
  <summary>USDC 주소 표시</summary>

```text
0xe36a336fC6cc9Daae657b4A380dA492AB9601e73
```

> [!WARNING]
> USDC는 Arbitrum One에만 전송하세요. 다른 네트워크를 통해 전송된 경우 도착하지 않으며 영구적으로 손실될 수 있습니다.
</details>

## <a id="license"></a>라이선스

MIT 라이선스 - 전문은 [LICENSE](../LICENSE)을 참조하세요.

---

**관리자:** andreszs
**상태:** 활성 개발 중
