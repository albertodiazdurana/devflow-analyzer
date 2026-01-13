# Ollama Setup with WSL

This document describes how to configure Ollama running on Windows to be accessible from WSL2.

## Problem

Ollama installed on Windows binds to `127.0.0.1` by default, which is not accessible from WSL2 due to network isolation.

## Solution

### 1. Install Ollama on Windows

Download and install from: https://ollama.com/download/windows

### 2. Pull a model

In PowerShell:
```powershell
ollama pull llama3
```

### 3. Start Ollama with network binding

By default, Ollama only listens on `127.0.0.1`. To make it accessible from WSL2, you need to bind to all interfaces:

```powershell
# Stop any existing Ollama process
Stop-Process -Name "ollama" -Force

# Set environment variable and start
$env:OLLAMA_HOST = "0.0.0.0"
ollama serve
```

Keep this PowerShell window open while using Ollama.

### 4. Find the Windows host IP from WSL

In WSL, run:
```bash
ip route show default | awk '{print $3}'
```

This returns an IP like `172.x.x.x`.

### 5. Configure the project

Update your `.env` file:
```
OLLAMA_BASE_URL=http://172.x.x.x:11434
```

Replace `172.x.x.x` with your actual IP.

### 6. Verify connection

From WSL:
```bash
curl -s http://172.x.x.x:11434/api/tags
```

Should return a JSON list of available models.

## Troubleshooting

### "Connection refused" error

1. Ensure Ollama is running in PowerShell with `$env:OLLAMA_HOST = "0.0.0.0"`
2. Check Windows Firewall - you may need to allow port 11434:
   ```powershell
   # Run as Administrator
   New-NetFirewallRule -DisplayName "Ollama WSL" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow
   ```

### IP address changes

The WSL-Windows bridge IP can change after restarts. If connection fails, re-run:
```bash
ip route show default | awk '{print $3}'
```

And update `.env` accordingly.

### Alternative: WSL localhost forwarding

Some WSL2 configurations support `localhost` forwarding. Try:
```
OLLAMA_BASE_URL=http://localhost:11434
```

This may work depending on your WSL2 version and Windows build.

## Notes

- Ollama runs on CPU/GPU of the Windows host machine
- The WSL environment only sends API requests to the Windows Ollama server
- Model files are stored in Windows at `C:\Users\<user>\.ollama\models`
