import os
import requests
import streamlit as st
from dotenv import load_dotenv
from agentmold import Agent, tool
import datetime
from zoneinfo import ZoneInfo
from datetime import datetime
import re

# --- CONFIGURAÇÃO DO AMBIENTE ---
load_dotenv()
os.environ["OPENAI_BASE_URL"] = "https://api.groq.com/openai/v1"

# ==========================================
# 1. FERRAMENTAS BÁSICAS (As "mãos" dos agentes)
# ==========================================

# * Nova linha adicionada
@tool
def get_current_time(city: str = "São Paulo") -> str:
    """Get the current time for a given city (e.g., 'Londres', 'Tóquio')."""
    try:
        # Mapeamento simples de nomes de cidades para fusos IANA
        timezone_map = {
            "são paulo": "America/Sao_Paulo",
            "sao paulo": "America/Sao_Paulo",
            "londres": "Europe/London",
            "london": "Europe/London",
            "tóquio": "Asia/Tokyo",
            "tokyo": "Asia/Tokyo",
            "nova york": "America/New_York",
            "new york": "America/New_York",
            "paris": "Europe/Paris",
            "berlim": "Europe/Berlin",
            "berlin": "Europe/Berlin",
            "sydney": "Australia/Sydney",
            "dubai": "Asia/Dubai",
            "singapura": "Asia/Singapore",
        }
        
        # Normaliza o nome da cidade (minúsculas, sem acentos)
        city_key = city.lower().strip()
        timezone_name = timezone_map.get(city_key)
        
        if not timezone_name:
            return f"Não tenho o fuso horário configurado para '{city}'. Tente Londres, Tóquio, Nova York, Paris, etc."
        
        # Obtém a hora atual no fuso horário especificado
        tz = ZoneInfo(timezone_name)
        now = datetime.now(tz)
        
        # Formata a resposta
        return f"A hora atual em {city} é {now.strftime('%H:%M:%S')} do dia {now.strftime('%d/%m/%Y')} (fuso: {timezone_name})."
    except Exception as e:
        return f"Erro ao buscar o horário: {e}"

@tool
def calculate(expression: str) -> str:
    """Evaluate a simple math expression."""
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"Erro: {e}"

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a given city name."""
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=pt&format=json"
        geo_resp = requests.get(geo_url).json()
        if "results" not in geo_resp or not geo_resp["results"]: return f"Cidade '{city}' não encontrada."
        
        lat, lon = geo_resp["results"][0]["latitude"], geo_resp["results"][0]["longitude"]
        nome = geo_resp["results"][0]["name"]
        
        w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code&timezone=auto"
        w_resp = requests.get(w_url).json()
        temp, codigo = w_resp["current"]["temperature_2m"], w_resp["current"]["weather_code"]
        
        climas = {0: "Céu limpo", 1: "Principalmente limpo", 2: "Parcialmente nublado", 3: "Nublado", 45: "Nevoeiro", 51: "Chuvisco leve", 61: "Chuva leve", 63: "Chuva moderada", 65: "Chuva forte", 95: "Tempestade"}
        return f"O clima em {nome} é: {climas.get(codigo, 'Desconhecido')}, com {temp}°C."
    except Exception as e: return f"Erro: {e}"

@tool
def search_cep(cep: str) -> str:
    """Search for an address using a Brazilian CEP."""
    try:
        cep_limpo = ''.join(filter(str.isdigit, cep))
        if len(cep_limpo) != 8: return "CEP inválido."
        resp = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/").json()
        if "erro" in resp: return "CEP não encontrado."
        return f"Rua: {resp.get('logradouro')}, Bairro: {resp.get('bairro')}, Cidade: {resp.get('localidade')}-{resp.get('uf')}"
    except Exception as e: return f"Erro: {e}"

@tool
def write_to_file(filename: str, content: str) -> str:
    """Write text content to a file."""
    try:
        if ".." in filename or "/" in filename or "\\" in filename: return "Nome inválido."
        with open(filename, "w", encoding="utf-8") as f: f.write(content)
        return f"Arquivo '{filename}' salvo."
    except Exception as e: return f"Erro: {e}"

@tool
def read_file(filename: str) -> str:
    """Read the contents of a file."""
    try:
        if ".." in filename or "/" in filename or "\\" in filename: return "Nome inválido."
        if not os.path.exists(filename): return "Arquivo não existe."
        with open(filename, "r", encoding="utf-8") as f: return f.read()
    except Exception as e: return f"Erro: {e}"

# ==========================================
# 2. CRIAÇÃO DOS AGENTES (Usando cache para não recriar a cada mensagem)
# ==========================================
llm_config = {"provider": "openai", "model": "openai/gpt-oss-20b"}

@st.cache_resource
def carregar_agentes():
    agente_clima = Agent(name="Especialista em Clima", instructions="Você é um meteorologista. Use get_weather.", tools=[get_weather], llm=llm_config)
    agente_arquivos = Agent(name="Especialista em Arquivos", instructions="Gerencie arquivos. Use read_file e write_to_file.", tools=[read_file, write_to_file], llm=llm_config)
    agente_financeiro = Agent(
        name="Especialista Financeiro", 
        instructions="Faça cálculos, CEPs e consulte horas. Use calculate, search_cep e get_current_time.", 
        tools=[calculate, search_cep, get_current_time],
        llm=llm_config
    )


    # agente_financeiro = Agent(name="Especialista Financeiro", instructions="Faça cálculos e CEPs. Use calculate e search_cep.", tools=[calculate, search_cep, get_current_time], llm=llm_config)


    @tool
    def chamar_clima(pergunta: str) -> str:
        """Chame para perguntas sobre clima."""
        return agente_clima.run(pergunta)

    @tool
    def chamar_arquivos(pergunta: str) -> str:
        """Chame para ler ou criar arquivos."""
        return agente_arquivos.run(pergunta)

    @tool
    def chamar_financeiro(pergunta: str) -> str:
        """Chame para cálculos e CEPs."""
        return agente_financeiro.run(pergunta)

    supervisor = Agent(
        name="Supervisor",
        instructions="Você é um gerente. SEMPRE que o usuário perguntar sobre horas, cálculos, CEP, clima ou arquivos, você DEVE chamar a ferramenta do especialista correspondente. NUNCA tente responder sozinho sem usar as ferramentas. Não use markdown (**).",
        tools=[chamar_clima, chamar_arquivos, chamar_financeiro],
        llm=llm_config,
    )
    return supervisor

supervisor = carregar_agentes()

# ==========================================
# 3. INTERFACE DO STREAMLIT
# ==========================================
st.set_page_config(page_title="Agente IA", page_icon="🤖")
st.title("🤖 Assitente em Desenvolvimento")
st.markdown("Converse com o seu agente multiagente em tempo real.")

# Inicializa o histórico de mensagens na sessão
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

# Mostra as mensagens antigas
for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Caixa de texto para o usuário digitar
if prompt := st.chat_input("Como posso ajudar?"):
    # 1. Adiciona a mensagem do usuário na tela
    st.session_state.mensagens.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Chama o agente e mostra o "Pensando..."
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            resposta = supervisor.run(prompt)
            resposta_limpa = resposta.replace("**", "")
            st.markdown(resposta_limpa)
            
    # 3. Salva a resposta no histórico
    st.session_state.mensagens.append({"role": "assistant", "content": resposta_limpa})