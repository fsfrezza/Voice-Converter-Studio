const $ = (id) => document.getElementById(id);
let recorder, chunks = [], recording = null, engine = 'passthrough';
const setStatus = (s) => { $('status').textContent = s; };
const sync = () => { $('convert').disabled = !recording; };

fetch('/api/health').then(r => r.json()).then(data => {
  engine = data.engine;
  $('neuralStatus').textContent = data.neural_ready
    ? 'Modelo neural pronto para conversão.'
    : `Modelo neural indisponível: ${data.neural_message}`;
  $('engine').textContent = data.neural_ready
    ? 'RVC configurado. O modo automático usará a conversão neural.'
    : 'Sem modelo neural: o modo automático usará o efeito DSP.';
}).catch(() => setStatus('Servidor indisponível.'));

function attach(blob) {
  recording = blob;
  $('original').src = URL.createObjectURL(blob);
  $('original').hidden = false;
  $('result').hidden = true;
  sync();
}

// Export microphone recordings as PCM WAV so the API accepts them uniformly.
async function encodeWav(blob) {
  const AudioContextType = window.AudioContext || window.webkitAudioContext;
  const ctx = new AudioContextType();
  try {
    const decoded = await ctx.decodeAudioData(await blob.arrayBuffer());
    const channels = Math.min(decoded.numberOfChannels, 2);
    const bytes = new ArrayBuffer(44 + decoded.length * channels * 2);
    const view = new DataView(bytes);
    const write = (offset, value) => [...value].forEach((c, i) => view.setUint8(offset + i, c.charCodeAt(0)));
    write(0, 'RIFF'); view.setUint32(4, bytes.byteLength - 8, true); write(8, 'WAVE');
    write(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
    view.setUint16(22, channels, true); view.setUint32(24, decoded.sampleRate, true);
    view.setUint32(28, decoded.sampleRate * channels * 2, true);
    view.setUint16(32, channels * 2, true); view.setUint16(34, 16, true);
    write(36, 'data'); view.setUint32(40, bytes.byteLength - 44, true);
    let offset = 44;
    const samples = Array.from({length: channels}, (_, i) => decoded.getChannelData(i));
    for (let i = 0; i < decoded.length; i++) for (let c = 0; c < channels; c++) {
      const v = Math.max(-1, Math.min(1, samples[c][i]));
      view.setInt16(offset, v < 0 ? v * 32768 : v * 32767, true); offset += 2;
    }
    return new Blob([bytes], {type: 'audio/wav'});
  } finally { await ctx.close(); }
}

$('record').onclick = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({audio: true});
    chunks = []; recorder = new MediaRecorder(stream);
    recorder.ondataavailable = e => { if (e.data.size) chunks.push(e.data); };
    recorder.onstop = async () => {
      try { $('recordStatus').textContent = 'Preparando WAV...'; attach(await encodeWav(new Blob(chunks, {type: recorder.mimeType}))); $('recordStatus').textContent = 'Gravação concluída.'; }
      catch(e) { $('recordStatus').textContent = `Erro ao preparar gravação: ${e.message}`; }
      finally { stream.getTracks().forEach(t => t.stop()); }
    };
    recorder.start(); $('record').disabled = true; $('stop').disabled = false;
    $('recordStatus').textContent = 'Gravando...';
  } catch(e) { $('recordStatus').textContent = `Microfone indisponível: ${e.message}`; }
};
$('stop').onclick = () => { if (recorder?.state === 'recording') recorder.stop(); $('record').disabled = false; $('stop').disabled = true; };
$('file').onchange = async e => {
  const f = e.target.files[0]; if (!f) return;
  if (!f.name.toLowerCase().endsWith('.wav')) { setStatus('Escolha um arquivo .wav.'); return; }
  attach(f);
};
$('convert').onclick = async () => {
  $('convert').disabled = true; setStatus('Processando...');
  try {
    const form = new FormData(); form.append('file', recording, 'gravacao.wav'); form.append('preset', $('preset').value); form.append('engine_mode', $('engineMode').value);
    const response = await fetch('/api/convert', {method: 'POST', body: form});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Falha na conversão');
    $('converted').src = data.audio_url; $('download').href = data.audio_url;
    $('result').hidden = false;
    setStatus(data.engine === 'rvc' ? 'Conversão neural RVC concluída.' : data.engine === 'announcer-dsp' ? 'Efeito DSP aplicado: sua identidade vocal permanece.' : 'Conversão externa concluída.');
  } catch(e) { setStatus(`Erro: ${e.message}`); }
  finally { sync(); }
};
