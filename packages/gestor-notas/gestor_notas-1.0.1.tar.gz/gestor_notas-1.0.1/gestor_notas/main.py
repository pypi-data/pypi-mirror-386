#!/usr/bin/env python3
import os
import sys
import termios
import tty
from gestor_notas import GestorNotas


def main():
    gestor = GestorNotas()
    mostrar_menu = True  # controla si se debe mostrar el menú completo

    while True:
        # Mostrar menú solo si es necesario
        if mostrar_menu:
            print("---------------------\n\tMENÚ\n---------------------")
            print("1. Cargar notas desde archivo")
            print("2. Ver todas las notas")
            print("3. Agregar una nota")
            print("4. Buscar texto en una nota")
            print("5. Editar una nota")
            print("6. Abrir nota por número de índice")
            print("7. Eliminar notas")
            print("8. Salir")

        # Pedir opción (sin limpiar pantalla si no se muestra menú)
        opcion = input("\n[+] Escoge una opción: ").strip()

        # ────────────────────────────────
        # 1. Cargar notas desde archivo
        # ────────────────────────────────
        if opcion == "1":
            nombre_archivo = input(
                "\n[+] Indica el nombre del archivo (por defecto 'tareas.txt'): "
            ).strip() or "tareas.txt"
            gestor.cargar_desde_archivo(nombre_archivo)

        # ────────────────────────────────
        # 2. Ver todas las notas
        # ────────────────────────────────
        elif opcion == "2":
            notas = gestor.leer_notas()
            if notas:
                print("\n[+] Mostrando todas las notas:\n")
                for i, nota in enumerate(notas):
                    print(f"{i+1}: {nota}")

                eliminar = input("\n[?] ¿Deseas eliminar alguna nota? (número, 'all' o Enter para no): ").strip().lower()
                if eliminar == "all":
                    gestor.eliminar_todas()
                elif eliminar.isdigit():
                    idx = int(eliminar) - 1
                    gestor.eliminar_nota(idx)
            else:
                print("\n[!] No hay notas registradas.")

        # ────────────────────────────────
        # 3. Agregar una nota
        # ────────────────────────────────
        elif opcion == "3":
            posicion = input("\n[+] Indica la posición donde insertar la nota (Enter para final): ").strip()
            contenido = input("\n[+] Contenido de la nota: ").strip()

            if not contenido:
                print("\n[!] No se puede agregar una nota vacía.")
            else:
                if posicion.isdigit():
                    pos = int(posicion) - 1
                    gestor.agregar_nota(contenido, pos)
                    print(f"\n[+] Nota añadida en la posición #{pos+1}")
                else:
                    gestor.agregar_nota(contenido)
                    print("\n[+] Nota agregada correctamente al final de la lista.")

        # ────────────────────────────────
        # 4. Buscar texto en una nota
        # ────────────────────────────────
        elif opcion == "4":
            texto_busqueda = input("\n[+] Ingresa el texto a buscar en las notas: ").strip()
            resultados = gestor.buscar_nota(texto_busqueda)

            if resultados:
                print("\n[+] Notas que coinciden con el texto:\n")
                for nota in resultados:
                    indice_original = next(
                        (i for i, n in enumerate(gestor.notas) if n.contenido == nota.contenido), -1)
                    print(f"[{indice_original + 1 if indice_original >= 0 else '?'}]: {nota}")
                print(f"\n\t[+] Se han encontrado #{len(resultados)} notas coincidentes")


                eliminar = input("\n[?] ¿Deseas eliminar alguna nota? (número, 'all' o Enter para no): ").strip().lower()
                if eliminar == "all":
                    gestor.eliminar_todas()
                elif eliminar.isdigit():
                    idx = int(eliminar) - 1
                    gestor.eliminar_nota(idx)
            else:
                print("\n[!] No se encontraron coincidencias.")

        # ────────────────────────────────
        # 5. Editar una nota
        # ────────────────────────────────
        elif opcion == "5":
            notas = gestor.leer_notas()
            if not notas:
                print("\n[!] No hay notas para editar.")
            else:
                print("\n[+] Notas disponibles:\n")
                for i, nota in enumerate(notas):
                    print(f"{i+1}: {nota}")
                idx = input("\n[+] Indica el número de la nota a editar: ").strip()
                if idx.isdigit():
                    idx = int(idx) - 1
                    if 0 <= idx < len(notas):
                        nuevo_contenido = input("\n[+] Nuevo contenido de la nota: ").strip()
                        gestor.editar_nota(idx, nuevo_contenido)
                    else:
                        print("\n[!] Número fuera de rango.")
                else:
                    print("\n[!] Entrada no válida.")

        #────────────────────────────────
        #6. Abrir nota por número de índice
        #────────────────────────────────
        elif opcion == "6":
            indice = input("\n[+] Indica el número de índice a mostrar: ").strip()
            if indice.isdigit():
                idx = int(indice) - 1
                nota = gestor.ver_nota(idx)
                if nota:
                    print(f"\n[+] Nota #{idx+1}: {nota}")
                else:
                    print("\n[!] No existe ninguna nota con ese índice.")
            else:
                print("\n[!] Entrada no válida, debe ser un número.")

        # ────────────────────────────────
        # 7. Eliminar notas
        # ────────────────────────────────
        elif opcion == "7":
            notas = gestor.leer_notas()
            if notas:
                print("\n[+] Notas disponibles:\n")
                for i, nota in enumerate(notas):
                    print(f"{i+1}: {nota}")

                eliminar = input("\n[?] ¿Deseas eliminar alguna nota? (número, 'all' o Enter para no): ").strip().lower()
                if eliminar == "all":
                    gestor.eliminar_todas()
                elif eliminar.isdigit():
                    idx = int(eliminar) - 1
                    gestor.eliminar_nota(idx)
            else:
                print("\n[!] No hay notas registradas.")

        # ────────────────────────────────
        # 8. Salir
        # ────────────────────────────────
        elif opcion == "8":
            print("\n[+] Saliendo del programa...")
            break

        else:
            print("\n[!] La opción indicada es incorrecta.")

        # ────────────────────────────────
        # Control de pantalla / flujo
        # ────────────────────────────────
        accion = esperar_tecla()

        if accion == 'ctrl_l':
            os.system('cls' if os.name == 'nt' else 'clear')
            mostrar_menu = True
        elif accion == 'enter':
            mostrar_menu = False
            continue
        else:
            mostrar_menu = True


def esperar_tecla():
    """Esperar una tecla y devolver 'enter', 'ctrl_l' o None."""
    print("\n[+] Presiona <Enter> para continuar sin limpiar o Ctrl+L para limpiar pantalla y mostrar el menú...")
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x0c':  # Ctrl+L
            return 'ctrl_l'
        elif ch == '\r':  # Enter
            return 'enter'
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return None


if __name__ == '__main__':
    main()

