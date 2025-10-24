from seleniumwire import webdriver
from selenium import webdriver as selenium_normal
from selenium.webdriver.chrome.options import Options
import os
import tempfile

def iniciar_chrome(
    modo="normal",
    proxy=None,
    headless=False,
    usar_seleniumwire=True,
    perfil=None
):
    """
    Inicia una sesión de Chrome flexible con soporte para perfiles, headless y proxy.

    :param modo: 'normal', 'extension' o 'limpio'
    :param proxy: dict o str con proxy (ej: 'usuario:clave@host:puerto')
    :param headless: bool para ejecutar sin interfaz visible
    :param usar_seleniumwire: bool para usar seleniumwire o webdriver normal
    :param perfil: ruta al perfil de Chrome (solo si modo='extension')
    :return: driver listo para usar
    """

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_argument("--remote-debugging-port=0")
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    )

    if headless:
        chrome_options.add_argument("--headless=new")

    # --- MODO EXTENSION ---
    if modo == "extension":
        perfil_path = perfil or r"C:\SeleniumProfile"
        if not os.path.exists(perfil_path):
            os.makedirs(perfil_path, exist_ok=True)
        chrome_options.add_argument(fr"user-data-dir={os.path.abspath(perfil_path)}")

    # --- MODO LIMPIO ---
    elif modo == "limpio":
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--disable-extensions")

    # --- CONFIGURAR PROXY ---
    seleniumwire_options = {}
    if proxy:
        if isinstance(proxy, str):
            proxy = {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}",
                "no_proxy": "localhost,127.0.0.1"
            }
        seleniumwire_options["proxy"] = proxy
        seleniumwire_options["verify_ssl"] = False

    # --- CREAR DRIVER ---
    if usar_seleniumwire:
        driver = webdriver.Chrome(options=chrome_options, seleniumwire_options=seleniumwire_options)
    else:
        driver = selenium_normal.Chrome(options=chrome_options)

    return driver
