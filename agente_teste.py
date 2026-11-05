import os
import requests
from dotenv import load_dotenv
from agentmold import Agent, tool
import datetime

load_dotenv()
os.environ["OPENAI_BASE_URL"] = "https://api.groq.com/openai/v1"

# ==========================================
# 1. FERRAMENTAS BÁSICAS (As "mãos" dos agentes)
# ==========================================
@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
# 2. CRIAÇÃO DOS AGENTES ESPECIALISTAS
# ==========================================
llm_config = {"provider": "openai", "model": "openai/gpt-oss-20b"}

agente_clima = Agent(
    name="Especialista em Clima",
    instructions="Você é um meteorologista. Use a ferramenta get_weather para responder. Seja direto.",
    tools=[get_weather],
    llm=llm_config,
)

agente_arquivos = Agent(
    name="Especialista em Arquivos",
    instructions="Você gerencia arquivos de texto. Use read_file e write_to_file. Seja direto.",
    tools=[read_file, write_to_file],
    llm=llm_config,
)

agente_financeiro = Agent(
    name="Especialista Financeiro",
    instructions="Você faz cálculos, busca CEPs e verifica horas. Use calculate, search_cep e get_current_time. Seja direto.",
    tools=[calculate, search_cep, get_current_time],
    llm=llm_config,
)

# ==========================================
# 3. TRANSFORMANDO AGENTES EM FERRAMENTAS
# ==========================================
# Aqui está o segredo do multiagente: criamos ferramentas que chamam os agentes menores.
@tool
def chamar_especialista_clima(pergunta: str) -> str:
    """Chame esta ferramenta se o usuário perguntar sobre o clima ou temperatura de alguma cidade."""
    return agente_clima.run(pergunta)

@tool
def chamar_especialista_arquivos(pergunta: str) -> str:
    """Chame esta ferramenta se o usuário pedir para ler, criar ou salvar arquivos de texto."""
    return agente_arquivos.run(pergunta)

@tool
def chamar_especialista_financeiro(pergunta: str) -> str:
    """Chame esta ferramenta para cálculos matemáticos, consultas de CEP ou para saber as horas."""
    return agente_financeiro.run(pergunta)

# ==========================================
# 4. O AGENTE SUPERVISOR (O Chefe)
# ==========================================
supervisor = Agent(
    name="Supervisor",
    instructions=(
        "Você é um gerente de equipe. Você não faz o trabalho braçal. "
        "Seu único trabalho é analisar o pedido do usuário e decidir qual dos seus especialistas chamar. "
        "Você tem especialistas em Clima, Arquivos e Finanças/CEPs. "
        "Chame a ferramenta correta com a pergunta do usuário. "
        "Se o especialista responder, repasse a resposta para o usuário de forma educada. "
        "Não use formatação markdown (como **)."
    ),
    tools=[chamar_especialista_clima, chamar_especialista_arquivos, chamar_especialista_financeiro],
    llm=llm_config,
)

# ==========================================
# 5. O CHAT (Agora conversa com o Supervisor)
# ==========================================
print("👔 Agente Supervisor iniciado! (Digite 'sair' para encerrar)\n")

while True:
    try:
        pergunta = input("👤 Você: ")
        if pergunta.lower().strip() in ['sair', 'exit', 'quit']:
            print("👔 Até logo!")
            break
        if not pergunta.strip(): continue

        print("👔 Supervisor Pensando...")
        resposta = supervisor.run(pergunta)
        
        print(f"👔 Supervisor: {resposta.replace('**', '')}\n")

    except KeyboardInterrupt:
        print("\n👔 Até logo!")
        break
    except Exception as e:
        print(f"\n❌ Ocorreu um erro: {e}\n")