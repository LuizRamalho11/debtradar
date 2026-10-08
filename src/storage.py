"""Leitura e gravação dos arquivos JSON do projeto."""
import json


def load_json(path):
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
