# 🚀 Easy-flashsystem-jetson

> **用于Jetson设备上安装CUDA和OpenCV的工具。**

## ✨ 功能特点

- ✅ 支持CUDA安装
- ✅ 支持OpenCV安装（>4.4.0）
- ✅ 显示可用的组件版本
- ✅ 详细的安装日志

## 📋 安装前准备

### 🔧 步骤1：设置WSL2环境
> 💡 **注意**：您可以选择按照我们提供的步骤操作，或者参考[NVIDIA WSL2系统文档](https://docs.nvidia.com/sdk-manager/wsl-systems/index.html)获取官方指导。两种方法都能达到相同的结果。

#### 安装和配置WSL2
1. 安装Windows Terminal（推荐）和所需的Linux发行版
    ```bash
    ## 以管理员方式打开powershell
    wsl --install 
    wsl --list --online 
    wsl --install -d <DistroName>
    ## 更新wsl内核
    wsl.exe --update
    ```
2. 安装必要的软件包：
    ```bash
    sudo apt update && sudo apt install wslu -y
    ```
3. 安装USBIPD（版本4.3.0或更高）：
    ```bash
    winget install --interactive --exact dorssel.usbipd-win
    ```

#### 设置Linux环境
[NVIDIA wls-systems 文档](https://docs.nvidia.com/sdk-manager/wsl-systems/index.html)
1. 安装额外的软件包：
    ```bash
    sudo apt update
    sudo apt install iputils-ping iproute2 netcat iptables dnsutils network-manager usbutils net-tools python3-yaml dosfstools libgetopt-complete-perl openssh-client binutils xxd cpio udev dmidecode -y
    ```
2. 安装USB刷机包：
   ```bash
   sudo apt install linux-tools-virtual hwdata
   ```
3. 从[NVIDIA开发者网站](https://developer.nvidia.com/nvidia-sdk-manager)下载并安装SDK Manager

#### 刷写Jetson设备
1. 通过USB将Jetson设备连接到Windows机器
2. 将Jetson设备启动到恢复模式
3. 将USB设备附加到WSL：
   ```bash
   # 在Windows PowerShell（管理员）中运行
   usbipd.exe list
   usbipd.exe bind --busid <BUSID> --force
   usbipd.exe attach --wsl --busid=<BUSID> --auto-attach
   ```
4. 验证设备连接：
   ```bash
   lsusb
   ```
5. 运行SDK Manager并选择手动设置模式
6. 完成刷写过程（可能需要25分钟）
7. 完成后断开USB连接：
   ```bash
   usbipd.exe unbind --guid=<GUID>
   ```

### 🔄 步骤2：系统迁移
1. 解压系统镜像包：
    ```bash
    # 从以下链接下载系统镜像包：https://drive.google.com/file/d/1qSpLcZPKl3f-v36QqbXRhY27SCZdU5Es/view?usp=drive_link
    unzip installers/rootOnNVme.zip
    cd rootOnNVme
    ```
2. 运行安装脚本：
    ```bash
    sudo chmod 777 install.sh
    sudo ./install.sh
    ```
3. 按照屏幕提示完成迁移过程
4. 完成后重启系统
5. 验证系统是否从SSD运行：
    ```bash
    df -h
    ```

## 📥 安装

### 📦 步骤1：克隆仓库
1. 克隆项目仓库：
    ```bash
    git clone https://github.com/CraftsionBoo/Easy-flashsystem-jetson.git
    cd Easy-flashsystem-jetson
    ```

### 📦 步骤2：安装依赖
1. 安装所需的Python包：
    ```bash
    pip install -r requirements.txt
    ```

## 💻 使用方法

### 🔍 步骤1：检查版本
1. 列出可用的组件版本：
    ```bash
    python app.py --list-versions
    ```

### 🔧 步骤2：安装CUDA
1. 安装CUDA工具包：
    ```bash
    python app.py --install-cuda
    ```

### 🔧 步骤3：安装OpenCV
1. 使用默认版本安装OpenCV：
    ```bash
    python app.py --install-opencv
    ```
2. 或指定自定义版本：
    ```bash
    python app.py --install-opencv --opencv-version 4.8.0
    ```

## ⚠️ 注意事项

- 确保有足够的磁盘空间
- 安装过程可能需要较长时间
- 建议使用稳定的网络连接
- 仔细按照预安装步骤操作以确保环境正确设置

## ❓ 常见问题

<details>
<summary>Q1: 进入Jetson OS系统后无法打开终端</summary>

这通常是由于语言和地区设置未配置导致的。通过SSH连接后，配置LANG和LANGUAGE设置：
```bash
locale 
## 输出
LANG=en_US.UTF-8
LANGUAGE=en_US
LC_CTYPE="en_US.UTF-8"
LC_NUMERIC=zh_CN.UTF-8
...
```
</details>

<details>
<summary>Q2: 网络问题</summary>

1. 换源即可(建议使用清华源)

2. 追加国内公共DNS服务器(阿里云)：
```bash
sudo vim /etc/resolv.conf
# 追加
nameserver 223.5.5.5
nameserver 223.6.6.6
```
</details>

## 📥 下载链接

### OpenCV 安装包
- [opencv-4.4.0.tar.gz](https://drive.google.com/file/d/1brdgg9v3_C-MApta_dKNIVlhl5Cl9ZKk/view?usp=drive_link)
- [opencv_contrib-4.4.0.tar.gz](https://drive.google.com/file/d/1brdgg9v3_C-MApta_dKNIVlhl5Cl9ZKk/view?usp=drive_link)
- [opencv-download-cache](https://drive.google.com/file/d/1OkTOj-I_3XVX4ZepicZQkfoj-E4WLIhT/view?usp=drive_link)

## �� 许可证

MIT License 