from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, NoSuchElementException
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
    campo_monto_prestamo = driver.find_element(By.XPATH, xpath)
    campo_monto_prestamo.clear()
