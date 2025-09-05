
Circuito MiniPreço
Este repositório contém o código-fonte de um aplicativo web interativo, desenvolvido com Streamlit, para o acompanhamento do Circuito MiniPreço. A aplicação permite visualizar o desempenho das lojas em tempo real, com dados extraídos diretamente do SharePoint.

Funcionalidades Principais
Pista de Corrida do Circuito: Uma visualização dinâmica que mostra o progresso das lojas em direção à linha de chegada, baseada em sua pontuação total.

Pódio e Classificação Completa: Acompanhe o ranking das lojas, veja os líderes e o pódio dos ganhadores.

Visão Geral: Um painel de controle que apresenta as principais métricas do circuito.

Visão por Loja: Filtre e visualize o desempenho detalhado de uma loja específica, com a pontuação por cada etapa do circuito.

Visão por Etapa: Confira o ranking das lojas em cada etapa individual, destacando os 10 melhores colocados.

Tecnologias
O aplicativo é construído com as seguintes ferramentas e bibliotecas:

Python 3.x

Streamlit: Para a interface do usuário.

Pandas: Para manipulação e análise dos dados.

Plotly: Para a criação de gráficos interativos.

Office365-SharePoint: Para a conexão e extração dos dados do SharePoint.

Como Instalar e Rodar
Siga os passos abaixo para configurar e executar o aplicativo localmente.

1. Requisitos
Certifique-se de ter o Python 3.x instalado.

2. Instalação das Dependências
Crie um ambiente virtual (opcional, mas recomendado) e instale as bibliotecas necessárias:

Bash

pip install -r requirements.txt
Ou instale manualmente:

Bash

pip install streamlit pandas numpy plotly office365-sharepoint
3. Configuração do SharePoint
O aplicativo se conecta a um arquivo de dados do SharePoint usando credenciais seguras. Você precisa configurar um arquivo secrets.toml na pasta .streamlit do seu projeto. Crie a pasta e o arquivo, e adicione suas credenciais:

Ini, TOML

# .streamlit/secrets.toml
[sharepoint_credentials]
username = "seu_usuario@empresa.com"
password = "sua_senha"
ATENÇÃO: Nunca compartilhe este arquivo e garanta que ele não seja enviado para o GitHub. Adicione .streamlit/secrets.toml ao seu arquivo .gitignore.

4. Executando o Aplicativo
No terminal, na pasta raiz do projeto, execute o comando:

Bash

streamlit run circuito_lojas_app.py
O aplicativo será aberto automaticamente no seu navegador. Agora você pode interagir com o painel e acompanhar o Circuito MiniPreço.
