import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_suspense_key')

# --- 🔌 SUPABASE DATABASE CONNECTION ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables.")

# Initialize the Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


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


# --- 🛣️ ROUTES & CONTROLLERS ---

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
        
        try:
            # Insert into Supabase 'users' table
            data, count = supabase.table("users").insert({
                "username": username,
                "email": email,
                "password": hashed_password,
                "current_level": 1  # Default level for new players
            }).execute()
            
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            # Typically triggers on unique constraint violations (username/email already exists)
            flash('Username or Email already exists!', 'danger')
            
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier'].strip()
        password = request.form['password']
        
        # Query matching username OR email
        response_user = supabase.table("users").select("*").eq("username", identifier).execute()
        if not response_user.data:
            response_user = supabase.table("users").select("*").eq("email", identifier).execute()
            
        if response_user.data:
            user = response_user.data[0]
            if check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('game'))
                
        flash('Invalid credentials.', 'danger')
            
    return render_template('login.html')


@app.route('/game', methods=['GET', 'POST'])
def game():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Fetch current user level from Supabase
    response = supabase.table("users").select("current_level").eq("id", session['user_id']).execute()
    if not response.data:
        session.clear()
        return redirect(url_for('login'))
        
    current_level = response.data[0]['current_level']
    puzzle = generate_puzzle(current_level)
    
    if request.method == 'POST':
        user_answer = request.form.get('answer', '').strip().lower()
        if puzzle and puzzle['answer'] and user_answer == puzzle['answer'].lower():
            current_level += 1
            
            # Update user level in Supabase
            supabase.table("users").update({"current_level": current_level}).eq("id", session['user_id']).execute()
            return redirect(url_for('game'))
        else:
            flash('Incorrect code. The mechanism fails to move...', 'danger')
            
    return render_template('game.html', puzzle=puzzle, level=current_level)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- 🏃‍♂️ EXECUTION ---
if __name__ == '__main__':
    app.run(debug=True)
