# Primeiro teste neural (Windows / CPU)

O CLI `infer/cli.py --help` iniciou corretamente no computador do usuário (Python 3.12, PyTorch 2.4.1+cpu).

## Dependências de inferência

A versão atual do RVC usa `assets/hubert_base/pytorch_model.bin`, `assets/hubert_base/config.json` e `assets/rmvpe/rmvpe.pt`. A versão anterior do tutorial baixou `assets/hubert/hubert_base.pt`, que não substitui os novos arquivos.

No PowerShell:

```powershell
cd C:\RVC
.\.venv\Scripts\hf.exe download lj1995/VoiceConversionWebUI --include "hubert_base/*" --local-dir assets
Test-Path .\assets\hubert_base\pytorch_model.bin
Test-Path .\assets\hubert_base\config.json
Test-Path .\assets\rmvpe\rmvpe.pt
```

## Modelo de voz para teste

Obtenha um checkpoint *de inferência* `.pth` que possa ser utilizado legalmente, preferencialmente gravado por um locutor que autorize o projeto. Não confunda pesos de pré-treino `assets/pretrained_v2/f0G40k.pth` com uma voz-alvo treinada para inferência.

Coloque-o em `C:\RVC\assets\weights\NarradorOriginal.pth`.

```powershell
cd C:\RVC
.\.venv\Scripts\python.exe infer\cli.py --model assets\weights\NarradorOriginal.pth --list-speakers
```

Crie um WAV de fala próprio em `C:\RVC\entrada.wav` e teste:

```powershell
.\.venv\Scripts\python.exe infer\cli.py --model assets\weights\NarradorOriginal.pth --input entrada.wav --output teste-neural.wav --pitch 0 --f0-method rmvpe --index-rate 0
```

O `--index-rate 0` dispensa um índice FAISS no primeiro teste. Uma indexação válida e autorizada pode ser configurada posteriormente.

## Conectar o Voice Converter Studio

O servidor do Studio usa variáveis de ambiente, carregadas **antes** de iniciar o servidor. O Python do RVC é separado do ambiente Python do Studio.

```powershell
cd C:\Voice-Converter-Studio-Git
git pull --ff-only
$env:RVC_ROOT = "C:\RVC"
$env:RVC_MODEL = "C:\RVC\assets\weights\NarradorOriginal.pth"
$env:RVC_PYTHON = "C:\RVC\.venv\Scripts\python.exe"
.\start-windows.bat
```

Na interface, selecione `Neural RVC (exigir modelo)`. O sistema não deve confundir efeitos DSP com conversão neural.

**Limite de verificação:** o endpoint checa a presença dos arquivos, não garante inferência válida. Só declare o modelo funcional após produzir e ouvir um WAV de saída.

**Nota legal:** o trecho de Dragon Ball fornecido pelo usuário é referência de interpretação, não uma licença para treino/clonagem de um dublador. Não hospede gravações ou modelos pessoais em um repositório público.
