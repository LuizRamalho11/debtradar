# DebtRadar etapa 2

Análise acústica local de podcast sobre dívida técnica. A etapa 1 continua disponível em main.py. A etapa 2 usa audio_main.py.

## Fonte

Software Engineering Radio, episódio 224, Sven Johann e Eberhard Wolff, publicado em 1 de abril de 2015.
Página: https://se-radio.net/2015/04/episode-224-sven-johann-and-eberhard-wolff-on-technical-debt/
Áudio público obtido pelo enclosure do feed https://feeds.libsyn.com/21070/rss. Não há transcrição automática implementada. A página oferece uma transcrição editorial, que não foi usada para calcular medidas acústicas.

## Instalação e demonstração

```powershell
python -m pip install -r requirements-audio.txt
python tools/baixar_audio.py
python audio_main.py --help
python audio_main.py --file data/audio/raw/seradio224.mp3
python audio_main.py --file data/audio/raw/seradio224.mp3 --seconds 30 --threshold -35 --output data/audio/teste
```

O padrão analisa os primeiros 180 segundos, incluindo possível abertura musical. Não representa o episódio inteiro. O JSON registra duração total e duração analisada separadamente, parâmetros e hash SHA256 do arquivo.

## Teoria

Amplitude digital normalizada descreve o sinal. RMS = raiz da média dos quadrados por janela de 25 ms. Energia em dBFS = 20 log10(RMS), com piso numérico. Janelas abaixo de -40 dBFS são de baixa energia. Sequências de pelo menos 300 ms são contadas como pausas candidatas. O espectrograma usa janelas de 1024 amostras e sobreposição de 512, mostrando frequências até 5 kHz. A média dos canais produz mono e pode cancelar sinais em oposição de fase.

## Limitações

As medidas não identificam dívida técnica, emoções, falantes ou palavras. Música e ruído afetam a energia. Pausa candidata não significa silêncio confirmado. O limiar é configurável e precisa de calibração. Um episódio e um recorte não permitem generalização.

## Diário de bordo

1. A primeira fonte bloqueou acesso automatizado. Solução: áudio público no feed oficial do Software Engineering Radio.
2. O ambiente não tinha bibliotecas acústicas e gráficas. Solução: dependências separadas em requirements-audio.txt.
3. Um episódio longo aumenta memória e tempo. Solução: leitura limitada ao recorte, com duração explícita no resumo.

## Roteiro de 10 minutos

Integrante 1: tema e fonte (1 min), amostragem e amplitude (1 min), RMS e limiar (1,5 min), implementação e parâmetros (1,5 min).
Integrante 2: resultados e espectrograma (2 min), limitações (1 min), diário de bordo (0,5 min), código e demonstração (1,5 min).

Mostrar audio_main.py e executar os comandos acima. Explicar as opções --file, --seconds, --threshold e --output usando --help. Reservar saída e gráfico já gerados para falha na demonstração.

Onde aprender: https://python-soundfile.readthedocs.io/ , https://docs.scipy.org/doc/scipy/reference/signal.html , https://matplotlib.org/stable/tutorials/

Entrega: etapa2-DebtRadar.pdf no SIGAA. Confirmar prazo e aviso do tema exigidos pela disciplina.
