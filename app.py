
from flask import Flask, request, jsonify, render_template

from flask_cors import CORS

import mysql.connector

from werkzeug.utils import secure_filename

import os
import time

#--------------------------------------------------------------------

app = Flask(__name__)
CORS(app)

#--------------------------------------------------------------------

class Catalogo:

    #----------------------------------------------------------------

    def __init__(self, host, user, password, database):
        
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        self.cursor = self.conn.cursor()

        try:
            self.cursor.execute(f"USE {database}")
        except mysql.connector.Error as err:
            
            if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.cursor.execute(f"CREATE DATABASE {database}")
                self.conn.database = database
            else:
                raise err

        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
            codigo INT,
            nombre VARCHAR(255) NOT NULL,
            ingredientes VARCHAR(255) NOT NULL,
            cantidad INT NOT NULL,
            precio DECIMAL(10, 2) NOT NULL,
            imagen_url VARCHAR(255),
            proveedor INT(4))''')
        self.conn.commit()

        self.cursor.close()
        self.cursor = self.conn.cursor(dictionary=True)
        
    #----------------------------------------------------------------

    def agregar_producto(self, codigo, nombre, ingredientes, cantidad, precio, imagen, proveedor):
        
        self.cursor.execute(f"SELECT * FROM productos WHERE codigo = {codigo}")
        producto_existe = self.cursor.fetchone()
        if producto_existe:
            return False

        
        sql = "INSERT INTO productos (codigo, nombre, ingredientes, cantidad, precio, imagen_url, proveedor) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        valores = (codigo, nombre, ingredientes, cantidad, precio, imagen, proveedor)

        self.cursor.execute(sql, valores)        
        self.conn.commit()
        return True

    #----------------------------------------------------------------

    def consultar_producto(self, codigo):
        
        self.cursor.execute(f"SELECT * FROM productos WHERE codigo = {codigo}")
        return self.cursor.fetchone()

    #----------------------------------------------------------------

    def modificar_producto(self, codigo, nuevo_nombre, nuevo_ingredientes, nueva_cantidad, nuevo_precio, nueva_imagen, nuevo_proveedor):
        
        sql = "UPDATE productos SET nombre = %s, ingredientes = %s, cantidad = %s, precio = %s, imagen_url = %s, proveedor = %s WHERE codigo = %s"
        valores = (nuevo_nombre, nuevo_ingredientes, nueva_cantidad, nuevo_precio, nueva_imagen, nuevo_proveedor, codigo)
        self.cursor.execute(sql, valores)
        self.conn.commit()
        return self.cursor.rowcount > 0

    #----------------------------------------------------------------

    def listar_productos(self):
        self.cursor.execute("SELECT * FROM productos")
        productos = self.cursor.fetchall()
        return productos

    #----------------------------------------------------------------

    def eliminar_producto(self, codigo):
       
        self.cursor.execute(f"DELETE FROM productos WHERE codigo = {codigo}")
        self.conn.commit()
        return self.cursor.rowcount > 0

    #----------------------------------------------------------------

    def mostrar_producto(self, codigo):
       
        producto = self.consultar_producto(codigo)
        if producto:
            print("-" * 40)
            print(f"Código......: {producto['codigo']}")
            print(f"Nombre......: {producto['nombre']}")
            print(f"Ingredientes: {producto['ingredientes']}")
            print(f"Cantidad....: {producto['cantidad']}")
            print(f"Precio......: {producto['precio']}")
            print(f"Imagen......: {producto['imagen_url']}")
            print(f"Proveedor...: {producto['proveedor']}")
            print("-" * 40)
        else:
            print("Producto no encontrado.")


#--------------------------------------------------------------------
# Cuerpo del programa
#--------------------------------------------------------------------

# catalogo = Catalogo(host='localhost', user='root', password='root', database='miapp')
catalogo = Catalogo(host='elavincho.mysql.pythonanywhere-services.com', user='elavincho', password='root1234', database='elavincho$miapp')

# Carpeta para guardar las imagenes.
# RUTA_DESTINO = './static/imagenes/'

#Al subir al servidor, deberá utilizarse la siguiente ruta. USUARIO debe ser reemplazado por el nombre de usuario de Pythonanywhere
RUTA_DESTINO = '/home/elavincho/mysite/static/imagenes'


#--------------------------------------------------------------------
# Listar todos los productos
#--------------------------------------------------------------------

#La ruta Flask /productos con el método HTTP GET está diseñada para proporcionar los detalles de todos los productos almacenados en la base de datos.
#El método devuelve una lista con todos los productos en formato JSON.

@app.route("/productos", methods=["GET"])
def listar_productos():
    productos = catalogo.listar_productos()
    return jsonify(productos)


#--------------------------------------------------------------------
# Mostrar un sólo producto según su código
#--------------------------------------------------------------------

#La ruta Flask /productos/<int:codigo> con el método HTTP GET está diseñada para proporcionar los detalles de un producto específico basado en su código.
#El método busca en la base de datos el producto con el código especificado y devuelve un JSON con los detalles del producto si lo encuentra, o None si no lo encuentra.

@app.route("/productos/<int:codigo>", methods=["GET"])
def mostrar_producto(codigo):
    producto = catalogo.consultar_producto(codigo)
    if producto:
        return jsonify(producto), 201
    else:
        return "Producto no encontrado", 404


#--------------------------------------------------------------------
# Agregar un producto
#--------------------------------------------------------------------

@app.route("/productos", methods=["POST"])

#La ruta Flask `/productos` con el método HTTP POST está diseñada para permitir la adición de un nuevo producto a la base de datos.
#La función agregar_producto se asocia con esta URL y es llamada cuando se hace una solicitud POST a /productos.

def agregar_producto():

    codigo = request.form['codigo']
    nombre = request.form['nombre']
    ingredientes = request.form['ingredientes']
    cantidad = request.form['cantidad']
    precio = request.form['precio']
    imagen = request.files['imagen']
    proveedor = request.form['proveedor']  
    nombre_imagen=""

    
    producto = catalogo.consultar_producto(codigo)
    
    if not producto:
        
        nombre_imagen = secure_filename(imagen.filename) 
        nombre_base, extension = os.path.splitext(nombre_imagen)
        nombre_imagen = f"{nombre_base}_{int(time.time())}{extension}"
        
        if  catalogo.agregar_producto(codigo, nombre, ingredientes, cantidad, precio, nombre_imagen, proveedor):
            imagen.save(os.path.join(RUTA_DESTINO, nombre_imagen))

            return jsonify({"mensaje": "Producto agregado correctamente.", "imagen": nombre_imagen}), 201
        else:
            return jsonify({"mensaje": "Error al agregar el producto."}), 500

    else:
        return jsonify({"mensaje": "Producto ya existe."}), 400
    

#--------------------------------------------------------------------
# Modificar un producto según su código
#--------------------------------------------------------------------

@app.route("/productos/<int:codigo>", methods=["PUT"])
#La ruta Flask /productos/<int:codigo> con el método HTTP PUT está diseñada para actualizar la información de un producto existente en la base de datos, identificado por su código.
#La función modificar_producto se asocia con esta URL y es invocada cuando se realiza una solicitud PUT a /productos/ seguido de un número (el código del producto).

def modificar_producto(codigo):
   
    nuevo_nombre = request.form.get("nombre")
    nuevo_ingredientes = request.form.get("ingredientes")
    nueva_cantidad = request.form.get("cantidad")
    nuevo_precio = request.form.get("precio")
    nuevo_proveedor = request.form.get("proveedor")
    imagen = request.files['imagen']

    # Procesamiento de la imagen
    nombre_imagen = secure_filename(imagen.filename)
    nombre_base, extension = os.path.splitext(nombre_imagen)
    nombre_imagen = f"{nombre_base}_{int(time.time())}{extension}"

    # Busco el producto guardado
    producto = producto = catalogo.consultar_producto(codigo)
    if producto:
        imagen_vieja = producto["imagen_url"]
        # Armo la ruta a la imagen
        ruta_imagen = os.path.join(RUTA_DESTINO, imagen_vieja)

        # Y si existe la borro.
        if os.path.exists(ruta_imagen):
            os.remove(ruta_imagen)
    
    # Se llama al método modificar_producto pasando el codigo del producto y los nuevos datos.
    if catalogo.modificar_producto(codigo, nuevo_nombre, nuevo_ingredientes, nueva_cantidad, nuevo_precio, nombre_imagen, nuevo_proveedor):
        #La imagen se guarda en el servidor.
        imagen.save(os.path.join(RUTA_DESTINO, nombre_imagen))

        #Si la actualización es exitosa, se devuelve una respuesta JSON con un mensaje de éxito y un código de estado HTTP 200 (OK).
        return jsonify({"mensaje": "Producto modificado"}), 200
    else:
        #Si el producto no se encuentra (por ejemplo, si no hay ningún producto con el código dado), se devuelve un mensaje de error con un código de estado HTTP 404 (No Encontrado).
        return jsonify({"mensaje": "Producto no encontrado"}), 403



#--------------------------------------------------------------------
# Eliminar un producto según su código
#--------------------------------------------------------------------

@app.route("/productos/<int:codigo>", methods=["DELETE"])
#La ruta Flask /productos/<int:codigo> con el método HTTP DELETE está diseñada para eliminar un producto específico de la base de datos, utilizando su código como identificador.
#La función eliminar_producto se asocia con esta URL y es llamada cuando se realiza una solicitud DELETE a /productos/ seguido de un número (el código del producto).

def eliminar_producto(codigo):
    # Busco el producto en la base de datos
    producto = catalogo.consultar_producto(codigo)
    if producto: # Si el producto existe, verifica si hay una imagen asociada en el servidor.
        imagen_vieja = producto["imagen_url"]
        # Armo la ruta a la imagen
        ruta_imagen = os.path.join(RUTA_DESTINO, imagen_vieja)

        # Y si existe, la elimina del sistema de archivos.
        if os.path.exists(ruta_imagen):
            os.remove(ruta_imagen)

        # Luego, elimina el producto del catálogo
        if catalogo.eliminar_producto(codigo):
            #Si el producto se elimina correctamente, se devuelve una respuesta JSON con un mensaje de éxito y un código de estado HTTP 200 (OK).
            return jsonify({"mensaje": "Producto eliminado"}), 200
        else:
            #Si ocurre un error durante la eliminación (por ejemplo, si el producto no se puede eliminar de la base de datos por alguna razón), se devuelve un mensaje de error con un código de estado HTTP 500 (Error Interno del Servidor).
            return jsonify({"mensaje": "Error al eliminar el producto"}), 500
    else:
        #Si el producto no se encuentra (por ejemplo, si no existe un producto con el codigo proporcionado), se devuelve un mensaje de error con un código de estado HTTP 404 (No Encontrado). 
        return jsonify({"mensaje": "Producto no encontrado"}), 404

#--------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)