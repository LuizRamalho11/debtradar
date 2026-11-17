"""DebtRadar etapa 2: análise acústica reproduzível de áudio local."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import soundfile as sf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import spectrogram


def analyze(path, output, seconds, threshold):
    """Analisa um recorte inicial sem carregar o episódio inteiro."""
    output.mkdir(parents=True, exist_ok=True)
    info = sf.info(path)
    audio, rate = sf.read(path, frames=int(seconds * info.samplerate),
                          always_2d=True, dtype='float32')
    if len(audio) == 0:
        raise ValueError('Arquivo sem amostras de áudio')
    mono = audio.mean(axis=1)
    frame = max(1, int(rate * .025))
    complete = len(mono) // frame
    if complete < 1:
        raise ValueError('Áudio menor que uma janela de 25 ms')
    windows = mono[:complete * frame].reshape(complete, frame)
    rms = np.sqrt(np.mean(windows ** 2, axis=1))
    db = 20 * np.log10(np.maximum(rms, 1e-10))
    quiet = db < threshold
    edges = np.diff(np.r_[False, quiet, False].astype(int))
    starts = np.flatnonzero(edges == 1)
    ends = np.flatnonzero(edges == -1)
    lengths = (ends - starts) * frame / rate
    pauses = lengths[lengths >= .3]
    result = {
        'arquivo': path.name,
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'duracao_episodio_s': info.duration,
        'duracao_analisada_s': len(mono) / rate,
        'taxa_hz': rate,
        'canais_originais': info.channels,
        'janela_ms': 25,
        'limiar_dbfs': threshold,
        'baixa_energia_percentual': float(quiet.mean() * 100),
        'pausas_min_300ms': len(pauses),
        'maior_pausa_s': float(pauses.max()) if len(pauses) else 0,
        'rms_global': float(np.sqrt(np.mean(mono ** 2))),
        'pico_absoluto': float(np.abs(mono).max()),
        'limite': 'Baixa energia não comprova silêncio ou ausência de fala. Música e ruído afetam as medidas. As medidas acústicas não identificam dívida técnica.'
    }
    time = np.arange(len(mono)) / rate
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), constrained_layout=True)
    step = max(1, len(mono) // 120000)
    axes[0].plot(time[::step], mono[::step], linewidth=.4)
    axes[0].set(title='Forma de onda', ylabel='Amplitude')
    axes[1].plot(np.arange(complete) * frame / rate, db, linewidth=.5)
    axes[1].axhline(threshold, color='red', label=f'Limiar {threshold} dBFS')
    axes[1].set(title='Energia por janela de 25 ms', ylabel='dBFS')
    axes[1].legend()
    freq, times, power = spectrogram(mono, rate, nperseg=1024, noverlap=512)
    keep = freq <= 5000
    axes[2].pcolormesh(times, freq[keep], 10 * np.log10(power[keep] + 1e-12), shading='auto')
    axes[2].set(title='Espectrograma até 5 kHz', ylabel='Frequência (Hz)')
    for axis in axes:
        axis.set_xlabel('Tempo (s)')
    fig.savefig(output / 'analise_audio.png', dpi=160)
    plt.close(fig)
    (output / 'resumo_audio.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file', type=Path, required=True, help='MP3, WAV ou FLAC local')
    parser.add_argument('--seconds', type=float, default=180, help='Recorte inicial em segundos')
    parser.add_argument('--threshold', type=float, default=-40, help='Limiar de baixa energia em dBFS')
    parser.add_argument('--output', type=Path, default=Path('data/audio/results'))
    args = parser.parse_args()
    if args.seconds <= 0 or not np.isfinite(args.seconds):
        parser.error('--seconds deve ser positivo e finito')
    if not np.isfinite(args.threshold) or args.threshold >= 0:
        parser.error('--threshold deve ser negativo e finito')
    try:
        analyze(args.file, args.output, args.seconds, args.threshold)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f'Erro no áudio: {error}\n')


if __name__ == '__main__':
    main()
