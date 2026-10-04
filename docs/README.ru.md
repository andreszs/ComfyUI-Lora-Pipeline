<h4 align="center">
  <a href="./README.md">English</a> | <a href="./README.de.md">Deutsch</a> | <a href="./README.es.md">Español</a> | <a href="./README.fr.md">Français</a> | <a href="./README.pt.md">Português</a> | Русский | <a href="./README.ja.md">日本語</a> | <a href="./README.ko.md">한국어</a> | <a href="./README.zh.md">中文</a> | <a href="./README.zh-TW.md">繁體中文</a>
</h4>



<p align="center">
  <img alt="Version" src="https://img.shields.io/github/v/tag/andreszs/comfyui-lora-pipeline?label=version" />
  <img alt="Last Commit" src="https://img.shields.io/github/last-commit/andreszs/comfyui-lora-pipeline" />
  <img alt="License" src="https://img.shields.io/github/license/andreszs/comfyui-lora-pipeline" />
</p>
<br />

# ComfyUI LoRA Pipeline

Оболочки кондиционирования на основе области LoRA и узлы планирования LoRA для ComfyUI.

---

## Оглавление

- ✨ [Особенности](#features)
- 📦 [Установка](#installation)
- ✅ [Рекомендуемая настройка (несколько областей / несколько предметов)](#recommended-setup-multi-area--multi-subject)
- 🔧 [Узлы](#nodes)
  - [Conditioning Pipeline (Set Area)](#conditioning-pipeline-set-area)
  - [Conditioning Pipeline (Combine)](#conditioning-pipeline-combine)
  - [ScheduledLoRALoader](#scheduledloraloader)
- 🧩 [Необязательные зависимости](#optional-dependencies)
- 🧭 [Пример workflow с несколькими зонами](#example-workflow-multi-area-conditioning-pipeline)
- 🖼️ [Галерея](#gallery)
- 🚀 [История изменений](#changelog)
- 💙 [Финансирование и поддержка](#funding--support)
- 📄 [Лицензия](#license)

---

## <a id="features"></a>Функции

- Конвейер кондиционирования на основе территории для подсказок по нескольким предметам и регионам.
- Плановый контроль силы LoRA в одном узле с выводом предварительного просмотра кривой.
- Для согласованной многопредметной композиции в нескольких областях настоятельно рекомендуется **ControlNet + OpenPose** через [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio).
- Без ControlNet/OpenPose композиция из нескольких предметов и нескольких областей часто бывает непоследовательной и может потребовать много повторных попыток.
- Только Python: никаких зависимостей JavaScript или внешнего интерфейса не требуется.

---

## <a id="installation"></a>Установка

### Требования
- ComfyUI (последняя сборка)
- Python 3.10+
- Необязательные зависимости для каждого узла: `matplotlib`

### Шаги

1. Клонируйте этот репозиторий в `ComfyUI/custom_nodes/`.
2. Перезапустите ComfyUI.
3. Подтвердите, что узлы появляются под `LoRA Pipeline/`.

---

## <a id="recommended-setup-multi-area--multi-subject"></a>Рекомендуемая настройка (несколько областей / несколько предметов)

- Используйте ControlNet OpenPose (рекомендуется): [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio).
- Сохраняйте глобальное приглашение минимальным и общим.
- Держите `global_strength` на низком уровне (практическое правило: ниже `0.5`).
- Баланс силы по областям: `global_strength` и LoRA силы; не используйте все силы на максимуме.
- Примеры базовых значений, которые сработали хорошо: сильные стороны области около `0.75`, сильные стороны LoRA около `0.90`.

---

## <a id="nodes"></a>Узлы

| Conditioning Pipeline (Combine) | Conditioning Pipeline (Set Area) | Load LoRA (Scheduled) |
|---|---|---|
| ![Conditioning Pipeline (Combine)](../assets/conditioning_pipeline_combine.png) | ![Conditioning Pipeline (Set Area)](../assets/conditioning_pipeline_set_area.png) | ![Load LoRA (Scheduled)](../assets/scheduled_lora_loader.png) |

### <a id="conditioning-pipeline-set-area"></a>Conditioning Pipeline (Set Area)

Определите одну запись с условием области за раз. Этот узел определяет прямоугольную область с шириной, высотой, x и y, а затем применяет к этой области специальную подсказку и силу кондиционирования как часть цепочки конвейера кондиционирования.

**Вкратце:**
- Используйте один экземпляр узла для каждого региона/темы.
- Объедините несколько экземпляров в цепочку для создания регионального конвейера обработки.
- Обеспечивает чистый контроль нескольких объектов перед окончательным объединением.

**Входы:**
- `conditioning` (`CONDITIONING`, обязательно)
- `width`, `height`, `x`, `y` (`FLOAT`, нормализованное `0.0-1.0`)
- `strength` (`FLOAT`, по умолчанию `1.0`)
- `pipeline_in` (`CONDITIONING_PIPELINE`, необязательно)

**Выходы:**
- `pipeline_out` (`CONDITIONING_PIPELINE`)

**Примечания к поведению:**
- Создает новый конвейер, если `pipeline_in` не подключен.
- Добавляет новую региональную запись при подключении `pipeline_in`.
- Сохраняет записи в порядке, чтобы вы могли создавать предсказуемые региональные стеки.
- Более низкая интенсивность областей часто улучшает общее качество изображения, но снижает возможности контроля каждой области.
- Сбалансируйте силу области вместе с силой global_strength и силой LoRA в Create Hook Lora.

**Распространённые ошибки:**
- Предоставление координат пикселей вместо нормализованных значений `0.0-1.0`.
- Устанавливать `width`/`height` рядом с `0` и ожидать видимого эффекта.
- Забывать передавать последний pipeline в `Conditioning Pipeline (Combine)`.

---

### <a id="conditioning-pipeline-combine"></a>Conditioning Pipeline (Combine)

Объедините глобальное положительное/негативное кондиционирование с региональным конвейером для получения результатов с учетом региона. Вместе с Set Area это основной путь для нескольких LoRA и отдельных условий для каждого субъекта/зоны.

**Вкратце:**
- Преобразует ваш региональный конвейер в окончательные положительные/отрицательные результаты.
- Сохраняет глобальный контекст подсказки при добавлении локального регионального контроля.

**Входы:**
- `global_positive` (`CONDITIONING`, обязательно)
- `global_negative` (`CONDITIONING`, обязательно)
- `pipeline` (`CONDITIONING_PIPELINE`, обязательно)
- `global_strength` (`FLOAT`, по умолчанию `0.3`)
- `fast_mode` (`BOOLEAN`, по умолчанию `false`)

**Выходы:**
- `positive_out` (`CONDITIONING`)
- `negative_out` (`CONDITIONING`)
- `areas_out` (`CONDITIONING_AREAS`)

**Подробности об `areas_out`:**

`areas_out` предоставляет список настроенных областных регионов в виде структурированных выходных данных. Каждая запись содержит нормализованные координаты (`x`, `y`, `width`, `height`) и `strength`, определённые в конвейере через `Conditioning Pipeline (Set Area)`. Подключите `areas_out` к [ComfyUI-OpenPose-Studio](https://github.com/andreszs/comfyui-openpose-studio), чтобы автоматически отобразить ваши области обусловливания в редакторе OpenPose — расположение поз будет совпадать с теми самыми регионами, которые вы обусловили. Этот выход также может быть использован любым другим расширением или узлом, принимающим метаданные областей для генерации масок или регионально-ориентированной нисходящей обработки.

**Примечания к поведению:**
- Если конвейер пуст/недействителен, выходные данные возвращаются к глобальным входам, а `areas_out` является пустым списком.
- Применяет региональные записи, а затем комбинированный проход по умолчанию для непокрытых регионов.
- `global_strength` контролирует, насколько сильно глобальный контекст конкурирует с локальными областями.
- Слишком высокое значение global_strength может уменьшить влияние обработки каждой области и отрицательно повлиять на качество изображения.
- Хорошие результаты обычно достигаются за счет баланса глобальной силы с силой по регионам и силы LoRA, а не за счет максимизации всех значений.
- `fast_mode` является необязательным и по умолчанию отключён, поэтому существующие workflows сохраняют прежнее поведение.
- При включении Fast Mode глобальное положительное кондиционирование добавляется к каждому региональному положительному кондиционированию. `global_strength` не игнорируется: он масштабирует только добавленную глобальную часть.
- Если настроенные регионы покрывают весь холст, Fast Mode исключает отдельный глобальный положительный проход. При неполном покрытии сохраняется глобальный fallback, поэтому ускорение будет меньше.
- Fast Mode математически не идентичен стандартному пути и может изменить баланс prompt, композицию или точность субъектов. Сравните результаты перед использованием в production workflows.

**Распространённые ошибки:**
- Подача только одного обуславливающего потока вместо одновременно положительного и отрицательного.
- Перегрузка `global_strength` и размытие деталей области.
- Создавать записи области, но забывать подключать объединённые выходы к пути сэмплера.

---

### <a id="scheduledloraloader"></a>ScheduledLoRALoader

Примените один LoRA с постоянной силой или запланированную кривую в зависимости от прогресса диффузии в одном чистом узле.

**Вкратце:**
- Заменяет беспорядочные цепочки из нескольких собственных узлов LoRA/control.
- Сохраняет синхронизацию, интерполяцию и предварительный просмотр вместе.
- Более четкое соединение графов для временного поведения LoRA.

**Входы:**
- `model` (`MODEL`, обязательно)
- `clip` (`CLIP`, обязательно)
- `lora_name` (`STRING`, обязательно)
- `strength_start`, `strength_end` (`FLOAT`)
- `interpolation` (`STRING`: `linear`, `ease_in`, `ease_out`, `ease_in_out`)
- `start_percent`, `end_percent` (`FLOAT`, `0.0-1.0`)
- `keyframes_count` (`INT`, по умолчанию `4`)
- `apply_to_conds` (`BOOLEAN`, необязательно)

**Выходы:**
- `model` (`MODEL`)
- `clip` (`CLIP`)
- `curve_preview` (`IMAGE`)

**Примечания к поведению:**
- Если `lora_name` равен `None`, прохождение модели/клипа и предварительный просмотр по-прежнему визуализируются.
- Если начальная и конечная сильные стороны совпадают, оно ведет себя как постоянное приложение LoRA.
- Предварительный просмотр кривой помогает быстро проверить время перед полной визуализацией.

**Распространённые ошибки:**
- Забывание `matplotlib` при использовании `curve_preview`.
- Использование окна расписания, которое не соответствует назначению времени выборки.
- Ожидается, что этот узел напрямую выведет `CONDITIONING`.

---

## <a id="optional-dependencies"></a>Дополнительные зависимости

Устанавливайте только то, что вам нужно, в той же среде Python, которую использует ComfyUI.

- `ScheduledLoRALoader` предварительный просмотр кривой: `python -m pip install matplotlib`

---

## <a id="example-workflow-multi-area-conditioning-pipeline"></a>Пример workflow с несколькими зонами

[![Полный рабочий процесс](../workflows/conditioninig_pipeline_area_wf.png)](../workflows/conditioninig_pipeline_area_wf.png)

Вы можете перетащить это изображение рабочего процесса в ComfyUI, чтобы импортировать/загрузить полный график.

#### Настройка зоны 1

[![Кондиционирование зоны 1](../assets/conditioninig_area_1.png)](../assets/conditioninig_area_1.png)

- Используйте собственный `Create Hook Lora` для загрузки одного LoRA и определения запроса/условия области для области 1.
- Подключите это условие к `Conditioning Pipeline (Set Area)` и установите `width`, `height`, `x`, `y` и `strength` для этого региона.

#### Настройка зоны 2

[![Кондиционирование зоны 2](../assets/conditioninig_area_2.png)](../assets/conditioninig_area_2.png)

- Повторите ту же самую схему: еще один `Create Hook Lora` + еще один `Conditioning Pipeline (Set Area)`.
- Вы можете продолжать повторять этот шаблон для дополнительных областей.

#### Цепочка pipeline и объединение

[![Conditioning Combine](../assets/conditioning_combine.png)](../assets/conditioning_combine.png)

- Соедините `pipeline_out` из области 1 в область 2 (соединенные записи конвейера).
- Отправьте `pipeline_out` из последней области в `Conditioning Pipeline (Combine)`, что объединит конвейер области с глобальным кондиционированием.
- Направьте объединенный вывод непосредственно в `KSampler` или в `ControlNet`; в этом примере он направляется в `ControlNet`.

#### OpenPose / ControlNet руководство

- OpenPose/ControlNet в целом является необязательным, но для этого конкретного рабочего процесса составления нескольких предметов и нескольких областей настоятельно рекомендуется для последовательной композиции.
- См. [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio) от того же автора (более новый репозиторий).

#### Глобальное размещение `Styler Pipeline`

[![Глобальное размещение `Styler Pipeline` с кондиционированием территории + ControlNet](../assets/styler_pipeline_node.png)](../assets/styler_pipeline_node.png)

Глобальное оформление означает применение `Styler Pipeline` один раз ко всему изображению в дополнение (или вместо) кондиционирования каждой области.

- Общее правило: подключайте `Styler Pipeline` перед `KSampler`.
- При использовании ControlNet `Styler Pipeline` можно подключить либо до применения ControlNet, либо после применения ControlNet.
- На практике результат обычно эквивалентен, поэтому выберите наиболее удобное расположение на графике.

#### `global_strength` компромиссов

- Слишком большое увеличение `global_strength` снижает относительное влияние обусловленности каждой области и может ослабить идентичность LoRA/стиля каждой области.
- Более высокая глобальная сила также может негативно повлиять на качество изображения.
- Держите `global_strength` на низком уровне и сохраняйте глобальное приглашение минимальным/общим.
- Эмпирическое правило: обычно используйте значения ниже `0.5` (проверено до `0.5`) и не полагайтесь на глобальные условия, выходящие за рамки общих рекомендаций.
- Снижение силы LoRA имеет тенденцию снижать идентичность LoRA или точность персонажа, в то время как снижение силы области имеет тенденцию уменьшать контроль над каждой областью.
- Не рекомендуется использовать все до максимума, поскольку высокие комбинированные значения могут привести к ухудшению качества изображения. Это особенно актуально при смешивании LoRA от разных авторов, что может привести к нестабильному качеству.
- Эмпирическое правило для многосимвольных LoRA: по возможности используйте LoRA от одного и того же автора или аналогичный подход к обучению для более согласованных комбинированных результатов.

---

## <a id="gallery"></a>Галерея

| Предварительный просмотр | Описание |
|---------|-------------|
| [![conditioning_pipeline_area](../workflows/conditioninig_pipeline_area.png)](../workflows/conditioninig_pipeline_area.png) | **Конвейер подготовки — несколько областей с ControlNet OpenPose**<br><br>Демонстрирует несколько вертикальных областей с несколькими LoRA без кровотечения LoRA с использованием ControlNet OpenPose.<br><br>Требуется [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio). |
| [![conditioning_pipeline_styled](../workflows/conditioninig_pipeline_styled.png)](../workflows/conditioninig_pipeline_styled.png) | **Конвейер подготовки — несколько областей с ControlNet и стилями**<br><br>Демонстрирует несколько областей и несколько LoRA со стилем для каждой области, применяемым к каждой области независимо.<br><br>Требуются [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio) и [comfyui-styler-pipeline](https://github.com/andreszs/comfyui-styler-pipeline).<br><br>Этот рабочий процесс использует стили для каждой области, то есть каждая область имеет свои собственные стили, настроенные отдельно. Глобальное оформление также возможно, подключив узел Styler непосредственно перед ControlNet. |

В [этой статье](https://www.andreszsogon.com/building-a-multi-character-comfyui-workflow-with-area-conditioning-openpose-control-and-style-layering/) можно увидеть полный workflow, объединяющий несколько conditioning area, OpenPose, ControlNet и Styler, используемых одновременно.

---

## <a id="changelog"></a>История изменений

### 1.1.4

- Оптимизация регионального кондиционирования сократила измеренное время генерации примерно со 144 до 70 секунд в протестированном SDXL workflow с двумя регионами — примерно на 51% меньше времени рендеринга.
- Необязательный Fast Mode завершил эквивалентный тест с полным покрытием примерно за 54 секунды — до 63% меньше времени по сравнению с предыдущей реализацией.
- Производительность зависит от GPU, модели, разрешения, sampler, конфигурации ControlNet и покрытия регионов. Fast Mode также может давать визуальные отличия, поэтому по умолчанию он отключён.

---

## <a id="funding--support"></a>Финансирование и поддержка

### Почему ваша поддержка важна

Этот плагин разрабатывается и поддерживается независимо, с регулярным использованием **платных агентов искусственного интеллекта** для ускорения отладки, тестирования и улучшения качества жизни. Если вы считаете это полезным, финансовая поддержка поможет обеспечить устойчивое развитие.

Ваш вклад помогает:

* Финансирование инструментов ИИ для более быстрых исправлений и новых функций.
* Покрывает текущие работы по обслуживанию и совместимости обновлений ComfyUI.
* Предотвращает замедление разработки при достижении пределов использования.

> [!TIP]
> Не жертвуете? Звезда GitHub ⭐ по-прежнему очень помогает, улучшая видимость и помогая большему количеству пользователей.

### 💙 Поддержите этот проект

<table style="width: 100%; table-layout: fixed;">
  <tr>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">Ko-fi</h4>
        <a href="https://ko-fi.com/D1D716OLPM" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_kofi.svg" alt="Ko-fi Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="https://ko-fi.com/D1D716OLPM" target="_blank" rel="noopener noreferrer">Купить кофе</a></p>
      </div>
    </td>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">PayPal</h4>
        <a href="https://www.paypal.com/ncp/payment/GEEM324PDD9NC" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_paypal.svg" alt="PayPal Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="https://www.paypal.com/ncp/payment/GEEM324PDD9NC" target="_blank" rel="noopener noreferrer">Открыть PayPal</a></p>
      </div>
    </td>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">USDC (только Arbitrum ⚠️)</h4>
        <a href="https://arbiscan.io/address/0xe36a336fC6cc9Daae657b4A380dA492AB9601e73" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_usdc.svg" alt="USDC Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="#usdc-address">Показать адрес</a></p>
      </div>
    </td>
  </tr>
</table>

<details>
  <summary>Предпочитаете сканирование? Показать QR-коды</summary>
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
  <summary>Показать адрес USDC</summary>

```text
0xe36a336fC6cc9Daae657b4A380dA492AB9601e73
```

> [!WARNING]
> Отправляйте USDC только через Arbitrum One. Переводы, отправленные в любую другую сеть, не дойдут и могут быть безвозвратно потеряны.
</details>

## <a id="license"></a>Лицензия

Лицензия MIT — полный текст см. в [LICENSE](../LICENSE).

---

**Поддерживает:** andreszs
**Статус:** Активная разработка
