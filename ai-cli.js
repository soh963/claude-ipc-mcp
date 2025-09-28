#!/usr/bin/env node
// -*- coding: utf-8 -*-

/**
 * Unified AI CLI Interface
 * Entry point for all AI CLI operations
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const AICLIClient = require('./ai-cli-client');
const EnvironmentBridge = require('./env-bridge');

class UnifiedAICLI {
    constructor() {
        this.envBridge = new EnvironmentBridge();
        this.currentDir = process.cwd();
    }

    // Display help
    showHelp() {
        console.log(`
AI CLI - Unified Interface for AI Command Line Tools
=====================================================

Usage: ai-cli <command> [options]

Commands:
  start-server      Start the IPC server
  claude [cmd]      Run Claude CLI with IPC support
  gemini [cmd]      Run Gemini CLI with IPC support
  codex [cmd]       Run Codex CLI with IPC support
  chat              Start interactive chat mode
  env <key>         Get environment variable
  exec <cmd>        Execute command with AI CLI environment
  test              Test all CLI connections
  setup             Run initial setup

Options:
  --no-ipc          Disable IPC communication
  --debug           Enable debug mode
  --help            Show this help message

Examples:
  ai-cli start-server           # Start IPC server
  ai-cli claude analyze code    # Run Claude CLI
  ai-cli chat                   # Interactive mode
  ai-cli exec "npm test"        # Run with AI environment
        `);
    }

    // Start IPC server
    async startServer() {
        console.log('Starting IPC server...');
        const serverPath = path.join(__dirname, 'ipc-server.js');

        const server = spawn('node', [serverPath], {
            stdio: 'inherit',
            cwd: this.currentDir
        });

        server.on('error', (error) => {
            console.error('Failed to start IPC server:', error);
        });
    }

    // Run specific CLI
    async runCLI(cliType, args) {
        console.log(`Running ${cliType} CLI...`);

        // Check if IPC is enabled
        const ipcEnabled = await this.envBridge.getEnv('AI_CLI_IPC_ENABLED');

        if (ipcEnabled === 'true') {
            // Start with IPC support
            const client = new AICLIClient({ cliType });

            try {
                await client.connect();
                console.log(`Connected to IPC server as ${cliType}`);

                // Execute command through IPC
                if (args.length > 0) {
                    client.broadcast({
                        command: args.join(' '),
                        cwd: this.currentDir
                    });
                }

                // Start interactive mode
                client.startInteractive();
            } catch (error) {
                console.error('IPC connection failed, running standalone...');
                this.runStandalone(cliType, args);
            }
        } else {
            this.runStandalone(cliType, args);
        }
    }

    // Run CLI in standalone mode
    runStandalone(cliType, args) {
        const cliCommands = {
            claude: 'npx claude-cli',
            gemini: 'gemini-cli',
            codex: 'codex-cli'
        };

        const command = cliCommands[cliType];
        if (!command) {
            console.error(`Unknown CLI type: ${cliType}`);
            return;
        }

        const proc = spawn(command, args, {
            shell: true,
            stdio: 'inherit',
            cwd: this.currentDir,
            env: {
                ...process.env,
                CURRENT_DIR: this.currentDir
            }
        });

        proc.on('error', (error) => {
            console.error(`Failed to run ${cliType}:`, error.message);
        });
    }

    // Interactive chat mode
    async startChat() {
        console.log('Starting interactive chat mode...');
        console.log('Connecting all available CLIs...\n');

        const clients = {
            claude: new AICLIClient({ cliType: 'claude' }),
            gemini: new AICLIClient({ cliType: 'gemini' }),
            codex: new AICLIClient({ cliType: 'codex' })
        };

        // Try to connect all clients
        for (const [name, client] of Object.entries(clients)) {
            try {
                await client.connect();
                console.log(`✅ ${name} connected`);
            } catch (error) {
                console.log(`❌ ${name} unavailable`);
            }
        }

        console.log('\nChat mode ready. Type /help for commands.\n');

        // Start interactive session
        const readline = require('readline');
        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
            prompt: 'AI> '
        });

        rl.prompt();

        rl.on('line', (line) => {
            const [cmd, ...args] = line.trim().split(' ');

            switch (cmd) {
                case '/help':
                    console.log(`
Chat Commands:
  /claude <msg>  - Send to Claude
  /gemini <msg>  - Send to Gemini
  /codex <msg>   - Send to Codex
  /all <msg>     - Send to all CLIs
  /exit          - Exit chat mode
                    `);
                    break;

                case '/claude':
                case '/gemini':
                case '/codex':
                    const cliType = cmd.substring(1);
                    if (clients[cliType] && clients[cliType].connected) {
                        clients[cliType].broadcast(args.join(' '));
                        console.log(`Sent to ${cliType}`);
                    } else {
                        console.log(`${cliType} is not connected`);
                    }
                    break;

                case '/all':
                    Object.entries(clients).forEach(([name, client]) => {
                        if (client.connected) {
                            client.broadcast(args.join(' '));
                        }
                    });
                    console.log('Sent to all connected CLIs');
                    break;

                case '/exit':
                    rl.close();
                    process.exit(0);
                    break;

                default:
                    // Send to all by default
                    Object.entries(clients).forEach(([name, client]) => {
                        if (client.connected) {
                            client.broadcast(line);
                        }
                    });
            }

            rl.prompt();
        });
    }

    // Test connections
    async testConnections() {
        console.log('Testing AI CLI connections...\n');

        const tests = [
            { name: 'Environment Variables', test: () => this.testEnv() },
            { name: 'IPC Server', test: () => this.testIPC() },
            { name: 'Claude CLI', test: () => this.testCLI('claude') },
            { name: 'Gemini CLI', test: () => this.testCLI('gemini') },
            { name: 'Codex CLI', test: () => this.testCLI('codex') }
        ];

        for (const { name, test } of tests) {
            process.stdout.write(`Testing ${name}... `);
            try {
                await test();
                console.log('✅ OK');
            } catch (error) {
                console.log(`❌ Failed: ${error.message}`);
            }
        }

        console.log('\nTest complete!');
    }

    // Test environment variables
    async testEnv() {
        const required = ['AI_CLI_HOME', 'AI_CLI_REGISTRY', 'AI_CLI_CACHE'];
        for (const key of required) {
            const value = await this.envBridge.getEnv(key);
            if (!value) {
                throw new Error(`Missing environment variable: ${key}`);
            }
        }
    }

    // Test IPC server
    async testIPC() {
        const client = new AICLIClient({ cliType: 'test' });
        await client.connect();
        const state = await client.sync();
        if (!state) {
            throw new Error('Failed to sync state');
        }
    }

    // Test specific CLI
    async testCLI(cliType) {
        const client = new AICLIClient({ cliType });
        await client.connect();
        await client.sync();
    }

    // Run setup
    async runSetup() {
        console.log('Running AI CLI setup...');
        const setupPath = path.join(__dirname, 'setup-ai-cli-env.ps1');

        const setup = spawn('powershell', [
            '-ExecutionPolicy', 'Bypass',
            '-File', setupPath
        ], {
            stdio: 'inherit'
        });

        setup.on('exit', (code) => {
            if (code === 0) {
                console.log('\nSetup completed successfully!');
                console.log('Please restart your terminal to apply changes.');
            } else {
                console.error('Setup failed with code:', code);
            }
        });
    }

    // Main entry point
    async run(args) {
        const [command, ...commandArgs] = args;

        switch (command) {
            case 'start-server':
                await this.startServer();
                break;

            case 'claude':
            case 'gemini':
            case 'codex':
                await this.runCLI(command, commandArgs);
                break;

            case 'chat':
                await this.startChat();
                break;

            case 'env':
                const value = await this.envBridge.getEnv(commandArgs[0]);
                console.log(value || '(not set)');
                break;

            case 'exec':
                const result = await this.envBridge.executeCommand(commandArgs.join(' '));
                if (result.success) {
                    console.log(result.stdout);
                } else {
                    console.error(result.error);
                }
                break;

            case 'test':
                await this.testConnections();
                break;

            case 'setup':
                await this.runSetup();
                break;

            case '--help':
            case 'help':
            case undefined:
                this.showHelp();
                break;

            default:
                console.error(`Unknown command: ${command}`);
                this.showHelp();
                process.exit(1);
        }
    }
}

// Run if executed directly
if (require.main === module) {
    const cli = new UnifiedAICLI();
    cli.run(process.argv.slice(2)).catch((error) => {
        console.error('Error:', error.message);
        process.exit(1);
    });
}

module.exports = UnifiedAICLI;