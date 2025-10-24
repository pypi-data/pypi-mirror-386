from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from typing import Optional
from threading import Thread
import time
import os

def invoke_api_list(link: str, token: str, method: Optional[str] = "GET", headers: Optional[str] = None, print_response: Optional[bool] = False) -> dict:
    import requests

    """
    Exemplo de uso abaixo:

        import BCFOX as bc

        def invoke_api_list(self):
            link = 'https://linK_api.com.br/apis/{parametros}'
            token = 12345ABCDE12345ABCDE12345ABCDE12345ABCDE12345

            bc.invoke_api_list(link, token, print_response=True)

        OBS: o print_response vem por padrão desligado, caso você queira ativa o print da view coloque 'ON'

        """
    http_methods = {
        "POST": requests.post,
        "GET": requests.get,
        "PUT": requests.put,
        "DELETE": requests.delete,
        "PATCH": requests.patch
    }

    # Verifica se o método fornecido é válido
    method = method.upper()
    if method not in http_methods:
        raise ValueError(f"Método HTTP inválido. Use um dos seguintes: {', '.join(http_methods.keys())}.")

    payload = {}
    if headers is None: headers = {"x-access-token": token}
    else: {headers: token}

    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        from .get_driver import RD, RESET
        try:

            # Realiza a requisição com o método correto
            if method == "GET" or method == "DELETE": response_insert = http_methods[method](link, params=payload, headers=headers)
            else: response_insert = http_methods[method](link, json=payload, headers=headers)
            if "Sequelize" in response_insert.json(): raise SystemError(f" {RD}>>> {response_insert.json()}{RESET}")

            if print_response == True:
                print(f"\n{response_insert.json()}")

            return response_insert.json()

        except Exception as e:
            print(f"Tentativa {attempt} falhou: {e}")

            if attempt < max_attempts:
                print("Tentando novamente em 5 segundos...")
                time.sleep(5)
                continue

            else: raise ValueError("Api list falhou")

def invoke_api_proc(link: str, payload_vars: dict, token: str, method: str, print_response: Optional[bool | str] = False) -> str:
    import requests

    """
    Exemplo de uso abaixo:

    import BCFOX as bc

    def invoke_api_proc_final(self):
        link = https://linK_api.com.br/apis/{parametros}
        token = 12345ABCDE12345ABCDE12345ABCDE12345ABCDE12345

        payload = [
        {"ID":self.id},
        {"STATUS":self.status},
        {"PAGAMENTO":self.pagamento}
        ...
        ]

        bc.invoke_api_proc_final(link, payload, token, print_response=True)

    OBS: o print_response vem por padrão desligado, caso você queria ver o returno do response coloque 'ON'
    OBS2: Caso queria printar o json response intero coloque: 'print_response = "full"'

    """

    if isinstance(print_response, str):
        if print_response.lower().strip() ==  "full":
            print_response = "full"

        else:
            raise ValueError("print_response com variável inválida\n Use tipo 'bool' ou escreva 'full' (str) para response completo")

    http_methods = {
        "POST": requests.post,
        "GET": requests.get,
        "PUT": requests.put,
        "DELETE": requests.delete,
        "PATCH": requests.patch,
    }

    # Verifica se o método fornecido é válido
    method = method.upper()
    if method not in http_methods:
        raise ValueError(f"Método HTTP inválido. Use um dos seguintes: {', '.join(http_methods.keys())}.")

    # PROC PARA FINALIZAR PROCESSO
    url = link

    payload = payload_vars

    if print_response == True or print_response == "full":
        print(f'payload: {payload}')

    headers = {"x-access-token": token}

    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            # Realiza a requisição com o método correto
            if method == "GET" or method == "DELETE": response_insert = http_methods[method](url, params=payload, headers=headers)
            else: response_insert = http_methods[method](url, json=payload, headers=headers)

            response_insert.raise_for_status()

            if print_response == True or print_response == "full":
                print(response_insert.json())

            if print_response == "full":
                return response_insert.json()

            status = response_insert.json()[0]['STATUS']
            return status

        except Exception as e:
            print(f"Tentativa {attempt} falhou: {e}")

            if attempt < max_attempts:
                print("Tentando novamente em 5 segundos...")
                time.sleep(5)
                continue

            else: raise ValueError("Api proc final falhou")

