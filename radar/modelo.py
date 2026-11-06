"""Normalized role + text utilities. Every rule match runs on lowercase, accent-free text."""
import hashlib
import html as _html
import re
import unicodedata
from dataclasses import dataclass, field


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.lower()).strip()


def html_para_texto(h):
    h = re.sub(r"(?is)<(script|style).*?</\1>", " ", h or "")
    h = re.sub(r"(?i)<(br|/p|/li|/h\d|/div)[^>]*>", "\n", h)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"[ \t]+", " ", _html.unescape(h)).strip()


@dataclass
class Vaga:
    fonte: str                 # greenhouse:acme, ashby:globex, himalayas, gupy ...
    id_fonte: str
    empresa: str
    titulo: str
    local: str = ""
    link: str = ""
    descricao_html: str = ""   # HTML as it came (goes to checar_vaga)
    tipo: str = ""             # FullTime, PartTime...
    publicada: str = ""        # YYYY-MM-DD, if the source provides it
    prazo: str = ""
    salario: str = ""
    fundo: str = ""            # marked in the watchlist
    extra: dict = field(default_factory=dict)

    @property
    def descricao(self):
        return html_para_texto(self.descricao_html)

    @property
    def chave(self):
        return f"{self.fonte}#{self.id_fonte}"

    @property
    def chave_semantica(self):
        """The same role reposted by an aggregator: company + title, normalized."""
        return "sem#" + norm(self.empresa) + "|" + norm(self.titulo)

    @property
    def hash(self):
        return hashlib.sha1((norm(self.titulo) + "|" + norm(self.descricao)).encode()).hexdigest()[:12]
