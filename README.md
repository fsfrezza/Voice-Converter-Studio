# Voice Converter — MVP

Conversor de gravações de voz para Windows e Android, com uma API única e motor de conversão substituível.

## Estado

- Backend Python/FastAPI: gravações em WAV, upload, efeitos DSP originais de locução, execução opcional de motor externo autorizado e download.
- Cliente web responsivo: gravação, upload, reprodução, download e consulta de trabalhos. O cliente pode ser usado no navegador do Windows; no Android exige hospedagem HTTPS para liberar o microfone (ou seleção de arquivo gravado pelo aparelho).
- A versão Android nativa/instalável e a integração efetiva com um modelo RVC treinado ainda são etapas seguintes.
- **O projeto não inclui um modelo da voz de Sílvio Luiz nem gravações protegidas.** Use apenas modelos e áudios que você tem autorização para utilizar. Identifique publicamente áudio sintético como tal.

## Teste rápido no Windows (versão 0.1 experimental)

1. Abra [Code → Download ZIP](https://github.com/fsfrezza/Voice-Converter-Studio/archive/refs/heads/main.zip) e extraia a pasta.
2. Instale [Python 3.11+](https://www.python.org/downloads/windows/) com o Python Launcher habilitado, caso ainda não tenha.
3. Clique duas vezes em `start-windows.bat`. Na primeira execução, aguarde as dependências serem instaladas.
4. Abra `http://127.0.0.1:8765` se o navegador não abrir sozinho.
5. Grave uma fala, pare a gravação, escolha Conversação / Apresentação / Combate e clique em **Converter gravação**.
6. Ouça o resultado e baixe o WAV. Para fechar o servidor, pressione Ctrl+C na janela de comando.

> **Limitação:** esta versão aplica equalização e dinâmica. Ela não substitui sua identidade vocal por outra voz neural.

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

### Adicionar conversão real

Configure `VOICE_CONVERTER_COMMAND` com o caminho para um executável/script próprio que aceite os argumentos `--input INPUT.wav --output OUTPUT.wav` e grave WAV PCM no caminho de saída. A API valida a saída. O comando é uma configuração administrativa do servidor, nunca recebido do usuário da interface. Integre nesse adaptador uma instalação local de RVC com modelo de voz autorizado.

```bash
VOICE_CONVERTER_COMMAND=/caminho/para/conversor uvicorn app.main:app
```

O limite por arquivo é 25 MiB. Arquivos ficam em `data/` e não são apagados automaticamente nesta versão de desenvolvimento. Evite exposição pública da API: ainda não há autenticação nem isolamento multiusuário.

## API

- `GET /api/health`: verifica motor em uso.
- `POST /api/convert`: multipart `file` (WAV) e `preset` opcional; retorna ID e URLs.
- `GET /api/jobs/{id}`: estado do processamento.
- `GET /api/jobs/{id}/audio`: áudio convertido.

## Próximos passos

1. Incorporar engine RVC com gerenciamento de modelos autorizados, verificação de GPU e CPU.
2. Adicionar processamento em segundo plano, fila e progresso.
3. Empacotar Windows (instalador) e Android (APK, cliente nativo ou TWA com HTTPS).
4. Implementar remoção automática, autenticação e consentimento para modelos.
