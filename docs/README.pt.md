<h4 align="center">
  <a href="./README.md">English</a> | <a href="./README.de.md">Deutsch</a> | <a href="./README.es.md">Español</a> | <a href="./README.fr.md">Français</a> | Português | <a href="./README.ru.md">Русский</a> | <a href="./README.ja.md">日本語</a> | <a href="./README.ko.md">한국어</a> | <a href="./README.zh.md">中文</a> | <a href="./README.zh-TW.md">繁體中文</a>
</h4>



<p align="center">
  <img alt="Version" src="https://img.shields.io/github/v/tag/andreszs/comfyui-lora-pipeline?label=version" />
  <img alt="Last Commit" src="https://img.shields.io/github/last-commit/andreszs/comfyui-lora-pipeline" />
  <img alt="License" src="https://img.shields.io/github/license/andreszs/comfyui-lora-pipeline" />
</p>
<br />

# ComfyUI LoRA Pipeline

Wrappers de condicionamento LoRA baseados em área e nós de agendamento LoRA para ComfyUI.

---

## Índice

- ✨ [Recursos](#features)
- 📦 [Instalação](#installation)
- ✅ [Configuração recomendada (multiárea / multiassunto)](#recommended-setup-multi-area--multi-subject)
- 🔧 [Nós](#nodes)
  - [Conditioning Pipeline (Set Area)](#conditioning-pipeline-set-area)
  - [Conditioning Pipeline (Combine)](#conditioning-pipeline-combine)
  - [ScheduledLoRALoader](#scheduledloraloader)
- 🧩 [Dependências opcionais](#optional-dependencies)
- 🧭 [Workflow de exemplo multiárea](#example-workflow-multi-area-conditioning-pipeline)
- 🖼️ [Galeria](#gallery)
- 🚀 [Registro de alterações](#changelog)
- 💙 [Financiamento e Apoio](#funding--support)
- 📄 [Licença](#license)

---

## <a id="features"></a>Características

- Pipeline de condicionamento baseado em área para prompts multissujeitos e multirregionais.
- Controle de força LoRA agendado de um nó com uma saída de visualização de curva.
- Para uma composição consistente de vários assuntos em várias áreas, **ControlNet + OpenPose é fortemente recomendado** via [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio).
- Sem ControlNet/OpenPose, a composição de vários assuntos e áreas múltiplas costuma ser inconsistente e pode exigir muitas tentativas.
- Somente Python: não são necessárias dependências de JavaScript ou frontend.

---

## <a id="installation"></a>Instalação

### Requisitos
- ComfyUI (compilação recente)
- Python 3.10+
- Deps opcionais por nó: `matplotlib`

### Passos

1. Clone este repositório em `ComfyUI/custom_nodes/`.
2. Reinicie ComfyUI.
3. Confirme se os nós aparecem em `LoRA Pipeline/`.

---

## <a id="recommended-setup-multi-area--multi-subject"></a>Configuração recomendada (multiárea/multiassunto)

- Use ControlNet OpenPose (recomendado): [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio).
- Mantenha o prompt global mínimo e geral.
- Mantenha `global_strength` baixo (regra geral: abaixo de `0.5`).
- Equilibre a força por área, força `global_strength` e força LoRA; não maximize todas as forças.
- Exemplos de valores de referência que funcionaram bem: intensidades de área em torno de `0.75`, intensidades de LoRA em torno de `0.90`.

---

## <a id="nodes"></a>Nós

| Conditioning Pipeline (Combine) | Conditioning Pipeline (Set Area) | Load LoRA (Scheduled) |
|---|---|---|
| ![Conditioning Pipeline (Combine)](../assets/conditioning_pipeline_combine.png) | ![Conditioning Pipeline (Set Area)](../assets/conditioning_pipeline_set_area.png) | ![Load LoRA (Scheduled)](../assets/scheduled_lora_loader.png) |

### <a id="conditioning-pipeline-set-area"></a>Conditioning Pipeline (Set Area)

Defina uma entrada condicionada por área por vez. Este nó define uma região retangular com largura, altura, x e y e, em seguida, aplica um prompt de condicionamento dedicado e força a essa região como parte de um pipeline de condicionamento encadeado.

**Em resumo:**
- Use uma instância de nó por prompt de região/assunto.
- Encadeie várias instâncias para construir um pipeline de condicionamento regional.
- Permite um controle limpo de vários assuntos antes da combinação final.

**Entradas:**
- `conditioning` (`CONDITIONING`, obrigatório)
- `width`, `height`, `x`, `y` (`FLOAT`, `0.0-1.0` normalizado)
- `strength` (`FLOAT`, padrão `1.0`)
- `pipeline_in` (`CONDITIONING_PIPELINE`, opcional)

**Saídas:**
- `pipeline_out` (`CONDITIONING_PIPELINE`)

**Notas de comportamento:**
- Cria um novo pipeline se `pipeline_in` não estiver conectado.
- Acrescenta uma nova entrada regional quando `pipeline_in` está conectado.
- Mantém as entradas ordenadas para que você possa criar pilhas regionais previsíveis.
- As intensidades de área mais baixas geralmente melhoram a qualidade geral da imagem, mas reduzem a autoridade de controle por área.
- Equilibre a força da área junto com global_strength e a força de LoRA em Create Hook Lora.

**Erros comuns:**
- Fornecendo coordenadas de pixel em vez de valores `0.0-1.0` normalizados.
- Definir `width`/`height` perto de `0` e esperar efeito visível.
- Esquecendo de passar o pipeline final para `Conditioning Pipeline (Combine)`.

---

### <a id="conditioning-pipeline-combine"></a>Conditioning Pipeline (Combine)

Combine o condicionamento positivo/negativo global com o pipeline de área para resultados conscientes da região. Juntamente com Set Area, este é o caminho principal para multi-LoRAs e condicionamentos separados por assunto/zona.

**Em resumo:**
- Converte seu pipeline regional em resultados finais positivos/negativos.
- Mantém o contexto de prompt global enquanto adiciona controle regional local.

**Entradas:**
- `global_positive` (`CONDITIONING`, obrigatório)
- `global_negative` (`CONDITIONING`, obrigatório)
- `pipeline` (`CONDITIONING_PIPELINE`, obrigatório)
- `global_strength` (`FLOAT`, padrão `0.3`)
- `fast_mode` (`BOOLEAN`, padrão `false`)

**Saídas:**
- `positive_out` (`CONDITIONING`)
- `negative_out` (`CONDITIONING`)
- `areas_out` (`CONDITIONING_AREAS`)

**Detalhes sobre `areas_out`:**

`areas_out` expõe a lista de regiões de área configuradas como uma saída de dados estruturada. Cada entrada contém as coordenadas normalizadas (`x`, `y`, `width`, `height`) e `strength` definidas no pipeline via `Conditioning Pipeline (Set Area)`. Conecte `areas_out` ao [ComfyUI-OpenPose-Studio](https://github.com/andreszs/comfyui-openpose-studio) para espelhar automaticamente suas áreas de condicionamento no editor OpenPose — o posicionamento das poses se alinhará com as regiões exatas que você condicionou. Esta saída também pode ser consumida por qualquer outra extensão ou nó que aceite metadados de área para geração de máscaras ou processamento posterior com reconhecimento de região.

**Notas de comportamento:**
- Se o pipeline estiver vazio/inválido, as saídas voltam para as entradas globais e `areas_out` é uma lista vazia.
- Aplica entradas regionais e, em seguida, um passe combinado padrão para regiões descobertas.
- `global_strength` controla a intensidade com que o contexto global compete com as áreas locais.
- Pressionar global_strength muito alto pode reduzir a influência do condicionamento por área e impactar negativamente a qualidade da imagem.
- Bons resultados geralmente vêm do equilíbrio da força global com a força por área e da força LoRA, em vez de maximizar todos os valores.
- `fast_mode` é opcional e vem desativado, portanto os workflows existentes mantêm o comportamento anterior.
- Quando ativado, Fast Mode concatena o condicionamento positivo global em cada condicionamento positivo regional. `global_strength` não é ignorado: ele dimensiona apenas a parte global adicionada.
- Quando as regiões configuradas cobrem todo o canvas, Fast Mode evita um passe positivo global separado. Se a cobertura estiver incompleta, o fallback global será mantido e o ganho de velocidade será menor.
- Fast Mode não é matematicamente idêntico ao caminho padrão e pode alterar o equilíbrio do prompt, a composição ou a fidelidade dos temas. Compare os resultados antes de usá-lo em produção.

**Erros comuns:**
- Alimentando apenas um fluxo de condicionamento em vez de positivo e negativo.
- Forçar `global_strength` em excesso e perder detalhes da área.
- Construindo entradas de área, mas esquecendo de conectar as saídas combinadas ao caminho do amostrador.

---

### <a id="scheduledloraloader"></a>ScheduledLoRALoader

Aplique um LoRA com força constante ou uma curva programada sobre o progresso da difusão, em um nó limpo.

**Em resumo:**
- Substitui cadeias confusas de vários nós nativos LoRA/controle.
- Mantém o tempo, a interpolação e a visualização juntos.
- Fiação de gráfico mais limpa para comportamento LoRA temporal.

**Entradas:**
- `model` (`MODEL`, obrigatório)
- `clip` (`CLIP`, obrigatório)
- `lora_name` (`STRING`, obrigatório)
- `strength_start`, `strength_end` (`FLOAT`)
- `interpolation` (`STRING`: `linear`, `ease_in`, `ease_out`, `ease_in_out`)
- `start_percent`, `end_percent` (`FLOAT`, `0.0-1.0`)
- `keyframes_count` (`INT`, padrão `4`)
- `apply_to_conds` (`BOOLEAN`, opcional)

**Saídas:**
- `model` (`MODEL`)
- `clip` (`CLIP`)
- `curve_preview` (`IMAGE`)

**Notas de comportamento:**
- Se `lora_name` for `None`, o modelo/clip passa e a visualização ainda é renderizada.
- Se as forças inicial e final corresponderem, ele se comporta como um aplicativo LoRA constante.
- A visualização da curva ajuda a verificar rapidamente o tempo antes da renderização completa.

**Erros comuns:**
- Esquecendo `matplotlib` ao usar `curve_preview`.
- Usando uma janela de agendamento que não corresponde à intenção de tempo do amostrador.
- Esperando que este nó produza diretamente `CONDITIONING`.

---

## <a id="optional-dependencies"></a>Dependências opcionais

Instale apenas o que você precisa, no mesmo ambiente Python usado por ComfyUI.

- `ScheduledLoRALoader` visualização da curva: `python -m pip install matplotlib`

---

## <a id="example-workflow-multi-area-conditioning-pipeline"></a>Workflow de exemplo multiárea

[![Fluxo de trabalho completo](../workflows/conditioninig_pipeline_area_wf.png)](../workflows/conditioninig_pipeline_area_wf.png)

Você pode arrastar e soltar esta imagem de fluxo de trabalho em ComfyUI para importar/carregar o gráfico completo.

#### Configuração da área 1

[![Condicionamento da área 1](../assets/conditioninig_area_1.png)](../assets/conditioninig_area_1.png)

- Use `Create Hook Lora` nativo para carregar um LoRA e definir o prompt/condicionamento da área para a Área 1.
- Conecte esse condicionamento em `Conditioning Pipeline (Set Area)` e defina `width`, `height`, `x`, `y` e `strength` para essa região.

#### Configuração da área 2

[![Condicionamento da área 2](../assets/conditioninig_area_2.png)](../assets/conditioninig_area_2.png)

- Repita exatamente o mesmo padrão: outro `Create Hook Lora` + outro `Conditioning Pipeline (Set Area)`.
- Você pode continuar repetindo esse padrão para áreas adicionais.

#### Encadeamento de pipeline e combinação

[![Combinação de condicionamento](../assets/conditioning_combine.png)](../assets/conditioning_combine.png)

- Encadeie `pipeline_out` da Área 1 para a Área 2 (entradas de pipeline concatenadas).
- Envie `pipeline_out` da última área para `Conditioning Pipeline (Combine)`, que mescla o pipeline da área com o condicionamento global.
- Roteie a saída combinada para `KSampler` diretamente ou para `ControlNet`; neste exemplo, ele é roteado para `ControlNet`.

#### Orientação OpenPose / ControlNet

- OpenPose/ControlNet é opcional em geral, mas para este fluxo de trabalho específico de composição multiassunto e multiárea é altamente recomendado para uma composição consistente.
- Consulte [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio) do mesmo autor (repositório mais recente).

#### Posicionamento global do `Styler Pipeline`

[![Colocação `Styler Pipeline` global com condicionamento de área + ControlNet](../assets/styler_pipeline_node.png)](../assets/styler_pipeline_node.png)

Estilo global significa aplicar `Styler Pipeline` uma vez a toda a imagem, além de (ou em vez de) condicionamento por área.

- Regra geral: conecte `Styler Pipeline` antes de `KSampler`.
- Ao usar ControlNet, `Styler Pipeline` pode ser conectado antes de aplicar ControlNet ou depois de aplicar ControlNet.
- Na prática, o resultado geralmente é equivalente, então escolha o posicionamento que for mais conveniente em seu gráfico.

#### `global_strength` compensações

- Aumentar muito `global_strength` reduz a influência relativa dos condicionamentos por área e pode enfraquecer a identidade de LoRA/estilo por área.
- Uma maior força global também pode impactar negativamente a qualidade da imagem.
- Mantenha `global_strength` baixo e mantenha o prompt global mínimo/geral.
- Regra prática: use valores abaixo de `0.5` em geral (testados até `0.5`) e evite confiar no condicionamento global além da orientação geral.
- Reduzir a força de LoRA tende a reduzir a identidade de LoRA ou a fidelidade do personagem, enquanto diminuir a força da área tende a reduzir o controle por área.
- Não é recomendado maximizar tudo, porque altas forças combinadas podem sacrificar a qualidade da imagem. Isto é especialmente verdadeiro ao misturar LoRAs de autores diferentes, o que pode produzir qualidade inconsistente.
- Regra geral para LoRAs com vários caracteres: quando possível, use LoRAs do mesmo autor ou abordagem de treinamento semelhante para obter resultados combinados mais consistentes.

---

## <a id="gallery"></a>Galeria

| Visualização | Descrição |
|---------|-------------|
| [![condicionamento_pipeline_area](../workflows/conditioninig_pipeline_area.png)](../workflows/conditioninig_pipeline_area.png) | **Pipeline de condicionamento — Multiáreas com ControlNet OpenPose**<br><br>Demonstra múltiplas áreas verticais com múltiplos LoRAs sem sangramento de LoRA, usando ControlNet OpenPose.<br><br>Requer [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio). |
| [![condicionamento_pipeline_styled](../workflows/conditioninig_pipeline_styled.png)](../workflows/conditioninig_pipeline_styled.png) | **Pipeline de condicionamento — múltiplas áreas com ControlNet e estilo**<br><br>Demonstra múltiplas áreas e vários LoRAs com estilo por área aplicado a cada região independentemente.<br><br>Requer [comfyui-openpose-studio](https://github.com/andreszs/comfyui-openpose-studio) e [comfyui-styler-pipeline](https://github.com/andreszs/comfyui-styler-pipeline).<br><br>Este fluxo de trabalho usa estilo por área, o que significa que cada área tem seus próprios estilos configurados separadamente. O estilo global também é possível conectando o nó Styler logo antes de ControlNet. |

Veja [este post](https://www.andreszsogon.com/building-a-multi-character-comfyui-workflow-with-area-conditioning-openpose-control-and-style-layering/) para um workflow completo combinando múltiplas áreas de conditioning, OpenPose, ControlNet e Styler usados ao mesmo tempo.

---

## <a id="changelog"></a>Registro de alterações

### 1.1.4

- A otimização do condicionamento regional reduziu o tempo medido de geração de aproximadamente 144 para 70 segundos em um workflow SDXL testado com duas regiões — cerca de 51% menos tempo de renderização.
- O Fast Mode opcional concluiu um teste equivalente com cobertura completa em aproximadamente 54 segundos — até cerca de 63% menos tempo que a implementação anterior.
- O desempenho varia conforme GPU, modelo, resolução, sampler, configuração do ControlNet e cobertura regional. Fast Mode também pode produzir diferenças visuais e, por isso, permanece desativado por padrão.

---

## <a id="funding--support"></a>Financiamento e Apoio

### Por que seu apoio é importante

Este plug-in é desenvolvido e mantido de forma independente, com uso regular de **agentes de IA pagos** para acelerar a depuração, testes e melhorias na qualidade de vida. Se você achar útil, o apoio financeiro ajudará a manter o desenvolvimento em andamento constante.

Sua contribuição ajuda:

* Financie ferramentas de IA para soluções mais rápidas e novos recursos
* Cubra o trabalho contínuo de manutenção e compatibilidade em ComfyUI atualizações
* Evite lentidão no desenvolvimento quando os limites de uso forem atingidos

> [!TIP]
> Não está doando? Uma estrela do GitHub ⭐ ainda ajuda muito melhorando a visibilidade e ajudando mais usuários

### 💙 Apoie este projeto

<table style="width: 100%; table-layout: fixed;">
  <tr>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">Ko-fi</h4>
        <a href="https://ko-fi.com/D1D716OLPM" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_kofi.svg" alt="Ko-fi Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="https://ko-fi.com/D1D716OLPM" target="_blank" rel="noopener noreferrer">Compre um café</a></p>
      </div>
    </td>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">PayPal</h4>
        <a href="https://www.paypal.com/ncp/payment/GEEM324PDD9NC" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_paypal.svg" alt="PayPal Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="https://www.paypal.com/ncp/payment/GEEM324PDD9NC" target="_blank" rel="noopener noreferrer">Abrir PayPal</a></p>
      </div>
    </td>
    <td align="center" style="width: 33.33%; padding: 20px;">
      <div>
        <h4 style="margin: 8px 0;">USDC (somente Arbitrum ⚠️)</h4>
        <a href="https://arbiscan.io/address/0xe36a336fC6cc9Daae657b4A380dA492AB9601e73" target="_blank" rel="noopener noreferrer">
          <img src="../assets/badge_usdc.svg" alt="USDC Badge" width="180" />
        </a>
        <p style="margin: 8px 0; font-size: 12px;"><a href="#usdc-address">Mostrar endereço</a></p>
      </div>
    </td>
  </tr>
</table>

<details>
  <summary>Prefere digitalizar? Mostrar códigos QR</summary>
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
  <summary>Mostrar endereço USDC</summary>

```text
0xe36a336fC6cc9Daae657b4A380dA492AB9601e73
```

> [!WARNING]
> Envie USDC somente no Arbitrum One. As transferências enviadas em qualquer outra rede não chegarão e poderão ser perdidas permanentemente.
</details>

## <a id="license"></a>Licença

Licença MIT - consulte [LICENSE](../LICENSE) para obter o texto completo.

---

**Mantido por:** andreszs
**Status:** Desenvolvimento Ativo
