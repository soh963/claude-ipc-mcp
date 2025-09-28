#!/usr/bin/env node
// -*- coding: utf-8 -*-

/**
 * AI CLI Connection Test Suite
 * Comprehensive testing of all components
 */

const AICLIClient = require('./ai-cli-client');
const EnvironmentBridge = require('./env-bridge');
const { spawn } = require('child_process');
const net = require('net');

class TestSuite {
    constructor() {
        this.results = [];
        this.envBridge = new EnvironmentBridge();
    }

    // Add test result
    addResult(name, success, message = '') {
        this.results.push({ name, success, message });
        const status = success ? '✅' : '❌';
        console.log(`${status} ${name}: ${message}`);
    }

    // Test environment setup
    async testEnvironment() {
        console.log('\n🔍 Testing Environment Setup...');

        const requiredVars = [
            'AI_CLI_HOME',
            'AI_CLI_REGISTRY',
            'AI_CLI_CACHE',
            'AI_CLI_IPC_ENABLED'
        ];

        for (const varName of requiredVars) {
            const value = await this.envBridge.getEnv(varName);
            if (value) {
                this.addResult(`Env: ${varName}`, true, value);
            } else {
                this.addResult(`Env: ${varName}`, false, 'Not set');
            }
        }
    }

    // Test directory structure
    async testDirectories() {
        console.log('\n📁 Testing Directory Structure...');

        const fs = require('fs');
        const dirs = [
            'D:\\.ai-cli-ipc',
            'D:\\.ai-cli-ipc\\shared',
            'D:\\.ai-cli-ipc\\queue',
            'D:\\.ai-cli-ipc\\logs',
            'D:\\.ai-cli-registry',
            'D:\\.ai-cli-cache'
        ];

        for (const dir of dirs) {
            const exists = fs.existsSync(dir);
            this.addResult(`Dir: ${dir}`, exists, exists ? 'Exists' : 'Missing');
        }
    }

    // Test IPC server connectivity
    async testIPCServer() {
        console.log('\n🔌 Testing IPC Server...');

        // Check if server is running
        const isRunning = await this.checkServerRunning();
        this.addResult('IPC Server Status', isRunning, isRunning ? 'Running' : 'Not running');

        if (!isRunning) {
            console.log('  Starting IPC server for testing...');
            await this.startTestServer();
            await this.sleep(2000);
        }

        // Test connection
        try {
            const client = new AICLIClient({ cliType: 'test' });
            await client.connect();
            this.addResult('IPC Connection', true, 'Connected successfully');

            // Test sync
            const state = await client.sync();
            this.addResult('IPC Sync', true, 'State synchronized');

            // Test query
            const clients = await client.query('clients');
            this.addResult('IPC Query', true, `${clients.length} clients connected`);

        } catch (error) {
            this.addResult('IPC Connection', false, error.message);
        }
    }

    // Check if server is running
    checkServerRunning() {
        return new Promise((resolve) => {
            const client = net.createConnection('\\\\.\\pipe\\ai-cli-ipc');

            client.on('connect', () => {
                client.end();
                resolve(true);
            });

            client.on('error', () => {
                // Try TCP
                const tcpClient = net.createConnection(7777, '127.0.0.1');

                tcpClient.on('connect', () => {
                    tcpClient.end();
                    resolve(true);
                });

                tcpClient.on('error', () => {
                    resolve(false);
                });
            });
        });
    }

    // Start test server
    startTestServer() {
        return new Promise((resolve) => {
            const server = spawn('node', ['ipc-server.js'], {
                detached: true,
                stdio: 'ignore'
            });

            server.unref();
            resolve();
        });
    }

    // Test command execution
    async testCommandExecution() {
        console.log('\n⚡ Testing Command Execution...');

        try {
            const result = await this.envBridge.executeCommand('echo Test');
            this.addResult('Command Execution', result.success, 'Echo command works');
        } catch (error) {
            this.addResult('Command Execution', false, error.message);
        }

        try {
            const result = await this.envBridge.executeCommand('node --version');
            this.addResult('Node.js', result.success, result.stdout.trim());
        } catch (error) {
            this.addResult('Node.js', false, 'Not available');
        }
    }

    // Test CLI availability
    async testCLIAvailability() {
        console.log('\n🤖 Testing CLI Availability...');

        const clis = [
            { name: 'Claude CLI', command: 'npx claude-cli --version' },
            { name: 'Gemini CLI', command: 'gemini-cli --version' },
            { name: 'Codex CLI', command: 'codex-cli --version' }
        ];

        for (const cli of clis) {
            try {
                const result = await this.envBridge.executeCommand(cli.command);
                this.addResult(cli.name, result.success, result.success ? 'Available' : 'Not found');
            } catch (error) {
                this.addResult(cli.name, false, 'Not installed');
            }
        }
    }

    // Sleep helper
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Generate report
    generateReport() {
        console.log('\n' + '='.repeat(60));
        console.log('📊 TEST SUMMARY');
        console.log('='.repeat(60));

        const total = this.results.length;
        const passed = this.results.filter(r => r.success).length;
        const failed = total - passed;

        console.log(`Total Tests: ${total}`);
        console.log(`Passed: ${passed} ✅`);
        console.log(`Failed: ${failed} ❌`);
        console.log(`Success Rate: ${Math.round(passed / total * 100)}%`);

        if (failed > 0) {
            console.log('\n❌ Failed Tests:');
            this.results.filter(r => !r.success).forEach(r => {
                console.log(`  - ${r.name}: ${r.message}`);
            });
        }

        console.log('\n' + '='.repeat(60));
        return passed === total;
    }

    // Run all tests
    async runAll() {
        console.log('🚀 AI CLI Integration Test Suite');
        console.log('='.repeat(60));

        await this.testEnvironment();
        await this.testDirectories();
        await this.testIPCServer();
        await this.testCommandExecution();
        await this.testCLIAvailability();

        const success = this.generateReport();

        if (success) {
            console.log('\n✅ All tests passed! System is ready.');
        } else {
            console.log('\n⚠️  Some tests failed. Please run setup:');
            console.log('  npm run setup');
            console.log('  or');
            console.log('  ai-cli setup');
        }

        return success;
    }
}

// Run tests if executed directly
if (require.main === module) {
    const tester = new TestSuite();
    tester.runAll().then((success) => {
        process.exit(success ? 0 : 1);
    });
}

module.exports = TestSuite;