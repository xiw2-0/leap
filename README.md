# Leap: Web Trading APIs Based on mini-QMT (aka xtquant) for China A-Share Stock Market

Leap is a Web API framework built on top of mini-QMT (also known as xtquant) for China's A-share stock market. It enables remote access to trading and market data through HTTP/WebSocket APIs.

## Prerequisites

- Ubuntu/Debian Linux system
- Wine (to run Windows-based mini-QMT client)
- Virtual framebuffer for GUI applications

## Setup Instructions

### 1. Install Wine

Add 32-bit architecture support:
```
sudo dpkg --add-architecture i386
```

Add Wine repository key:
```
sudo mkdir -pm755 /etc/apt/keyrings
wget -O- https://dl.winehq.org/wine-builds/winehq.key | gpg --dearmor | sudo tee /etc/apt/keyrings/winehq-archive.key
```

Add Wine repository:
```
sudo wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/$(lsb_release -sc)/winehq-$(lsb_release -sc).sources
```

Install Wine:
```
sudo apt update
sudo apt install --install-recommends winehq-stable
```

### 2. Install Chinese Fonts (Important for Chinese Characters)

Install Chinese fonts to ensure proper display of Chinese characters in the mini-QMT client:
```
sudo apt install -y fonts-wqy-zenhei fonts-wqy-microhei
```

### 3. Set Up Virtual Display

To run Windows GUI applications (like mini-QMT) under Wine, you need to set up a virtual display:

```
sudo apt install -y xvfb x11vnc

# Start virtual framebuffer with nohup to ensure it persists after SSH logout
nohup Xvfb :99 -screen 0 800x600x16 > xvfb.log 2>&1 &

# Start VNC server for remote access (optional) with nohup
nohup x11vnc -display :99 -forever -passwd 123 -shared > x11vnc.log 2>&1 &

# Export display
export DISPLAY=:99
```

### 4. Install Python Under Wine

Download and install Python 3.11.9 for Windows:

```
wget https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

# Install Python under Wine
wine python-3.11.9-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
```

### 5. Install mini-QMT Client

1. Download the mini-QMT client (XtItClient_x64.exe) from your broker
2. Run the installer under Wine:
```
wine XtItClient_x64.exe
```

3. Configure and start the mini-QMT client with nohup:
```
nohup wine .wine/drive_c/Program\ Files/qmt_test/bin.x64/XtMiniQmt.exe > qmt_client.log 2>&1 &
```

### 6. Prepare Configuration File

Create a .env file to store configuration settings:

```
mkdir -p .data
echo "# Configuration for leap trading API" > .env
echo "# Add any required environment variables here" >> .env
echo "# LEAP_HOST=0.0.0.0" >> .env
echo "# LEAP_PORT=8000" >> .env
```

### 7. Install Leap Trading API

1. Install pip upgrade (under Wine):
```
wine python -m pip install --upgrade pip
```

2. Install the leap package:
```
wine python -m pip install leap-0.1.0-py3-none-any.whl
```

### 8. Run the Leap API Server

Start the Leap API server in the background with nohup to ensure it continues running after SSH session ends:

```
nohup wine python -m uvicorn leap.main:app --host 0.0.0.0 --port 8000 > leap.log 2>&1 &
```

The API will be accessible at `http://your-server-ip:8000`.

You can check the logs with:
```
tail -f leap.log
```

## Dependencies

- [mini-QMT](https://github.com/xt-plugins/xtquant_private_docs): Quantitative trading platform
- [FastAPI](https://fastapi.tiangolo.com/): Modern, fast web framework for Python
- [uvicorn](https://www.uvicorn.org/): ASGI server
- [xtquant](https://pypi.org/project/xtquant/): Quantitative trading library

## Notes

- This setup runs Windows-based mini-QMT client under Wine on Linux
- Requires a virtual display (Xvfb) to run GUI applications
- Make sure to install Chinese fonts to avoid issues with Chinese characters in the interface
- Create a .env file for configuration settings
- Use nohup to run processes in the background to prevent termination on SSH disconnect
- Make sure mini-QMT is properly configured with your trading account before starting the API
- For production deployment, consider security measures like authentication and SSL encryption