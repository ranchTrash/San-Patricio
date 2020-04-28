# San-Patricio

Sistema de control para colegio de artes y deportes.

### Introducción

Servidor web creado en Flask para controlar y gestionar datos de un colegio de artes y deportes.

### Pre-requisitos

* [Python](https://www.python.org/downloads/release/python-382/) - Necesario para ejecutar Flask
* [Git](https://git-scm.com/downloads) - Para gestionar repositorios

### Instrucciones para ejecutar el servidor

#### Clonar el repositorio

A través de la línea de comandos o Powershell ejecuta:

```
git clone https://github.com/ranchTrash/San-Patricio.git
```

Ingresa a la carpeta de la repo clonada, y después hasta la carpeta _src_:

```
cd San-Patricio
cd src
```

Activa el entorno virtual para cargar las dependencias de Python:

```
venv\Scripts\activate
```

Indica desde dónde iniciará el servidor web:

* ##### Línea de comandos (cmd, Command prompt)
```
> set FLASK_APP=main.py
```

* ##### Powershell
```
PS > $env:FLASK_APP="main.py"
```

Ejecuta el servidor:

* ##### Sólo máquina local
```
flask run
```

* ##### Para acceder al servidor a través de un dispositivo que no sea el equipo local:
```
flask run --host=0.0.0.0
```

Abrir el navegador y escribir la URL del servidor, conformada por la IP de _localhost_ y el puerto desde el que se está cargando el servidor:
```
localhost:5000
```

o

```
127.0.0.1:5000
```

### TODO (también conocido como Lista de quehaceres): 
* Hacer la ventana de Login responsiva.
* Hacer funcional el menu_responsive. No tiene referencias hacia ninguna página.
* Descargar la fuente "Roboto" y agregarla como archivo local para determinarla como fuente por defecto, en lugar de importarla desde Google Fonts en el archivo Login.css. Esto debido a que no sé cómo importar desde web a Flask con url_for, y ni siquiera sé si lo permite el framework.

### Cambios importantes
* Se agregaron algunas notas e instrucciones para ejecutar el servidor.
* Se elimnaron los archivos JS de JQuery (3.5.0) que no funcionaban correctamente con la última versión de Bootstrap (4.4.x). Se hizo un downgrade de la versión 3.5.0 de JQuery a la versión 3.4.1.

