import numpy as np

def saludar():
    print("Hola te saludo  desde saludos.saludar()")

def prueba():
    print("Esto es una nueva prueba de la nuevaa version")

def generar_array(numeros):
    return np.arange(numeros)
        

class saludo:
    def __init__(self):
        print("Hola te sludo desde saludos.innit")

if __name__ == "__main__":
    print(generar_array(5))
 