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

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'docx', 'pdf', 'txt', 'xlsx', 'pptx', 'zip', 'rar'}

# --------------------------------------------------
# Rutas de la aplicación
# --------------------------------------------------

# Root

@app.route('/')
def index():
    crearTablaUsers()
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
    results = cursor.fetchall()
    
    posts = []
    for row in results:
        post = {
            "id": row[0],
            "user_id": row[1],
            "description": row[2],
            "content": row[3],
            "created_at": row[4],
            "updated_at": row[5],
            "user_name": row[6]
        }
        posts.append(post)
    data = {
        "posts": posts
    }
    return render_template('home.html', data=data)

# Users

@app.route('/new_user')
def new_user():
    return render_template('auth/new.html')

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
    else:
        flash('Error Al Editar El Usuario', 'danger')
    return redirect(request.referrer)

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
    user_friend = get_user_friend_by_user_id_and_friend_id(current_user.id, id) if not is_my_profile else None
    friend_status = user_friend["status"] if user_friend else None
    user_friend_id = user_friend["id"] if user_friend else None
    data = {
        'posts':posts,
        'user': ModelUser.get_by_id(con_bd, id),
        'is_my_profile': is_my_profile,
        'friend_status': friend_status,
        'user_friend_id': user_friend_id,
    }
    return render_template('profile.html', data = data)

# Sesión

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
            
            # Loggear al usuario
            logged_user = ModelUser.login(con_bd, email, password)
            login_user(logged_user)
            flash('Usuario Registrado Correctamente', 'info')
            return redirect(url_for('home'))
        except Exception as e:
            flash('Error Al Registrar El Usuario: ' + str(e), 'danger')
    else:
        flash('Error Al Registrar El Usuario', 'danger')
    return redirect(request.referrer)

@app.route('/logout')
def logout():
    logout_user()
    flash("Sesión cerrada correctamente", "success")
    return redirect(url_for('login'))
    
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

# Friends

STATUS_USER_FRIENDS = {'pending': 'Pendiente', 'accepted': 'Aceptado'}

@app.route('/friends')
def friends():
    createUserFriendsTable()
    cursor = con_bd.cursor()
    if not current_user.id:
        flash('Error Al Listar Los Amigos: No Hay Usuario Logueado', 'danger')
        return redirect(request.referrer)
    id = current_user.id
    incoming_requests = []
    try:
        sql_incoming_requests = """
            SELECT user_friends.*, u1.name as user_name, u2.name as friend_name
            FROM user_friends
            JOIN users u1
            ON user_friends.user_id = u1.id
            JOIN users u2
            ON user_friends.friend_id = u2.id
            WHERE user_friends.friend_id = %s AND user_friends.status = 'pending'
            ORDER BY user_friends.id DESC
        """
        cursor.execute(sql_incoming_requests, (id,))
        results = cursor.fetchall()

        for row in results:
            if current_user.id == row[1]:
                user_id = row[1]
                user_name = row[6]
                friend_id = row[2]
                friend_name = row[7]
            else:
                user_id = row[2]
                user_name = row[7]
                friend_id = row[1]
                friend_name = row[6]
            user_friend = {
                "id": row[0],
                "user_id": user_id,
                "friend_id": friend_id,
                "status": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "user_name": user_name,
                "friend_name": friend_name
            }
            incoming_requests.append(user_friend)
    except Exception as e:
        flash('Error Al Listar Los Amigos Con Solicitud Pendiente: ' + str(e), 'danger')
    requests_sent = []
    try:
        sql_requests_sent = """
            SELECT user_friends.*, u1.name as user_name, u2.name as friend_name
            FROM user_friends
            JOIN users u1
            ON user_friends.user_id = u1.id
            JOIN users u2
            ON user_friends.friend_id = u2.id
            WHERE user_friends.user_id = %s AND user_friends.status = 'pending'
            ORDER BY user_friends.id DESC
        """
        cursor.execute(sql_requests_sent, (id,))
        results = cursor.fetchall()

        for row in results:
            if current_user.id == row[1]:
                user_id = row[1]
                user_name = row[6]
                friend_id = row[2]
                friend_name = row[7]
            else:
                user_id = row[2]
                user_name = row[7]
                friend_id = row[1]
                friend_name = row[6]
            user_friend = {
                "id": row[0],
                "user_id": user_id,
                "friend_id": friend_id,
                "status": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "user_name": user_name,
                "friend_name": friend_name
            }
            requests_sent.append(user_friend)
    except Exception as e:
        flash('Error Al Listar Los Amigos Con Solicitud Pendiente: ' + str(e), 'danger')
    list_friends = []
    try:
        sql_list_friends = """
            SELECT user_friends.*, u1.name as user_name, u2.name as friend_name
            FROM user_friends
            JOIN users u1
            ON user_friends.user_id = u1.id
            JOIN users u2
            ON user_friends.friend_id = u2.id
            WHERE (user_friends.user_id = %s OR user_friends.friend_id = %s) AND user_friends.status = 'accepted'
            ORDER BY user_friends.id DESC
        """
        cursor.execute(sql_list_friends, (id,id))
        results = cursor.fetchall()
        for row in results:
            if current_user.id == row[1]:
                user_id = row[1]
                user_name = row[6]
                friend_id = row[2]
                friend_name = row[7]
            else:
                user_id = row[2]
                user_name = row[7]
                friend_id = row[1]
                friend_name = row[6]
            user_friend = {
                "id": row[0],
                "user_id": user_id,
                "friend_id": friend_id,
                "status": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "user_name": user_name,
                "friend_name": friend_name
            }
            list_friends.append(user_friend)
    except Exception as e:
        flash('Error Al Listar Tus Amigos: ' + str(e), 'danger')
    data = {
            "incoming_requests": incoming_requests,
            "requests_sent": requests_sent,
            "list_friends": list_friends
        }
    try:
        return render_template('friends.html', data=data)
    except Exception as e:
        flash('Error Al Renderizar La Vista De Tus Amigos: ' + str(e), 'danger')
    return redirect(request.referrer)

