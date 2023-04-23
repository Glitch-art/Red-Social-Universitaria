from flask import Flask, render_template, request, redirect, url_for, flash
from config import *
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from datetime import datetime
from werkzeug.utils import secure_filename
import os

from models.ModelUser import ModelUser
from models.entities.User import User

app = Flask(__name__)

con_bd = EstablecerConexion()

login_manager_app = LoginManager(app)

@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(con_bd, id)

# Constantes

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif' 'mp4'}

# --------------------------------------------------
# Rutas de la aplicación
# --------------------------------------------------

# Root

@app.route('/')
def index():
    crearTablaUsers()
    crearTablaProductos()
    return redirect(url_for('login'))

# Home

@app.route('/home')
@login_required
def home():
    cursor = con_bd.cursor()
    sql = """
        SELECT posts.*, users.name
        FROM posts
        JOIN users
        ON posts.user_id = users.id
        ORDER BY posts.id DESC
    """
    cursor.execute(sql)
    posts = cursor.fetchall()
    data = {
        "posts": posts
    }
    return render_template('home.html', data=data)

# Users

@app.route('/login', methods=['GET', 'POST'])
def login():
    crearTablaUsers()
    if request.method == 'POST':
        # print(request.form['email'])
        # print(request.form['password'])
        email = request.form['email']
        password = request.form['password']
        logged_user = ModelUser.login(con_bd, email, password)
        if logged_user != None:
            if logged_user.password:
                login_user(logged_user)
                flash(f"Bienvenido, {current_user.name}!", "success")
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
    name = form['name']
    type_user = form['type_user']
    now = datetime.now()
    if email and password and name and type_user:
        try:
            sql = """
                INSERT INTO
                users (
                    email,
                    password,
                    name,
                    type_user,
                    created_at
                )
                VALUES
                ( %s, %s, %s, %s, %s);
            """
            cursor.execute(sql,(email, password, name, type_user, now))
            con_bd.commit()
            flash('Usuario Registrado Correctamente', 'info')
            return redirect(url_for('index'))
        except Exception as e:
            flash('Error Al Registrar El Usuario: ' + str(e), 'danger')
    else:
        flash('Error Al Registrar El Usuario', 'danger')
    return redirect(request.referrer)

@app.route('/editar_user/<int:id>')
def editar_user(id):
    cursor = con_bd.cursor()
    form = request.form
    email = form['email']
    password = User.passwordHash(form['password'])
    name = form['name']
    type_user = form['type_user']
    now = datetime.now()
    if email and password and name and type_user:
        sql = """
            UPDATE users
            SET email = %s, password = %s, name = %s, type_user = %s, updated_at = %s
            WHERE id = %s
        """
        cursor.execute(sql, (email, password, name, type_user, now, id))
        con_bd.commit()
        flash('Usuario Editado Correctamente', 'info')
        return redirect(url_for('home'))
    else:
        flash('Error Al Editar El Usuario', 'danger')
    return redirect(request.referrer)


@app.route('/logout')
def logout():
    logout_user()
    flash("Sesión cerrada correctamente", "success")
    return redirect(url_for('login'))

@app.route('/profile/<int:id>')
@login_required
def profile(id):
    createPostsTable()
    cursor = con_bd.cursor()
    sql = """
        SELECT posts.*, users.name 
        FROM posts 
        JOIN users 
        ON posts.user_id = users.id 
        WHERE posts.user_id = %s 
        ORDER BY posts.id DESC
    """
    cursor.execute(sql, (id,))
    posts = cursor.fetchall()
    
    is_my_profile = id == current_user.id
    data = {
        'posts':posts,
        'is_my_profile': is_my_profile,
        'user': ModelUser.get_by_id(con_bd, id),
    }
    return render_template('profile.html', data = data)
    
# Posts

@app.route('/create_post', methods=['POST'])
def create_post():
    createPostsTable()
    cursor = con_bd.cursor()
    form = request.form
    description = form['description']
    content = request.files['content']
    user_id = current_user.id
    now = datetime.now()

    if user_id == None:
        flash('Error Al Crear El Post: No Hay Usuario Logueado', 'danger')
        return redirect(request.referrer)
    if content:
        filename = secure_filename(content.filename)
        if allowed_file(filename) == False:
            flash('Error Al Crear El Post: El Archivo No Es Valido', 'danger')
            return redirect(request.referrer)
        base_path = os.path.dirname(__file__)
        filename_complete = create_filename_complete(filename)
        createUploadsFolder()
        content_route = os.path.join(base_path, app.config['UPLOAD_FOLDER'], filename_complete)
        try:
            content.save(content_route)
        except Exception as e:
            flash('Error Al Crear El Post: ' + str(e), 'danger')
    else:
        filename_complete = ""
    try:
        sql = """
            INSERT INTO
            posts (
                user_id,
                description,
                content,
                created_at
            )
            VALUES
            ( %s, %s, %s, %s);
        """
        cursor.execute(sql,(user_id, description, filename_complete, now))
        con_bd.commit()
        flash('Post Creado Correctamente', 'success')
        return redirect(url_for('home'))
    except Exception as e:
        flash('Error Al Crear El Post: ' + str(e), 'danger')
    return redirect(request.referrer)

