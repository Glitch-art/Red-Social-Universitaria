from flask import Flask, render_template, request, redirect, url_for, flash
from config import *
from flask_login import LoginManager, login_user, logout_user, login_required

from models.ModelUser import ModelUser
from models.entities.User import User

app = Flask(__name__)

con_bd = EstablecerConexion()

login_manager_app = LoginManager(app)

@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(con_bd, id)

@app.route('/')
def index():
    crearTablaUsers()
    crearTablaProductos()
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    crearTablaUsers()
    if request.method == 'POST':
        # print(request.form['email'])
        # print(request.form['password'])
        user = User(0, request.form['email'], request.form['password'])
        logged_user = ModelUser.login(con_bd, user)
        if logged_user != None:
            if logged_user.password:
                login_user(logged_user)
                flash("Bienvenido", "success")
                return redirect(url_for('home'))
            else:
                flash("Contraseña o usuario incorrecto", "danger")
                return render_template('auth/login.html')
        else:
            flash("Contraseña o usuario incorrecto", "danger")
            return render_template('auth/login.html')
    else:
        return render_template('auth/login.html')

@app.route('/new_user')
def new_user():
  return render_template('auth/new.html')

@app.route('/signup', methods=['POST'])
def add_user():
  crearTablaUsers()
  cursor = con_bd.cursor()
  form = request.form
  email = form['email']
  password = User.passwordHash(form['password'])
  if email and password:
    sql = """
    INSERT INTO
      users (
        email,
        password
      )
      VALUES
      ( %s, %s);
    """
    cursor.execute(sql,(email, password))
    con_bd.commit()
    flash('Usuario Registrado Correctamente', 'info')
    return redirect(url_for('index'))
  else:
    flash('Error Al Registrar El Usuario', 'danger')
    return "Error"

@app.route('/registrarProducto', methods=['POST'])
def registrarProducto():
  crearTablaProductos()
  cursor = con_bd.cursor()
  form = request.form
  nombreProducto = form['nombreProducto']
  valorProducto = form['valorProducto']
  cantidadProducto = form['cantidadProducto']
  if nombreProducto and valorProducto and cantidadProducto:
    sql = """
    INSERT INTO
      productos (
        nombreProducto,
        valorProducto,
        cantidadProducto
      )
      VALUES
      ( %s, %s, %s);
    """
    cursor.execute(sql,(nombreProducto, valorProducto, cantidadProducto))
    con_bd.commit()
    flash('Producto Guardado Correctamente', 'info')
    return redirect(url_for('home'))
  else:
    flash('Error Al Guardar El Producto', 'danger')
    return "Error"

@app.route('/home')
@login_required
def home():
    cursor = con_bd.cursor()
    sql = "SELECT * FROM productos ORDER BY id DESC"
    cursor.execute(sql)
    productosRegistrados = cursor.fetchall()
    return render_template('home.html', productos = productosRegistrados)

@app.route('/logout')
def logout():
    logout_user()
    flash("Sesión cerrada correctamente", "success")
    return redirect(url_for('login'))

@app.route('/editar_producto/<int:id>', methods=['POST'])
def editar(id):
    cursor = con_bd.cursor()
    form = request.form
    nombreProducto = form['nombreProducto']
    valorProducto = form['valorProducto']
    cantidadProducto = form['cantidadProducto']
    if nombreProducto and valorProducto and cantidadProducto:
        sql = """
            UPDATE productos
            SET nombreProducto=%s, valorProducto=%s, cantidadProducto=%s
            WHERE id = %s
        """
        cursor.execute(sql, (nombreProducto, valorProducto, cantidadProducto, id))
        con_bd.commit()
        flash('Producto Editado Correctamente', 'info')
        return redirect(url_for('home'))
    else:
        flash('Error al editar el producto', 'danger')
        return "Error en la consulta"

@app.route('/eliminar_producto/<int:id>')
def eliminar(id):
   cursor = con_bd.cursor()
   sql = "DELETE FROM productos WHERE id = {0}".format(id)
   cursor.execute(sql)
   con_bd.commit()
   flash('Producto Eliminado Correctamente', 'info')
   return redirect(url_for('home'))

def crearTablaUsers():
    cursor = con_bd.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users(
        id serial NOT NULL,
        email character varying(50),
        password character varying(255),
        CONSTRAINT pk_user_id PRIMARY KEY (id)
        );
    ''')
    con_bd.commit()

def crearTablaProductos():
    cursor = con_bd.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos(
        id serial NOT NULL,
        nombreProducto character varying(100),
        valorProducto integer,
        cantidadProducto integer,
        CONSTRAINT pk_productos_id PRIMARY KEY (id)
        );
    ''')
    con_bd.commit()

def status_401(error):
    return redirect(url_for('login'))

def status_404(error):
    return "<h1>Página no encontrada</h1>", 404

if __name__ == '__main__':
    app.config.from_object(config['development'])
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run(port=5001)