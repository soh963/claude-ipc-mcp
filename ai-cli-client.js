#!/usr/bin/env node
// -*- coding: utf-8 -*-

/**
 * AI CLI Client Library
 * Common client for all AI CLI instances to communicate
 */

const net = require('net');
const { EventEmitter } = require('events');
const readline = require('readline');

class AICLIClient extends EventEmitter {
    constructor(options = {}) {
        super();
        this.cliType = options.cliType || 'claude'; // claude, gemini, codex
        this.name = options.name || `${this.cliType}-${Date.now()}`;
        this.socketPath = '\\\\.\\pipe\\ai-cli-ipc';
        this.tcpPort = 7777;
        this.tcpHost = '127.0.0.1';
        this.connected = false;
        this.socket = null;
        this.encoding = 'utf8';
        this.messageBuffer = '';
    }

    // Connect to IPC server
    connect() {
        return new Promise((resolve, reject) => {
            // Try Windows Named Pipe first
            this.socket = net.createConnection(this.socketPath);

            this.socket.setEncoding(this.encoding);

            this.socket.on('connect', () => {
                console.log(`Connected to IPC server (pipe)`);
                this.connected = true;
                this.register();
                resolve();
            });

            this.socket.on('error', (error) => {
                if (!this.connected) {
                    console.log('Named pipe unavailable, trying TCP...');
                    this.connectTcp(resolve, reject);
                } else {
                    console.error('Connection error:', error.message);
                }
            });

            this.socket.on('data', (data) => {
                this.handleData(data);
            });

            this.socket.on('close', () => {
                this.connected = false;
                console.log('Disconnected from IPC server');
                this.emit('disconnect');
            });
        });
    }

    // Connect via TCP
    connectTcp(resolve, reject) {
        this.socket = net.createConnection(this.tcpPort, this.tcpHost);

        this.socket.setEncoding(this.encoding);

        this.socket.on('connect', () => {
            console.log(`Connected to IPC server (TCP)`);
            this.connected = true;
            this.register();
            resolve();
        });

        this.socket.on('error', (error) => {
            console.error('TCP connection failed:', error.message);
            reject(error);
        });

        this.socket.on('data', (data) => {
            this.handleData(data);
        });

        this.socket.on('close', () => {
            this.connected = false;
            console.log('Disconnected from IPC server');
            this.emit('disconnect');
        });
    }

    // Handle incoming data
    handleData(data) {
        this.messageBuffer += data;
        const lines = this.messageBuffer.split('\n');

        // Keep incomplete line in buffer
        this.messageBuffer = lines.pop() || '';

        lines.forEach(line => {
            if (line.trim()) {
                try {
                    const message = JSON.parse(line);
                    this.handleMessage(message);
                } catch (error) {
                    console.error('Failed to parse message:', error);
                }
            }
        });
    }

    // Handle incoming messages
    handleMessage(message) {
        console.log(`Received: ${message.type}`);

        switch (message.type) {
            case 'registered':
                console.log(`Registered as: ${message.clientId}`);
                this.emit('registered', message);
                break;

            case 'broadcast':
                console.log(`Broadcast from ${message.from}:`, message.data);
                this.emit('broadcast', message);
                break;

            case 'execute-request':
                console.log(`Execute request from ${message.from}:`, message.command);
                this.emit('execute', message);
                break;

            case 'query-response':
                this.emit('query-response', message);
                break;

            case 'state-sync':
                this.emit('state-sync', message);
                break;

            case 'error':
                console.error('Server error:', message.message);
                this.emit('error', message);
                break;

            default:
                console.log('Unknown message:', message);
        }
    }

    // Register with server
    register() {
        this.send({
            type: 'register',
            cliType: this.cliType,
            name: this.name,
            capabilities: this.getCapabilities()
        });
    }

    // Get CLI capabilities
    getCapabilities() {
        const capabilities = {
            claude: ['code-generation', 'analysis', 'documentation'],
            gemini: ['multi-modal', 'reasoning', 'translation'],
            codex: ['code-completion', 'refactoring', 'debugging']
        };

        return capabilities[this.cliType] || [];
    }

    // Send message to server
    send(message) {
        if (this.connected && this.socket) {
            const data = JSON.stringify(message);
            this.socket.write(data + '\n', this.encoding);
        } else {
            console.error('Not connected to IPC server');
        }
    }

    // Broadcast message to all CLIs
    broadcast(data) {
        this.send({
            type: 'broadcast',
            data
        });
    }

    // Query server
    query(queryType) {
        return new Promise((resolve) => {
            this.once('query-response', (response) => {
                resolve(response.data);
            });

            this.send({
                type: 'query',
                query: queryType
            });
        });
    }

    // Execute command on another CLI
    execute(target, command) {
        this.send({
            type: 'execute',
            target,
            command
        });
    }

    // Sync state
    sync() {
        return new Promise((resolve) => {
            this.once('state-sync', (response) => {
                resolve(response.state);
            });

            this.send({
                type: 'sync'
            });
        });
    }

    // Interactive mode
    startInteractive() {
        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
            prompt: `[${this.cliType}]> `
        });

        console.log(`\nAI CLI Interactive Mode (${this.cliType})`);
        console.log('Commands:');
        console.log('  /list         - List connected CLIs');
        console.log('  /send <msg>   - Broadcast message');
        console.log('  /exec <cli> <cmd> - Execute on another CLI');
        console.log('  /sync         - Sync state');
        console.log('  /exit         - Exit');
        console.log('');

        rl.prompt();

        rl.on('line', async (line) => {
            const [cmd, ...args] = line.trim().split(' ');

            switch (cmd) {
                case '/list':
                    const clients = await this.query('clients');
                    console.log('Connected CLIs:', clients);
                    break;

                case '/send':
                    this.broadcast(args.join(' '));
                    console.log('Message sent');
                    break;

                case '/exec':
                    const [target, ...cmdArgs] = args;
                    this.execute(target, cmdArgs.join(' '));
                    console.log(`Execution request sent to ${target}`);
                    break;

                case '/sync':
                    const state = await this.sync();
                    console.log('State:', JSON.stringify(state, null, 2));
                    break;

                case '/exit':
                    rl.close();
                    process.exit(0);
                    break;

                default:
                    if (line.trim()) {
                        // Send as broadcast by default
                        this.broadcast(line);
                    }
            }

            rl.prompt();
        });

        // Handle incoming broadcasts
        this.on('broadcast', (message) => {
            console.log(`\n[${message.from}]: ${message.data}`);
            rl.prompt();
        });

        // Handle execution requests
        this.on('execute', (message) => {
            console.log(`\n[EXEC from ${message.from}]: ${message.command}`);
            // Here you would execute the command and send back results
            rl.prompt();
        });
    }
}

// CLI interface
if (require.main === module) {
    const args = process.argv.slice(2);
    const cliType = args[0] || 'claude';

    const client = new AICLIClient({ cliType });

    client.connect()
        .then(() => {
            client.startInteractive();
        })
        .catch((error) => {
            console.error('Failed to connect:', error.message);
            process.exit(1);
        });
}

module.exports = AICLIClient;