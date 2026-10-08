"""Processamento de Linguagem Natural com spaCy.

Para cada documento o spaCy fornece:

- tokenização: o texto dividido em palavras, pontuação e símbolos;
- lematização: a forma de dicionário de cada palavra ("removed" -> "remove");
- stopwords: palavras muito comuns ("the", "and") que não entram nas contagens;
- part-of-speech (POS): a classe gramatical de cada token;
- NER: as entidades nomeadas reconhecidas pelo modelo estatístico.

As tecnologias do domínio NÃO vêm do NER: são tratadas em
technology_analyzer.py, com uma lista própria do projeto.
"""
from collections import Counter

import spacy
from spacy.language import Language

# Classes gramaticais contadas como termos relevantes.
# Nomes próprios (PROPN) ficam de fora: aparecem em entidades e tecnologias.
RELEVANT_POS = {"NOUN": "noun", "ADJ": "adjective", "VERB": "verb"}

# Palavras que o spaCy não trata como stopword, mas que não ajudam a
# caracterizar o conteúdo. Basta acrescentar itens aqui para ignorá-los.
EXTRA_STOPWORDS = {"etc", "e.g", "i.e"}

# Rótulos numéricos do NER. Em texto técnico eles só geram ruído: o modelo
# marca números de issue como MONEY e medidas em pixels como DATE.
NUMERIC_LABELS = {"CARDINAL", "ORDINAL", "MONEY", "DATE", "TIME", "PERCENT", "QUANTITY"}

MIN_TERM_LENGTH = 3


@Language.component("blank_line_sentences")
def blank_line_sentences(doc):
    """Componente próprio do pipeline: linha em branco encerra a sentença.

    Títulos e itens de lista não terminam com ponto; sem isso o spaCy os
    emenda no parágrafo seguinte.
    """
    for token in doc[:-1]:
        if token.text.count("\n") >= 2:
            doc[token.i + 1].is_sent_start = True
    return doc


def load_pipeline(model_name):
    """Carrega o modelo do spaCy e acrescenta o componente de sentenças."""
    nlp = spacy.load(model_name)
    nlp.add_pipe("blank_line_sentences", before="parser")
    return nlp


def is_identifier(token):
    """Nomes de código como runInTerminal: letra maiúscula no meio da palavra."""
    text = token.text
    return not text.isupper() and any(char.isupper() for char in text[1:])


def is_relevant(token):
    """Decide se o token entra nas contagens de frequência."""
    return (
        token.is_alpha                      # só letras: sem números, caminhos, símbolos
        and not token.is_stop               # stopwords do spaCy
        and len(token.text) >= MIN_TERM_LENGTH
        and not is_identifier(token)
        and token.lemma_.lower() not in EXTRA_STOPWORDS
    )


def count_lemmas(doc):
    """Frequência dos lemas relevantes, separada por classe gramatical."""
    counts = {name: Counter() for name in RELEVANT_POS.values()}
    for token in doc:
        if token.pos_ in RELEVANT_POS and is_relevant(token):
            counts[RELEVANT_POS[token.pos_]][token.lemma_.lower()] += 1
    return {name: dict(counter.most_common()) for name, counter in counts.items()}


def count_noun_phrases(doc):
    """Expressões nominais com duas ou mais palavras relevantes.

    Ex.: "the chat input widgets" -> "chat input widget" (a última palavra
    é reduzida ao lema, para juntar singular e plural).
    """
    counts = Counter()
    for chunk in doc.noun_chunks:
        words = [token for token in chunk if is_relevant(token)]
        if len(words) >= 2:
            phrase = [token.text.lower() for token in words[:-1]] + [words[-1].lemma_.lower()]
            counts[" ".join(phrase)] += 1
    return dict(counts.most_common())


def is_clean_entity(entity):
    """Descarta entidades numéricas e trechos que claramente são código."""
    text = entity.text
    return (
        entity.label_ not in NUMERIC_LABELS
        and "\n" not in text
        and not any(char.isdigit() or char in "._/\\#=<>" for char in text)
        and any(char.isalpha() for char in text)
    )


def extract_entities(doc):
    """Entidades do NER do modelo, com rótulo e número de ocorrências."""
    counts = Counter()
    for entity in doc.ents:
        if is_clean_entity(entity):
            text = entity.text.removesuffix("'s").strip()
            counts[(text, entity.label_)] += 1
    return [
        {"text": text, "label": label, "count": count}
        for (text, label), count in counts.most_common()
    ]


def analyze_doc(doc):
    """Resume a análise linguística de um documento já processado pelo spaCy."""
    words = [token for token in doc if not token.is_space]
    pos_counts = Counter(token.pos_ for token in words)
    return {
        "tokens": len(words),
        "sentences": sum(1 for _ in doc.sents),
        "pos": dict(pos_counts.most_common()),
        "lemmas": count_lemmas(doc),
        "noun_phrases": count_noun_phrases(doc),
        "entities": extract_entities(doc),
    }


def describe_tokens(doc):
    """Lista, token a token, o que o spaCy extraiu (usado em --text)."""
    return [
        {
            "text": token.text,
            "lemma": token.lemma_,
            "pos": token.pos_,
            "stopword": token.is_stop,
            "relevant": token.pos_ in RELEVANT_POS and is_relevant(token),
        }
        for token in doc
        if not token.is_space
    ]

