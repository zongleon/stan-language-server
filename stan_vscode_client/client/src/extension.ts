/* --------------------------------------------------------------------------------------------
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License. See License.txt in the project root for license information.
 * ------------------------------------------------------------------------------------------ */
import * as vscode from 'vscode';
import * as os from 'os';
import * as path from 'path';
import * as https from 'https';
import * as child_process from 'child_process';
import * as fs from 'fs';
import { ExtensionContext } from 'vscode';

import {
	LanguageClient,
	LanguageClientOptions,
	ServerOptions,
} from 'vscode-languageclient/node';

let client: LanguageClient;
const outputChannel = vscode.window.createOutputChannel('STAN LSP');

function getPlatformAndArch(): { platform: string; arch: string } {
    const platform = os.platform();
    const arch = os.arch();
    return { platform, arch };
}

function getStancUrl(): string | null {
    const { platform, arch } = getPlatformAndArch();
    // version 2.36.0
    const binaryUrls: { [key: string]: string } = {
        'win32_x64': 'https://github.com/stan-dev/stanc3/releases/download/v2.36.0/windows-stanc',
        'linux_x64': 'https://github.com/stan-dev/stanc3/releases/download/v2.36.0/linux-stanc',
        'linux_arm64': 'https://github.com/stan-dev/stanc3/releases/download/v2.36.0/linux-arm64-stanc',
        'darwin_x64': 'https://github.com/stan-dev/stanc3/releases/download/v2.36.0/mac-stanc',
        'darwin_arm64': 'https://github.com/stan-dev/stanc3/releases/download/v2.36.0/mac-stanc',
    };
    const key = `${platform}_${arch}`;
    return binaryUrls[key] || null;
}

async function downloadBinary(url: string, destination: string): Promise<void> {
    return new Promise((resolve, reject) => {
        const dir = path.dirname(destination);

        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }

        const file = fs.createWriteStream(destination);
        const handleRequest = (url: string) => {
            https.get(url, (response) => {
                if (response.statusCode === 302 && response.headers.location) {
                    // Follow the redirect
                    handleRequest(response.headers.location);
                } else if (response.statusCode === 200) {
                    // Download the binary
                    response.pipe(file);
                    file.on('finish', () => file.close(() => { resolve(); }));
                } else {
                    reject(new Error(`Failed to download: ${response.statusCode}`));
                }
            }).on('error', (err) => {
                fs.unlink(destination, () => reject(err));
            });
        };

        handleRequest(url);
    });
}

async function installStanCompiler(context: vscode.ExtensionContext) {
	const stancUrl = getStancUrl();
    if (!stancUrl) {
        vscode.window.showErrorMessage('Unsupported platform or architecture.');
        return null;
    }

    const stancPath = path.join(context.globalStorageUri.fsPath, 
		os.platform() === 'win32' ? 'stanc.exe' : 'stanc');

    await vscode.window.withProgress(
        {
            location: vscode.ProgressLocation.Notification,
            title: 'Downloading language server...',
        },
        async () => {
            const tempPath = path.join(context.globalStorageUri.fsPath, "stanc");
            await downloadBinary(stancUrl, tempPath);
            fs.renameSync(tempPath, stancPath);
        }
    );

    if (os.platform() !== 'win32') {
        fs.chmodSync(stancPath, 0o755);
    }

    return stancPath;

}
async function installLanguageServer(context: vscode.ExtensionContext) {
    const serverPath = context.globalStorageUri.fsPath;
    const pythonExecutable = 'python3'; // maybe 'python'?

    // Ensure the global storage directory exists
    await vscode.workspace.fs.createDirectory(vscode.Uri.file(serverPath));

    try {
        vscode.window.showInformationMessage('Installing language server...');
        child_process.execSync(
            `${pythonExecutable} -m pip install stan-language-server --target "${serverPath}"`,
            { stdio: 'inherit' }
        );
        vscode.window.showInformationMessage('Language server installed successfully.');
        return serverPath;
    } catch (error) {
        vscode.window.showErrorMessage('Failed to install the language server. Please check your Python environment.');
        console.error(error);
        return null;
    }
}

export async function activate(context: ExtensionContext) {
    const stancPath = await installStanCompiler(context);
    if (!stancPath) {
        return;
    }

	const serverPath = await installLanguageServer(context);
    if (!serverPath) {
        return;
    }

    const binaryPath = path.join(serverPath, 'bin', 'stan-language-server');

    // language server options
    const serverOptions: ServerOptions = {
        run: { command: binaryPath, args: ['--stan-path', `${stancPath}`],
            options: {
                env: {
                    ...process.env, // Preserve existing environment variables
                    PYTHONPATH: `${serverPath}:${process.env.PYTHONPATH || ''}`
                }
            }
        },
        debug: { command: binaryPath, args: ['-vv', '--stan-path', `${stancPath}`],
            options: {
                env: {
                    ...process.env, // Preserve existing environment variables
                    PYTHONPATH: `${serverPath}:${process.env.PYTHONPATH || ''}`
                }
            }
         }
    };

	// Options to control the language client
	const clientOptions: LanguageClientOptions = {
		// Register the server for plain text documents
		documentSelector: [{ scheme: 'file', language: 'stan' }],
	};

	// Create the language client and start the client.
	client = new LanguageClient(
		'stan-language-server',
		'STAN Language Server',
		serverOptions,
		clientOptions
	);

	// Start the client. This will also launch the server
	client.start();
}

export function deactivate(): Thenable<void> | undefined {
	if (!client) {
		return undefined;
	}
	return client.stop();
}
