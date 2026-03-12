from flask import Flask, abort, flash, redirect, render_template, request, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

app = Flask(__name__)
app.secret_key = 'pepeshnelyawatafa1488'
DB_PATH = "cybersport_final.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# === Главная ===
@app.route('/')
def index():
    return render_template('index.html')

# === Игроки ===
@app.route('/players')
def players():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.nickname, p.rating_2_0, p.kpr, p.adr, t.name AS team_name
            FROM players p
            LEFT JOIN teams t ON p.team_id = t.id
        """)
        players = cur.fetchall()
        cur.close()
    return render_template('players.html', players=players)

# === Команды ===
@app.route('/teams')
def teams():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, country FROM teams")
        teams = cur.fetchall()
        cur.close()
    return render_template('teams.html', teams=teams)

# === Страница конкретной команды ===
@app.route('/team/<int:team_id>')
def team_detail(team_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, country FROM teams WHERE id=?", (team_id,))
        team = cur.fetchone()

        cur.execute("""
            SELECT nickname, position, rating, kpr, adr
            FROM players
            WHERE team_id=?
        """, (team_id,))
        players = cur.fetchall()
        cur.close()

    if not team:
        return render_template('error.html', message="Команда не найдена")
    return render_template('team_detail.html', team=team, players=players)

# === Турниры ===
@app.route('/tournaments')
def tournaments():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, location, year, prize_money
            FROM tournaments ORDER BY year DESC
        """)
        tournaments = cur.fetchall()
        cur.close()
    return render_template('tournaments.html', tournaments=tournaments)

# === Страница конкретного турнира ===
@app.route('/tournament/<int:tournament_id>')
def tournament_detail(tournament_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, location, year, prize_money
            FROM tournaments WHERE id=?
        """, (tournament_id,))
        tournament = cur.fetchone()

        cur.execute("""
            SELECT t.name AS team_name, tt.placement
            FROM tournament_teams tt
            JOIN teams t ON tt.team_id = t.id
            WHERE tt.tournament_id=?
            ORDER BY tt.placement ASC
        """, (tournament_id,))
        results = cur.fetchall()
        cur.close()

    if not tournament:
        return render_template('error.html', message="Турнир не найден")
    return render_template('tournament_detail.html', tournament=tournament, results=results)
#Админская часть
@app.route('/admin/')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        abort(403)
    return render_template('admin_dashboard.html')

@app.route('/admin/players')
def admin_players():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM players")
        players = cur.fetchall()
        cur.close()
    return render_template('admin_players.html', players=players)

@app.route('/admin/edit_player/<int:id>', methods=['GET', 'POST'])
def edit_player(id):
    if request.method == 'POST':
        nickname = request.form['nickname']
        rating = float(request.form['rating'])
        
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE players SET nickname=?, rating=? WHERE id=?", (nickname, rating, id))
            conn.commit()
            
        flash(f'Игрок {nickname} успешно обновлен!', category='success')
        return redirect(url_for('admin_players'))
    
    else:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM players WHERE id=?", (id,))
            player = cur.fetchone()
            cur.close()
        return render_template('edit_player.html', player=player)
    
@app.route('/admin/delete_player/<int:id>', methods=['POST'])
def delete_player(id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM players WHERE id=?", (id,))
        conn.commit()
    flash('Игрок удалён.', category='warning')
    return redirect(url_for('admin_players'))

@app.route('/admin/add_player', methods=['GET', 'POST'])
def add_player():
    if request.method == 'POST':
        nickname = request.form['nickname']
        rating = float(request.form['rating'])
        
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO players(nickname, rating) VALUES(?, ?)", (nickname, rating))
            conn.commit()
            
        flash(f'Игрок {nickname} успешно добавлен!', category='success')
        return redirect(url_for('admin_players'))
    
    return render_template('add_player.html')
#Авторизация
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id, username, role):
        self.id = user_id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return User(row['id'], row['username'], row['role'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)
        
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users WHERE username=?", (username,))
            count = cur.fetchone()[0]
            if count > 0:
                flash('Пользователь с таким именем уже зарегистрирован.', category='danger')
                return render_template('register.html')
                
            cur.execute("INSERT INTO users(username, password_hash) VALUES(?, ?)",
                        (username, hashed_password))
            conn.commit()
        
        flash('Вы зарегистрированы!', category='success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=?", (username,))
            user_row = cur.fetchone()
            if user_row and check_password_hash(user_row['password_hash'], password):
                user = User(user_row['id'], user_row['username'], user_row['role'])
                login_user(user)
                next_url = request.args.get('next') or '/'
                return redirect(next_url)
            else:
                flash('Ошибка ввода имени пользователя или пароля.', category='danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# === Ошибка ===
@app.route('/error')
def error_page():
    return render_template('error.html', message="Страница не найдена")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
