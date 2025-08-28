const express = require("express");
const http = require("http");
const { Server } = require("socket.io");

const app = express();
const server = http.createServer(app);
const io = new Server(server);

app.use(express.static("public")); // serve static files

io.on("connection", (socket) => {
  console.log("User connected:", socket.id);

  socket.on("blackout", (duration) => {
    console.log(`Blackout for ${duration}ms triggered by admin`);
    io.emit("blackout", duration); // send to all clients
  });

  socket.on("endBlackout", () => {
    console.log("End blackout triggered by admin");
    io.emit("endBlackout");
  });
});

server.listen(3000, () => {
  console.log("Server running on http://localhost:3000");
});
