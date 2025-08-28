const express = require("express");
const http = require("http");
const { Server } = require("socket.io");

const app = express();
const server = http.createServer(app);
const io = new Server(server);

app.use(express.static("public")); // serve admin.html + assets

let playerCounter = 1;

io.on("connection", (socket) => {
    const player_id = `player${playerCounter++}`;
    socket.player_id = player_id;

    // store hostname when client registers
    socket.on("register_client", ({ hostname }) => {
        socket.hostname = hostname;
        socket.ip = socket.handshake.address.replace("::ffff:", "");
        console.log(`Player ${player_id} connected: ${hostname}, IP: ${socket.ip}`);
        io.emit("update_players", getAllPlayers());
        socket.emit("your_id", player_id); // send player ID to client
    });

    socket.on("disconnect", () => {
        console.log(`Player ${player_id} disconnected`);
        io.emit("update_players", getAllPlayers());
    });

    // selective blackout
    socket.on("selectiveBlackout", ({ players, duration }) => {
        console.log(`Selective blackout for ${players} for ${duration}ms`);
        blackoutSelected(players, duration);
    });

    // blackout all
    socket.on("blackoutAll", (duration) => {
        console.log(`Blackout all clients for ${duration}ms`);
        blackoutAll(duration);
    });

    // selective end blackout
    socket.on("selectiveEndBlackout", ({ players }) => {
        console.log(`End blackout for ${players}`);
        endBlackoutSelected(players);
    });

    // end blackout for all
    socket.on("endBlackoutAll", () => {
        console.log("End blackout for all clients");
        endBlackoutAll();
    });
});

// helper functions
function getAllPlayers() {
    const players = [];
    for (let [id, socket] of io.sockets.sockets) {
        players.push({
            id: socket.player_id,
            hostname: socket.hostname || "unknown",
            ip: socket.ip || "unknown"
        });
    }
    return players;
}

function blackoutSelected(players, duration) {
    for (let [id, socket] of io.sockets.sockets) {
        if (players.includes(socket.player_id)) {
            socket.emit("blackout", duration);
        }
    }
}

function endBlackoutSelected(players) {
    for (let [id, socket] of io.sockets.sockets) {
        if (players.includes(socket.player_id)) {
            socket.emit("endBlackout");
        }
    }
}

function blackoutAll(duration) {
    for (let [id, socket] of io.sockets.sockets) {
        socket.emit("blackout", duration);
    }
}

function endBlackoutAll() {
    for (let [id, socket] of io.sockets.sockets) {
        socket.emit("endBlackout");
    }
}

server.listen(3000, "0.0.0.0", () => {
    console.log("Server running on http://0.0.0.0:3000");
});
