import SelFw

driver = SelFw.iniciar_chrome(
    modo="normal",
    proxy="8a805f4cc051243a3655__cr.us:13196fc0d040d72a@gw.dataimpulse.com:823",
    headless=False,
    usar_seleniumwire=True,
    perfil=None
)
SelFw.abrir('https://ipify.org', driver)
SelFw.esperar(8888)