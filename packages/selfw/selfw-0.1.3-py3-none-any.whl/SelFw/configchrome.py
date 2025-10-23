from seleniumwire import webdriver
from selenium import webdriver as selenium_normal
from selenium.webdriver.chrome.options import Options
import os

def iniciar_chrome(modo="normal", extension_path=None, proxy=None, headless=False, usar_seleniumwire=True):
    """
    Inicia una sesión de Chrome flexible.
    
    :param modo: 'normal', 'extension' o 'limpio'
    :param extension_path: ruta a la extensión .crx (solo si modo='extension')
    :param proxy: dict con proxies o cadena (ej: 'usuario:clave@host:puerto')
    :param headless: bool para ejecutar sin interfaz visible
    :param usar_seleniumwire: bool para usar seleniumwire o webdriver normal
    :return: instancia de driver lista para usar
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

    # Modo extensión
    if modo == "extension" and extension_path:
        if not os.path.exists(extension_path):
            raise FileNotFoundError(f"No se encontró la extensión en: {extension_path}")
        chrome_options.add_argument(f"--load-extension={os.path.abspath(extension_path)}")

    # Modo limpio
    elif modo == "limpio":
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--disable-extensions")

    # Configurar proxy si existe
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

    # Crear el driver
    if usar_seleniumwire:
        driver = webdriver.Chrome(options=chrome_options, seleniumwire_options=seleniumwire_options)
    else:
        driver = selenium_normal.Chrome(options=chrome_options)

    return driver