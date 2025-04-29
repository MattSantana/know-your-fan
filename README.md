# Know Your Fan - Um App para a FURIA Conhecer os Fãs

Falaaaaaaa avaliador, beleza? Aqui é o Matheus! 👋 Criei esse app pro desafio técnico da FURIA, e ele foi pensado pra ajudar o time a conhecer melhor os fãs de uma forma bem prática.  
O Know Your Fan coleta informações pessoais, verifica a identidade com RG e selfie, e também analisa se o fã tá ligado no universo de esports que a FURIA curte, como CS:GO e Valorant.  
Vou explicar tudo de forma clara e organizada pra você entender direitinho como ele funciona. Bora? 🚀

## O que o App Faz?

O Know Your Fan é uma aplicação web que realiza as seguintes funções:

### 📝 Cadastro do Fã

O usuário preenche um formulário com informações básicas: nome, CPF, endereço, interesses (como "gosto de jogos de tiro") e atividades (por exemplo, "jogo CS:GO nos fins de semana"). Essas informações são armazenadas em um banco de dados.

### 🆔 Validação de Identidade

O usuário envia duas imagens: uma do RG (ou outro documento com foto) e uma selfie. O app:

- Extrai o CPF do RG utilizando OCR (com a biblioteca Tesseract).
- Compara as faces do RG e da selfie para verificar se pertencem à mesma pessoa (usando a biblioteca face_recognition).

> Observação: essa etapa pode demorar alguns segundos devido ao processamento da análise facial.

### 🎮 Análise de Engajamento com Esports

O usuário pode fornecer um link de um perfil online (como Twitch ou Twitter), e o app verifica se esse perfil está relacionado aos interesses da FURIA (buscando palavras-chave como "CS:GO", "Valorant", "FURIA", entre outras).  
Caso o perfil seja relevante, ele é marcado como tal.

### 👤 Exibição do Perfil do Fã

Após as etapas, o app exibe um resumo com as informações do usuário, o status da validação de identidade e se o perfil de esports é relevante para os interesses da FURIA.

### 🗑️ Exclusão de Perfil

Há uma opção para que o usuário remova seu cadastro do banco de dados, caso deseje.

## Como o App Funciona?

O Know Your Fan foi desenvolvido com FastAPI, um framework de Python para criação de APIs, e possui uma interface web construída com HTML e estilizada com Tailwind CSS.  
Ele roda localmente e utiliza um banco de dados SQLite para armazenar os dados.

O fluxo de uso é o seguinte:

- O usuário acessa a aplicação pelo navegador em http://localhost:8000.
- Preenche o formulário inicial com suas informações.
- Envia o RG e a selfie para validação de identidade.
- Fornece um link de perfil de esports (opcional).
- Visualiza o perfil com os resultados das validações.

## Como Executar o App?

### 1. Pré-requisitos

Antes de executar a aplicação, é necessário ter os seguintes itens instalados:

- **Python 3.8 ou superior**: Para executar o código.
- **Tesseract OCR (obrigatório)**: Essa ferramenta é essencial para extrair o CPF do RG.  
  Você precisará baixar e instalar o Tesseract no seu sistema. Faça o download aqui: [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki).  
  Após a instalação, anote o caminho onde o `tesseract.exe` foi instalado (ex.: `C:\Program Files\Tesseract-OCR\tesseract.exe`).  
  No código, o caminho está configurado como `G:\Program Files\Tesseract-OCR\tesseract.exe`.  

  > ⚠️ Atenção: se o Tesseract estiver em um caminho diferente no seu sistema, você deve atualizar o caminho na variável `tesseract_path` no arquivo `backend/main.py`, senão o app não vai funcionar.

- **Dependências do Python**: Instale as bibliotecas necessárias com o seguinte comando:

```bash
pip install fastapi uvicorn jinja2 opencv-python pytesseract face_recognition requests beautifulsoup4 textblob numpy
