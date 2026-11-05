# 🤖 Meu Agente Multiagente com Python

Este é um projeto de estudo de **IA Agêntica** usando a biblioteca `agentmold` e a API rápida da **Groq**.

## 🧠 O que ele faz?
O sistema é composto por um **Supervisor** e três **Especialistas**:
- 🌤️ **Clima:** Busca a previsão do tempo em tempo real (Open-Meteo).
- 📁 **Arquivos:** Cria e lê arquivos de texto locais.
- 🧮 **Financeiro:** Faz cálculos matemáticos e consulta CEPs (ViaCEP).

## 🛠️ Como rodar o projeto na sua máquina
1. Clone o repositório.
2. Crie e ative um ambiente virtual: `python -m venv venv` e `.\venv\Scripts\activate`
3. Instale as dependências: `pip install agentmold python-dotenv requests "agentmold[openai]"`
4. Crie um arquivo `.env` baseado no `.env.example` e coloque sua chave da Groq.
5. Rode: `python agente_teste.py`

## 🚀 Tecnologias
- Python 3.15
- Groq API (Llama 3)
- Agentmold
- Requests