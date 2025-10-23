#!/usr/bin/env python3

class Notas:
    def __init__(self, contenido):
        self.contenido = contenido

    def coincide(self, texto_busqueda):
        return texto_busqueda.lower() in self.contenido.lower()

    def __str__(self):
        return self.contenido
