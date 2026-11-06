#!/usr/bin/env python3
"""
Anti-AI-text audit.

Usage: python3 checar_texto.py file.pdf
       python3 checar_texto.py file.md
       cat text | python3 checar_texto.py -
       python3 checar_texto.py letter.pdf email.md   <- compares the two

Checks LLM vocabulary, structural cliches, dashes/curly quotes, repeated
constructions, and measures burstiness (variation in sentence length).

Two checks exist because the script used to let these through:
  1. SENTENCE-OPENING PATTERN. A letter had four sentences opening with
     "At <Company> I ...". Rhythm and vocabulary were clean; the formula
     was in the structure.
  2. A SENTENCE REPEATED ACROSS TWO FILES. The email repeated the letter's
     punchline word for word. The reader opens both in the same minute.
     Pass the second file as the second argument.

Also checked: REPEATED CONSTRUCTIONS. The script measured sentence rhythm
but did not count structures, which is how five "X rather than Y" and six
"one of Brazil's largest" got through. A repeated construction gives away
generated text as much as vocabulary does, and is harder to see on a reread.
"""
import re
import statistics
import subprocess
import sys

BLACKLIST = """delve leverage foster ignite empower uncover unleash underscore optimise optimize
streamline seamless robust multifaceted pivotal dynamic tapestry landscape beacon realm symphony
testament journey roadmap transformative revolutionary unlock myriad plethora comprehensive
unwavering furthermore moreover additionally navigate synergy paradigm elevate scalable ultimately
cutting-edge holistic bespoke curated meticulous nuanced""".split()

CLICHES = [
    "in conclusion", "it is important to note", "deep dive", "dive in", "at its core",
    "in essence", "here's the kicker", "that's only half", "here's the truth", "real talk",
    "why does this matter", "picture this", "imagine a world", "at the end of the day",
    "i am writing to express", "game-changer", "in today's", "ever-evolving", "aims to",
    "i would put it this way", "let's face it", "the reality is",
]


# (construction, tolerated limit). Above the limit, it becomes a warning.
CONSTRUCOES = [   # constructions
    (r"\brather than\b",                          1),
    (r"\bnot (?:just|only|merely)\b",              1),
    (r"\binstead of\b",                            1),
    (r"\bone of (?:the )?\w+(?:'s)? (?:largest|biggest|leading|top)\b", 2),
    (r"\b(?:largest|leading|top|biggest)\b",       3),
    (r"\bend to end\b",                            2),
    (r"\bowned\b",                                 3),
    (r"\bran\b",                                   3),
    (r"\bled\b",                                   3),
    (r"\bdrove\b",                                 2),
    (r"\bkey\b",                                   2),
]


def carregar(caminho):
    if caminho == "-":
        return sys.stdin.read()
    if caminho.lower().endswith(".pdf"):
        return subprocess.run(["pdftotext", caminho, "-"],
                              capture_output=True, text=True).stdout
    return open(caminho, encoding="utf-8").read()


def aberturas(frases):
    """Counts the first two tokens of each sentence, normalizing proper
    names to <X>. Four sentences opening the same way is a formula, not rhythm."""
    padroes = {}
    for f in frases:
        toks = re.findall(r"[A-Za-z']+", f)[:3]
        if len(toks) < 2:
            continue
        chave = " ".join("<X>" if w[:1].isupper() and i else w.lower()
                         for i, w in enumerate(toks[:2]))
        padroes[chave] = padroes.get(chave, 0) + 1
    return {k: v for k, v in padroes.items() if v >= 3}


def frases_em_comum(a, b, minimo=6):
    """Sequences of >= `minimo` words that appear in both texts."""
    pal_b = re.findall(r"[a-z']+", b.lower())
    grupos_b = {" ".join(pal_b[i:i + minimo]) for i in range(len(pal_b) - minimo + 1)}
    pal_a = re.findall(r"[a-z']+", a.lower())
    achados = []
    for i in range(len(pal_a) - minimo + 1):
        g = " ".join(pal_a[i:i + minimo])
        if g in grupos_b:
            achados.append(g)
    # drop overlaps
    limpo = []
    for g in achados:
        if not any(g in x for x in limpo):
            limpo.append(g)
    return limpo[:5]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    texto = re.sub(r"\s+", " ", carregar(sys.argv[1])).strip()
    baixo = texto.lower()

    achados = sorted({w for w in BLACKLIST
                      if re.search(r"\b" + re.escape(w) + r"\b", baixo)})
    cliches = [c for c in CLICHES if c in baixo]
    tipografia = re.findall(r"[—–‘’“”]", texto)

    frases = [f.strip() for f in re.split(r"(?<=[.!?]) ", texto) if f.strip()]
    tam = [len(f.split()) for f in frases]

    abre = aberturas(frases)

    comum = []
    if len(sys.argv) > 2:
        outro = re.sub(r"\s+", " ", carregar(sys.argv[2])).strip()
        comum = frases_em_comum(texto, outro)

    print("AI vocabulary     :", ", ".join(achados) if achados else "clean")
    print("cliches            :", ", ".join(cliches) if cliches else "clean")
    print("dash/curly quote  :", len(tipografia) or "clean")

    repetidas = []
    for padrao, limite in CONSTRUCOES:
        n = len(re.findall(padrao, baixo))
        if n > limite:
            rotulo = padrao.replace("\\b", "").replace("(?:", "(")
            repetidas.append(f"{rotulo} x{n} (limit {limite})")
    print("constructions      :", " · ".join(repetidas) if repetidas else "clean")

    if len(tam) < 2:
        print("\ntext too short to measure rhythm")
        return 0

    media = statistics.mean(tam)
    desvio = statistics.pstdev(tam)
    curtas = sum(1 for t in tam if t <= 8)
    longas = sum(1 for t in tam if t >= 30)

    print(f"\nsentences: {len(frases)} | mean: {media:.1f} | deviation: {desvio:.1f} "
          f"| min/max: {min(tam)}/{max(tam)}")
    print(f"short (<=8): {curtas} | long (>=30): {longas}")
    print("distribution:", tam)
    print("repeated openings:",
          " · ".join(f'"{k}..." x{v}' for k, v in abre.items()) if abre else "clean")
    if len(sys.argv) > 2:
        print("passages in common with", sys.argv[2], ":",
              " | ".join(f'"{c}"' for c in comum) if comum else "clean")

    print()
    alertas = []
    if desvio < 7:
        alertas.append("low deviation: sentences too uniform, an LLM pattern. "
                       "Break it with a sentence of 4 to 6 words.")
    if curtas == 0:
        alertas.append("no short sentence. Human text has fragments.")
    if max(tam) < 28:
        alertas.append("no long sentence. It lacks range.")
    if achados or cliches or tipografia:
        alertas.append("clean up the vocabulary and typography above.")
    if repetidas:
        alertas.append("construction repeated too often: vary or cut. "
                       "Repeating a structure gives it away as much as repeating a word.")
    if abre:
        alertas.append("too many sentences opening the same way. Three is a pattern, four is a formula. "
                       "Rewrite the openings, not the content.")
    if comum:
        alertas.append("passage repeated word for word in the other file. The reader opens "
                       "both in the same minute - rewrite one of them.")

    if alertas:
        for a in alertas:
            print("  ! " + a)
    else:
        print("  ok: no obvious signs of generated text.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
