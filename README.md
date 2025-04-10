# 🚀 Easy-flashsystem-jetson

> **A comprehensive tool for Jetson device system flashing and environment setup through WSL2, including CUDA and OpenCV installation.**

[中文文档](README_zh.md)

## ✨ Features

- ✅ Support for CUDA installation
- ✅ Support for OpenCV installation (>4.4.0)
- ✅ Display available component versions
- ✅ Detailed installation logs

## 📋 Pre-Installation

### 🔧 Step1: Setup WSL2 Environment
> 💡 **Note**: You can either follow our steps below or refer to the [NVIDIA WSL2 Systems Documentation](https://docs.nvidia.com/sdk-manager/wsl-systems/index.html) for official guidance. Both methods will achieve the same result.

#### Install and Configure WSL2
1. Install Windows Terminal (recommended) and required Linux distribution
    ```bash
    ## Open PowerShell as administrator
    wsl --install 
    wsl --list --online 
    wsl --install -d <DistroName>
    ## Update wsl kernel
    wsl.exe --update
    ```
2. Install required packages:
    ```bash
    sudo apt update && sudo apt install wslu -y
    ```
3. Install USBIPD (version 4.3.0 or higher):
    ```bash
    winget install --interactive --exact dorssel.usbipd-win
    ```

#### Setup Linux Environment
1. Install additional packages:
    ```bash
    sudo apt update
    sudo apt install iputils-ping iproute2 netcat iptables dnsutils network-manager usbutils net-tools python3-yaml dosfstools libgetopt-complete-perl openssh-client binutils xxd cpio udev dmidecode -y
    ```
2. Install USB flashing packages:
   ```bash
   sudo apt install linux-tools-virtual hwdata
   ```
3. Download and install SDK Manager from [NVIDIA Developer](https://developer.nvidia.com/nvidia-sdk-manager)

#### Flash Jetson Device
1. Connect Jetson device to Windows machine via USB
2. Boot Jetson into Recovery mode
3. Attach USB device to WSL:
   ```bash
   # From Windows PowerShell (admin)
   usbipd.exe list
   usbipd.exe bind --busid <BUSID> --force
   usbipd.exe attach --wsl --busid=<BUSID> --auto-attach
   ```
4. Verify device connection:
   ```bash
   lsusb
   ```
5. Run SDK Manager and select Manual Setup Mode
6. Complete flash process (may take up to 25 minutes)
7. Detach USB after completion:
   ```bash
   usbipd.exe unbind --guid=<GUID>
   ```

### 🔄 Step2: System Migration
1. Extract the system image package:
    ```bash
    # Download the system image package from: https://drive.google.com/file/d/1qSpLcZPKl3f-v36QqbXRhY27SCZdU5Es/view?usp=drive_link
    unzip installers/rootOnNVme.zip
    cd rootOnNVme
    ```
2. Run the installation script:
    ```bash
    sudo chmod 777 install.sh
    sudo ./install.sh
    ```
3. Follow the on-screen instructions to complete the migration
4. Reboot the system after completion
5. Verify the system is running from SSD:
    ```bash
    df -h
    ```

## 📥 Installation

### 📦 Step1: Clone Repository
1. Clone the project repository:
    ```bash
    git clone https://github.com/CraftsionBoo/Easy-flashsystem-jetson.git
    cd Easy-flashsystem-jetson
    ```

### 📦 Step2: Install Dependencies
1. Install required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

## 💻 Usage

### 🔍 Step1: Check Versions
1. List available component versions:
    ```bash
    python app.py --list-versions
    ```

### 🔧 Step2: Install CUDA
1. Install CUDA toolkit:
    ```bash
    python app.py --install-cuda
    ```

### 🔧 Step3: Install OpenCV
1. Install OpenCV with default version:
    ```bash
    python app.py --install-opencv
    ```
2. Or specify a custom version:
    ```bash
    python app.py --install-opencv --opencv-version 4.8.0
    ```

## ⚠️ Notes

- Ensure sufficient disk space is available
- Installation process may take a long time
- A stable network connection is recommended
- Follow pre-installation steps carefully to ensure proper environment setup

## ❓ FAQ

<details>
<summary>Q1: Terminal not opening after entering Jetson OS system</summary>

This is usually due to unconfigured language and region settings. After SSH connection, configure the LANG and LANGUAGE settings:
```bash
locale
## output
LANG=en_US.UTF-8
LANGUAGE=en_US
LC_CTYPE="en_US.UTF-8"
LC_NUMERIC=zh_CN.UTF-8
...
```
</details>

<details>
<summary>Q2: Network Issues</summary>

1. Change the source (recommended to use Tsinghua source)

2. Add domestic public DNS servers (Aliyun):
```bash
sudo vim /etc/resolv.conf
# Add
nameserver 223.5.5.5
nameserver 223.6.6.6
```
</details>

## 📥 Download Links

### OpenCV Installation Packages
- [opencv-4.4.0.tar.gz](https://drive.google.com/file/d/1brdgg9v3_C-MApta_dKNIVlhl5Cl9ZKk/view?usp=drive_link)
- [opencv_contrib-4.4.0.tar.gz](https://drive.google.com/file/d/1brdgg9v3_C-MApta_dKNIVlhl5Cl9ZKk/view?usp=drive_link)
- [opencv-download-cache](https://drive.google.com/file/d/1OkTOj-I_3XVX4ZepicZQkfoj-E4WLIhT/view?usp=drive_link)

## 📄 License

MIT License
