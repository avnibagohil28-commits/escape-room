import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_suspense_key'

# Change this line in app.py to use Render's persistent disk path
DATABASE = os.environ.get('DISK_PATH', '') + '/data/database.db' if os.environ.get('RENDER') else 'database.db'

# --- 🚀 AUTOMATED 50-LEVEL PUZZLE ENGINE ---
def generate_puzzle(level):
    """Dynamically generates 50 distinct aesthetic mystery rooms and puzzles."""
    if level > 50:
        return {
            "story": "The final heavy iron door swings open. A soft breeze hits your face. You have completely beaten the labyrinth.",
            "clue": "Congratulations! You successfully escaped all 50 rooms!",
            "answer": None
        }
    
    # Mathematical progression locks
    if level % 3 == 1:
        base_num = 3 * level + 2
        diff = 2 + (level // 5)
        sequence = [base_num, base_num + diff, base_num + (diff * 2)]
        ans = str(base_num + (diff * 3))
        
        return {
            "story": f"You step into Sector {level}. A brass sequence lock bars the exit. Mechanical gears click behind the wall as three numbers glow softly.",
            "clue": f"The pattern reads: {sequence[0]}, {sequence[1]}, {sequence[2]}, [?]",
            "answer": ans
        }
        
    # Cipher / Codebreaker levels
    elif level % 3 == 2:
        words_pool = ["lock", "key", "door", "gate", "room", "pass", "code", "find", "open", "seek"]
        target_word = words_pool[level % len(words_pool)]
        # Simple shift cipher text
        scrambled = "".join(chr(ord(c) + 1) for c in target_word)
        
        return {
            "story": f"Vault Room {level} is dead silent. A sleek stone pedestal rises from the floor holding an elegant keyboard template. An inscription demands a decrypted phrase.",
            "clue": f"Shift each letter backward by 1 position to decipher the key: '{scrambled}'",
            "answer": target_word
        }
        
    # Logic Riddles & Classic Chamber locks
    else:
        riddles = [
            ("What has hands but cannot clap?", "clock"),
            ("The more of them you take, the more you leave behind.", "footsteps"),
            ("What can travel around the world while staying in a corner?", "stamp"),
            ("I speak without a mouth and hear without ears.", "echo"),
            ("What goes up but never comes down?", "age"),
            ("If you drop me I'm sure to crack, but give me a smile and I'll smile back.", "mirror"),
            ("What has keys but can't open a single lock?", "piano"),
            ("The person who makes it has no need of it; the person who buys it has no use for it. What is it?", "coffin")
        ]
        riddle_story, riddle_ans = riddles[level % len(riddles)]
        
        return {
            "story": f"Chamber {level} features a massive iron mirror. An archaic text fades into the glass surface, asking you a silent question.",
            "clue": f"Riddle: {riddle_story}",
            "answer": riddle_ans
        }

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.before_request
def init_db():
    if not os.path.exists(DATABASE):
        conn = get_db_connection()
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        conn.close()

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('game'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, hashed_password))
            conn.commit()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or Email already exists!', 'danger')
        finally:
            conn.close()
            
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier'].strip()
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', (identifier, identifier)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('game'))
        else:
            flash('Invalid credentials.', 'danger')
            
    return render_template('login.html')

@app.route('/game', methods=['GET', 'POST'])
def game():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT current_level FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    current_level = user['current_level']
    
    # Generate the room logic programmatically
    puzzle = generate_puzzle(current_level)
    
    if request.method == 'POST':
        user_answer = request.form.get('answer', '').strip().lower()
        if puzzle and puzzle['answer'] and user_answer == puzzle['answer'].lower():
            current_level += 1
            conn.execute('UPDATE users SET current_level = ? WHERE id = ?', (current_level, session['user_id']))
            conn.commit()
            conn.close()
            return redirect(url_for('game'))
        else:
            flash('Incorrect code. The mechanism fails to move...', 'danger')
            
    conn.close()
    return render_template('game.html', puzzle=puzzle, level=current_level)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)