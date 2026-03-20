<h4 align="center">
  <a href="./README.md">English</a> | Deutsch | <a href="./README.es.md">Español</a> | <a href="./README.fr.md">Français</a> | <a href="./README.pt.md">Português</a> | <a href="./README.ru.md">Русский</a> | <a href="./README.ja.md">日本語</a> | <a href="./README.ko.md">한국어</a> | <a href="./README.zh.md">中文</a> | <a href="./README.zh-TW.md">繁體中文</a>
</h4>



<p align="center">
  <img alt="Version" src="https://img.shields.io/github/v/tag/andreszs/comfyui-lora-pipeline?label=version" />
  <img alt="Last Commit" src="https://img.shields.io/github/last-commit/andreszs/comfyui-lora-pipeline" />
  <img alt="License" src="https://img.shields.io/github/license/andreszs/comfyui-lora-pipeline" />
</p>
<br />

# ComfyUI LoRA Pipeline

Bereichsbasierte LoRA Konditionierungs-Wrapper und LoRA Planungsknoten für ComfyUI.

---

## Inhaltsverzeichnis

- ✨ [Funktionen](#features)
- 📦 [Installation](#installation)
- ✅ [Empfohlene Einrichtung (mehrere Bereiche / mehrere Themen)](#recommended-setup-multi-area--multi-subject)
- 🔧 [Knoten](#nodes)
  - [Conditioning Pipeline (Set Area)](#conditioning-pipeline-set-area)
  - [Conditioning Pipeline (Combine)](#conditioning-pipeline-combine)
  - [ScheduledLoRALoader](#scheduledloraloader)
- 🧩 [Optionale Abhängigkeiten](#optional-dependencies)
- 🧭 [Mehrbereich-Beispielworkflow](#example-workflow-multi-area-conditioning-pipeline)
- 🖼️ [Galerie](#gallery)
- 💙 [Finanzierung & Unterstützung](#funding--support)
- 📄 [Lizenz](#license)

---

## <a id="features"></a>Funktionen

- Bereichsbasierte Konditionierungspipeline für Eingabeaufforderungen für mehrere Themen und Regionen.
- Ein-Knoten-gesteuerte LoRA-Stärkesteuerung mit einer Kurvenvorschau-Ausgabe.
- Für eine konsistente Komposition mit mehreren Themen über mehrere Bereiche hinweg wird **ControlNet + OpenPose dringend empfohlen** über [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio).
- Ohne ControlNet/OpenPose ist die Komposition mit mehreren Themen und mehreren Bereichen oft inkonsistent und erfordert möglicherweise viele Wiederholungsversuche.
- Nur Python: Keine JavaScript- oder Frontend-Abhängigkeiten erforderlich.

---

## <a id="installation"></a>Installation

### Anforderungen
- ComfyUI (aktueller Build)
- Python 3.10+
- Optionale Abhängigkeiten pro Knoten: `matplotlib`

### Schritte

1. Klonen Sie dieses Repository in `ComfyUI/custom_nodes/`.
2. Starten Sie ComfyUI neu.
3. Bestätigen Sie, dass Knoten unter `LoRA Pipeline/` angezeigt werden.

---

## <a id="recommended-setup-multi-area--multi-subject"></a>Empfohlenes Setup (Mehrbereich / Mehrsubjekt)

- Verwenden Sie ControlNet OpenPose (empfohlen): [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio).
- Halten Sie die globale Eingabeaufforderung minimal und allgemein.
- Halten Sie `global_strength` niedrig (Faustregel: unter `0.5`).
- Balance pro Bereich Stärke, `global_strength` und LoRA Stärke; Maximieren Sie nicht alle Stärken.
- Beispielhafte Grundwerte, die gut funktioniert haben: Flächenstärken um `0.75`, LoRA Stärken um `0.90`.

---

## <a id="nodes"></a>Knoten

| Conditioning Pipeline (Combine) | Conditioning Pipeline (Set Area) | Load LoRA (Scheduled) |
|---|---|---|
| ![Conditioning Pipeline (Combine)](../assets/conditioning_pipeline_combine.png) | ![Conditioning Pipeline (Set Area)](../assets/conditioning_pipeline_set_area.png) | ![Load LoRA (Scheduled)](../assets/scheduled_lora_loader.png) |

### <a id="conditioning-pipeline-set-area"></a>Conditioning Pipeline (Set Area)

Definieren Sie jeweils einen bereichsbedingten Eintrag. Dieser Knoten definiert einen rechteckigen Bereich mit Breite, Höhe, x und y und wendet dann als Teil einer verketteten Konditionierungspipeline eine spezielle Konditionierungsaufforderung und -stärke auf diesen Bereich an.

**Auf einen Blick:**
- Verwenden Sie eine Knoteninstanz pro Region/Betreff-Eingabeaufforderung.
- Verketten Sie mehrere Instanzen, um eine regionale Konditionierungspipeline aufzubauen.
- Ermöglicht eine saubere Mehrsubjektkontrolle vor der endgültigen Kombination.

**Eingaben:**
- `conditioning` (`CONDITIONING`, erforderlich)
- `width`, `height`, `x`, `y` (`FLOAT`, normalisiert `0.0-1.0`)
- `strength` (`FLOAT`, Standard `1.0`)
- `pipeline_in` (`CONDITIONING_PIPELINE`, optional)

**Ausgaben:**
- `pipeline_out` (`CONDITIONING_PIPELINE`)

**Hinweise zum Verhalten:**
- Erstellt eine neue Pipeline, wenn `pipeline_in` nicht verbunden ist.
- Fügt einen neuen regionalen Eintrag hinzu, wenn `pipeline_in` verbunden ist.
- Hält die Einträge geordnet, sodass Sie vorhersehbare regionale Stapel aufbauen können.
- Niedrigere Bereichsstärken verbessern häufig die Gesamtbildqualität, verringern jedoch die Kontrollbefugnis pro Bereich.
- Balancieren Sie die Flächenstärke zusammen mit global_strength und der LoRA-Stärke in Create Hook Lora.

**Häufige Fehler:**
- Bereitstellung von Pixelkoordinaten anstelle normalisierter `0.0-1.0`-Werte.
- `width`/`height` in die Nähe von `0` setzen und sichtbare Wirkung erwarten.
- Vergessen, die letzte Pipeline an `Conditioning Pipeline (Combine)` zu übergeben.

---

### <a id="conditioning-pipeline-combine"></a>Conditioning Pipeline (Combine)

Kombinieren Sie globale positive/negative Konditionierung mit der Bereichspipeline für regionalbezogene Ergebnisse. Zusammen mit Set Area ist dies der Kernpfad für Multi-LoRAs und separate Konditionierungen pro Subjekt/Zone.

**Auf einen Blick:**
- Wandelt Ihre regionale Pipeline in endgültige positive/negative Ergebnisse um.
- Behält den globalen Eingabeaufforderungskontext bei und fügt gleichzeitig lokale regionale Kontrolle hinzu.

**Eingaben:**
- `global_positive` (`CONDITIONING`, erforderlich)
- `global_negative` (`CONDITIONING`, erforderlich)
- `pipeline` (`CONDITIONING_PIPELINE`, erforderlich)
- `global_strength` (`FLOAT`, Standard `0.3`)

**Ausgaben:**
- `positive_out` (`CONDITIONING`)
- `negative_out` (`CONDITIONING`)

**Hinweise zum Verhalten:**
- Wenn die Pipeline leer/ungültig ist, greifen die Ausgaben auf die globalen Eingaben zurück.
- Wendet regionale Einträge an und anschließend einen Standard-Kombinationsdurchgang für nicht abgedeckte Regionen.
- `global_strength` steuert, wie stark der globale Kontext mit lokalen Bereichen konkurriert.
- Wenn Sie global_strength zu hoch einstellen, kann dies den Einfluss der bereichsspezifischen Konditionierung verringern und sich negativ auf die Bildqualität auswirken.
- Gute Ergebnisse werden im Allgemeinen dadurch erzielt, dass die globale Stärke mit der Stärke pro Bereich und der LoRA-Stärke in Einklang gebracht wird, anstatt alle Werte zu maximieren.

**Häufige Fehler:**
- Es wird nur ein Konditionierungsstrom zugeführt, statt sowohl positiv als auch negativ.
- Übersteuerung von `global_strength` und Auswaschen von Bereichsdetails.
- Erstellen Sie Bereichseinträge, vergessen Sie jedoch, die kombinierten Ausgänge mit Ihrem Sampler-Pfad zu verbinden.

---

### <a id="scheduledloraloader"></a>ScheduledLoRALoader

Tragen Sie einen LoRA mit konstanter Stärke oder einer geplanten Kurve über den Diffusionsfortschritt in einem sauberen Knoten auf.

**Auf einen Blick:**
- Ersetzt chaotische Ketten mehrerer nativer LoRA/Kontrollknoten.
- Hält Timing, Interpolation und Vorschau zusammen.
- Sauberere Diagrammverkabelung für zeitliches LoRA-Verhalten.

**Eingaben:**
- `model` (`MODEL`, erforderlich)
- `clip` (`CLIP`, erforderlich)
- `lora_name` (`STRING`, erforderlich)
- `strength_start`, `strength_end` (`FLOAT`)
- `interpolation` (`STRING`: `linear`, `ease_in`, `ease_out`, `ease_in_out`)
- `start_percent`, `end_percent` (`FLOAT`, `0.0-1.0`)
- `keyframes_count` (`INT`, Standard `4`)
- `apply_to_conds` (`BOOLEAN`, optional)

**Ausgaben:**
- `model` (`MODEL`)
- `clip` (`CLIP`)
- `curve_preview` (`IMAGE`)

**Hinweise zum Verhalten:**
- Wenn `lora_name` `None` ist, wird das Modell/der Clip durchlaufen und die Vorschau wird weiterhin gerendert.
- Wenn Start- und Endstärke übereinstimmen, verhält es sich wie eine konstante LoRA-Anwendung.
- Mithilfe der Kurvenvorschau können Sie das Timing vor dem vollständigen Rendern schnell überprüfen.

**Häufige Fehler:**
- `matplotlib` vergessen, wenn `curve_preview` verwendet wird.
- Verwendung eines Zeitplanfensters, das nicht mit der Timing-Absicht des Samplers übereinstimmt.
- Es wird erwartet, dass dieser Knoten `CONDITIONING` direkt ausgibt.

---

## <a id="optional-dependencies"></a>Optionale Abhängigkeiten

Installieren Sie nur das, was Sie benötigen, in derselben Python-Umgebung, die von ComfyUI verwendet wird.

- `ScheduledLoRALoader` Kurvenvorschau: `python -m pip install matplotlib`

---

## <a id="example-workflow-multi-area-conditioning-pipeline"></a>Mehrbereich-Beispielworkflow

[![Vollständiger Workflow](../workflows/conditioninig_pipeline_area_wf.png)](../workflows/conditioninig_pipeline_area_wf.png)

Sie können dieses Workflow-Bild per Drag & Drop in ComfyUI ziehen, um das vollständige Diagramm zu importieren/laden.

#### Einrichtung von Bereich 1

[![Bereich 1 Konditionierung](../assets/conditioninig_area_1.png)](../assets/conditioninig_area_1.png)

- Verwenden Sie natives `Create Hook Lora`, um ein LoRA zu laden und die Bereichsaufforderung/-konditionierung für Bereich 1 zu definieren.
- Verbinden Sie diese Konditionierung mit `Conditioning Pipeline (Set Area)` und legen Sie `width`, `height`, `x`, `y` und `strength` für diese Region fest.

#### Einrichtung von Bereich 2

[![Bereich 2 Konditionierung](../assets/conditioninig_area_2.png)](../assets/conditioninig_area_2.png)

- Wiederholen Sie genau das gleiche Muster: ein weiterer `Create Hook Lora` + ein weiterer `Conditioning Pipeline (Set Area)`.
- Sie können dieses Muster für weitere Bereiche wiederholen.

#### Pipeline-Verkettung und Kombination

[![Conditioning Combine](../assets/conditioning_combine.png)](../assets/conditioning_combine.png)

- Verketten Sie `pipeline_out` von Bereich 1 in Bereich 2 (verkettete Pipeline-Einträge).
- Senden Sie `pipeline_out` vom letzten Bereich an `Conditioning Pipeline (Combine)`, wodurch die Bereichspipeline mit der globalen Konditionierung zusammengeführt wird.
- Leiten Sie die kombinierte Ausgabe direkt an `KSampler` oder an `ControlNet` weiter. In diesem Beispiel wird es an `ControlNet` weitergeleitet.

#### OpenPose / ControlNet Anleitung

- OpenPose/ControlNet ist im Allgemeinen optional, wird jedoch für diesen speziellen Kompositionsworkflow mit mehreren Themen und mehreren Bereichen für eine konsistente Komposition dringend empfohlen.
- Siehe [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio) vom selben Autor (neueres Repository).

#### Globale `Styler Pipeline`-Platzierung

[![Globale `Styler Pipeline` Platzierung mit Flächenkonditionierung + ControlNet](../assets/styler_pipeline_node.png)](../assets/styler_pipeline_node.png)

Globales Styling bedeutet, dass `Styler Pipeline` zusätzlich zur bereichsbezogenen Konditionierung (oder anstelle dieser) einmal auf das gesamte Bild angewendet wird.

- Allgemeine Regel: Verbinden Sie `Styler Pipeline` vor `KSampler`.
- Bei Verwendung von ControlNet kann `Styler Pipeline` entweder vor der Anwendung von ControlNet oder nach der Anwendung von ControlNet verbunden werden.
- In der Praxis ist das Ergebnis in der Regel gleichwertig. Wählen Sie daher die Platzierung, die in Ihrem Diagramm bequemer ist.

#### `global_strength` Kompromisse

- Eine zu starke Erhöhung von `global_strength` verringert den relativen Einfluss der Konditionierungen pro Bereich und kann die Identität von LoRA/Stil pro Bereich schwächen.
- Eine höhere globale Stärke kann sich auch negativ auf die Bildqualität auswirken.
- Halten Sie `global_strength` niedrig und halten Sie die globale Eingabeaufforderung minimal/allgemein.
- Faustregel: Verwenden Sie im Allgemeinen Werte unter `0.5` (getestet bis `0.5`) und verlassen Sie sich nicht auf globale Konditionierungen, die über allgemeine Richtlinien hinausgehen.
- Eine Verringerung der LoRA-Stärke verringert tendenziell die LoRA-Identität oder die Charaktertreue, während eine Verringerung der Bereichsstärke tendenziell die Kontrolle pro Bereich verringert.
- Es wird nicht empfohlen, alles zu maximieren, da hohe kombinierte Stärken die Bildqualität beeinträchtigen können. Dies gilt insbesondere dann, wenn LoRAs von verschiedenen Autoren gemischt werden, was zu inkonsistenter Qualität führen kann.
- Faustregel für LoRAs mit mehreren Zeichen: Verwenden Sie nach Möglichkeit LoRAs desselben Autors oder einen ähnlichen Trainingsansatz, um konsistentere kombinierte Ergebnisse zu erzielen.

---

## <a id="gallery"></a>Galerie

| Vorschau | Beschreibung |
|---------|-------------|
| [![conditioning_pipeline_area](../workflows/conditioninig_pipeline_area.png)](../workflows/conditioninig_pipeline_area.png) | **Konditionierungspipeline – mehrere Bereiche mit ControlNet OpenPose**<br><br>Demonstriert mehrere vertikale Bereiche mit mehreren LoRAs ohne LoRA-Bleeding unter Verwendung von ControlNet OpenPose.<br><br>Erfordert [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio). |
| [![conditioning_pipeline_styled](../workflows/conditioninig_pipeline_styled.png)](../workflows/conditioninig_pipeline_styled.png) | **Konditionierungspipeline – mehrere Bereiche mit ControlNet und Styling**<br><br>Demonstriert mehrere Bereiche und mehrere LoRAs mit bereichsspezifischem Styling, das unabhängig auf jede Region angewendet wird.<br><br>Erfordert [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio) und [comfyui-styler-pipeline](https://github.com/andreszs/comfyui-styler-pipeline).<br><br>Dieser Workflow verwendet Pro-Bereichs-Styling, was bedeutet, dass jeder Bereich seine eigenen Stile hat, die separat konfiguriert werden. Globales Styling ist auch möglich, indem der Styler-Knoten direkt vor ControlNet verbunden wird. |

In [diesem Beitrag](https://www.andreszsogon.com/building-a-multi-character-comfyui-workflow-with-area-conditioning-openpose-control-and-style-layering/) findest du ein vollständiges Workflow, das mehrere Conditioning-Bereiche, OpenPose, ControlNet und Styler gleichzeitig kombiniert.

---

## <a id="funding--support"></a>Finanzierung und Unterstützung

### Warum Ihre Unterstützung wichtig ist

Dieses Plugin wird unabhängig entwickelt und gepflegt, wobei regelmäßig **kostenpflichtige KI-Agenten** eingesetzt werden, um Debugging, Tests und Verbesserungen der Lebensqualität zu beschleunigen. Wenn Sie es sinnvoll finden, trägt finanzielle Unterstützung dazu bei, dass die Entwicklung stetig voranschreitet.

Ihr Beitrag hilft:

* Finanzieren Sie KI-Tools für schnellere Korrekturen und neue Funktionen
* Decken Sie laufende Wartungs- und Kompatibilitätsarbeiten für ComfyUI-Updates ab
* Verhindern Sie Entwicklungsverlangsamungen, wenn die Nutzungsgrenzen erreicht sind

> [!TIP]
> Nicht spenden? Ein GitHub-Star ⭐ hilft immer noch sehr, indem er die Sichtbarkeit verbessert und mehr Benutzern hilft

### 💙 Unterstützen Sie dieses Projekt

<table style="width: 100%; table-layout: fixed;">
  <tr>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">Ko-fi</h4>
        <a href="https://ko-fi.com/D1D716OLPM" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_kofi.svg" alt="Ko-fi Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="https://ko-fi.com/D1D716OLPM" target="_blank" rel="noopener noreferrer">Kaufe einen Kaffee</a></p>
      </div>
    </td>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">PayPal</h4>
        <a href="https://www.paypal.com/ncp/payment/GEEM324PDD9NC" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_paypal.svg" alt="PayPal Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="https://www.paypal.com/ncp/payment/GEEM324PDD9NC" target="_blank" rel="noopener noreferrer">PayPal öffnen</a></p>
      </div>
    </td>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">USDC (nur Arbitrum ⚠️)</h4>
        <a href="https://arbiscan.io/address/0xe36a336fC6cc9Daae657b4A380dA492AB9601e73" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_usdc.svg" alt="USDC Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="#usdc-address">Adresse anzeigen</a></p>
      </div>
    </td>
  </tr>
</table>

<details>
  <summary>Scannen Sie lieber? QR-Codes anzeigen</summary>
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
  <summary>USDC-Adresse anzeigen</summary>

```text
0xe36a336fC6cc9Daae657b4A380dA492AB9601e73
```

> [!WARNING]
> Senden Sie USDC ausschließlich über Arbitrum One. Überweisungen über jedes andere Netzwerk kommen nicht an und können dauerhaft verloren gehen.
</details>

## <a id="license"></a>Lizenz

MIT-Lizenz – siehe [LICENSE](../LICENSE) für den vollständigen Text.

---

**Verwaltet von:** andreszs
**Status:** Aktive Entwicklung
