from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json
import traceback

# ---------- Config ----------
options = Options()
options.add_argument("--disable-extensions")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
# options.add_argument("--headless")  # descomente se quiser sem UI (útil em servidor)
navegador = webdriver.Chrome(options=options)
navegador.maximize_window()
wait = WebDriverWait(navegador, 20)

# ---------- Credenciais ----------
nome = ""      # substitua se desejar automatizar login
senha = "" # substitua se desejar automatizar login

# ---------- Helpers ----------
def salvar_checkpoint(dados, path="instagram_checkpoint.json"):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Erro ao salvar checkpoint:", e)

def extrair_username_de_href(href):
    if not href:
        return None
    href = href.split("?")[0].rstrip("/")
    parts = href.split("/")
    if len(parts) >= 4 and "instagram.com" in href:
        username = parts[-1]
        # ignorar caminhos que não são perfis
        if username in ("explore", "p", "tags", "developer", "about", ""):
            return None
        return username
    return None

# ---------- Login ----------
try:
    navegador.get("https://www.instagram.com/")
    user_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
    pass_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))

    user_input.clear()
    user_input.send_keys(nome)
    pass_input.clear()
    pass_input.send_keys(senha)
    pass_input.send_keys(Keys.ENTER)

    # espera o perfil aparecer e clica
    perfil = wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[contains(@href, '/{nome}')]")))
    perfil.click()
    time.sleep(2)
except Exception:
    print("Erro no login/abrir perfil:")
    traceback.print_exc()
    navegador.quit()
    raise

# ---------- Função de coleta ----------
def pegar_lista_portugues(tipo_pt, max_iters=2000, sleep_between_scrolls=1.2):
    """
    tipo_pt: 'seguidores' ou 'seguindo'
    Retorna lista de usernames (strings). Imprime progresso no terminal.
    """
    mapa = {"seguidores": "followers", "seguindo": "following"}
    if tipo_pt not in mapa:
        raise ValueError("tipo_pt deve ser 'seguidores' ou 'seguindo'")

    fragment = mapa[tipo_pt]
    print(f"\n=== Coletando {tipo_pt} ({fragment}) ===")

    # abre o diálogo
    try:
        link_xpath = f"//a[contains(@href, '/{fragment}')]"
        link = wait.until(EC.element_to_be_clickable((By.XPATH, link_xpath)))
        link.click()
    except Exception:
        print("Não foi possível clicar no link", fragment)
        traceback.print_exc()
        return []

    # espera o diálogo
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']")))
    except:
        print("Diálogo não apareceu.")
        return []

    # tenta localizar a caixa rolável dentro do dialog
    caixa_xpaths = [
        "//div[@role='dialog']//div[contains(@class,'isgrP')]",                # instagram comum
        "//div[@role='dialog']//div[contains(@style,'overflow')]",             # fallback por style
        "//div[@role='dialog']//ul",                                           # outra opção
        "//div[@role='dialog']//div[.//a]"                                     # última tentativa: div que contenha links
    ]

    caixa = None
    for xp in caixa_xpaths:
        try:
            caixa = wait.until(EC.presence_of_element_located((By.XPATH, xp)))
            # se achar caixa, quebra
            break
        except:
            pass

    if caixa is None:
        print("Não encontrou a caixa rolável; abortando coleta desse tipo.")
        return []

    vistos = set()
    usuarios = []
    ultimo_tamanho = -1
    stable_count = 0

    try:
        for it in range(max_iters):
            # re-obter caixa para evitar stale
            found = False
            for xp in caixa_xpaths:
                try:
                    caixa = navegador.find_element(By.XPATH, xp)
                    found = True
                    break
                except:
                    continue
            if not found:
                # fallback: dialog
                caixa = navegador.find_element(By.XPATH, "//div[@role='dialog']")

            # scroll na caixa
            try:
                navegador.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", caixa)
            except Exception:
                # fallback para window scroll
                navegador.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            time.sleep(sleep_between_scrolls)

            # coleta anchors atuais dentro da caixa
            try:
                anchors = caixa.find_elements(By.TAG_NAME, "a")
            except Exception:
                anchors = []

            novos = 0
            for a in anchors:
                try:
                    href = a.get_attribute("href")
                except Exception:
                    href = None
                username = extrair_username_de_href(href)
                if username and username not in vistos:
                    vistos.add(username)
                    usuarios.append(username)
                    novos += 1

            print(f"[{tipo_pt}] iter {it+1}: encontrados no total = {len(usuarios)} (novos nesta iteração = {novos})")

            # verificação de estabilidade: se não entrou nenhum novo por N iterações, assume fim
            if novos == 0:
                stable_count += 1
            else:
                stable_count = 0

            if stable_count >= 4:
                print(f"[{tipo_pt}] sem novos usuários por {stable_count} iterações — considerando fim.")
                break

            # proteção extra: se o número parou de crescer e altura não muda
            try:
                altura = navegador.execute_script("return arguments[0].scrollHeight", caixa)
            except Exception:
                altura = None

            if altura == ultimo_tamanho:
                # conta como uma estabilidade extra
                pass
            ultimo_tamanho = altura

        # fim loop
    except Exception:
        print(f"Erro durante scroll/extração de {tipo_pt}:")
        traceback.print_exc()

    # tenta fechar o diálogo
    try:
        fechar_btn = navegador.find_element(By.XPATH, "//div[@role='dialog']//button")
        fechar_btn.click()
    except Exception:
        try:
            navegador.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except:
            pass

    time.sleep(1)
    return usuarios

# ---------- Execução principal com salvamento seguro ----------
dados = {"Seguidores": [], "Seguindo": []}
try:
    seguidores = pegar_lista_portugues("seguidores")
    dados["Seguidores"] = seguidores
    # salva checkpoint assim que terminar seguidores
    salvar_checkpoint(dados)

    seguindo = pegar_lista_portugues("seguindo")
    dados["Seguindo"] = seguindo
    salvar_checkpoint(dados)

    # salva final
    with open("instagram.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

    # imprime resultados no terminal (um por linha)
    print("\n=== Seguidores (total {}) ===".format(len(dados["Seguidores"])))
    for u in dados["Seguidores"]:
        print(u)

    print("\n=== Seguindo (total {}) ===".format(len(dados["Seguindo"])))
    for u in dados["Seguindo"]:
        print(u)

    print("\nDados salvos em: instagram.json (e checkpoint em instagram_checkpoint.json)")
except Exception:
    print("Erro inesperado na execução principal:")
    traceback.print_exc()
    # tenta salvar o que coletou até agora
    salvar_checkpoint(dados)
finally:
    try:
        navegador.quit()
    except:
        pass
