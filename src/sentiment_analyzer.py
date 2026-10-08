"""Análise de sentimento com o VADER.

O VADER é um analisador baseado em léxico, feito para textos em inglês:
cada palavra tem uma valência (positiva ou negativa) e a pontuação final
("compound") vai de -1 a +1. Não exige treinamento.

O sentimento descreve o tom do texto; é uma característica complementar
do discurso e não mede a dívida técnica em si.

Dois cuidados, ambos motivados pelos dados reais:

1. A pontuação é calculada por sentença e depois se tira a média. Aplicado
   ao documento inteiro, o VADER satura perto de -1 ou +1 em textos longos.
2. Palavras que em software são termos técnicos têm a valência removida.
   No léxico original, "shared" e "approval" contam como elogio e "kill"
   e "argument" como algo negativo. O mesmo vale para "no" isolado.
"""
import re

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Termos técnicos sem carga de opinião no contexto de software.
# Inclui "debt": é o assunto do corpus, e não um julgamento sobre ele.
TECHNICAL_NEUTRAL = {
    "debt",
    "share", "shares", "shared", "sharing",
    "approve", "approved", "approval",
    "support", "supports", "supported", "supporting",
    "trust", "trusted",
    "value", "values",
    "block", "blocks", "blocked",
    "argument", "arguments",
    "commit", "commits",
    "kill", "kills", "killed",
    "error", "errors", "warning", "warnings",
    "active", "responsive", "kind", "top", "collapse", "free", "security",
}

# "no" tem valência negativa no léxico, mas em texto técnico é descritivo
# ("no tests", "no protocol change"). Sem a valência própria ele continua
# invertendo a palavra seguinte: "no good" permanece negativo.
NEUTRAL_FUNCTION_WORDS = {"no"}

# Limites usuais do VADER para o rótulo.
POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05

# Uma sentença termina em ponto, exclamação ou interrogação seguidos de
# espaço, ou em uma quebra de linha.
SENTENCE_END = re.compile(r"(?<=[.!?])\s+|\n+")


def split_sentences(text):
    return [part.strip() for part in SENTENCE_END.split(text) if part.strip()]


def label_for(compound):
    if compound >= POSITIVE_THRESHOLD:
        return "positive"
    if compound <= NEGATIVE_THRESHOLD:
        return "negative"
    return "neutral"


class SentimentAnalyzer:
    """Calcula o sentimento de documentos em inglês."""

    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        for word in TECHNICAL_NEUTRAL | NEUTRAL_FUNCTION_WORDS:
            self.vader.lexicon.pop(word, None)

    def analyze(self, text):
        """Devolve o rótulo do documento e os números que o justificam."""
        scores = [self.vader.polarity_scores(sentence)["compound"]
                  for sentence in split_sentences(text)]
        compound = sum(scores) / len(scores) if scores else 0.0
        labels = [label_for(score) for score in scores]
        return {
            "label": label_for(compound),
            "compound": round(compound, 4),
            "sentences": len(scores),
            "positive_sentences": labels.count("positive"),
            "negative_sentences": labels.count("negative"),
            "neutral_sentences": labels.count("neutral"),
        }
