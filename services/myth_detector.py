"""Detetor educacional de mitos e verdades.

O módulo usa uma base de conhecimento curada e procura a afirmação mais
semelhante ao texto do utilizador. Quando scikit-learn está disponível, a
similaridade é calculada com TF-IDF e cosseno; caso contrário, existe um
fallback por sobreposição de palavras-chave para manter a aplicação local
simples de executar.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:  # pragma: no cover
    TfidfVectorizer = None
    cosine_similarity = None


KNOWLEDGE_BASE = [
    {"claim": "A pilula protege contra ISTs", "label": "MITO", "explanation": "A pilula previne gravidez, mas nao protege contra infeccoes sexualmente transmissiveis.", "keywords": ["pilula", "ists", "contracepcao"]},
    {"claim": "O preservativo reduz o risco de ISTs", "label": "VERDADE", "explanation": "Quando usado corretamente, o preservativo reduz bastante o risco de ISTs e gravidez.", "keywords": ["preservativo", "ists", "prevencao"]},
    {"claim": "So pessoas adultas precisam de educacao sexual", "label": "MITO", "explanation": "Educacao sexual adequada a idade ajuda jovens a tomar decisoes informadas e seguras.", "keywords": ["educacao sexual", "jovens"]},
    {"claim": "Consentimento pode ser retirado a qualquer momento", "label": "VERDADE", "explanation": "Consentimento deve ser livre, informado, especifico e pode ser retirado em qualquer momento.", "keywords": ["consentimento", "respeito"]},
    {"claim": "ISTs sempre apresentam sintomas visiveis", "label": "MITO", "explanation": "Muitas ISTs podem nao apresentar sintomas; testes e acompanhamento de saude sao importantes.", "keywords": ["ists", "sintomas", "testes"]},
    {"claim": "Falar sobre sexualidade incentiva comportamentos de risco", "label": "MITO", "explanation": "Informacao correta tende a reduzir riscos, aumentar protecao e melhorar comunicacao.", "keywords": ["sexualidade", "informacao"]},
    {"claim": "Planeamento familiar ajuda a prevenir gravidez nao planeada", "label": "VERDADE", "explanation": "Planeamento familiar permite escolher metodos adequados e decidir com responsabilidade.", "keywords": ["planeamento familiar", "gravidez"]},
    {"claim": "A primeira relacao sexual nao pode causar gravidez", "label": "MITO", "explanation": "Gravidez pode ocorrer em qualquer relacao sexual sem protecao, incluindo a primeira.", "keywords": ["primeira vez", "gravidez"]},
    {"claim": "Duas camadas de preservativo protegem mais", "label": "MITO", "explanation": "Usar dois preservativos aumenta friccao e risco de rompimento.", "keywords": ["preservativo", "duplo"]},
    {"claim": "Vacina contra HPV ajuda a prevenir alguns cancros", "label": "VERDADE", "explanation": "A vacina contra HPV reduz o risco de infeccoes por tipos associados a cancros.", "keywords": ["hpv", "vacina", "cancro"]},
    {"claim": "Lavar-se depois da relacao evita gravidez", "label": "MITO", "explanation": "Higiene depois da relacao nao impede fecundacao nem substitui contraceptivos.", "keywords": ["gravidez", "higiene"]},
    {"claim": "Contraceptivos devem ser escolhidos com orientacao qualificada", "label": "VERDADE", "explanation": "Profissionais de saude ajudam a escolher o metodo mais adequado e seguro.", "keywords": ["contraceptivos", "saude"]},
    {"claim": "So raparigas precisam aprender sobre contracepcao", "label": "MITO", "explanation": "Contracepcao e responsabilidade partilhada por todas as pessoas envolvidas.", "keywords": ["contracepcao", "responsabilidade"]},
    {"claim": "Pressao para ter sexo e sinal de relacao saudavel", "label": "MITO", "explanation": "Relacoes saudaveis respeitam limites, tempo e vontade de cada pessoa.", "keywords": ["pressao", "relacao"]},
    {"claim": "Vergonha pode impedir jovens de procurar ajuda", "label": "VERDADE", "explanation": "Estigma e vergonha dificultam perguntas, testes e acesso a informacao confiavel.", "keywords": ["vergonha", "ajuda"]},
    {"claim": "Redes sociais sempre sao fontes confiaveis", "label": "MITO", "explanation": "Redes sociais podem conter informacao incorreta; e importante confirmar em fontes oficiais.", "keywords": ["redes sociais", "fontes"]},
    {"claim": "Conversar com familia pode apoiar decisoes informadas", "label": "VERDADE", "explanation": "Quando ha abertura, dialogo familiar pode orientar e reduzir desinformacao.", "keywords": ["familia", "dialogo"]},
    {"claim": "Metodos contraceptivos sao todos iguais", "label": "MITO", "explanation": "Metodos diferem em eficacia, uso, efeitos e indicacao.", "keywords": ["metodos", "contraceptivos"]},
    {"claim": "Testes de IST sao parte de cuidado preventivo", "label": "VERDADE", "explanation": "Testagem ajuda a diagnosticar cedo, tratar e proteger parceiros.", "keywords": ["testes", "ists"]},
    {"claim": "Uma pessoa parece saudavel, entao nao pode ter IST", "label": "MITO", "explanation": "Aparencia nao confirma estado de saude sexual; algumas infeccoes sao silenciosas.", "keywords": ["aparencia", "ists"]},
    {"claim": "Informacao escolar pode reduzir mitos", "label": "VERDADE", "explanation": "Educacao escolar estruturada ajuda a substituir boatos por conhecimento verificavel.", "keywords": ["escola", "mitos"]},
    {"claim": "Alcool melhora a capacidade de consentir", "label": "MITO", "explanation": "Alcool pode reduzir julgamento; consentimento exige clareza e liberdade.", "keywords": ["alcool", "consentimento"]},
    {"claim": "Abstinencia e uma forma de evitar gravidez e ISTs", "label": "VERDADE", "explanation": "Nao ter contacto sexual elimina risco de gravidez e reduz risco de muitas ISTs.", "keywords": ["abstinencia", "prevencao"]},
    {"claim": "ISTs desaparecem sempre sozinhas", "label": "MITO", "explanation": "ISTs podem agravar sem tratamento; atendimento de saude e essencial.", "keywords": ["ists", "tratamento"]},
    {"claim": "Preservativo deve ser usado desde o inicio da relacao", "label": "VERDADE", "explanation": "Uso desde o inicio reduz exposicao a fluidos e risco de gravidez/ISTs.", "keywords": ["preservativo", "uso correto"]},
    {"claim": "O coito interrompido e totalmente seguro", "label": "MITO", "explanation": "Coito interrompido tem falhas frequentes e nao protege contra ISTs.", "keywords": ["coito interrompido", "gravidez"]},
    {"claim": "Conhecer o proprio corpo ajuda a identificar sinais de alerta", "label": "VERDADE", "explanation": "Autoconhecimento facilita procurar ajuda quando algo muda ou preocupa.", "keywords": ["corpo", "sinais"]},
    {"claim": "Gravidez nao planeada so acontece por irresponsabilidade", "label": "MITO", "explanation": "Pode envolver falta de acesso, informacao, violencia, falha de metodo ou pressao social.", "keywords": ["gravidez", "irresponsabilidade"]},
    {"claim": "Servicos de saude devem respeitar confidencialidade", "label": "VERDADE", "explanation": "Confidencialidade melhora confianca e acesso a orientacao.", "keywords": ["confidencialidade", "saude"]},
    {"claim": "Pessoas jovens nao podem fazer perguntas sobre sexualidade", "label": "MITO", "explanation": "Perguntar e uma forma responsavel de aprender e prevenir riscos.", "keywords": ["perguntas", "jovens"]},
    {"claim": "Violencia sexual nunca e culpa da vitima", "label": "VERDADE", "explanation": "A responsabilidade e sempre de quem pratica a violencia.", "keywords": ["violencia", "vitima"]},
    {"claim": "Namoro exige prova sexual de amor", "label": "MITO", "explanation": "Afeto nao exige sexo; limites e consentimento devem ser respeitados.", "keywords": ["namoro", "amor"]},
    {"claim": "Fontes oficiais de saude sao melhores para duvidas clinicas", "label": "VERDADE", "explanation": "Fontes oficiais e profissionais qualificados reduzem risco de desinformacao.", "keywords": ["fontes oficiais", "saude"]},
    {"claim": "Contracepcao de emergencia deve ser rotina diaria", "label": "MITO", "explanation": "Ela e para situacoes especificas; nao substitui metodo regular orientado.", "keywords": ["emergencia", "contracepcao"]},
    {"claim": "Camisinha tem prazo de validade", "label": "VERDADE", "explanation": "Validade e conservacao importam para evitar rompimento ou perda de eficacia.", "keywords": ["camisinha", "validade"]},
    {"claim": "Mitos podem ser corrigidos com dialogo e evidencia", "label": "VERDADE", "explanation": "Dialogo respeitoso e dados confiaveis ajudam a mudar crencas incorretas.", "keywords": ["mitos", "evidencia"]},
    {"claim": "Todas as ISTs impedem uma vida saudavel", "label": "MITO", "explanation": "Com diagnostico, tratamento e acompanhamento, muitas pessoas vivem com saude.", "keywords": ["ists", "vida saudavel"]},
    {"claim": "Preservativo feminino tambem e opcao de protecao", "label": "VERDADE", "explanation": "E uma alternativa eficaz quando usada corretamente.", "keywords": ["preservativo feminino", "protecao"]},
    {"claim": "Informacao dos colegas nunca precisa ser verificada", "label": "MITO", "explanation": "Colegas podem repetir boatos; verificar em fontes confiaveis e essencial.", "keywords": ["colegas", "verificar"]},
    {"claim": "Autoestima e comunicacao influenciam escolhas saudaveis", "label": "VERDADE", "explanation": "Pessoas com apoio e comunicacao tendem a negociar limites e protecao melhor.", "keywords": ["autoestima", "comunicacao"]},
    {"claim": "Sangramento apos relacao e sempre normal", "label": "MITO", "explanation": "Sangramento pode ter varias causas e deve ser avaliado se preocupa ou persiste.", "keywords": ["sangramento", "saude"]},
    {"claim": "Gravidez na adolescencia pode afetar percurso escolar", "label": "VERDADE", "explanation": "Pode trazer desafios sociais, economicos e escolares que exigem apoio.", "keywords": ["adolescencia", "escola"]},
    {"claim": "Homens nao precisam fazer testes de IST", "label": "MITO", "explanation": "Todos podem precisar de testes, independentemente do genero.", "keywords": ["homens", "testes"]},
    {"claim": "Comunidade e escola podem trabalhar juntas na prevencao", "label": "VERDADE", "explanation": "Acoes integradas melhoram acesso a informacao e reduzem risco coletivo.", "keywords": ["comunidade", "escola"]},
    {"claim": "E impossivel engravidar durante a menstruacao", "label": "MITO", "explanation": "O risco e menor em alguns casos, mas nao e impossivel, especialmente com ciclos irregulares.", "keywords": ["menstruacao", "gravidez"]},
    {"claim": "Saude sexual inclui bem-estar fisico, emocional e social", "label": "VERDADE", "explanation": "Nao se limita a ausencia de doenca; envolve respeito, seguranca e informacao.", "keywords": ["saude sexual", "bem-estar"]},
    {"claim": "Apenas quem tem muitos parceiros contrai IST", "label": "MITO", "explanation": "Qualquer pessoa exposta sem protecao pode contrair IST.", "keywords": ["parceiros", "ists"]},
    {"claim": "Usar lubrificante adequado pode reduzir rompimento do preservativo", "label": "VERDADE", "explanation": "Lubrificante compativel reduz friccao e pode melhorar seguranca.", "keywords": ["lubrificante", "preservativo"]},
    {"claim": "Educacao sexual substitui valores familiares", "label": "MITO", "explanation": "Educacao sexual fornece conhecimento; familias continuam importantes na formacao de valores.", "keywords": ["valores", "familia"]},
    {"claim": "Pedir ajuda cedo pode evitar agravamento de problemas", "label": "VERDADE", "explanation": "Orientacao precoce facilita cuidado, tratamento e decisao informada.", "keywords": ["ajuda", "prevencao"]},
]


def normalize(text: str) -> str:
    """Normaliza texto para comparacao robusta por palavras."""

    return re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z0-9À-ÿ\s]", " ", str(text).lower())).strip()


def detect_myth(statement: str) -> dict:
    """Encontra o mito/verdade mais parecido e devolve explicacao educativa."""

    query = normalize(statement)
    if not query:
        return {"label": "INDETERMINADO", "confidence": 0, "explanation": "Escreva uma afirmacao para analisar.", "match": None}

    documents = [normalize(f"{item['claim']} {' '.join(item['keywords'])}") for item in KNOWLEDGE_BASE]
    if TfidfVectorizer and cosine_similarity:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(documents + [query])
        scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
        best_index = int(scores.argmax())
        confidence = round(float(scores[best_index]) * 100, 1)
    else:  # pragma: no cover
        scores = [SequenceMatcher(None, query, doc).ratio() for doc in documents]
        best_index = max(range(len(scores)), key=lambda index: scores[index])
        confidence = round(scores[best_index] * 100, 1)

    match = KNOWLEDGE_BASE[best_index]
    return {
        "label": match["label"],
        "confidence": confidence,
        "explanation": match["explanation"],
        "match": match["claim"],
        "keywords": match["keywords"],
    }
