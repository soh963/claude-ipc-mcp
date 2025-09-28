#!/usr/bin/env node

/**
 * AI CLI 환경변수 브릿지 서비스
 * 환경변수 접근 제한 문제를 해결하는 프록시 서비스
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

class EnvironmentBridge {
    constructor() {
        this.cacheFile = 'D:\\.ai-cli-cache\\env-cache.json';
        this.configFile = 'D:\\.ai-cli-registry\\config.json';
        this.envCache = {};
        this.loadCache();
    }

    // 캐시 로드
    loadCache() {
        try {
            if (fs.existsSync(this.cacheFile)) {
                this.envCache = JSON.parse(fs.readFileSync(this.cacheFile, 'utf8'));
            }
        } catch (error) {
            console.error('캐시 로드 실패:', error);
            this.envCache = {};
        }
    }

    // 캐시 저장
    saveCache() {
        try {
            const dir = path.dirname(this.cacheFile);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            fs.writeFileSync(this.cacheFile, JSON.stringify(this.envCache, null, 2));
        } catch (error) {
            console.error('캐시 저장 실패:', error);
        }
    }

    // 환경변수 가져오기 (PowerShell 사용)
    async getEnv(key) {
        try {
            // 캐시 확인
            if (this.envCache[key] && this.envCache[key].expires > Date.now()) {
                return this.envCache[key].value;
            }

            // PowerShell로 환경변수 읽기
            const { stdout } = await execPromise(
                `powershell -Command "[System.Environment]::GetEnvironmentVariable('${key}', 'User')"`
            );

            const value = stdout.trim();

            // 캐시 업데이트 (5분간 유효)
            this.envCache[key] = {
                value: value || process.env[key] || '',
                expires: Date.now() + 300000
            };
            this.saveCache();

            return value || process.env[key] || '';
        } catch (error) {
            console.error(`환경변수 ${key} 읽기 실패:`, error);
            return process.env[key] || '';
        }
    }

    // 환경변수 설정 (PowerShell 사용)
    async setEnv(key, value) {
        try {
            // PowerShell로 환경변수 설정 (사용자 레벨)
            await execPromise(
                `powershell -Command "[System.Environment]::SetEnvironmentVariable('${key}', '${value}', 'User')"`
            );

            // 현재 프로세스에도 설정
            process.env[key] = value;

            // 캐시 업데이트
            this.envCache[key] = {
                value: value,
                expires: Date.now() + 300000
            };
            this.saveCache();

            return true;
        } catch (error) {
            console.error(`환경변수 ${key} 설정 실패:`, error);
            return false;
        }
    }

    // 명령어 실행 (환경변수 주입)
    async executeCommand(command, options = {}) {
        try {
            // 필요한 환경변수 로드
            const aiEnvVars = {
                AI_CLI_HOME: await this.getEnv('AI_CLI_HOME'),
                AI_CLI_REGISTRY: await this.getEnv('AI_CLI_REGISTRY'),
                AI_CLI_CACHE: await this.getEnv('AI_CLI_CACHE'),
                CLAUDE_CLI_PATH: await this.getEnv('CLAUDE_CLI_PATH'),
                AI_CLI_IPC_ENABLED: await this.getEnv('AI_CLI_IPC_ENABLED')
            };

            // 환경변수 병합
            const env = { ...process.env, ...aiEnvVars, ...options.env };

            // 명령어 실행
            const { stdout, stderr } = await execPromise(command, {
                ...options,
                env,
                shell: true
            });

            return { success: true, stdout, stderr };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // PATH 업데이트
    async updatePath(newPath) {
        try {
            const currentPath = await this.getEnv('Path');
            if (!currentPath.includes(newPath)) {
                const updatedPath = `${currentPath};${newPath}`;
                await this.setEnv('Path', updatedPath);
                return true;
            }
            return true;
        } catch (error) {
            console.error('PATH 업데이트 실패:', error);
            return false;
        }
    }
}

// CLI 인터페이스
if (require.main === module) {
    const bridge = new EnvironmentBridge();
    const args = process.argv.slice(2);

    (async () => {
        switch (args[0]) {
            case 'get':
                const value = await bridge.getEnv(args[1]);
                console.log(value);
                break;

            case 'set':
                const success = await bridge.setEnv(args[1], args[2]);
                console.log(success ? 'Success' : 'Failed');
                break;

            case 'exec':
                const result = await bridge.executeCommand(args.slice(1).join(' '));
                if (result.success) {
                    console.log(result.stdout);
                    if (result.stderr) console.error(result.stderr);
                } else {
                    console.error('실행 실패:', result.error);
                }
                break;

            case 'path':
                const pathSuccess = await bridge.updatePath(args[1]);
                console.log(pathSuccess ? 'PATH 업데이트 성공' : 'PATH 업데이트 실패');
                break;

            default:
                console.log(`
사용법:
  node env-bridge.js get <KEY>          - 환경변수 가져오기
  node env-bridge.js set <KEY> <VALUE>  - 환경변수 설정
  node env-bridge.js exec <COMMAND>     - 명령어 실행
  node env-bridge.js path <PATH>        - PATH 추가
                `);
        }
    })();
}

module.exports = EnvironmentBridge;