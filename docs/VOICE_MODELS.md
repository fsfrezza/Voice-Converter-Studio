# Integração de modelos neurais autorizados

O efeito DSP incluído não faz clonagem de voz. Para conversão neural é necessário configurar um motor de voz externo e um modelo obtido de forma legítima.

## Contrato para o adaptador

Configure a variável de ambiente `VOICE_CONVERTER_COMMAND` com um caminho absoluto para um executável (Windows: `.exe` ou wrapper executável).

O servidor chamará:

```text
motor --input <WAV PCM de entrada> --output <WAV PCM de saída>
```

O motor deve manter as palavras da gravação e produzir um WAV PCM válido antes de terminar com código zero. O limite é 180 segundos por requisição.

Esse contrato permite usar implementações RVC que disponibilizem um CLI próprio, sem acoplar o aplicativo a uma versão específica de bibliotecas de pesquisa que mudam com frequência.

## Perfis

- Conversação: mais natural e discreto.
- Apresentação: corpo e presença maiores.
- Combate: intensidade e projeção mais fortes.

Esses três perfis são efeitos DSP quando nenhum motor neural está configurado. O motor externo, na versão atual, recebe apenas os argumentos de arquivos; ele não recebe o preset. A integração dos controles de estilo no modelo neural é uma tarefa futura.

## Requisitos e direitos

- Não há pesos de modelos de terceiros ou trechos de obras protegidas no repositório.
- Use somente modelos e gravações com autorização adequada.
- Informe claramente quando uma publicação contiver áudio sintético.
- Não exponha o serviço diretamente na internet enquanto não houver autenticação.
