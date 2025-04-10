import os 
import subprocess
import shutil
import json
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass, field
from .download import Downloader, DownloaderInfo
from .path import download_path
from ..logger.logger import info, warning, error, verbose

@dataclass
class ComponentVersion:
    """Component version information"""
    major: int
    minor: int
    patch: int = 0
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
@dataclass
class OpencvConfig:
    """OpenCV configuration"""
    version: ComponentVersion
    enable_cuda: bool = True
    build_option: Dict[str, str] = field(default_factory=lambda:{
        'CMAKE_BUILD_TYPE': 'RELEASE',
        'CMAKE_INSTALL_PREFIX': '/usr',
        'EIGEN_INCLUDE_PATH': '/usr/include/eigen3',
        'WITH_OPENCL': 'OFF',
        'WITH_CUDA': 'ON',
        'WITH_CUDNN': 'ON',
        'WITH_CUBLAS': 'ON',
        'ENABLE_FAST_MATH': 'ON',
        'CUDA_FAST_MATH': 'ON',
        'OPENCV_DNN_CUDA': 'ON',
        'ENABLE_NEON': 'ON',
        'WITH_QT': 'OFF',
        'WITH_OPENMP': 'ON',
        'BUILD_TIFF': 'ON',
        'WITH_FFMPEG': 'ON',
        'WITH_GSTREAMER': 'ON',
        'WITH_TBB': 'ON',
        'BUILD_TBB': 'ON',
        'BUILD_TESTS': 'OFF',
        'WITH_EIGEN': 'ON',
        'WITH_V4L': 'ON',
        'WITH_LIBV4L': 'ON',
        'WITH_PROTOBUF': 'ON',
        'OPENCV_ENABLE_NONFREE': 'ON',
        'INSTALL_C_EXAMPLES': 'OFF',
        'INSTALL_PYTHON_EXAMPLES': 'OFF',
        'OPENCV_GENERATE_PKGCONFIG': 'ON',
        'BUILD_EXAMPLES': 'OFF'
    })
    
    @property
    def main_url(self) -> str:
        return f"https://github.com/opencv/opencv/archive/{self.version}.zip"
    
    @property
    def contrib_url(self) -> str:
        return f"https://github.com/opencv/opencv_contrib/archive/{self.version}.zip"

@dataclass
class InstallStatus:
    """Installation status record"""
    dependencies_installed: bool = False
    opencv_downloaded: bool = False
    opencv_extracted: bool = False
    opencv_configured: bool = False
    opencv_compiled: bool = False
    opencv_installed: bool = False

    def save(self, path: Path):
        """Save installation status to file"""
        with open(path, 'w') as f:
            json.dump(self.__dict__, f)
    
    @classmethod
    def load(cls, path: Path) -> 'InstallStatus':
        """Load installation status from file"""
        if not path.exists():
            return cls()
        with open(path, 'r') as f:
            data = json.load(f)
            return cls(**data)

