from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import JavascriptException, TimeoutException, ElementNotInteractableException, NoSuchElementException
import time


def existe(xpath, driver, timeout=10):
    """Verifica si el elemento existe y es visible"""
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
        return True
    except TimeoutException:
        return False


def click(xpath, driver, timeout=10):
    """Hace click cuando el elemento es clickeable"""
    try:
        elem = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
        elem.click()
        return True
    except (TimeoutException, ElementNotInteractableException) as e:
        # fallback al click JS
        try:
            elem = driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].click();", elem)
            return True
        except Exception as e2:
            print(f"[click] Error en {xpath}: {e2}")
            return False


def send_keys(xpath, valor, driver, timeout=10):
    """Envía texto a un campo visible y habilitado"""
    try:
        elem = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
        elem.clear()
        elem.send_keys(valor)
        return True
    except (TimeoutException, ElementNotInteractableException):
        # fallback con JavaScript
        try:
            elem = driver.find_element(By.XPATH, xpath)
            driver.execute_script("""
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('input', {bubbles:true}));
                arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
            """, elem, valor)
            return True
        except Exception as e2:
            print(f"[send_keys] Error en {xpath}: {e2}")
            return False


def select(xpath, buscar, driver, attr="value", timeout=10):
    """Selecciona una opción de un <select>"""
    try:
        select_element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_element)
        sel = Select(select_element)
        buscar = str(buscar)
        if attr == "value":
            sel.select_by_value(buscar)
        elif attr == "text":
            sel.select_by_visible_text(buscar)
        else:
            for option in sel.options:
                if option.get_attribute(attr) == buscar:
                    option.click()
                    break
            else:
                raise ValueError(f"No se encontró opción con {attr}='{buscar}'")
        return True
    except Exception as e:
        print(f"[select] Error en {xpath}: {e}")
        return False


def clear(xpath, driver):
    campo = driver.find_element(By.XPATH, xpath)
    campo.clear()

def quitar_disable(xpath, driver, timeout=10):
    """
    Elimina atributos que impiden la edición de un elemento localizado por XPath.
    Intenta quitar 'readonly' y 'disabled' y además fuerza element.readOnly = false.

    :param xpath: XPath del elemento (ejemplo: "//input[@id='fecha']")
    :param driver: instancia activa de Selenium WebDriver
    :param timeout: segundos a esperar por el elemento (default 10)
    :return: True si se realizó algún cambio, False si no se encontró/el cambio falló
    """
    try:
        # Espera a que el elemento esté presente
        elemento = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )

        # Ejecuta JS para quitar ambos atributos y forzar readOnly = false
        js = (
            "if (arguments[0]) {"
            "  arguments[0].removeAttribute('readonly');"
            "  arguments[0].removeAttribute('disabled');"
            "  try { arguments[0].readOnly = false; } catch(e) {};"
            "  return true;"
            "}"
            "return false;"
        )
        result = driver.execute_script(js, elemento)
        time.sleep(1)
        elemento.click()
        return bool(result)

    except TimeoutException:
        print(f"[Advertencia] No se encontró el elemento con XPath (timeout {timeout}s): {xpath}")
        return False
    except NoSuchElementException:
        print(f"[Advertencia] No se encontró el elemento con XPath: {xpath}")
        return False
    except JavascriptException as e:
        print(f"[Error] Error al ejecutar JS para eliminar atributos: {e}")
        return False
    except Exception as e:
        # captura cualquier otra excepción inesperada
        print(f"[Error inesperado] {e}")
        return False
    

def agregar_clase_valid(driver, xpath=None, xpaths=None, timeout=10):
    """
    Añade la clase 'valid' a uno o varios elementos localizados por XPath sin eliminar otras clases.

    :param driver: instancia activa de Selenium WebDriver
    :param xpath: XPath de un solo elemento (string)
    :param xpaths: lista opcional de XPaths para varios elementos
    :param timeout: segundos a esperar por cada elemento (default 10)
    :return: número de elementos modificados con éxito
    """
    # Normalizar la lista de XPaths
    if xpaths is None:
        if xpath is None:
            raise ValueError("Debe especificarse 'xpath' o 'xpaths'.")
        xpaths = [xpath]

    modificados = 0
    js = "if (arguments[0]) { arguments[0].classList.add('valid'); return true; } return false;"

    for xp in xpaths:
        try:
            elemento = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xp))
            )
            result = driver.execute_script(js, elemento)
            if result:
                modificados += 1
        except TimeoutException:
            print(f"[Advertencia] No se encontró el elemento con XPath (timeout {timeout}s): {xp}")
        except JavascriptException as e:
            print(f"[Error JS en {xp}] {e}")
        except Exception as e:
            print(f"[Error inesperado en {xp}] {e}")

    return modificados