def invoke_api_proc_log(link, id_robo, token):
    import requests

    """Só colocar o ID do robo e o Token direto """

    payload = {
        "id": id_robo
    }

    print(payload)

    headers = {
        "x-access-token": token}

    responseinsert = requests.request(
        "POST", link, json=payload, headers=headers)
    print(f"\n{responseinsert.json()}")

def login_2fac(driver, certificate, system, token, code_timeout=10):
    import requests
    import pyautogui
    from . import mostrar_mensagem

    class login_2fac:
        def __init__(self):
            self.certificate = certificate
            self.system = system
            self.token = token
            self.code_timeout = code_timeout
            self.driver = driver

    class Pop_up_protection(login_2fac):
        def __init__(self):
            super().__init__()
            self.status = False

        def __monitor(self):
            while self.status:

                handles = self.driver.window_handles
                if len(handles) > 1:
                    self.driver.switch_to.window(self.driver.window_handles[-1])

                try:
                    alert = self.driver.switch_to.alert
                    alert.accept()
                except:
                    pass

                time.sleep(0.1)

        def start(self):
            self.status = True
            protection = Thread(target=self.__monitor, daemon=True)
            protection.start()

        def stop(self):
            self.status = False

    class tool(login_2fac):
        def find_element_with_wait(self, by, value, timeout=10):
            global driver
            return WebDriverWait(
                self.driver, timeout).until(
                EC.presence_of_element_located(
                    (by, value)))

        def find_elements_with_wait(self, by, value, timeout=10):
            return WebDriverWait(
                self.driver, timeout).until(
                EC.presence_of_all_elements_located(
                    (by, value)))

    class invokes_whoom(login_2fac):
        def __init__(self):
            super().__init__()

            self.list_codes = []

        def invoke_get_codes(self):

            url = "https://api-4.bcfox.com.br/bcjur/views/codigo-validacao"
            headers = {"x-access-token": self.token}

            max_attempts = 5
            for attempt in range(1, max_attempts + 1):
                try:
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()  # Lança uma exceção se a resposta não for bem-sucedida

                    self.list_codes = response.json()
                    # print(self.list_codes)
                    return self.list_codes

                except Exception as e:
                    print(f'Tentativa {attempt} falhou: {e}')

                    if attempt < max_attempts:
                        print('Tentando novamente em 5 segundos...')
                        time.sleep(5)
                        continue
                    else:
                            raise('Todas as tentativas falharam!')

        def invoke_update_status(self, id):

            url = f"https://api-4.bcfox.com.br/bcjur/views/codigo-validacao/{id}"
            headers = {"x-access-token": self.token}

            max_attempts = 5
            for attempt in range(1, max_attempts + 1):
                try:
                    responseinsert = requests.put(url, headers=headers)
                    responseinsert.raise_for_status()  # Lança uma exceção se a resposta não for bem-sucedida

                    print(responseinsert)
                    return responseinsert

                except Exception as e:
                    print(f'Tentativa {attempt} falhou: {e}')

                    if attempt < max_attempts:
                        print('Tentando novamente em 5 segundos...')
                        time.sleep(5)
                        continue
                    else:
                        raise('Todas as tentativas falharam!')

    class whoom_codes(login_2fac):
        def __init__(self):
            super().__init__()

        def extension_check(self):

            self.driver.get('chrome-extension://lnidijeaekolpfeckelhkomndglcglhh/index.html')
            time.sleep(3)

            for _ in range(10):

                # Caso a extensão já esteja instalada
                try:
                    tools.find_element_with_wait(By.XPATH, '//input[@placeholder="Digite ou selecione um sistema pra acessar"]', timeout=1)
                    return
                except: pass

                try:
                    tools.find_element_with_wait(By.XPATH, '//input[@placeholder="Insira aqui o seu email"]', timeout=1)
                    return
                except: pass

                # Caso a extensão não esteja instala
                if 'This page has been blocked by Chrome' in driver.page_source:
                    break

                if 'eliezer@bcfox.com.br' in self.driver.page_source:
                    tools.find_element_with_wait(By.XPATH, "//span[text()='alterar']").click()
                    return

            # Abrir uma nova aba
            self.driver.execute_script("window.open('');")

            # Fechar a aba original
            self.driver.close()

            # Mudar para a nova aba
            self.driver.switch_to.window(self.driver.window_handles[-1])

            time.sleep(1)

            self.driver.get("https://chromewebstore.google.com/detail/whom-gerenciador-de-certi/lnidijeaekolpfeckelhkomndglcglhh")

            tools.find_element_with_wait(By.XPATH, "//span[contains(text(), 'no Chrome') or contains(text(), 'Usar') or contains(text(), 'Add to Chrome')]").click()
            time.sleep(5)

            # Envia TAB e ENTER do teclado físico
            pyautogui.press('tab')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(5)

            self.driver.get('chrome-extension://lnidijeaekolpfeckelhkomndglcglhh/index.html')

        def codes_2_fac(self):
            element_sistema = '//input[(contains(@placeholder,"selecione um sistema pra acessar") or contains(@name, "system")) and contains(@role, "combobox")]'
            element_email = '//input[contains(@placeholder,"Insira aqui o seu email") or contains(@placeholder,"e-mail")]'
            email = 'eliezer@bcfox.com.br'
            element_code = '//input[contains(@placeholder,"Digite aqui o código que enviamos para o seu e-mail") or contains(@placeholder,"código") or contains(@type,"password")]'
            element_submit ='//button[contains(@type, "submit")]'
            try:
                tools.find_element_with_wait(By.XPATH, f'{element_sistema}', timeout=2).send_keys(self.system)
                code_insertion = True

            except:
                self.driver.get('chrome-extension://lnidijeaekolpfeckelhkomndglcglhh/index.html')

                # Request the code
                for _ in range(50):  # Wait the extension to load
                    time.sleep(1)
                    try:
                        tools.find_element_with_wait(By.XPATH, f'{element_email}', timeout=1).send_keys(f'{email}')
                        time.sleep(1)
                        break
                    except:
                        self.driver.get('chrome-extension://lnidijeaekolpfeckelhkomndglcglhh/index.html')

                # Envia o código pro email, o for é só para tratativa de bugs
                for _ in range(10):
                    try:
                        tools.find_element_with_wait(By.XPATH, f'{element_code}', timeout=1)
                        break

                    except:
                        try:
                            element = tools.find_element_with_wait(By.XPATH, f'{element_email}', timeout=1)
                            element.clear()
                            element.send_keys(f'{email}')
                            tools.find_element_with_wait(By.XPATH, f'{element_submit}').click()
                            time.sleep(1)
                        except:
                            break

                # Attempts the new codes until success or requests limit
                for _ in range(code_timeout):
                    def adicionar_code():
                        responses = api.invoke_get_codes()
                        if not responses:
                            time.sleep(2)
                            return [], None
                        # Try new codes
                        code_insertion = False
                        for response in responses:
                            time.sleep(1)

                            if 'Escolha um certificado' in self.driver.page_source:
                                break

                            CODE = response['CODIGO']
                            ID = response['ID']

                            element = tools.find_element_with_wait(By.XPATH, '//input[@type="password"]')
                            element.clear()
                            element.send_keys(CODE)
                            button_entrar_click = False
                            for _ in range(20):
                                try:
                                    button = tools.find_element_with_wait(By.XPATH, f'{element_submit}', timeout=2)
                                    if button.get_attribute('disabled'):
                                        time.sleep(1.5)
                                        continue
                                    button.click()
                                    button_entrar_click = True
                                    if 'Escolha um certificado' in self.driver.page_source:
                                        break

                                    time.sleep(1)
                                except:
                                    break

                                if int(_) == 20 and button_entrar_click == False:
                                    raise TimeoutError('Código Whom falhou ao entrar')

                            return responses, ID

                    responses, ID = adicionar_code()

                    if 'Sair' in self.driver.page_source and not 'Verifique seu e-mail' in self.driver.page_source:
                        api.invoke_update_status(ID)  # FIX: Update
                        break

                    if 'Verifique seu e-mail':
                        responses,ID = adicionar_code()

                    for _ in range(60):
                        if not(responses):
                            responses,ID  = adicionar_code()
                            time.sleep(1)
                        else:
                            break

                    if not (responses):
                        raise TimeoutError('Código WHOOM não chegou dentro do timeout estabelecido')
                        # Wrong

                    try:
                        tools.find_element_with_wait(By.XPATH, "//span[contains(text(), 'Senha inválida')]",
                                                     timeout=1)
                        tools.find_element_with_wait(By.XPATH, "//button[text()='Voltar']", timeout=1).click()
                        code_insertion = False
                        break

                    except:
                        pass

                    if 'Sair' in self.driver.page_source and not 'Verifique seu e-mail' in self.driver.page_source:
                        api.invoke_update_status(ID)  # FIX: Update
                        break

                code_insertion = False
                # Check the code result
                for _ in range(30):
                    if code_insertion:
                        break
                    # Correct
                    try:
                        tools.find_element_with_wait(By.XPATH,"//input[(contains(@name,'certificate') or contains(@placeholder,'certificado')) and not(contains(@type, 'hidden'))]", timeout=1).send_keys(self.certificate)
                        list_certific = tools.find_elements_with_wait(By.XPATH,'//div[contains(@role,"option")]')
                        list_certific[0].click()
                        time.sleep(1)
                        code_insertion = True
                        break
                    except:
                        pass

                time.sleep(4)
                code_insertion = False
                for _ in range(30):
                    try:
                        # input('\n\n > Selecione o sistema e aperte alguma tecla.')
                        tools.find_element_with_wait(By.XPATH, f'{element_sistema}', timeout=1).send_keys(self.system)
                        time.sleep(1)
                        list_sistemas = tools.find_elements_with_wait(By.XPATH, '//div[contains(@role,"option")]')
                        if len(list_sistemas) == 1:
                            list_sistemas[0].click()
                            code_insertion = True
                            break
                        else:
                            mostrar_mensagem(
                                'Mais de um sistema encontrado, verifique o nome do sistema no WHOOM e coloque um nome único na função')
                            raise ValueError('Mais de um sistema encontrado, verifique o nome')
                    except:
                        pass

                    if code_insertion:
                        break

            if code_insertion:
                tools.find_element_with_wait(By.XPATH, f"//button[contains(@data-testid,'submit') or contains(text(), 'Acessar')]").click()
                print('Logado')
            else:
                raise TimeoutError('Código WHOOM não chegou dentro do timeout estabelecido')

            time.sleep(2)
            self.driver.switch_to.window(self.driver.window_handles[-1])
            attempt = 0
            while 'whoom' in self.driver.title.strip().lower() and attempt <= 180:
                if 'Sistema temporariamente indisponível. Tente novamente mais tarde.' in self.driver.page_source:
                    raise SystemError('Sistema indisponivel no momento.')
                time.sleep(1)
                attempt += 1
            time.sleep(5)

            if attempt >= 180:
                mostrar_mensagem('Whoom congelou no conectar com site.')
                raise SystemError('Whoom congelou no conectar com site.')

            protection.stop()
            if len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[0])
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[-1])

    # Instances
    tools = tool()
    api = invokes_whoom()
    protection = Pop_up_protection()
    bot = whoom_codes()

    # Operacional
    bot.extension_check()
    protection.start()
    bot.codes_2_fac()