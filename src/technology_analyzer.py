"""Identificação de tecnologias com uma lista própria do projeto.

O NER do spaCy não foi treinado para reconhecer linguagens, frameworks e
ferramentas, então as tecnologias são procuradas com um dicionário e o
PhraseMatcher do spaCy. Isso NÃO é NER: é uma busca por nomes conhecidos,
feita sobre os tokens (e não sobre os caracteres).

Buscar por tokens evita o erro clássico de encontrar "Java" dentro de
"JavaScript": para o spaCy são dois tokens diferentes.

O tokenizador não separa nomes colados por barra quando há símbolos ou
pontos em volta ("C++/Rust", "Node.js/Electron"): o trecho vira um token
só. Por isso os tokens que contêm barra são analisados de novo, com as
partes separadas.

Para acrescentar uma tecnologia, basta incluir uma linha em TECHNOLOGIES:
    "Nome oficial": ["apelido", "outra grafia"],
"""
from collections import Counter

from spacy.matcher import PhraseMatcher
from spacy.util import filter_spans

TECHNOLOGIES = {
    "language": {
        "Python": ["python3"],
        "JavaScript": ["JS"],
        "TypeScript": [],
        "Java": [],
        "C++": ["cpp"],
        "C#": ["csharp"],
        "Go": ["golang"],
        "Rust": [],
        "HTML": [],
        "CSS": [],
        "SQL": [],
        "Bash": [],
        "PowerShell": [],
    },
    "framework": {
        "React": ["React.js", "ReactJS"],
        "Angular": ["AngularJS"],
        "Vue": ["Vue.js", "VueJS"],
        "Node.js": ["NodeJS"],
        "Django": [],
        "Flask": [],
        "Spring": ["Spring Boot"],
        "Electron": [],
    },
    "database": {
        "PostgreSQL": ["Postgres"],
        "MySQL": [],
        "MongoDB": ["Mongo"],
        "SQLite": [],
        "Redis": [],
    },
    "tool": {
        "Docker": [],
        "Kubernetes": ["k8s"],
        "Git": [],
        "GitHub": [],
        "npm": [],
        "ESLint": [],
        "Playwright": [],
        "VS Code": ["VSCode", "Visual Studio Code"],
        "Copilot": [],
        "Claude": [],
        "Codex": [],
    },
    "platform": {
        "Linux": [],
        "Windows": [],
        "macOS": ["OS X"],
    },
}

# Nomes que também são palavras comuns do inglês ("react to", "in spring",
# "windows"). Para estes o nome precisa aparecer com a grafia exata da lista;
# os demais nomes e todos os apelidos valem com maiúsculas ou minúsculas.
CASE_SENSITIVE = {"React", "Angular", "Vue", "Spring", "Flask", "Rust", "Windows"}

# "Go" é ambíguo mesmo com maiúscula ("Go to Settings"): só o apelido
# "golang" é procurado.
ALIASES_ONLY = {"Go"}


class TechnologyAnalyzer:
    """Procura as tecnologias de TECHNOLOGIES em documentos do spaCy."""

    def __init__(self, nlp):
        self.make_doc = nlp.make_doc
        self.category_of = {}
        # attr="LOWER" compara os tokens em minúsculas; attr="ORTH", a grafia exata.
        self.any_case = PhraseMatcher(nlp.vocab, attr="LOWER")
        self.exact_case = PhraseMatcher(nlp.vocab, attr="ORTH")
        for category, technologies in TECHNOLOGIES.items():
            for name, aliases in technologies.items():
                self.category_of[name] = category
                if name in CASE_SENSITIVE:
                    self.exact_case.add(name, [nlp.make_doc(name)])
                elif name not in ALIASES_ONLY:
                    self.any_case.add(name, [nlp.make_doc(name)])
                if aliases:
                    self.any_case.add(name, [nlp.make_doc(alias) for alias in aliases])

    def _names_in(self, doc):
        """Nomes de tecnologia encontrados em um documento, um por ocorrência."""
        spans = self.any_case(doc, as_spans=True) + self.exact_case(doc, as_spans=True)
        # filter_spans fica com o maior trecho quando dois se sobrepõem:
        # "Spring Boot" conta uma vez, e não também como "Spring".
        return [span.label_ for span in filter_spans(spans)]

    def find(self, doc):
        """Devolve as tecnologias citadas no documento, com a contagem."""
        counts = Counter(self._names_in(doc))
        for token in doc:
            # "C++/Rust" é um token só: separa as partes e procura de novo.
            if "/" in token.text.strip("/"):
                counts.update(self._names_in(self.make_doc(token.text.replace("/", " / "))))
        return [
            {"name": name, "category": self.category_of[name], "count": count}
            for name, count in counts.most_common()
        ]
