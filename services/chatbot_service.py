"""Chatbot educativo baseado em regras.

Esta implementação é simples, transparente e preparada para futura troca por
um provedor de IA generativa mantendo a mesma função answer_question().
"""


RESPONSES = {
    "ist": "ISTs são infeções sexualmente transmissíveis. A prevenção inclui preservativo, testagem e orientação médica.",
    "puberdade": "A puberdade é uma fase de mudanças físicas e emocionais. Cada pessoa tem o seu ritmo.",
    "gravidez": "A gravidez precoce pode impactar saúde e estudos. Informação, planeamento familiar e acesso a serviços ajudam na prevenção.",
    "contraceptivo": "Métodos contraceptivos incluem preservativo, pílula, injetáveis, implantes e DIU. Um profissional de saúde ajuda a escolher.",
    "consentimento": "Consentimento deve ser livre, informado, reversível e claro. Sem consentimento, não há relação saudável.",
    "planeamento": "Planeamento familiar envolve decisões informadas sobre se e quando ter filhos, com apoio de serviços de saúde.",
    "educação sexual": "Educação sexual oferece informação científica sobre corpo, respeito, prevenção, relações e saúde.",
}


def answer_question(question: str) -> dict:
    """Responde a pergunta procurando palavras-chave educativas."""

    normalized = question.lower()
    for keyword, response in RESPONSES.items():
        if keyword in normalized:
            return {"answer": response, "topic": keyword}
    return {
        "answer": "Posso ajudar com educação sexual, puberdade, ISTs, contraceptivos, consentimento e planeamento familiar.",
        "topic": "geral",
    }
