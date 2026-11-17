"""Baixa a fonte pública da etapa 2 pelo feed oficial, sem redistribuir o MP3."""
from pathlib import Path
from urllib.request import urlopen
import shutil
import xml.etree.ElementTree as ET

FEED = 'https://feeds.libsyn.com/21070/rss'
DEST = Path(__file__).resolve().parents[1] / 'data/audio/raw/seradio224.mp3'

def main():
    with urlopen(FEED, timeout=60) as response:
        feed = ET.fromstring(response.read())
    for item in feed.findall('./channel/item'):
        title = item.findtext('title', '')
        if '224' in title and 'Technical Debt' in title:
            enclosure = item.find('enclosure')
            if enclosure is None:
                raise RuntimeError('Episódio sem link de áudio no feed')
            DEST.parent.mkdir(parents=True, exist_ok=True)
            with urlopen(enclosure.attrib['url'], timeout=120) as response:
                with DEST.open('wb') as output:
                    shutil.copyfileobj(response, output)
            print(f'Áudio salvo em {DEST}')
            return
    raise RuntimeError('Episódio 224 não encontrado no feed')

if __name__ == '__main__':
    main()