def create_filename_complete(filename):
    now = datetime.now()
    short_date = now.strftime("%Y%m%d")
    filename_complete = f"{short_date}_{str(current_user.id)}_{filename}"
    return filename_complete

def allowed_file(file):
    file = file.split('.')
    if file[1] in ALLOWED_EXTENSIONS:
        return True
    return False

def createUploadsFolder():
    base_path = os.path.dirname(__file__)
    uploads_folder = os.path.join(base_path, app.config['UPLOAD_FOLDER'])
    if not os.path.exists(uploads_folder):
        os.makedirs(uploads_folder)

@app.route('/edit_post/<int:id>', methods=['POST'])
def edit_post(id):
    cursor = con_bd.cursor()
    form = request.form
    description = form['description']
    content = request.files['content']
    now = datetime.now()

    if not current_user.id:
        flash('Error Al Modificar El Post: No Hay Usuario Logueado', 'danger')
        return redirect(request.referrer)
    if content:
        filename = secure_filename(content.filename)
        if allowed_file(filename) == False:
            flash('Error Al Modificar El Post: El Archivo No Es Valido', 'danger')
            return redirect(request.referrer)
        base_path = os.path.dirname(__file__)
        filename_complete = create_filename_complete(filename)
        createUploadsFolder()
        content_route = os.path.join(base_path, app.config['UPLOAD_FOLDER'], filename_complete)
        try:
            content.save(content_route)
            sql = """
                UPDATE posts
                SET description=%s, content=%s, updated_at=%s
                WHERE id = %s
            """
            cursor.execute(sql,(description, filename_complete, now, id))
        except Exception as e:
            flash('Error Al Modificar El Post: ' + str(e), 'danger')
    else:
        #TODO
        sql = """
            UPDATE posts
            SET description=%s, updated_at=%s
            WHERE id = %s
        """
        cursor.execute(sql,(description, now, id))
    try:
        con_bd.commit()
        flash('Post Modificado Correctamente', 'success')
        return redirect(url_for('home'))
    except Exception as e:
        flash('Error Al Modificar El Post: ' + str(e), 'danger')
    return redirect(request.referrer)

@app.route('/eliminar_post/<int:id>')
def eliminar_post(id):
    try:
        cursor = con_bd.cursor()
        sql = "DELETE FROM posts WHERE id = {0}".format(id)
        cursor.execute(sql)
        con_bd.commit()
        flash('Post Eliminado Correctamente', 'info')
        return redirect(url_for('home'))
    except Exception as e:
        flash('Error Al Eliminar El Post: ' + str(e), 'danger')
        return request.referrer

# Crear Tablas

def crearTablaUsers():
    cursor = con_bd.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users(
        id serial NOT NULL,
        email character varying(255) NOT NULL,
        password character varying(255) NOT NULL,
        name character varying(255) NOT NULL,
        type_user character varying(255) NOT NULL,
        created_at timestamp without time zone,
        updated_at timestamp without time zone,
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

def createUserFriendsTable():
    cursor = con_bd.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_friends(
        id serial NOT NULL,
        user_id integer NOT NULL,
        friend_id integer NOT NULL,
        status character varying(255) NOT NULL,
        created_at timestamp without time zone,
        updated_at timestamp without time zone,
        CONSTRAINT pk_user_friends_id PRIMARY KEY (id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (friend_id) REFERENCES users(id)
        );
    ''')
    con_bd.commit()

def createPostsTable():
    cursor = con_bd.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts(
        id serial NOT NULL,
        user_id integer NOT NULL,
        description text,
        content text,
        created_at timestamp without time zone,
        updated_at timestamp without time zone,
        CONSTRAINT pk_posts_id PRIMARY KEY (id),
        FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')
    con_bd.commit()

def createAcademicFileTable():
    cursor = con_bd.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS academic_file(
        id serial NOT NULL,
        user_id integer NOT NULL,
        teacher_id integer NOT NULL,
        name character varying(255),
        content text,
        created_at timestamp without time zone,
        updated_at timestamp without time zone,
        CONSTRAINT pk_academic_file_id PRIMARY KEY (id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (teacher_id) REFERENCES users(id)
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