@app.route('/send_friend_request/<int:friend_id>')
def send_friend_request(friend_id):
    createUserFriendsTable()
    
    cursor = con_bd.cursor()
    user_id = current_user.id
    status = 'pending'
    now = datetime.now()

    if user_id == None:
        flash('Error Al Enviar La Solicitud De Amistad: No Hay Usuario Logueado', 'danger')
        return redirect(url_for('home'))
    if friend_id == None:
        flash('Error Al Enviar La Solicitud De Amistad: Usuario no encontrado', 'danger')
        return redirect(url_for('home'))
    user_friend = get_user_friend_by_user_id_and_friend_id(user_id, friend_id)
    if user_friend and user_friend['status'] not in ['pending', 'accepted']:
        flash('Error Al Enviar La Solicitud De Amistad: Ya Existe Una Solicitud De Amistad Entre Los Usuarios', 'danger')
        return redirect(url_for('home'))
    try:
        sql = """
            INSERT INTO user_friends (
                user_id,
                friend_id,
                status,
                created_at
            )
            VALUES
            ( %s, %s, %s, %s);
        """
        cursor.execute(sql,(user_id, friend_id, status, now))
        con_bd.commit()
        flash('Solicitud De Amistad Enviada Correctamente', 'success')
    except Exception as e:
        flash('Error Al Enviar La Solicitud De Amistad: ' + str(e), 'danger')
    return redirect(request.referrer)

@app.route('/accept_friend_request/<int:user_friend_id>')
def accept_friend_request(user_friend_id):
    createUserFriendsTable()
    cursor = con_bd.cursor()
    status = 'accepted'
    now = datetime.now()
    try:
        sql = """
            UPDATE user_friends
            SET status = %s, updated_at = %s
            WHERE id = %s
        """
        cursor.execute(sql, (status, now, user_friend_id))
        con_bd.commit()
        flash('Solicitud De Amistad Aceptada Correctamente', 'success')
    except Exception as e:
        flash('Error Al Aceptar La Solicitud De Amistad: ' + str(e), 'danger')
    return redirect(request.referrer)

