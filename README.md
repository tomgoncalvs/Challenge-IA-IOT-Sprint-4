# Classificação em Clusters com Inteligência Artificial

## Descrição do Projeto

Este projeto classifica usuários com base em seu comportamento de compra utilizando técnicas de Inteligência Artificial. O objetivo é agrupar usuários em clusters e gerar campanhas de marketing personalizadas para cada grupo, melhorando a segmentação e eficácia das estratégias de marketing.

# Integrantes do Grupo
- Beatriz Lucas - RM99104
- Enzo Farias - RM 98792
- Ewerton Gonçalves - RM98571
- Guilherme Tantulli - RM97890
- Thiago Zupelli - RM99085

# Vídeo da Execução (10m)
- [Execução Youtube](https://youtu.be/avwsiN9DSY0 "Execução Youtube")

## Tecnologias Usadas
* **Python (Flask)**: Para criação de rotas, views e gerenciamento de lógica de backend.
* **SQLAlchemy**: Para interação com o banco de dados.
* **OpenAI API**: Para geração de campanhas de marketing com base nos clusters de clientes.
* **dotenv**: Para gerenciar variáveis de ambiente e credenciais de API.

## Configuração Inicial
1. Clone o projeto e instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

2. Configuração do OpenAI API Key:
    * Crie um arquivo `.env` no diretório raiz.
    * Adicione a chave de API:
      ```plaintext
      OPENAI_API_KEY=seu_openai_api_key
      ```

3. Configuração do Banco de Dados:
    * Configure sua conexão no módulo `database.py`.
    * Execute as migrações para configurar as tabelas necessárias (usuários, clusters, etc.).

## Estrutura do Código
1. **Rotas de Flask**
    * `/`: Página inicial.
    * `/view_clusters`: Visualização dos clusters, mostrando informações como ID, nome, ticket médio e número de usuários.
    * `/add_cluster`: Adiciona um novo cluster ao banco de dados.
    * `/edit_cluster_name`: Edita o nome de um cluster existente.
    * `/update_cluster`: Atualiza os clusters usando o modelo de predição.
    * `/sugerir_clusters`: Sugere usuários para clusters com base em dados históricos.
    * `/get_analysis`: Retorna uma análise específica de um usuário dentro de um cluster.
    * `/add_feedback`: Adiciona feedback de um usuário sobre o cluster.
    * `/add_user_to_cluster`: Associa um usuário a um cluster.
    * `/gerar_campanha`: Gera uma campanha de marketing usando OpenAI com base nos dados de um cluster específico.
    * `/get_cluster_users/<int:cluster_id>`: Retorna todos os usuários associados a um cluster específico.

2. **Modelos de Dados**
    * `analises_usuario_cluster`: Define uma tabela para armazenar as análises geradas para cada usuário dentro de clusters.

3. **Integração com OpenAI**
    * A rota `/gerar_campanha` usa OpenAI para gerar campanhas personalizadas para cada cluster. Utilizando a API GPT-4, um prompt de marketing é passado com informações sobre o cluster e os produtos recomendados. A resposta é então retornada ao frontend e exibida para o usuário.

## Funcionalidades Principais
1. **Gestão de Clusters**: Adiciona, visualiza e edita clusters de clientes. Associa usuários aos clusters com base em dados de consumo e ticket médio.
2. **Análise de Usuários e Sugestões**: Sugere clusters para novos usuários com base em padrões de comportamento e histórico de dados.
3. **Geração de Campanhas de Marketing**: Cria campanhas personalizadas utilizando OpenAI.

## Estrutura do Banco de Dados
* **cluster_names**: Armazena informações dos clusters, incluindo nome, ticket médio e frequência de compras.
* **clusters**: Registra os usuários associados a cada cluster.
* **usuarios**: Contém dados dos usuários, como idade, cidade, ticket médio e frequência de compras.
* **analises_usuario_cluster**: Guarda as análises geradas para cada usuário em um cluster.
* **cluster_feedback**: Registra o feedback dos usuários sobre a associação com clusters específicos.

## Considerações Finais
Este sistema é projetado para escalar conforme novos dados de clientes e clusters são adicionados, permitindo uma análise detalhada e geração automática de campanhas.

---

## Modelo de Aprendizado e Técnicas Utilizadas
Este módulo utiliza aprendizado de máquina e processamento de linguagem natural (NLP) para sugerir e refinar o processo de clusterização de clientes em um sistema de CRM.

### Técnicas e Ferramentas Utilizadas
- **RandomForestClassifier (Scikit-Learn)**: Utilizado para prever a associação de usuários a clusters.
- **OpenAI GPT-4**: Processamento de linguagem natural para gerar análises textuais detalhadas de usuários.
- **Pickle**: Persistência do modelo de aprendizado para reuso sem necessidade de retreinamento.

### Funções e Métodos
- **`load_data()`**: Carrega dados de usuários e feedbacks armazenados no banco de dados.
- **`train_model()`**: Treina o modelo RandomForestClassifier com base nos dados carregados.
- **`load_model()`**: Carrega o modelo treinado de disco.
- **`predict_potential_users()`**: Gera sugestões de clusters para usuários que ainda não estão associados a nenhum cluster.
- **`generate_analysis_text(usuario, cluster)`**: Usa GPT-4 para criar uma análise breve e personalizada.
- **`get_or_create_analysis(usuario_id, cluster_id, usuario, cluster)`**: Gera ou recupera uma análise detalhada sobre a associação do usuário ao cluster.

---

## Fluxo do Processo de Clusterização e Análise
1. **Carregar Dados**: Obtenção de dados de usuários e clusters.
2. **Treinamento e Predição**: Treinamento do modelo RandomForest e predição de novos usuários para clusters.
3. **Geração de Análise**: Geração de análises textuais para sugerir clusters com base no comportamento do usuário.
4. **Armazenamento de Resultados**: Armazenamento das análises para uso futuro e consulta rápida.

---

## Considerações Finais
Este sistema é projetado para escalar conforme novos dados de clientes e clusters são adicionados, permitindo uma análise detalhada e geração automática de campanhas.

---

## Modelo de Aprendizado e Técnicas Utilizadas
Este módulo utiliza aprendizado de máquina e processamento de linguagem natural (NLP) para sugerir e refinar o processo de clusterização de clientes em um sistema de CRM. O objetivo é identificar usuários potenciais para clusters específicos com base em seus padrões de consumo e fornecer insights detalhados sobre suas características e potenciais.

### Técnicas e Ferramentas Utilizadas
1. **RandomForestClassifier (Scikit-Learn)**: Utilizado para prever a associação de usuários a clusters.
2. **OpenAI GPT-4**: Processamento de linguagem natural para gerar análises textuais detalhadas de usuários, justificando a associação a clusters específicos e prevendo o comportamento de compra.
3. **Pickle**: Persistência do modelo de aprendizado para reuso sem necessidade de retreinamento.
4. **SQLAlchemy**: Facilita o gerenciamento e consultas ao banco de dados.

### Funções e Métodos
1. **`load_data()`**  
   Carrega dados de usuários e feedbacks armazenados no banco de dados, incluindo:
   * **Ticket Médio**: Valor médio gasto por cada usuário.
   * **Intervalo de Dias**: Tempo médio entre compras.
   * **Pertence ao Cluster**: Indicador booleano derivado dos feedbacks, indicando se o usuário foi previamente associado ao cluster.
   
2. **`train_model()`**  
   Treina o modelo RandomForestClassifier:
   * **Entrada (X)**: Ticket médio e intervalo de dias do usuário.
   * **Rótulo (y)**: Indicação se o usuário pertence a um cluster.
   O modelo é salvo com Pickle para evitar retrainings desnecessários. A robustez do Random Forest captura relações não-lineares entre variáveis.

3. **`load_model()`**  
   Carrega o modelo treinado de disco, ou treina um novo caso o arquivo não exista. Garante que o sistema sempre tenha um modelo disponível.

4. **`predict_potential_users()`**  
   Gera sugestões de clusters para usuários ainda não associados:
   * Carrega dados de clusters e usuários.
   * Verifica se o ticket médio e intervalo de dias do usuário atendem aos critérios de algum cluster.
   * Se atendidos, uma análise é gerada com GPT-4 explicando a associação.

5. **`generate_analysis_text(usuario, cluster)`**  
   Usa GPT-4 para criar uma análise breve e personalizada explicando a associação do usuário ao cluster:
   * Inclui ticket médio e intervalo de dias do usuário e do cluster.
   * A análise é armazenada para futura consulta, ajudando a interpretar as associações.

6. **`get_or_create_analysis(usuario_id, cluster_id, usuario, cluster)`**  
   Gera ou recupera uma análise detalhada sobre a associação do usuário ao cluster:
   * Se a análise já existir: Retorna o texto salvo.
   * Se não existir: Gera uma nova análise detalhada com GPT-4, considerando dados específicos do usuário e do cluster.

---

## Modelo de Classificação com Random Forest
O Random Forest é usado para classificar a probabilidade de um usuário pertencer a um cluster específico. Este modelo é eficiente para dados com variáveis independentes contínuas, como ticket médio e intervalo de dias. Ele utiliza a média de várias árvores de decisão para melhorar a precisão e reduzir o risco de overfitting.

---

## Técnicas de NLP com GPT-4 para Geração de Análises
O GPT-4 permite gerar análises personalizadas com alta relevância contextual para cada usuário e cluster. Alguns aspectos da implementação incluem:
* **Análise de Qualificação**: Explica por que um usuário é adequado para um cluster específico, considerando suas características e as do cluster.
* **Feedback sobre o Potencial de Compra**: O modelo fornece previsões sobre o comportamento futuro do usuário, permitindo decisões de marketing mais informadas.

---

## Dados e Estrutura do Banco de Dados
Para suportar o sistema, o banco de dados contém:
* **Usuários**: Informações sobre ticket médio e intervalo de dias de cada usuário.
* **Clusters**: Regras de associação, incluindo requisitos de ticket médio e frequência de compras.
* **Feedbacks de Cluster**: Informações sobre a associação e o feedback dos usuários em relação aos clusters sugeridos.
* **Análises de Usuário e Cluster**: Texto gerado sobre a adequação de cada usuário a clusters específicos.

---

## Fluxo do Processo de Clusterização e Análise
1. **Carregar Dados**: Os dados de usuários e clusters são carregados.
2. **Treinamento e Predição**: O modelo Random Forest é treinado e usado para prever usuários potenciais para clusters.
3. **Geração de Análise**: Para cada usuário que atende aos critérios de um cluster, uma análise textual é gerada com o GPT-4.
4. **Armazenamento de Resultados**: As análises são armazenadas no banco para consulta futura, possibilitando insights rápidos e reutilização.

---

## Dificuldades e Aprendizados

### Dificuldades
1. **Integração de APIs e Modelos de IA**  
   * Desafio: Integrar a API do ChatGPT (ou GPT-4) para gerar análises e campanhas personalizadas, ajustando chamadas para eficiência.

2. **Treinamento e Avaliação do Modelo de Machine Learning**  
   * Desafio: Configurar e treinar o modelo Random Forest para clusters específicos, com cuidado na preparação dos dados e seleção de parâmetros.
   * Aprendizado: Entendimento sobre algoritmos de classificação e a importância de dados de qualidade.

3. **Manipulação de Dados com SQL e Pandas**  
   * Desafio: Trabalhar com consultas SQL complexas e transformar dados para análise e modelagem.
   * Aprendizado: Habilidades de SQL e maior experiência com manipulação de dados usando Pandas.

4. **Interface e Experiência do Usuário**  
   * Desafio: Criar uma interface intuitiva para que os usuários possam gerar campanhas e analisar clusters.
   * Aprendizado: Aprimoramento na criação de interfaces responsivas e intuitivas.

5. **Gerenciamento e Tratamento de Erros**  
   * Desafio: Lidar com falhas na API ou erros ao conectar-se ao banco de dados.
   * Aprendizado: Práticas de tratamento de erros para uma experiência de usuário estável e confiança na correção de problemas.

### Aprendizados
1. **Compreensão Profunda de Machine Learning**  
   Desenvolvimento, treino e validação do modelo de Machine Learning contribuíram para uma melhor compreensão dos algoritmos de classificação.

2. **Estruturação e Organização de Código**  
   A divisão do código em módulos, como clustering e modelo de previsão, ajudou a manter o projeto organizado, facilitando manutenções.

3. **Integração de Inteligência Artificial com Aplicações Práticas**  
   Aplicar GPT-4 para criar análises e campanhas personalizadas demonstrou o potencial da IA em tarefas práticas e de negócios.

4. **Práticas de Engenharia de Software e Documentação**  
   Manter o projeto documentado no GitHub facilitou a comunicação e a colaboração.

5. **Refinamento de Habilidades em Desenvolvimento Web**  
   A implementação de uma interface interativa para campanhas consolidou conhecimentos em HTML, CSS e JavaScript, com práticas modernas de UX/UI.

---

## Reflexão Final
O projeto proporcionou uma visão abrangente sobre o ciclo de desenvolvimento de uma aplicação que integra IA e Machine Learning com interfaces amigáveis. Cada dificuldade enfrentada contribuiu para o crescimento técnico e a capacidade de resolver problemas complexos, destacando a importância do aprendizado contínuo e da prática em situações do mundo real.

