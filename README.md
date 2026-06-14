# EduSex AI

EduSex AI é uma aplicação full stack para recolha, análise e visualização de dados sobre educação sexual. O fluxo implementado é:

Frontend HTML5/CSS3/Bootstrap/JavaScript/Chart.js -> API Flask REST -> Serviços -> Machine Learning -> MongoDB. 

## Estrutura

- `app.py`: cria a app Flask, regista blueprints, páginas e dados iniciais.
- `config.py`: centraliza MongoDB, JWT e modo de testes.
- `database/mongodb.py`: liga ao MongoDB real e usa fallback em memória para testes/demo.
- `models/`: cria e valida documentos `users` e `survey_responses`.
- `services/`: autenticação, RBAC, analytics, importação CSV e chatbot.
- `ml/`: índice explicável, DecisionTreeClassifier, predição e K-Means.
- `routes/`: endpoints REST de autenticação, inquéritos, analytics, chatbot, ML e API pública.
- `templates/` e `static/`: interface web ligada aos endpoints reais.
- `docs/swagger.yaml`: documentação OpenAPI.
- `tests/`: testes de login, JWT, RBAC, API e ML.

## Instalação

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Configure MongoDB em `.env`. Se não houver MongoDB local, a aplicação cai para base em memória para facilitar demonstrações.

## Execução

```bash
source venv/bin/activate
flask --app app run --debug
```

Aceda a `http://127.0.0.1:5000`.

## Autenticação e Autorização

O login em `/auth/login` gera `access_token` e `refresh_token` com Flask-JWT-Extended. O frontend guarda os tokens em `localStorage` e envia `Authorization: Bearer <token>` em cada pedido protegido.

Papéis:

- `ADMIN`: importa CSV, treina modelos, gera API keys e vê tudo.
- `RESEARCHER`: consulta estatísticas, clusters, predições e API.
- `USER`: responde inquéritos e usa chatbot.

Decorators RBAC:

- `admin_required`
- `researcher_required`

## Endpoints principais

- `POST /auth/register`: registo com bcrypt.
- `POST /auth/login`: login JWT.
- `POST /auth/logout`: revoga token.
- `POST /auth/refresh`: renova token.
- `GET /auth/profile`: perfil autenticado.
- `POST /surveys`: grava resposta.
- `POST /surveys/upload`: importa CSV.
- `GET /analytics/dashboard`: indicadores e gráficos.
- `GET /analytics/regions`: mapa/ranking de desinformação.
- `POST /chatbot/message`: chatbot educativo.
- `POST /ml/predict`: predição protegida.
- `POST /ml/train`: treino do modelo.
- `GET /api/v1/statistics`: API pública com API key.
- `GET /api/v1/export/csv|json|excel`: exportação anonimizada.

## Machine Learning

`calculate_disinformation_score()` soma 20 pontos por cada fator de risco: ausência de educação sexual, fonte pouco estruturada, vergonha, necessidade de mais informação e ausência de educação escolar. A escala é:

- 0-30: Baixo, bem informado.
- 31-60: Médio, moderadamente informado.
- 61-100: Alto risco.

`ml/train_model.py` treina um `DecisionTreeClassifier` com rótulos derivados desse índice. `ml/model_comparison.py` treina também um `RandomForestClassifier`, compara `accuracy`, `precision`, `recall` e `f1`, e grava o melhor modelo.

`ml/trend_prediction.py` usa `LinearRegression` e `RandomForestRegressor` para projetar a evolução futura do índice de desinformação e da necessidade de informação. `ml/hierarchical_clustering.py` adiciona clusterização hierárquica com perfis A-D para comparação com K-Means.

`services/explainable_ai.py` gera explicações usando:

- regras da decision tree simbólica
- importância manual das features
- SHAP, quando disponível

`services/myth_detector.py` contém uma base de conhecimento com mais de 50 afirmações e usa TF-IDF para encontrar a afirmação mais semelhante.

`services/recommendation_engine.py` gera recomendações personalizadas com base no risco, cluster, uso de contraceptivos e resultado da IA.

`services/report_generator.py` cria relatórios automáticos em TXT, PDF e DOCX.

`services/data_insights.py` produz insights, problemas, oportunidades e um `Sex Education Awareness Score` nacional.

## Dados

`data/sample_dataset.csv` contém 500 registos fictícios realistas. A app carrega uma amostra inicial se a base estiver vazia. A interface nunca desenha gráficos a partir de dados hardcoded; ela consome `/analytics/dashboard`.

## Testes

```bash
source venv/bin/activate
pytest
```

## Swagger

Abra `docs/swagger.yaml` num editor Swagger/OpenAPI ou importe-o para ferramentas como Swagger UI e Postman.

## Autores

## Integração com Hugging Face

1. Crie um ficheiro `.env` na raiz do projecto com a sua chave HF:

```
HF_TOKEN=seu_token_aqui
```

2. Opcional: trocar o modelo preferencial

```
HF_PREFERRED_MODEL=meta-llama/Llama-3-8B-Instruct
HF_FALLBACK_MODEL=mistralai/Mistral-7B-Instruct-v0.3
```

3. Instale dependências e execute:

```bash
pip install -r requirements.txt
flask --app app run --debug
```

4. Endpoints AI principais:

- `POST /api/v2/chat` body: {"message": "...", "user_id": "..."}
- `POST /api/v2/sentiment` body: {"text": "..."}
- `POST /api/v2/sentiment/batch` analisa todas as respostas e grava em `sentiment_results`
- `GET /api/v2/export-report/pdf` gera PDF com relatório AI
- `GET /api/v2/export-report/docx` gera DOCX com relatório AI
- `GET /api/v2/ai/insights` devolve Top 5 insights
- `GET /api/v2/recommendations/<user_id>` devolve recomendações personalizadas

Notas de segurança: o token da Hugging Face é lido exclusivamente a partir de `os.getenv("HF_TOKEN")` e nunca é exposto nas respostas da API.

