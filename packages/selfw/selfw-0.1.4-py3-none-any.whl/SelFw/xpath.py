from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

def existe(xpath, driver):
    return driver.find_element(By.XPATH, f'{xpath}')

def click(xpath, driver):
    element = driver.find_element(By.XPATH, f'{xpath}')
    element.click()

def send_keys(xpath, valor, driver):
    elemento = driver.find_element(By.XPATH, f'{xpath}')
    elemento.send_keys(valor)

def clear(xpath, driver):
    campo_monto_prestamo = driver.find_element(By.XPATH, xpath)
    campo_monto_prestamo.clear()

def get_text(xpath, driver):
    elemento = driver.find_element(By.XPATH, xpath)
    return elemento.text