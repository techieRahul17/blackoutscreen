// server.js
const express = require("express");
const http = require("http");
const socketio = require("socket.io");

const app = express();
const server = http.createServer(app);
const io = socketio(server);

app.use(express.static("public")); // serve admin.html and assets

let clients = [];

io.on("connection", (socket) => {
    console.log("New connection:", socket.id);

    socket.on("register_client", ({ username, hostname }) => {
        const name = username && username.trim() !== "" ? username : `Anonymous`;

        const clientInfo = {
            id: socket.id,
            username: name,
            hostname: hostname,
            ip: socket.handshake.address.replace("::ffff:", "")
        };

        socket.clientInfo = clientInfo;
        clients.push(clientInfo);

        console.log(`Client connected: ${name} - ${hostname} - ${clientInfo.ip}`);

        socket.emit("your_id", socket.id);
        io.emit("update_players", clients);
    });

    socket.on("disconnect", () => {
        console.log("Disconnected:", socket.id);
        clients = clients.filter(c => c.id !== socket.id);
        io.emit("update_players", clients);
    });

    // blackout events
    socket.on("blackoutAll", (duration) => {
        console.log(`Blackout all for ${duration}ms`);
        for (let [id, s] of io.sockets.sockets) {
            s.emit("blackout", duration);
        }
    });

    socket.on("endBlackoutAll", () => {
        console.log("End blackout all");
        for (let [id, s] of io.sockets.sockets) {
            s.emit("endBlackout");
        }
    });

    socket.on("selectiveBlackout", ({ players, duration }) => {
        console.log(`Selective blackout for ${players}`);
        for (let [id, s] of io.sockets.sockets) {
            if (players.includes(s.clientInfo?.id)) {
                s.emit("blackout", duration);
            }
        }
    });

    socket.on("selectiveEndBlackout", ({ players }) => {
        console.log(`Selective end blackout for ${players}`);
        for (let [id, s] of io.sockets.sockets) {
            if (players.includes(s.clientInfo?.id)) {
                s.emit("endBlackout");
            }
        }
    });

    socket.on("register_admin", () => {
        socket.isAdmin = true;
        socket.emit("update_players", clients);
    });
});

server.listen(3000, "0.0.0.0", () => {
    console.log("Server running on http://0.0.0.0:3000");
});
