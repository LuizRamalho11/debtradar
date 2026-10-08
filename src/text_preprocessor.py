"""Pré-processamento dos textos das issues.

Issues do GitHub são escritas em Markdown e misturam prosa, código, links
e HTML. Este módulo separa o código da prosa e remove a formatação, sem
apagar as palavras que interessam à análise.

Decisões:
- maiúsculas e minúsculas são preservadas: as Regex ignoram a caixa, e o
  spaCy precisa dela para reconhecer entidades;
- blocos de código não são descartados: vão para um campo separado, onde
  ainda se procuram marcadores como TODO e FIXME;
- código inline (`assim`) fica no texto, apenas sem as crases;
- referências a issues (#123) e identificadores (snake_case) são mantidos.
"""
import re
import unicodedata

# --- Trechos removidos ou separados -------------------------------------
# Bloco de código cercado por ``` ou ~~~ (três ou mais). O \1 exige que o
# bloco feche com a mesma cerca que abriu; se não fechar, vai até o fim.
CODE_BLOCK = re.compile(r"(`{3,}|~{3,})[^\n]*\n(.*?)(?:\1|\Z)", re.DOTALL)
# Comentário HTML, comum em modelos de issue: <!-- instruções -->
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
# Imagem: ![texto alternativo](endereço)
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
# Link: [texto](endereço) -> fica só o texto.
# O texto pode ter um nível de colchetes dentro, como em "[content[].text](url)".
LINK = re.compile(r"\[((?:[^\[\]]|\[[^\[\]]*\])+)\]\([^)]*\)")
# URL solta, com ou sem < > em volta
URL = re.compile(r"<?https?://[^\s<>)\]`]+>?")
# Somente tags HTML conhecidas: placeholders como <name> devem sobreviver.
HTML_TAG = re.compile(
    r"</?(?:details|summary|strong|em|b|i|u|br|p|div|span|img|a|sub|sup|kbd|code|pre"
    r"|table|thead|tbody|tr|td|th|ul|ol|li|h[1-6]|hr|blockquote|picture|source|video)"
    r"\b[^>]*>",
    re.IGNORECASE,
)
# Assinaturas no fim das mensagens de commit: "Co-authored-by: Fulano <e-mail>",
# "Signed-off-by: ...". São acrescentadas por ferramentas, não são discussão.
GIT_TRAILER = re.compile(r"^[ \t]*[A-Za-z]+(?:-[A-Za-z]+)*-by:.*$", re.MULTILINE | re.IGNORECASE)
# Menção a usuário (@fulano); não casa com pacotes como @types/node.
MENTION = re.compile(r"(?<![\w/.])@[A-Za-z0-9][A-Za-z0-9-]*(?![\w/])")

# --- Marcas de formatação do Markdown -----------------------------------
# Código inline entre crases simples ou duplas: `x` ou ``x``
INLINE_CODE = re.compile(r"`+([^`\n]+)`+")
QUOTE = re.compile(r"^[ \t]*>+[ \t]?", re.MULTILINE)
ALERT = re.compile(r"\[!(?:NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]", re.IGNORECASE)
HEADING = re.compile(r"^[ \t]*#{1,6}[ \t]+", re.MULTILINE)
BULLET = re.compile(r"^[ \t]*(?:[-*+]|\d+[.)])[ \t]+", re.MULTILINE)
CHECKBOX = re.compile(r"^\[[ xX]\][ \t]*", re.MULTILINE)
# Linha só com traços, barras e dois-pontos: régua (---) ou divisor de tabela.
# A quebra de linha sai junto, para o cabeçalho da tabela não se separar do resto.
TABLE_RULE = re.compile(r"^[ \t|:-]*-[ \t|:-]*$\n?", re.MULTILINE)
TABLE_ROW = re.compile(r"^[ \t]*\|.*$", re.MULTILINE)
BOLD = re.compile(r"\*\*(.+?)\*\*")
ITALIC = re.compile(r"(?<![\w*])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\w*])")
STRIKE = re.compile(r"~~(.+?)~~")

# --- Espaços ------------------------------------------------------------
SPACES = re.compile(r"[ \t]+")
SPACES_AROUND_NEWLINE = re.compile(r" ?\n ?")
BLANK_LINES = re.compile(r"\n{3,}")

CURLY_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})


def clean_text(text):
    """Limpa um texto em Markdown. Devolve (texto_limpo, codigo).

    'codigo' reúne o conteúdo dos blocos de código retirados do texto.
    """
    # 1. Normalização de caracteres
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("\r\n", "\n").translate(CURLY_QUOTES)

    # 2. Separa os blocos de código
    text = HTML_COMMENT.sub(" ", text)
    code_blocks = [block.group(2).strip() for block in CODE_BLOCK.finditer(text)]
    text = CODE_BLOCK.sub("\n", text)

    # 3. Remove o que não é texto
    text = IMAGE.sub(" ", text)
    text = LINK.sub(r"\1", text)
    text = URL.sub(" ", text)
    text = HTML_TAG.sub(" ", text)
    text = GIT_TRAILER.sub("", text)
    text = MENTION.sub(" ", text)

    # 4. Retira a formatação do Markdown, mantendo o conteúdo
    text = INLINE_CODE.sub(r"\1", text)
    text = QUOTE.sub("", text)
    text = ALERT.sub(" ", text)
    text = HEADING.sub("", text)
    text = BULLET.sub("", text)
    text = CHECKBOX.sub("", text)
    text = TABLE_RULE.sub("", text)
    text = TABLE_ROW.sub(lambda row: row.group(0).replace("|", " "), text)
    text = BOLD.sub(r"\1", text)
    text = ITALIC.sub(r"\1", text)
    text = STRIKE.sub(r"\1", text)

    # 5. Normaliza os espaços; quebras de linha simples são mantidas
    text = SPACES.sub(" ", text)
    text = SPACES_AROUND_NEWLINE.sub("\n", text)
    text = BLANK_LINES.sub("\n\n", text).strip()

    code = "\n".join(block for block in code_blocks if block)
    return text, code


# Contas automáticas que não usam o sufixo [bot]. Basta acrescentar nomes.
KNOWN_BOTS = {"k8s-ci-robot", "k8s-triage-robot"}


def is_bot(author):
    """Contas automáticas: nome terminado em [bot] ou listado em KNOWN_BOTS."""
    return author.endswith("[bot]") or author.lower() in KNOWN_BOTS


def preprocess_issue(issue):
    """Transforma um registro coletado em um documento pronto para análise.

    Vale para issues, pull requests e commits. O texto do documento junta
    título, corpo e comentários, já limpos. Comentários de bots ficam de
    fora: o interesse é o que as pessoas escrevem.
    """
    human_comments = [c for c in issue["comments"] if not is_bot(c["author"])]
    parts = [issue["title"], issue["body"]]
    parts += [comment["body"] for comment in human_comments]
    cleaned = [clean_text(part) for part in parts]

    return {
        # Coletas antigas só tinham issues e não gravavam o tipo.
        "type": issue.get("type", "issue"),
        "id": issue.get("id") or f"#{issue['number']}",
        "number": issue["number"],
        "title": issue["title"],
        "url": issue["url"],
        "author": issue["author"],
        "state": issue["state"],
        "labels": issue["labels"],
        "created_at": issue["created_at"],
        "updated_at": issue["updated_at"],
        "closed_at": issue["closed_at"],
        "comments_count": issue["comments_count"],
        "bot_comments_ignored": len(issue["comments"]) - len(human_comments),
        "text": "\n\n".join(text for text, _ in cleaned if text),
        "code": "\n".join(code for _, code in cleaned if code),
    }