class ComponentInstaller:
    """Component installer"""
    
    def __init__(self):
        self.downloader = Downloader()
        self.work_dir = download_path
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.status_file = self.work_dir / "install_status.json"
        self.status = InstallStatus.load(self.status_file)
        self.opencv_src_dir = None  # Add this member variable to save opencv_src_dir
        self.build_dir = None  # Add build_dir as a global variable
    
    def _run_command(self, cmd: str, cwd: Optional[Path] = None) -> Tuple[bool, str]:
        """Execute bash command"""
        try:
            # Display the command to be executed
            info(f"Executing command: {cmd}")
            if cwd:
                info(f"Working directory: {cwd}")
                
            process = subprocess.Popen(
                cmd,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output in real-time
            output = []
            while True:
                output_line = process.stdout.readline()
                if output_line == '' and process.poll() is not None:
                    break
                if output_line:
                    verbose(output_line.strip())  # Display command output using verbose level
                    output.append(output_line)
            
            # Get error output
            error_output = process.stderr.read()
            if error_output:
                warning(error_output.strip())  # Display error output using warning level
            
            return process.returncode == 0, ''.join(output)
        except Exception as e:
            return False, str(e)
    
    def _get_available_version(self, component: str=None) -> Dict[str, List[str]]:
        """
        Get available component versions
        
        Args:
            component: Component name, if None get all component versions
            
        Returns:
            Dict[str, List[str]]: Component version dictionary {component_name: [version_list]}
        """
        components = {
            'cuda' : 'cuda',
            'cudnn': 'libcudnn8',
            'tensorrt': 'tensorrt',
            'libnvinfer': 'libnvinfer8',
            'libnvvpi': 'libnvvpi2'
        }
        
        if component and component not in components:
            warning(f"Unknown component: {component}")
            return {}

        versions = {}
        check_components = {component: components[component]} if component else components
        for comp_name, package_name in check_components.items():
            try:
                # Get version information using apt-cache policy
                success, output = self._run_command(f"sudo apt-cache policy {package_name}")
                if not success:
                    warning(f"Failed to get {comp_name} version information")
                    versions[comp_name] = []
                    continue
                
                # Parse version information
                comp_versions = []
                in_version_list = False
                candidate_version = None
                
                for line in output.split('\n'):
                    line = line.strip()
                    
                    # Get candidate version
                    if line.startswith('Candidate:'):
                        candidate_version = line.split(':')[1].strip()
                        if candidate_version != '(none)':
                            comp_versions.append(f"{candidate_version} (candidate)")
                    
                    # Version list
                    if line.startswith('Version table:'):
                        in_version_list = True
                        continue
                    
                    if in_version_list and line:
                        # Extract version number from the first column
                        version = line.split()[0]
                        if version and version != '(none)':
                            # Clean version number
                            version = version.split('-')[0]  # Remove Ubuntu specific suffix
                            if version not in comp_versions:
                                comp_versions.append(version)
                
                versions[comp_name] = sorted(comp_versions, reverse=True)
            except Exception as e:
                error(f"Error getting {comp_name} version information: {e}")
                versions[comp_name] = []
        return versions
    
    def print_availabel_versions(self):
        """Print all available component versions"""
        versions = self._get_available_version()
        info("=== Available Component Versions ===")
        for component, version_list in versions.items():
            info(f"{component.upper()}: ")
            if version_list:
                for version in version_list:
                    info(f"  - {version}")
            else:
                info("  No available versions found")
                
    def install_cuda_stack(self) -> Tuple[bool, str]:
        """
        Install CUDA toolchain
        """
        try:
            # Use default
            commands = [
                "sudo apt-get update",
                "sudo apt-get install -y cuda",
                "sudo apt-get install -y libcudnn8 libcudnn8-dev",
                "sudo apt-get install -y tensorrt",
                "sudo apt-get install -y libnvvpi2"
            ]
            for cmd in commands:
                success, output = self._run_command(cmd)
                if not success:
                    return False, f"Installation failed: {output}"

            # Set environment variables
            env_vars = [
                'export PATH=/usr/local/cuda/bin:$PATH',
                'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH'
            ]
            
            # Write to .bashrc
            with open(os.path.expanduser('~/.bashrc'), 'a') as f:
                for var in env_vars:
                    f.write(f'\n{var}')
            
            # Refresh environment variables
            refresh_cmds = [
                "source ~/.bashrc",
                "hash -r"  # Clear command cache
            ]
            for cmd in refresh_cmds:
                success, output = self._run_command(cmd)
                if not success:
                    warning(f"Failed to refresh environment: {output}")
            
            # Verify installation
            verification_results = self.verify_all_components()
            if all(success for success,_ in verification_results.values()):
                info("All components installed successfully")
                return True, "Installation completed"
            else:
                failed_components = [comp for comp, (success, _) in verification_results.items() if not success]
                return False, f"Verification failed for: {', '.join(failed_components)}"
        except Exception as e:
            error(f"CUDA installation error: {e}")
            return False, str(e)
        
    def verify_all_components(self) -> Dict[str, Tuple[bool, str]]:
        """Verify all installed components"""
        results = {}
        
        # CUDA verification
        success, output = self._run_command("nvcc --version")
        results['cuda'] = (success, "Installed" if success else "Not installed")
        
        # cuDNN verification
        success, output = self._run_command("sudo dpkg -l | grep cudnn")
        results['cudnn'] = (success, "Installed" if success else "Not installed")
        
        # TensorRT verification
        success, output = self._run_command("sudo dpkg -l | grep tensorrt")
        results['tensorrt'] = (success, "Installed" if success else "Not installed")
        
        return results
    
    def _get_cuda_arch(self) -> str:
        """
        Get current device's CUDA architecture version
        Returns:
            str: CUDA architecture version (e.g., '7.2')
        """
        try:
            success, output = self._run_command("cat /proc/device-tree/model")
            if success:
                if "jetson-orin-nano" in output.lower():
                    info("Detected Jetson Orin Nano device, using architecture 8.6")
                    return "8.6"
                elif "jetson-orin-nx" in output.lower():
                    info("Detected Jetson Orin NX device, using architecture 8.7")
                    return "8.7"
                elif "jetson-agx" in output.lower():
                    info("Detected Jetson AGX device, using architecture 7.2")
                    return "7.2"
                elif "jetson-xaiver-nx" in output.lower():
                    info("Detected Jetson Xavier NX device, using architecture 6.2")
                    return "6.2"
                else:
                    warning("No Jetson device detected, using default architecture 7.2")
                    return "7.2"
            else:
                warning("Unable to get device information, using default architecture 7.2")
                return "7.2"
        except Exception as e:
            error(f"Failed to get CUDA architecture: {e}")
            return "7.2"
                    
    def _save_status(self):
        """Save current installation status"""
        self.status.save(self.status_file)

    def _ensure_build_dir(self) -> Tuple[bool, str]:
        """Ensure build directory exists and is properly set"""
        if not self.opencv_src_dir:
            return False, "OpenCV source directory not found"
            
        if not self.build_dir:
            self.build_dir = self.opencv_src_dir / 'build'
            
        if not self.build_dir.exists():
            self.build_dir.mkdir(exist_ok=True)
            
        return True, "Build directory ready"

    def _configure_opencv(self, opencv_config: OpencvConfig, opencv_dir: Path, version: ComponentVersion) -> Tuple[bool, str]:
        """Configure OpenCV"""
        success, message = self._ensure_build_dir()
        if not success:
            return False, message
            
        cmake_option = opencv_config.build_option.copy()
        cuda_arch = self._get_cuda_arch()
        cmake_option.update({
            'OPENCV_EXTRA_MODULES_PATH': f"{opencv_dir}/opencv_contrib-{version}/modules",
            'PYTHON_EXECUTABLE': '/usr/lib/python3/dist-packages',
            'CUDA_ARCH_BIN': cuda_arch
        })
        
        cmake_cmd = "cmake " + " ".join(f"-D{k}={v}" for k,v in cmake_option.items())
        cmake_cmd += " .."
        info(f"Executing cmake command: {cmake_cmd}")
        info(f"Working directory: {self.build_dir}")
        
        success, output = self._run_command(cmake_cmd, self.build_dir)
        if not success:
            return False, f"OpenCV configuration failed: {output}"
            
        return True, "Configuration successful"

    def _compile_opencv(self) -> Tuple[bool, str]:
        """Compile OpenCV"""
        success, message = self._ensure_build_dir()
        if not success:
            return False, message
            
        cpu_count = os.cpu_count() or 4
        info(f"Starting compilation in directory: {self.build_dir}")
        success, output = self._run_command(f"cd {self.build_dir} && make -j{cpu_count}")
        if not success:
            return False, f"OpenCV compilation failed: {output}"
            
        return True, "Compilation successful"

    def _install_opencv(self) -> Tuple[bool, str]:
        """Install OpenCV"""
        success, message = self._ensure_build_dir()
        if not success:
            return False, message
            
        info(f"Starting installation in directory: {self.build_dir}")
        success, output = self._run_command(f"cd {self.build_dir} && sudo make install")
        if not success:
            return False, f"OpenCV installation failed: {output}"
            
        success, output = self._run_command("sudo ldconfig")
        if not success:
            return False, f"OpenCV ldconfig failed: {output}"
            
        return True, "Installation successful"

    def install_opencv(self, version: ComponentVersion = ComponentVersion(4, 4, 0)) -> Tuple[bool, str]:
        try:
            opencv_config = OpencvConfig(version=version)
            opencv_dir = self.work_dir / f"opencv-{version}"
            opencv_dir.mkdir(exist_ok=True)
            
            # Check if installation is already complete
            if self.status.opencv_installed:
                info("OpenCV installation already complete, skipping installation steps")
                return True, "OpenCV already installed"
            
            # Check if download is needed
            if not self.status.opencv_downloaded:
                # Check if OpenCV 4.4.0 installation package exists locally
                if version == ComponentVersion(4, 4, 0):
                    local_opencv = self.work_dir / "opencv-4.4.0.tar.gz"
                    local_opencv_contrib = self.work_dir / "opencv_contrib-4.4.0.tar.gz"
                    if local_opencv.exists() and local_opencv_contrib.exists():
                        info("Using local OpenCV 4.4.0 installation package")
                        shutil.copy(local_opencv, opencv_dir / "opencv.tar.gz")
                        shutil.copy(local_opencv_contrib, opencv_dir / "opencv_contrib.tar.gz")
                    else:
                        # Download OpenCV
                        downloads = [
                            DownloaderInfo(
                                name="OpenCV",
                                version=str(version),
                                url=opencv_config.main_url,
                                filename=f"opencv-{version}.zip",
                                save_path=opencv_dir / f"opencv-{version}.zip"
                            ),
                            DownloaderInfo(
                                name="OpenCV-Contrib",
                                version=str(version),
                                url=opencv_config.contrib_url,
                                filename=f"opencv_contrib-{version}.zip",
                                save_path=opencv_dir / f"opencv_contrib-{version}.zip"
                            )]
                        for download_info in downloads:
                            success, message = self.downloader.download_file(download_info)
                            if not success:
                                return False, f"OpenCV download failed: {message}"
                else:
                    # Download specified version of OpenCV
                    downloads = [
                        DownloaderInfo(
                            name="OpenCV",
                            version=str(version),
                            url=opencv_config.main_url,
                            filename=f"opencv-{version}.zip",
                            save_path=opencv_dir / f"opencv-{version}.zip"
                        ),
                        DownloaderInfo(
                            name="OpenCV-Contrib",
                            version=str(version),
                            url=opencv_config.contrib_url,
                            filename=f"opencv_contrib-{version}.zip",
                            save_path=opencv_dir / f"opencv_contrib-{version}.zip"
                        )]
                    for download_info in downloads:
                        success, message = self.downloader.download_file(download_info)
                        if not success:
                            return False, f"OpenCV download failed: {message}"
                
                self.status.opencv_downloaded = True
                self._save_status()
            
            # Check if dependencies need to be installed
            if not self.status.dependencies_installed:
                # Install OpenCV dependencies
                deps_cmds = [
                    "sudo apt-get install qt5-default qtcreator -y",
                    "sudo apt-get install -y build-essential git unzip pkg-config zlib1g-dev",
                    "sudo apt-get install -y python3-dev python3-numpy",
                    "sudo apt-get install -y gstreamer1.0-tools libgstreamer-plugins-base1.0-dev",
                    "sudo apt-get install -y libgstreamer-plugins-good1.0-dev",
                    "sudo apt-get install -y libtbb2 libgtk-3-dev libxine2-dev",
                    "sudo apt-get install -y cmake",
                    "sudo apt-get install -y libjpeg-dev libjpeg8-dev libjpeg-turbo8-dev",
                    "sudo apt-get install -y libpng-dev libtiff-dev libglew-dev",
                    "sudo apt-get install -y libavcodec-dev libavformat-dev libswscale-dev",
                    "sudo apt-get install -y libgtk2.0-dev libgtk-3-dev libcanberra-gtk*",
                    "sudo apt-get install -y python3-pip",
                    "sudo apt-get install -y libxvidcore-dev libx264-dev",
                    "sudo apt-get install -y libtbb-dev libdc1394-22-dev libxine2-dev",
                    "sudo apt-get install -y libv4l-dev v4l-utils qv4l2",
                    "sudo apt-get install -y libtesseract-dev libpostproc-dev",
                    "sudo apt-get install -y libavresample-dev libvorbis-dev",
                    "sudo apt-get install -y libfaac-dev libmp3lame-dev libtheora-dev",
                    "sudo apt-get install -y libopencore-amrnb-dev libopencore-amrwb-dev",
                    "sudo apt-get install -y libopenblas-dev libatlas-base-dev libblas-dev",
                    "sudo apt-get install -y liblapack-dev liblapacke-dev libeigen3-dev gfortran",
                    "sudo apt-get install -y libhdf5-dev libprotobuf-dev protobuf-compiler",
                    "sudo apt-get install -y libgoogle-glog-dev libgflags-dev"
                ]
                
                for cmd in deps_cmds:
                    success, output = self._run_command(cmd)
                    if not success:
                        # If installation fails, try to fix dependencies
                        fix_cmd = "sudo apt --fix-broken install -y"
                        success, output = self._run_command(fix_cmd)
                        if not success:
                            return False, f"Installation failed: {output}"
                        
                        # Re-attempt to install dependencies
                        success, output = self._run_command(cmd)
                        if not success:
                            return False, f"Installation failed after fix: {output}"
                
                self.status.dependencies_installed = True
                self._save_status()
            
            # Check if files need to be extracted
            if not self.status.opencv_extracted:
                info(f"opencv_dir: {opencv_dir}")
                self.opencv_src_dir = None
                
                # Extract OpenCV source code
                for archive in opencv_dir.glob("*"):
                    if archive.is_file() and (archive.suffix == '.zip' or archive.name.endswith('.tar.gz')):
                        if archive.suffix == '.zip':
                            cmd = f"unzip -q {archive.name}"
                        else:
                            cmd = f"tar -xzf {archive.name}"
                        success, output = self._run_command(cmd, opencv_dir)
                        if not success:
                            return False, f"OpenCV extraction failed: {output}"
                        
                        if "contrib" not in archive.name:
                            self.opencv_src_dir = opencv_dir / f"opencv-{version}"
                
                if not self.opencv_src_dir:
                    return False, "Unable to find OpenCV source code"
                
                self.status.opencv_extracted = True
                self._save_status()
            else:
                # If already extracted, try to find source code directory
                self.opencv_src_dir = opencv_dir / f"opencv-{version}"
                if not self.opencv_src_dir.exists():
                    return False, "OpenCV source directory not found"
            
            # Check if configuration is needed
            if not self.status.opencv_configured:
                success, message = self._configure_opencv(opencv_config, opencv_dir, version)
                if not success:
                    return False, message
                self.status.opencv_configured = True
                self._save_status()
            
            # Check if compilation is needed
            if not self.status.opencv_compiled:
                success, message = self._compile_opencv()
                if not success:
                    return False, message
                self.status.opencv_compiled = True
                self._save_status()
            
            # Check if installation is needed
            if not self.status.opencv_installed:
                success, message = self._install_opencv()
                if not success:
                    return False, message
                self.status.opencv_installed = True
                self._save_status()
            
            info("OpenCV installation successful")
            return True, "OpenCV installation successful"
        
        except Exception as e:
            error(f"OpenCV installation error: {e}")
            return False, str(e)
            
            