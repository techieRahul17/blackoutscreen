// server.js
const express = require("express");
const http = require("http");
const socketio = require("socket.io");

const app = express();
const server = http.createServer(app);
const io = socketio(server);

// serve admin.html and assets
app.use(express.static("public"));

let playerCounter = 1;

// helper: only include registered players
function getAllPlayers() {
    const players = [];
    for (let [id, socket] of io.sockets.sockets) {
        if (socket.player_id && socket.hostname && socket.ip) {
            players.push({
                id: socket.player_id,
                hostname: socket.hostname,
                ip: socket.ip
            });
        }
    }
    return players;
}

io.on("connection", (socket) => {
    console.log("New connection:", socket.id);

    // register client
    socket.on("register_client", ({ hostname }) => {
        socket.player_id = `player${playerCounter++}`;
        socket.hostname = hostname;
        socket.ip = socket.handshake.address.replace("::ffff:", "");

        console.log(`Player ${socket.player_id} connected: ${hostname}, IP: ${socket.ip}`);
        socket.emit("your_id", socket.player_id);
        io.emit("update_players", getAllPlayers());
    });

    socket.on("disconnect", () => {
        console.log(`Player disconnected: ${socket.player_id || socket.id}`);
        io.emit("update_players", getAllPlayers());
    });

    // Selective blackout
    socket.on("selectiveBlackout", ({ players, duration }) => {
        console.log(`Selective blackout for ${players} for ${duration}ms`);
        for (let [id, s] of io.sockets.sockets) {
            if (players.includes(s.player_id)) {
                s.emit("blackout", duration);
            }
        }
    });

    // Blackout all
    socket.on("blackoutAll", (duration) => {
        console.log(`Blackout all clients for ${duration}ms`);
        for (let [id, s] of io.sockets.sockets) {
            s.emit("blackout", duration);
        }
    });

    socket.on("register_admin", () => {
        socket.isAdmin = true;
        console.log("Admin connected:", socket.id);
        // Always send current players, even if empty
        socket.emit("update_players", getAllPlayers());
    });

    // End selective blackout
    socket.on("selectiveEndBlackout", ({ players }) => {
        console.log(`End selective blackout for ${players}`);
        for (let [id, s] of io.sockets.sockets) {
            if (players.includes(s.player_id)) {
                s.emit("endBlackout");
            }
        }
    });

    // End blackout all
    socket.on("endBlackoutAll", () => {
        console.log("End blackout all clients");
        for (let [id, s] of io.sockets.sockets) {
            s.emit("endBlackout");
        }
    });
});

server.listen(3000, "0.0.0.0", () => {
    console.log("Server running on http://0.0.0.0:3000");
});
