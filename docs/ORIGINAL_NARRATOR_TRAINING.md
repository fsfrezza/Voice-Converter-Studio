# Narrador de Torneio — voz original

## Objetivo
Criar uma identidade vocal nova, masculina, com corpo, articulação e expressividade de locutor de torneios. O áudio de Dragon Ball fornecido na conversa é **referência de interpretação**, não dataset autorizado para clonagem nem checkpoint de voz. O repositório público não deve conter a gravação.

## Dataset autorizado
Recrutar um locutor que consinta expressamente com o treino e a utilização pretendida, ou gravar uma voz própria com permissão para uso. Fazer sessões em português brasileiro com variação de conversação, apresentação e combate; um alvo inicial prático é 15–30 minutos de fala *limpa* (mais material variado e consistente tende a melhorar o resultado). Esta é uma meta de coleta, não garantia de qualidade.

Regras de captura: uma voz por arquivo; sem música, reverb, ruído, efeitos ou interlocutores; mesma distância do microfone; evitar compressão agressiva e clipping. Guardar originais WAV e registro da autorização fora do Git público.

Organização local:

```
dataset/
  narrador-original/
    raw/
    reviewed/
    metadata.csv
```

Revisar e descartar sobreposição de falas e ruídos antes do treino. Reserve amostras não usadas no treino para avaliação cega. A ferramenta `scripts/check_reference.py` mede somente aspectos técnicos e não certifica que a pessoa está isolada.

## Experimentos e validação
1. Confirmar que o RVC converte uma gravação **de 5–10 segundos**, antes de testar minutos inteiros.
2. Selecionar um modelo com voz-alvo autorizada; modelos de demonstração como `kikiV1` não são o timbre final.
3. Comparar clareza fonética, timbre, volume, artefatos, inteligibilidade, estabilidade e preservação da emoção.
4. Testar locutor, pitch e método F0 individualmente, sem multiplicar alterações.
5. Na Intel Iris Xe local, a tentativa DirectML falhou, e a execução CPU/PM funcionou, embora lenta; não ativar DirectML automaticamente no projeto sem testes.

## Configuração atual de inferência

No PowerShell (substitua pelo checkpoint autorizado):

```powershell
cd C:\Voice-Converter-Studio-Git
git pull --ff-only
$env:RVC_ROOT = "C:\RVC"
$env:RVC_MODEL = "C:\RVC\assets\weights\modelo-autorizado.pth"
$env:RVC_PYTHON = "C:\RVC\.venv\Scripts\python.exe"
$env:RVC_F0_METHOD = "pm"
$env:RVC_SPEAKER_ID = "0"
.\start-windows.bat
```

O Studio usa `python -m infer.cli`, estabelece `PYTHONPATH` apontando à pasta RVC e aguarda até 40 minutos. **O perfil DSP é independente dos presets neurais**: nesta fase os nomes Conversação/Apresentação/Combate ainda não alteram a expressividade do RVC; será necessário um motor de prosódia/controle treinado para isso. A troca neural ocorre com pitch 0 para reduzir efeitos colaterais.

## Limitações
* Nenhum novo checkpoint `.pth` foi treinado.
* O teste `kikiV1` finalizado em CPU prova funcionamento do pipeline, mas qualidade inadequada e duração longa.
* O APK Android não está pronto.
* O uso de um checkpoint só deve ser considerado autorizado após verificação de licença e direitos da gravação.
