# Aplicación de Renta de Autos con Flask y MongoDB

Esta carpeta contiene una **aplicación mínima** para gestionar una empresa de renta de autos.  El objetivo principal es satisfacer los requerimientos funcionales descritos en el caso de estudio usando la tecnología más sencilla posible: **Python 3**, **Flask** y **MongoDB**.  El código está preparado para usarse con una instancia local de MongoDB (por ejemplo, instalada de manera estándar o administrada con MongoDB Compass), pero puede adaptarse fácilmente a una instancia remota cambiando la cadena de conexión.

## Pre‐requisitos

1. **Python 3.8 o superior**.  Si usas Windows/Mac/Linux y no tienes Python instalado, descárgalo desde [python.org](https://www.python.org/downloads/).
2. **MongoDB en la máquina local**.  Puedes instalar [MongoDB Community](https://www.mongodb.com/try/download/community) o utilizar [MongoDB Compass](https://www.mongodb.com/products/compass) para administrar tu base de datos.  La aplicación asume que MongoDB escucha en `mongodb://localhost:27017` y que se utilizará la base de datos `renta_autos`.
3. **Acceso a un terminal** (cmd, PowerShell, Terminal, etc.) para ejecutar comandos y arrancar el servidor Flask.

## Instalación rápida

1. **Clona o descarga** esta carpeta en tu equipo.  Navega hasta la carpeta `car_rental_app` con tu terminal.

2. Crea un **entorno virtual** para aislar las dependencias del proyecto (opcional pero recomendado):

   ```bash
   python -m venv venv
   # Activa el entorno virtual
   # En Windows:
   venv\Scripts\activate
   # En Mac/Linux:
   source venv/bin/activate
   ```

3. **Instala las dependencias** necesarias (Flask y PyMongo):

   ```bash
   pip install Flask pymongo
   ```

   Estos módulos permiten crear una API web con Flask y conectar con MongoDB usando PyMongo.  Para más detalles sobre cómo conectarse a MongoDB con PyMongo, consulta la documentación: PyMongo facilita la conexión y el envío de comandos a MongoDB【788983236826060†L95-L116】.

4. **Arranca MongoDB** si no se está ejecutando.  Normalmente puedes ejecutarlo con `mongod` en la terminal o mediante la interfaz de Compass.  La aplicación asumirá que MongoDB está escuchando en `localhost:27017` y que no requiere autenticación.

5. Ejecuta la aplicación Flask:

   ```bash
   python app.py
   ```

   Verás un mensaje similar a `* Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)`.  Este mensaje indica que la API está lista para recibir peticiones en el puerto 5000.

## Descripción general de la API

La API proporciona una serie de endpoints RESTful para gestionar clientes, autos, reparaciones, rentas, devoluciones y alertas.  El archivo principal `app.py` incluye la definición de todas las rutas y la lógica de negocio básica.  A continuación se resumen las operaciones principales:

| Endpoint | Verbo HTTP | Descripción breve |
|---------|------------|-------------------|
| `/clientes` | `GET` | Recupera la lista de clientes. |
| `/clientes` | `POST` | Crea un nuevo cliente. |
| `/clientes/<id>` | `PUT` | Modifica un cliente existente. |
| `/clientes/<id>` | `DELETE` | Elimina un cliente. |
| `/autos` | `GET` | Lista todos los autos. |
| `/autos` | `POST` | Crea un auto. |
| `/autos/<id>` | `PUT` | Actualiza un auto. |
| `/autos/<id>` | `DELETE` | Elimina un auto. |
| `/reparaciones` | `POST` | Registra una reparación. |
| `/reparaciones/consulta` | `GET` | Consulta reparaciones por periodo de fechas y costo. |
| `/autos/disponibles` | `GET` | Lista los autos disponibles para renta. |
| `/rentas` | `POST` | Registra una nueva renta de auto. |
| `/rentas/<id>` | `PUT` | Actualiza una renta existente. |
| `/rentas/ultimos` | `GET` | Devuelve rentas registradas en los últimos 2 meses. |
| `/devoluciones` | `POST` | Registra la devolución de un auto. |
| `/alertas` | `GET` | Consulta las alertas de autos devueltos en mal estado. |

### Estructura de la base de datos

La aplicación trabaja con varias **colecciones** en la base de datos `renta_autos`:

* **clientes**: almacena la información de cada cliente.  Cada documento contiene campos como nombre, apellido, dirección, teléfono, etc.
* **autos**: describe los vehículos disponibles.  Incluye datos como marca, modelo, año y un atributo `disponible` que indica si el auto está libre para renta.
* **reparaciones**: registra las reparaciones de los autos; incluye referencias al auto (`auto_id`), fecha de la reparación, descripción y costo.
* **rentas**: almacena las rentas activas o históricas.  Cada documento incluye `auto_id`, `cliente_id`, fechas de inicio y fin, costo y estado.
* **devoluciones**: registra cuándo se devuelve un auto.  Contiene el identificador de la renta (`renta_id`), la fecha de devolución y el estado del auto al momento de devolverse.
* **alertas**: guarda alertas generadas cuando un auto es devuelto en mal estado (campo `condicion` igual a `malo`).

### Resumen de los requerimientos cumplidos

* **RF01** – El endpoint `/clientes` permite a los empleados de atención al público crear, consultar, actualizar y eliminar datos de los clientes.
* **RF02** – El endpoint `/autos` posibilita que el encargado de autos mantenga el registro de cada auto (alta, actualización y baja).
* **RF03** – La ruta `/reparaciones` registra reparaciones de un auto.  Las reparaciones no se eliminan para mantener el historial de mantenimiento.
* **RF04** – El propietario puede obtener información de reparaciones filtrando por un periodo de tiempo y coste máximo a través de `/reparaciones/consulta`.
* **RF07** – El endpoint `/autos/disponibles` permite que un empleado consulte los vehículos libres para renta.
* **RF05** – La ruta `/rentas` registra y actualiza rentas de autos.  Se actualiza el estado `disponible` del auto y el estado de la renta correspondiente.
* **RF06** – El endpoint `/rentas/ultimos` consulta rentas realizadas en los últimos dos meses.
* **RF09** – La ruta `/devoluciones` permite registrar devoluciones de autos y actualizar el estado del vehículo en la colección `autos`.
* **RF08** – Si al registrar una devolución se indica que el auto está en mal estado (`condicion` = `malo`), se genera un documento de alerta en la colección `alertas`.

### Inicio de sesión y roles de usuario

Desde la versión actual, la aplicación incluye un **sistema de autenticación** básico con roles.  Para empezar a usarlo debes crear usuarios de demostración ejecutando la siguiente ruta una sola vez (desde el navegador o con `curl`):

```bash
http://127.0.0.1:5000/crear_usuarios_demo
```

Esto insertará tres usuarios en la colección `usuarios`:

| Usuario    | Contraseña       | Rol       |
|-----------|------------------|-----------|
| empleado  | empleado123      | empleado  |
| encargado | encargado123     | encargado |
| dueno     | dueno123         | dueno     |

Cada rol tiene permisos diferentes en la interfaz web y en los endpoints REST:

- **empleado**: puede gestionar clientes (`/clientes`), registrar y actualizar rentas (`/rentas`), y consultar autos disponibles.  La navegación web mostrará solo las secciones pertinentes (Clientes y Rentas).
- **encargado**: puede administrar autos (`/autos`), registrar reparaciones (`/reparaciones`), consultar rentas (`/rentas/lista` y `/rentas/ultimos`), registrar devoluciones (`/devoluciones`) y ver alertas (`/alertas`).
- **dueno**: su acceso se limita a consultar reparaciones para obtener reportes por periodo y costo (`/reparaciones/lista` y `/reparaciones/consulta`).

Para iniciar sesión, navega a `http://127.0.0.1:5000/login` e introduce el usuario y contraseña correspondientes.  Una vez autenticado, la aplicación recordará tu sesión mediante cookies de Flask.  Puedes cerrar sesión desde la barra de navegación.

### Limitaciones y tareas no implementadas

* **Automatización de respaldos (backups)** y **registros de log**: Aunque el enunciado menciona tareas automatizadas de respaldo completo semanal, respaldo diferencial diario y log de registros cada dos horas, estas funciones suelen configurarse a nivel de servidor o mediante scripts de sistema.  Para un entorno académico se recomienda utilizar la herramienta `mongodump` para crear respaldos manuales o programar tareas con `cron` (Linux/Mac) o el Programador de tareas (Windows).  PyMongo soporta operaciones de respaldo mediante comandos `dump`, pero su implementación queda fuera del alcance de este código minimalista.  Más información sobre inserción y consulta de datos con PyMongo se encuentra en la documentación oficial【788983236826060†L95-L134】.

## Cómo probar la API

Una vez que la aplicación esté en ejecución (`python app.py`), puedes utilizar herramientas como **Postman**, **Insomnia** o `curl` para enviar peticiones HTTP y verificar el funcionamiento.  A continuación se muestran ejemplos básicos utilizando `curl`:

### Crear un cliente

```bash
curl -X POST http://127.0.0.1:5000/clientes \
     -H "Content-Type: application/json" \
     -d '{"nombre": "Juan", "apellido": "Pérez", "telefono": "555123456", "direccion": "Calle 1 #100"}'
```

### Listar autos disponibles

```bash
curl http://127.0.0.1:5000/autos/disponibles
```

### Registrar una renta

```bash
curl -X POST http://127.0.0.1:5000/rentas \
     -H "Content-Type: application/json" \
     -d '{"auto_id": "<id_del_auto>", "cliente_id": "<id_del_cliente>", "fecha_inicio": "2025-08-01", "fecha_fin": "2025-08-05", "costo": 1000}'
```

Reemplaza `<id_del_auto>` y `<id_del_cliente>` por los valores devueltos al crear autos y clientes respectivamente.  El campo `fecha_fin` es opcional al crear la renta; se puede actualizar posteriormente con un `PUT` sobre `/rentas/<id>`.

Consulta el archivo `app.py` para ver más ejemplos de campos y estructuras.
