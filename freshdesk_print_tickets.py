from selenium import webdriver
import time
import base64
import os

# ==============================
# CONFIG
# ==============================
START_ID = 1
END_ID = 100
OUTPUT_DIR = "tickets_pdf"
DELAY = 1.5
ID_TENANT = "<<ingresar tu id de tenant"
CLIENT= "<<ingresar tu subdomain>>"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# ==============================
# FUNCIONES
# ==============================

def ticket_existe(driver):
    return "doesn't exist" not in driver.page_source.lower()

def esperar_render(driver, timeout=10):
    """Espera que el DOM esté completamente cargado"""
    for _ in range(timeout):
        estado = driver.execute_script("return document.readyState")
        if estado == "complete":
            return True
        time.sleep(1)
    return False

def guardar_pdf(driver, filename):
    try:
        pdf = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,
            "preferCSSPageSize": True
        })

        with open(filename, "wb") as f:
            f.write(base64.b64decode(pdf['data']))
        return True
    except Exception as e:
        print(f"Error PDF: {e}")
        return False

# ==============================
# DRIVER
# ==============================

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)

# BLOQUEAR window.print ANTES DE TODO
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        window.print = function() {
            console.log('Print bloqueado');
        };
    """
})

# ==============================
# LOGIN
# ==============================


url = f"https://{CLIENT}.freshworks.com/login?client_id={ID_TENANT}&redirect_uri=https%3A%2F%2F{CLIENT}.freshdesk.com%2Ffreshid%2Fauthorize_callback%3Fhd%3Dhttps%3A%2F%2F{CLIENT}.freshdesk.com"

driver.get(url)

input("Inicia sesión y presiona ENTER...")

print("Login correcto")

# ==============================
# LOOP
# ==============================

fallidos = []
procesados = 0

for i in range(START_ID, END_ID + 1):
    print(f"\n Ticket {i}")

    try:
        url = f"https://corpei.freshdesk.com/helpdesk/tickets/{i}/print"

        driver.get(url)

        # Esperar render
        esperar_render(driver)
        time.sleep(2)

        if not ticket_existe(driver):
            print("No existe")
            fallidos.append(i)
            continue

        filename = os.path.join(OUTPUT_DIR, f"ticket_{i}.pdf")

        ok = guardar_pdf(driver, filename)

        if ok:
            print(f"Guardado {filename}")
            procesados += 1
            

    except Exception as e:
        print(f"Error en ticket {i}: {e}")
        fallidos.append(i)

    time.sleep(DELAY)

# ==============================
# RESUMEN
# ==============================

print("\n====================")
print("RESULTADO")
print("====================")
print(f"Procesados: {procesados}")
print(f"Fallidos: {len(fallidos)}")

if fallidos:
    print(fallidos)

driver.quit()

