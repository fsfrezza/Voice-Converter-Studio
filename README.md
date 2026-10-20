# Voice Converter — MVP

Conversor de gravações de voz para Windows e Android, com uma API única e motor de conversão substituível.

## Estado

- Backend Python/FastAPI: gravações em WAV, upload, efeitos DSP originais de locução, execução opcional de motor externo autorizado e download.
- Cliente web responsivo: gravação, upload, reprodução, download e consulta de trabalhos. O cliente pode ser usado no navegador do Windows; no Android exige hospedagem HTTPS para liberar o microfone (ou seleção de arquivo gravado pelo aparelho).
- A versão Android nativa/instalável e o fornecimento de um modelo RVC autorizado ainda são etapas seguintes. A API já contém um adaptador para a CLI oficial RVC.
- **O projeto não inclui um modelo da voz de Sílvio Luiz nem gravações protegidas.** Use apenas modelos e áudios que você tem autorização para utilizar. Identifique publicamente áudio sintético como tal.

## Teste rápido no Windows (versão 0.1 experimental)

1. Abra [Code → Download ZIP](https://github.com/fsfrezza/Voice-Converter-Studio/archive/refs/heads/main.zip) e extraia a pasta.
2. Instale [Python 3.11+](https://www.python.org/downloads/windows/) com o Python Launcher habilitado, caso ainda não tenha.
3. Clique duas vezes em `start-windows.bat`. Na primeira execução, aguarde as dependências serem instaladas.
4. Abra `http://127.0.0.1:8765` se o navegador não abrir sozinho.
5. Grave uma fala, pare a gravação, escolha **Motor de conversão** e o estilo Conversação / Apresentação / Combate; clique em **Converter gravação**.
6. Ouça o resultado e baixe o WAV. Para fechar o servidor, pressione Ctrl+C na janela de comando.

> **Limitação:** sem um modelo RVC instalado, o modo automático usa DSP. O modo **Neural RVC** informa quando o modelo está ausente, em vez de simular conversão neural.

### Teste com Android

A interface foi preparada para telas pequenas, mas ainda **não há APK**. Para usar o microfone em outro dispositivo, é preciso implantar o serviço de forma segura com HTTPS e autenticação. Não publique a API de desenvolvimento diretamente na internet. No Android, uma alternativa inicial é gravar o WAV pelo celular e transferi-lo ao Windows para converter.

## Executar

Python 3.11+ recomendado:

```bash
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8765
```

Abra http://127.0.0.1:8765 no Windows. O motor inicial usa equalização e saturação suave, com perfis `conversation`, `presentation` e `combat`. **Ele altera a sonoridade, mas não converte a identidade vocal**. Isso permite validar o fluxo sem fingir que um modelo neural foi treinado.

### Conversão neural RVC (Windows)

O servidor inclui o adaptador para a [CLI oficial do RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/main/docs/en/cli.md), mas **não distribui modelo de voz**. Instale o RVC separadamente, com suas dependências, e use um modelo `.pth` para o qual você tenha autorização. Em PowerShell, antes de iniciar o servidor:

```powershell
$env:RVC_ROOT = "C:\\RVC"
$env:RVC_MODEL = "C:\\RVC\\assets\\weights\\modelo-autorizado.pth"
$env:RVC_PYTHON = "C:\\RVC\\runtime\\python.exe"
# Opcional: $env:RVC_INDEX = "C:\\RVC\\assets\\indices\\modelo.index"
uvicorn app.main:app --host 127.0.0.1 --port 8765
```

No aplicativo, selecione **Neural RVC (exigir modelo)** para impedir uma substituição silenciosa por DSP. Selecione **Automático** para usar RVC quando disponível e DSP caso contrário. O endpoint `/api/health` informa `neural_ready` e `neural_message`.

**Referência vocal:** o vídeo de Dragon Ball encaminhado nesta conversa é somente referência para análise de estilo e entonação. Não foi incorporado ao repositório nem utilizado para treinar ou distribuir um modelo que reproduza uma pessoa identificável. Para um novo modelo, use gravações limpas e autorizadas de um locutor original.

### Motor externo alternativo

Configure `VOICE_CONVERTER_COMMAND` com o caminho para um executável/script próprio que aceite os argumentos `--input INPUT.wav --output OUTPUT.wav` e grave WAV PCM no caminho de saída. A API valida a saída. O comando é uma configuração administrativa do servidor, nunca recebido do usuário da interface. Integre nesse adaptador uma instalação local de RVC com modelo de voz autorizado.

```bash
VOICE_CONVERTER_COMMAND=/caminho/para/conversor uvicorn app.main:app
```

O limite por arquivo é 25 MiB. Arquivos ficam em `data/` e não são apagados automaticamente nesta versão de desenvolvimento. Evite exposição pública da API: ainda não há autenticação nem isolamento multiusuário.

## API

- `GET /api/health`: verifica motor em uso.
- `POST /api/convert`: multipart `file` (WAV), `preset` opcional e `engine_mode` (`auto`/`neural`/`dsp`); retorna ID e URLs.
- `GET /api/jobs/{id}`: estado do processamento.
- `GET /api/jobs/{id}/audio`: áudio convertido.

## Próximos passos

1. Validar execução real do adaptador RVC com modelo autorizado e implementar gerenciamento de modelos, GPU e CPU.
2. Adicionar processamento em segundo plano, fila e progresso.
3. Empacotar Windows (instalador) e Android (APK, cliente nativo ou TWA com HTTPS).
4. Implementar remoção automática, autenticação e consentimento para modelos.
