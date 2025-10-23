# 📝 Gestor de Notas

**Gestor de Notas** es una aplicación de consola en **Python 3** que permite **crear, buscar, editar, eliminar y cargar notas** desde un menú interactivo.  
Las notas se guardan automáticamente en un archivo persistente (`notas.pkl`) utilizando el módulo `pickle`.

---

## 🚀 Instalación

Instala el paquete desde **PyPI** con:

```bash
pip3 install gestor_notas
```

Si obtienes un error de permisos:

```bash
pip3 install --break-system-packages gestor_notas
```

O instálalo localmente (si tienes el código fuente):

```bash
pip install .
```

---

## ⚙️ Uso rápido

Ejecuta el programa directamente desde la terminal:

```bash
notas
```

> 💡 También puedes ejecutarlo manualmente con:
> ```bash
> python3 -m gestor_notas.main
> ```

---

## 📖 Menú principal

Al iniciar el programa, verás un menú como este:

```
---------------------
	MENÚ
---------------------
1. Cargar notas desde archivo
2. Ver todas las notas
3. Agregar una nota
4. Buscar texto en una nota
5. Editar una nota
6. Abrir nota por número de índice
7. Eliminar notas
8. Salir
```

A continuación se explica cada opción 👇

---

## 🧩 Explicación de las opciones

### 1⃣ Cargar notas desde archivo

Permite importar varias notas desde un archivo de texto (`tareas.txt` por defecto).  
El archivo debe ser creado por el usuario y cada línea representará una nota distinta.

**Ejemplo de `tareas.txt`:**
```
revisar correo -> Pendiente
preparar reunión >> Hecho
actualizar sistema -> En progreso
```

**Flujo:**
- Si no se indica un nombre de archivo, se usa `tareas.txt`.  
- Si el archivo no existe, se muestra un aviso de error.  

---

### 2⃣ Ver todas las notas

Muestra una lista numerada de todas las notas guardadas.  
Además, ofrece eliminar notas directamente:

- Escribe el número → elimina esa nota.  
- Escribe `all` → elimina **todas las notas** (con confirmación).  
- Pulsa **Enter** → no elimina ninguna.  

---

### 3⃣ Agregar una nota

Permite añadir nuevas notas al sistema.

**Flujo:**
1. Pregunta la posición donde insertar la nota:  
   - Enter → la añade al final.  
   - Un número → la inserta en esa posición.  
2. Solicita el contenido de la nota.  

**Ejemplo:**
```
[+] Indica la posición donde insertar la nota (Enter para final): 1
[+] Contenido de la nota: Llamar a Juan
```

---

### 4⃣ Buscar texto en una nota

Busca coincidencias de texto dentro de las notas (sin importar mayúsculas o minúsculas).  
Muestra las coincidencias con su número de índice original.

**Ejemplo:**
```
[+] Ingresa el texto a buscar en las notas: proyecto
[+] Notas que coinciden con el texto:

[3]: Revisar proyecto del cliente
[8]: Proyecto nuevo -> Pendiente
```

También permite eliminar las coincidencias (`número`, `all`, o Enter para cancelar).

---

### 5⃣ Editar una nota

Permite modificar el contenido de una nota existente.

**Flujo:**
1. Muestra la lista actual de notas.  
2. Pide el número de la nota a editar.  
3. Solicita el nuevo contenido.  

**Ejemplo:**
```
[+] Indica el número de la nota a editar: 3
[+] Nuevo contenido de la nota: Revisar proyecto finalizado
```

---

### 6⃣ Abrir nota por número de índice

Muestra en pantalla el contenido de una nota específica según su índice.

**Ejemplo:**
```
[+] Indica el número de índice a mostrar: 4
Nota #4:
buscar redes wifi >> Pendiente
```

---

### 7⃣ Eliminar notas

Permite eliminar una nota concreta o todas las existentes.  
Antes de eliminar se solicita confirmación.

**Ejemplo:**
```
[?] ¿Deseas eliminar alguna nota? (número, 'all' o Enter para no): all
[!] ¿Seguro que deseas eliminar TODAS las notas? (s/n): s
[+] Todas las notas han sido eliminadas.
```

---

### 8⃣ Salir

Finaliza el programa de forma segura.

---

## 🧠 Atajos útiles

- **Enter** → Avanza al siguiente paso sin limpiar pantalla.  
- **Ctrl + L** → Limpia la pantalla y muestra nuevamente el menú principal.  

---

## 📂 Estructura del proyecto

```
gestor_notas/
├── gestor_notas/
│   ├── __init__.py
│   ├── main.py
│   ├── notas.py
│   └── gestor_notas.py
├── tareas.txt
├── README.md
├── LICENSE
├── setup.py
└── pyproject.toml
```

---

## 👨‍💻 Autor

**Aurisssss**  
📧 aurisssss@protonmail.com  
🌐 [GitHub](https://github.com/aurisssss)  
🌐 [PyPI](https://pypi.org/search/?q=aurisssss)

**Créditos:**  
Proyecto basado en un ejercicio de la academia [Hack4u.io](https://www.hack4u.io),  
posteriormente extendido y personalizado por **Aurisssss** con nuevas funciones.

---

## ⚖️ Licencia

Publicado bajo licencia **MIT**.  
Eres libre de usar, modificar y distribuir este software con fines personales o educativos.

---

⭐ **Si este proyecto te ha sido útil, deja una estrella en GitHub o PyPI.**  
¡Tu apoyo ayuda a seguir creando herramientas libres! ⭐

