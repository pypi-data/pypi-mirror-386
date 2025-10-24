#!/bin/bash

# Check if exactly 1 argument is provided
if [ $# -ne 1 ]; then
    echo "Usage: mern <name-app>"
    exit 1
fi

APP_NAME=$1

# Create app directory
mkdir "$APP_NAME"
cd "$APP_NAME" || exit

# Create backend folder and initialize
mkdir backend
cd backend || exit
npm init -y
npm install express mongoose dotenv cors

# Add 'module' to package.json
cat <<EOF > package.json
{
  "name": "backend",
  "version": "1.0.0",
  "description": "",
  "main": "index.js",
  "type": "module",
  "scripts": {
    "test": "echo \"Error: no test specified\" && exit 1"
  },
  "keywords": [],
  "author": "",
  "license": "ISC",
  "dependencies": {
    "cors": "^2.8.5",
    "dotenv": "^17.2.3",
    "express": "^5.1.0",
    "mongoose": "^8.19.2"
  }
}
EOF

# Create simple Express server
cat <<EOF > server.js
import express from 'express';
import mongoose from 'mongoose';
import cors from 'cors';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

app.get('/', (req, res) => {
  res.send('Hello from backend!');
});

mongoose.connect(process.env.MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => console.log('MongoDB connected'))
.catch(err => console.log(err));

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(\`Server running on port \${PORT}\`));
EOF

# Create .env
cat <<EOF > .env
MONGO_URI=mongodb://localhost:27017/mern-app
PORT=5000
EOF

# Go back to root
cd ../

# Create React frontend
npx create-react-app frontend

# Configure frontend
cd frontend/src
cat <<EOF > App.jsx
import { useEffect, useState } from 'react';

function App() {
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetch('http://localhost:5000/')
      .then(res => res.text())
      .then(data => setMessage(data));
  }, []);

  return (
    <div>
      <h1>{message}</h1>
    </div>
  );
}

export default App;
EOF

echo "MERN app '$APP_NAME' scaffolded successfully!"

# ------------------------------
# Start backend and frontend
# ------------------------------

# Start backend in background
cd "../../backend" || exit
node server.js &
BACKEND_PID=$!
xdg-open http://localhost:5000


# Start frontend in foreground on a free port
cd "../frontend" || exit

find_free_port() {
  local PORT=3000
  while lsof -i:"$PORT" >/dev/null 2>&1; do
    PORT=$((PORT + 1))
  done
  echo "$PORT"
}

FREE_PORT=$(find_free_port)
echo "Starting frontend on port $FREE_PORT..."

PORT=$FREE_PORT npm start

# Kill backend when frontend stops
kill $BACKEND_PID