@app.route('/delete_friend_request/<int:user_friend_id>')
def delete_friend_request(user_friend_id):
    try:
        cursor = con_bd.cursor()
        sql = """
            DELETE FROM user_friends
            WHERE id = %s
        """
        cursor.execute(sql, (user_friend_id,))
        con_bd.commit()
        flash('Amigo Eliminado Correctamente', 'info')
    except Exception as e:
        flash('Error Al Eliminar El Amigo: ' + str(e), 'danger')
    return redirect(request.referrer)


def get_user_friend_by_user_id_and_friend_id(user_id_1, user_id_2):
    createUserFriendsTable()
    cursor = con_bd.cursor()
    sql = """
        SELECT user_friends.*, u1.name as user_name, u2.name as friend_name
        FROM user_friends
        JOIN users u1
        ON user_friends.user_id = u1.id
        JOIN users u2
        ON user_friends.friend_id = u2.id
        WHERE (user_friends.user_id = %s AND user_friends.friend_id = %s)
        OR (user_friends.user_id = %s AND user_friends.friend_id = %s)
        ORDER BY user_friends.id DESC
    """
    cursor.execute(sql, (user_id_1, user_id_2, user_id_2, user_id_1))
    result = cursor.fetchone()
    if result:
        if current_user.id == result[1]:
            user_id = result[1]
            user_name = result[6]
            friend_id = result[2]
            friend_name = result[7]
        else:
            user_id = result[2]
            user_name = result[7]
            friend_id = result[1]
            friend_name = result[6]
        user_friend = {
            "id": result[0],
            "user_id": user_id,
            "friend_id": friend_id,
            "status": result[3],
            "created_at": result[4],
            "updated_at": result[5],
            "user_name": user_name,
            "friend_name": friend_name
        }
        return user_friend
    else:
        return None

# Academic Files

@app.route('/academic_files')
def academic_files():
    crearTablaUsers()
    createAcademicFileTable()
    if not current_user.id:
        flash('Error Al Listar Los Amigos: No Hay Usuario Logueado', 'danger')
        return redirect(request.referrer)
    cursor = con_bd.cursor()
    all_teachers = []
    try:
        sql_all_teachers = """
            SELECT *
            FROM users
            WHERE type_user = %s
        """
        cursor.execute(sql_all_teachers, ("teacher",))
        results = cursor.fetchall()

        for row in results:
            teacher = {
                "id": row[0],
                "email": row[1],
                # "password": row[2],
                "name": row[3]
                # "type_user": row[4],
                # "created_at": row[5],
                # "updated_at": row[6]
            }
            all_teachers.append(teacher)
    except Exception as e:
        flash('Error Al Listar Los Profesores: ' + str(e), 'danger')
    academic_files = []
    try:
        user_id = current_user.id
        sql_academic_files = """
            SELECT academic_files.*, users.name
            FROM academic_files
            JOIN users
            ON academic_files.teacher_id = users.id
            WHERE academic_files.user_id = %s
            ORDER BY academic_files.id DESC
        """
        cursor.execute(sql_academic_files, (user_id,))
        results = cursor.fetchall()
        for row in results:
            academic_file = {
                "id" : row[0],
                "user_id" : row[1],
                "teacher_id" : row[2],
                "teacher_name" : row[7] if row[7] else None,
                "name" : row[3],
                "content" : row[4],
                "created_at" : row[5],
                "updated_at" : row[6]
            }
            academic_files.append(academic_file)
    except Exception as e:
        flash('Error Al Listar Los Archivos Académicos: ' + str(e), 'danger')
    
    data = {
        "all_teachers": all_teachers,
        "academic_files": academic_files
    }
    try:
        return render_template('academic_files.html', data=data)
    except Exception as e:
        flash('Error Al Renderizar La Vista De Archivos Académicos: ' + str(e), 'danger')
    return redirect(request.referrer)

