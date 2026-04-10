# Guess Me If You Can - Multiplayer

A real-time 2-player turn-based multiplayer number guessing game built with Flask-SocketIO.

## Game Rules

- 4-digit secret number
- No leading zero, no repeated digits, no ascending consecutive adjacent digits (7→8 blocked, 8→7 fine)
- Per-digit feedback: `correct` (right spot), `exists` (wrong spot), `none` (not in number)
- Each player gets a different private secret number
- Turn-based gameplay with max 8 attempts per player
- First player to get all 4 digits correct wins

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the development server:
```bash
python app.py
```

3. Open http://127.0.0.1:5000 in your browser

## Deployment on Render.com

### Option 1: Using GitHub (Recommended)

1. **Push to GitHub**:
```bash
git init
git add .
git commit -m "Initial commit: multiplayer Guess Me If You Can"
git branch -M main
git remote add origin https://github.com/yourusername/guess-me-if-you-can.git
git push -u origin main
```

2. **Deploy on Render**:
   - Go to [Render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will automatically detect the Python configuration from `render.yaml`
   - Click "Create Web Service"

### Option 2: Direct Upload

1. **Create a ZIP file** of the entire project folder
2. Go to [Render.com](https://render.com)
3. Click "New +" → "Web Service" → "Upload a ZIP file"
4. Upload your ZIP file
5. Render will use the configuration from `render.yaml`

### Configuration Details

The deployment is configured through:
- `Procfile`: Specifies the Gunicorn command with threading worker
- `render.yaml`: Render blueprint with Python 3.11 environment
- `requirements.txt`: Python dependencies including Flask-SocketIO

## File Structure

```
GuessTheNumber/
├── game.py          # Core game logic (unchanged)
├── rooms.py         # In-memory room management
├── app.py           # Flask-SocketIO server
├── requirements.txt # Python dependencies
├── Procfile         # Heroku-style process definition
├── render.yaml      # Render deployment blueprint
├── README.md        # This file
└── templates/
    └── index.html   # Multiplayer UI with 4 screens
```

## Features

- **4-Single-Page App**: Home → Lobby → Game → End
- **Real-time multiplayer**: Turn-based gameplay with Socket.IO
- **Wordle-style UI**: Tile flip animations and color feedback
- **Mobile-first**: Responsive design optimized for mobile devices
- **Room system**: 4-character room codes with copy-to-clipboard
- **Progress tracking**: Visual progress bars for both players
- **Win conditions**: Win, draw, or forfeit (disconnect handling)

## Socket Events

### Client → Server
- `create_room` `{ nickname }`
- `join_room` `{ code, nickname }`
- `make_guess` `{ guess }`
- `leave_game` `{}`

### Server → Client
- `room_created` `{ code, your_sid }`
- `join_success` `{ code, your_sid }`
- `join_error` `{ message }`
- `state_update` `{ game state }`
- `guess_feedback` `{ feedback }`
- `game_over` `{ winner, secrets }`
- `opponent_left` `{}`

## Tech Stack

- **Backend**: Flask + Flask-SocketIO
- **Frontend**: Vanilla JavaScript + Socket.IO client
- **Styling**: Custom CSS with Inter and Bungee fonts
- **Deployment**: Render.com (free tier compatible)
