#!/usr/bin/env node
// -*- coding: utf-8 -*-

/**
 * AI CLI IPC Server
 * Central communication hub for all AI CLI instances
 */

const net = require('net');
const fs = require('fs');
const path = require('path');
const { EventEmitter } = require('events');

class IPCServer extends EventEmitter {
    constructor(options = {}) {
        super();
        this.port = options.port || 7777;
        this.host = options.host || '127.0.0.1';
        this.socketPath = options.socketPath || '\\\\.\\pipe\\ai-cli-ipc';
        this.clients = new Map();
        this.messages = [];
        this.maxMessages = 1000;
        this.stateFile = 'D:\\.ai-cli-ipc\\shared\\state.json';
        this.server = null;

        // UTF-8 encoding
        this.encoding = 'utf8';

        this.loadState();
    }

    // Load shared state
    loadState() {
        try {
            if (fs.existsSync(this.stateFile)) {
                const data = fs.readFileSync(this.stateFile, this.encoding);
                this.sharedState = JSON.parse(data);
            } else {
                this.sharedState = {
                    registry: {},
                    environment: {},
                    history: [],
                    sessions: {}
                };
            }
        } catch (error) {
            console.error('Failed to load state:', error);
            this.sharedState = {};
        }
    }

    // Save shared state
    saveState() {
        try {
            const dir = path.dirname(this.stateFile);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            fs.writeFileSync(
                this.stateFile,
                JSON.stringify(this.sharedState, null, 2),
                this.encoding
            );
        } catch (error) {
            console.error('Failed to save state:', error);
        }
    }

    // Start IPC server
    start() {
        // Windows Named Pipe
        this.server = net.createServer((socket) => {
            const clientId = `cli-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

            // Set UTF-8 encoding
            socket.setEncoding(this.encoding);

            console.log(`Client connected: ${clientId}`);
            this.clients.set(clientId, {
                socket,
                type: 'unknown',
                connected: Date.now()
            });

            socket.on('data', (data) => {
                this.handleMessage(clientId, data);
            });

            socket.on('error', (error) => {
                console.error(`Client ${clientId} error:`, error.message);
            });

            socket.on('close', () => {
                console.log(`Client disconnected: ${clientId}`);
                this.clients.delete(clientId);
            });
        });

        // Try Windows Named Pipe first
        this.server.listen(this.socketPath, () => {
            console.log(`IPC Server listening on: ${this.socketPath}`);
            console.log('Ready for AI CLI connections...');
        });

        // Fallback to TCP if pipe fails
        this.server.on('error', (error) => {
            if (error.code === 'EADDRINUSE' || error.code === 'EACCES') {
                console.log('Named pipe unavailable, falling back to TCP...');
                this.server = net.createServer((socket) => {
                    this.handleTcpConnection(socket);
                });
                this.server.listen(this.port, this.host, () => {
                    console.log(`IPC Server listening on: ${this.host}:${this.port}`);
                });
            }
        });

        // Graceful shutdown
        process.on('SIGINT', () => {
            console.log('\nShutting down IPC server...');
            this.saveState();
            this.server.close();
            process.exit(0);
        });
    }

    // Handle TCP connections
    handleTcpConnection(socket) {
        const clientId = `cli-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        // Set UTF-8 encoding
        socket.setEncoding(this.encoding);

        console.log(`TCP Client connected: ${clientId}`);
        this.clients.set(clientId, {
            socket,
            type: 'unknown',
            connected: Date.now()
        });

        socket.on('data', (data) => {
            this.handleMessage(clientId, data);
        });

        socket.on('close', () => {
            console.log(`TCP Client disconnected: ${clientId}`);
            this.clients.delete(clientId);
        });
    }

    // Handle incoming messages
    handleMessage(clientId, data) {
        try {
            const message = JSON.parse(data.toString(this.encoding));
            const client = this.clients.get(clientId);

            console.log(`Message from ${clientId}:`, message.type);

            switch (message.type) {
                case 'register':
                    this.registerClient(clientId, message);
                    break;

                case 'broadcast':
                    this.broadcastMessage(clientId, message);
                    break;

                case 'query':
                    this.handleQuery(clientId, message);
                    break;

                case 'execute':
                    this.handleExecute(clientId, message);
                    break;

                case 'sync':
                    this.syncState(clientId);
                    break;

                default:
                    this.sendToClient(clientId, {
                        type: 'error',
                        message: 'Unknown message type'
                    });
            }
        } catch (error) {
            console.error('Message handling error:', error);
            this.sendToClient(clientId, {
                type: 'error',
                message: error.message
            });
        }
    }

    // Register client
    registerClient(clientId, message) {
        const client = this.clients.get(clientId);
        if (client) {
            client.type = message.cliType || 'unknown';
            client.name = message.name || clientId;

            // Update registry
            this.sharedState.registry[client.name] = {
                type: client.type,
                connected: client.connected,
                capabilities: message.capabilities || []
            };

            this.saveState();

            this.sendToClient(clientId, {
                type: 'registered',
                clientId,
                state: this.sharedState
            });
        }
    }

    // Broadcast message to all clients
    broadcastMessage(senderId, message) {
        const broadcast = {
            type: 'broadcast',
            from: senderId,
            data: message.data,
            timestamp: Date.now()
        };

        this.clients.forEach((client, clientId) => {
            if (clientId !== senderId) {
                this.sendToClient(clientId, broadcast);
            }
        });

        // Save to history
        this.messages.push(broadcast);
        if (this.messages.length > this.maxMessages) {
            this.messages.shift();
        }
    }

    // Handle query requests
    handleQuery(clientId, message) {
        let response;

        switch (message.query) {
            case 'clients':
                response = Array.from(this.clients.keys()).map(id => ({
                    id,
                    ...this.clients.get(id)
                }));
                break;

            case 'state':
                response = this.sharedState;
                break;

            case 'messages':
                response = this.messages.slice(-50); // Last 50 messages
                break;

            default:
                response = null;
        }

        this.sendToClient(clientId, {
            type: 'query-response',
            query: message.query,
            data: response
        });
    }

    // Handle execute requests (cross-CLI execution)
    handleExecute(clientId, message) {
        const targetClient = message.target;
        const command = message.command;

        if (targetClient && this.clients.has(targetClient)) {
            // Forward execution request to target
            this.sendToClient(targetClient, {
                type: 'execute-request',
                from: clientId,
                command
            });
        } else {
            // Execute locally or broadcast
            this.broadcastMessage(clientId, {
                type: 'execute-broadcast',
                command
            });
        }
    }

    // Sync state with client
    syncState(clientId) {
        this.sendToClient(clientId, {
            type: 'state-sync',
            state: this.sharedState,
            clients: Array.from(this.clients.keys())
        });
    }

    // Send message to specific client
    sendToClient(clientId, message) {
        const client = this.clients.get(clientId);
        if (client && client.socket) {
            try {
                const data = JSON.stringify(message);
                client.socket.write(data + '\n', this.encoding);
            } catch (error) {
                console.error(`Failed to send to ${clientId}:`, error);
            }
        }
    }
}

// Start server if run directly
if (require.main === module) {
    const server = new IPCServer();
    server.start();

    console.log('AI CLI IPC Server v1.0');
    console.log('================================');
    console.log('Waiting for CLI connections...');
    console.log('');
    console.log('Supported CLIs:');
    console.log('- Claude CLI');
    console.log('- Gemini CLI');
    console.log('- Codex CLI');
    console.log('');
    console.log('Press Ctrl+C to stop');
}

module.exports = IPCServer;