#!/usr/bin/env python3

import pickle
from notas import Notas

class GestorNotas:

    def __init__(self, archivo_notas='notas.pkl'):
        self.archivo_notas = archivo_notas
        try:
            with open(self.archivo_notas, 'rb') as f:
                self.notas = pickle.load(f)
        except FileNotFoundError:
            self.notas = []

    def guardar_notas(self):
        with open(self.archivo_notas, "wb") as f:
            pickle.dump(self.notas, f)

    def agregar_nota(self, contenido, posicion=None):
        nueva_nota = Notas(contenido)
        if posicion is not None and 0 <= posicion <= len(self.notas):
            self.notas.insert(posicion, nueva_nota)
        else:
            self.notas.append(nueva_nota)
        self.guardar_notas()

    def leer_notas(self):
        return self.notas

    def ver_nota(self, indice):
        if 0 <= indice < len(self.notas):
            return self.notas[indice]
        else:
            return None

    def buscar_nota(self, texto_busqueda):
        return [nota for nota in self.notas if nota.coincide(texto_busqueda)]

    def editar_nota(self, index, nuevo_contenido):
        if 0 <= index < len(self.notas):
            self.notas[index].contenido = nuevo_contenido
            self.guardar_notas()
            print(f"\n[+] Nota actualizada correctamente.")
        else:
            print(f"\n[!] El índice indicado no existe.")

    def cargar_desde_archivo(self, archivo_tareas='tareas.txt'):
        try:
            with open(archivo_tareas, 'r', encoding='utf-8') as f:
                lineas = [linea.strip() for linea in f if linea.strip()]  # ignora líneas vacías

            if not lineas:
                print("\n[!] El archivo está vacío o no contiene tareas válidas.")
                return

            for linea in lineas:
                self.notas.append(Notas(linea))

            self.guardar_notas()
            print(f"\n[+] {len(lineas)} tareas cargadas desde '{archivo_tareas}' correctamente.")
        except FileNotFoundError:
            print(f"\n[!] No se encontró el archivo '{archivo_tareas}'.")

    def eliminar_nota(self, index):
        """Elimina una nota específica con confirmación."""
        if 0 <= index < len(self.notas):
            print(f"\n[?] Nota seleccionada: {self.notas[index]}")
            confirmacion = input("[!] ¿Seguro que deseas eliminar esta nota? (s/n): ").strip().lower()
            if confirmacion == "s":
                del self.notas[index]
                self.guardar_notas()
                print(f"\n[+] Nota #{index+1} eliminada correctamente.")
            else:
                print("\n[-] Operación cancelada.")
        else:
            print("\n[!] El índice proporcionado es incorrecto.\n")

    def eliminar_todas(self):
        confirmacion = input("\n[?] ¿Seguro que deseas eliminar TODAS las notas? (s/n): ").strip().lower()
        if confirmacion == "s":
            self.notas.clear()
            self.guardar_notas()
            print("\n[+] Todas las notas han sido eliminadas.")
        else:
            print("\n[-] Operación cancelada.")