@app.route('/create_academic_file', methods=['POST'])
def create_academic_file():
    createAcademicFileTable()
    cursor = con_bd.cursor()
    form = request.form
    user_id = current_user.id
    teacher_id = form['teacher_id']
    name = form['name']
    content = request.files['content']
    now = datetime.now()

    if user_id == None:
        flash('Error Al Crear El Archivo Académico: No Hay Usuario Logueado', 'danger')
        return redirect(request.referrer)
    if content:
        filename = secure_filename(content.filename)
        if allowed_file(filename) == False:
            flash('Error Al Crear El Archivo Académico: El Archivo No Es Valido', 'danger')
            return redirect(request.referrer)
        base_path = os.path.dirname(__file__)
        filename_complete = create_filename_complete(filename)
        createUploadsFolder()
        content_route = os.path.join(base_path, app.config['UPLOAD_FOLDER'], filename_complete)
        try:
            content.save(content_route)
        except Exception as e:
            flash('Error Al Guardar El Contenido Del Archivo Académico: ' + str(e), 'danger')
    else:
        filename_complete = ""
    try:
        sql = """
            INSERT INTO
            academic_files (
                user_id,
                teacher_id,
                name,
                content,
                created_at
            )
            VALUES
            ( %s, %s, %s, %s, %s );
        """
        cursor.execute(sql,(user_id, teacher_id, name, filename_complete, now))
        con_bd.commit()
        flash('Archivo Académico Creado Correctamente', 'success')
        return redirect(url_for('academic_files'))
    except Exception as e:
        flash('Error Al Crear El Archivo Académico: ' + str(e), 'danger')
    return redirect(request.referrer)

@app.route('/edit_academic_file/<int:academic_file_id>', methods=['POST'])
def edit_academic_file(academic_file_id):
    createAcademicFileTable()
    cursor = con_bd.cursor()
    form = request.form
    user_id = current_user.id
    teacher_id = form['teacher_id']
    name = form['name']
    content = request.files['content']
    now = datetime.now()

    if user_id == None:
        flash('Error Al Modificar El Archivo Académico: No Hay Usuario Logueado', 'danger')
        return redirect(request.referrer)
    if content:
        filename = secure_filename(content.filename)
        if allowed_file(filename) == False:
            flash('Error Al Modificar El Archivo Académico: El Archivo No Es Valido', 'danger')
            return redirect(request.referrer)
        base_path = os.path.dirname(__file__)
        filename_complete = create_filename_complete(filename)
        createUploadsFolder()
        content_route = os.path.join(base_path, app.config['UPLOAD_FOLDER'], filename_complete)
        try:
            content.save(content_route)
            sql = """
                UPDATE academic_files
                SET teacher_id=%s, name=%s, content=%s, updated_at=%s
                WHERE id = %s
            """
            cursor.execute(sql,(teacher_id, name, filename_complete, now, academic_file_id))
        except Exception as e:
            flash('Error Al Modificar El Archivo Académico: ' + str(e), 'danger')
    else:
        sql = """
            UPDATE academic_files
            SET teacher_id=%s, name=%s, updated_at=%s
            WHERE id = %s
        """
        cursor.execute(sql,(teacher_id, name, now, academic_file_id))
    try:
        con_bd.commit()
        flash('Archivo Académico Modificado Correctamente', 'success')
        return redirect(url_for('academic_files'))
    except Exception as e:
        flash('Error Al Modificar El Archivo Académico: ' + str(e), 'danger')
    return redirect(request.referrer)

@app.route('/eliminar_academic_file/<int:academic_file_id>')
def eliminar_academic_file(academic_file_id):
    try:
        cursor = con_bd.cursor()
        sql = "DELETE FROM academic_files WHERE id = {0}".format(academic_file_id)
        cursor.execute(sql)
        con_bd.commit()
        flash('Archivo Académico Eliminado Correctamente', 'info')
        return redirect(url_for('home'))
    except Exception as e:
        flash('Error Al Eliminar El Archivo Académico: ' + str(e), 'danger')
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
        CREATE TABLE IF NOT EXISTS academic_files(
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

# Errores

def status_401(error):
    return redirect(url_for('login'))

def status_404(error):
    return "<h1>Página no encontrada</h1>", 404

# Iniciar Aplicación

if __name__ == '__main__':
    app.config.from_object(config['development'])
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run(port=5001)
