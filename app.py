import argparse
from cores.download.install import ComponentInstaller, ComponentVersion
from cores.logger.logger import info, error

def main():
    parser = argparse.ArgumentParser(description='Jetson Environment Builder Tool')
    parser.add_argument('--install-cuda', action='store_true', help='Install CUDA toolchain')
    parser.add_argument('--install-opencv', action='store_true', help='Install OpenCV')
    parser.add_argument('--opencv-version', type=str, default='4.4.0', help='OpenCV version (default: 4.4.0)')
    parser.add_argument('--list-versions', action='store_true', help='List available component versions')
    
    args = parser.parse_args()
    installer = ComponentInstaller()
    
    try:
        if args.list_versions:
            installer.print_availabel_versions()
            return
            
        if args.install_cuda:
            info("Starting CUDA toolchain installation...")
            success, message = installer.install_cuda_stack()
            if success:
                info("CUDA toolchain installed successfully")
            else:
                error(f"CUDA toolchain installation failed: {message}")
                return
        
        if args.install_opencv:
            info(f"Starting OpenCV {args.opencv_version} installation...")
            try:
                major, minor, patch = map(int, args.opencv_version.split('.'))
                version = ComponentVersion(major, minor, patch)
            except ValueError:
                error(f"Invalid OpenCV version format: {args.opencv_version}")
                return
                
            success, message = installer.install_opencv(version)
            if success:
                info("OpenCV installed successfully")
            else:
                error(f"OpenCV installation failed: {message}")
                return
        
        if not any([args.install_cuda, args.install_opencv, args.list_versions]):
            parser.print_help()
            
    except KeyboardInterrupt:
        error("\nOperation interrupted by user")
    except Exception as e:
        error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
