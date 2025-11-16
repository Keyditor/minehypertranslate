import json
import random
import time
from googletrans import Translator, LANGUAGES
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Caminho do arquivo de idioma
ARQUIVO_JSON = "pt_br.json"
ARQUIVO_SAIDA_JSON = "hp_pt.json"
NUM_IDIOMAS = 50
NUM_THREADS = 8

def carregar_json(caminho_json):
    """Carrega o arquivo JSON e retorna um dicionário."""
    with open(caminho_json, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_json(dados, caminho_json):
    """Salva o dicionário em um arquivo JSON."""
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

def hiper_traduzir(texto, idiomas_alvo):
    """
    Traduz o texto sequencialmente por uma lista de idiomas e retorna ao português.
    """
    texto_traduzido = texto
    tradutor = Translator() # Cria uma nova instância para cada thread
    idioma_atual = 'pt'
    for codigo_idioma in idiomas_alvo:
        try:
            traducao = tradutor.translate(texto_traduzido, src=idioma_atual, dest=codigo_idioma)
            texto_traduzido = traducao.text
            idioma_atual = codigo_idioma
            time.sleep(0.2) # Pequena pausa para evitar sobrecarregar a API
        except Exception as e:
            print(f"Erro ao traduzir para {LANGUAGES.get(codigo_idioma, codigo_idioma)}: {e}. Pulando este idioma.")
            continue

    # Traduz de volta para o português
    try:
        traducao_final = tradutor.translate(texto_traduzido, src=idioma_atual, dest='pt')
        return traducao_final.text
    except Exception as e:
        print(f"Erro ao traduzir de volta para 'pt': {e}. Retornando o texto original.")
        return texto

def worker_traducao(item, idiomas_selecionados):
    """
    Função de trabalho para uma thread. Traduz um único item do JSON.
    """
    chave, valor = item
    if isinstance(valor, str) and valor.strip() != "":
        valor_traduzido = hiper_traduzir(valor, idiomas_selecionados)
        return chave, valor_traduzido
    else:
        # Mantém valores que não são strings ou estão vazios
        return chave, valor

if __name__ == "__main__":
    dados_originais = carregar_json(ARQUIVO_JSON)
    dados_traduzidos = {}

    # Obtém todos os códigos de idioma disponíveis, exceto português
    codigos_idiomas = [lang for lang in LANGUAGES.keys() if lang != 'pt']

    if len(codigos_idiomas) < NUM_IDIOMAS:
        raise ValueError(f"Não há idiomas suficientes para a tradução em cadeia. Pedido: {NUM_IDIOMAS}, Disponível: {len(codigos_idiomas)}")

    # Seleciona 50 idiomas aleatoriamente
    idiomas_selecionados = random.sample(codigos_idiomas, NUM_IDIOMAS)

    print(f"Iniciando a hiper-tradução através de {NUM_IDIOMAS} idiomas usando {NUM_THREADS} threads...")
    print("Atenção: Este processo pode ser demorado e depende da conexão com a internet.")

    # Usa ThreadPoolExecutor para traduzir em paralelo
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        # Submete cada tarefa de tradução para o executor
        futures = {executor.submit(worker_traducao, item, idiomas_selecionados): item for item in dados_originais.items()}

        # Itera sobre os resultados conforme eles são concluídos, com uma barra de progresso
        for future in tqdm(as_completed(futures), total=len(dados_originais), desc="Traduzindo"):
            try:
                chave, valor_traduzido = future.result()
                dados_traduzidos[chave] = valor_traduzido
            except Exception as e:
                chave_original, _ = futures[future]
                print(f"\nOcorreu um erro ao processar a chave '{chave_original}': {e}")
                dados_traduzidos[chave_original] = dados_originais[chave_original] # Mantém o original em caso de erro
    # Salvar o resultado em um novo arquivo JSON
    salvar_json(dados_traduzidos, ARQUIVO_SAIDA_JSON)

    print("\nTradução concluída!")
    print(f"Arquivo JSON gerado: {ARQUIVO_SAIDA_JSON}")
