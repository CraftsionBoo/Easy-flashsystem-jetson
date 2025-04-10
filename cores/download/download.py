import requests 
import time 
import hashlib
from tqdm import tqdm
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from requests.exceptions import RequestException
from ..logger.logger import info,warning,error

@dataclass
class DownloaderInfo:
    name: str
    version: str
    url: str
    filename: str 
    checksum: Optional[str] = None
    save_path: Optional[Path] = None
    
    def __post_init__(self):
        if not self.filename:
            self.filename = Path(self.url).name
        if not self.save_path:
            self.save_path = Path("downloads") / self.filename

class Downloader:
    
    def __init__(self, 
                 chunk_size: int = None,
                 timeout: int = 60, 
                 retries: int = 3,
                 retry_delay: int = 2):
        """
        Initialize downloader
        
        Args:
            chunk_size: Size of data chunk to read at a time (bytes)
            timeout: Request timeout in seconds
            retries: Maximum number of retries
            retry_delay: Base delay between retries in seconds
        """
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay
        
        # Create persistent session
        self.session = requests.session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        })
    
    def verify_file(self, file_path: Path, expected_hash: Optional[str] = None) -> bool:
        """
        Verify file integrity
        
        Args:
            file_path: Path to the file
            expected_hash: Expected SHA256 hash value (optional)
            
        Returns:
            bool: Whether the file is valid
        """
        if not file_path.exists():
            return False

        if expected_hash:
            sha256_hash = hashlib.sha256()
            try:
                with open(file_path, "rb") as f:
                    for byte_block in iter(lambda: f.read(self.chunk_size), b""):
                        sha256_hash.update(byte_block)
                actual_hash = sha256_hash.hexdigest()
                if actual_hash != expected_hash:
                    warning(f"File checksum mismatch: {file_path}")
                    return False
            except IOError as e:
                error(f"IO error during file verification: {e}")
                return False
        return True

    def _get_file_size(self, url: str) ->Optional[int]:
        """Get remote file size"""
        try:
            response = self.session.head(url, timeout=self.timeout)
            response.raise_for_status()
            return int(response.headers.get('Content-Length', 0))
        except Exception as e:
            warning(f"Failed to get file size: {e}")
            return None
    
    def download_file(self, download_info: DownloaderInfo)-> Tuple[bool, str]:
        """
        Download file with support for resumable downloads, hash verification and automatic retries
        
        Args:
            download_info: Download information object
            
        Returns:
            Tuple[bool, str]: (Success status, Message)
        """
        save_path = download_info.save_path
        url = download_info.url
        
        try:
            # Create root directory
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if already downloaded
            file_size = 0
            if save_path.exists():
                if self.verify_file(save_path, download_info.checksum):
                    info(f"File exists and verified: {save_path}")
                    return True, "File already downloaded"
                file_size = save_path.stat().st_size
            
            # Get remote file size
            total_size = self._get_file_size(url)
            if total_size is not None and file_size >= total_size:
                if self.verify_file(save_path, download_info.checksum):
                    return True, "File already downloaded"
                warning("Local file size abnormal, redownloading")
                file_size = 0
            
            # Resume download
            headers = {'Range' : f'btyes={file_size}-'} if file_size > 0 else {}
            
            # Retry loop
            for attempt in range(self.retries):
                try:
                    with self.session.get(
                        url,
                        stream=True,
                        headers=headers,
                        timeout=self.timeout
                    ) as response:
                        response.raise_for_status()
                        total_size = int(response.headers.get('Content-Length', 0)) + file_size
                        
                        with tqdm(
                            total=total_size,
                            initial=file_size,
                            unit='iB',
                            unit_scale=True,
                            unit_divisor=1024,
                            desc=f"Downloading {download_info.name} {download_info.version}"
                        ) as progress_bar:
                            mode = 'ab' if file_size > 0 else 'wb'
                            with open(save_path, mode) as f:
                                for chunk in response.iter_content(chunk_size=self.chunk_size):
                                    if chunk:
                                        f.write(chunk)
                                        progress_bar.update(len(chunk))
                        
                        if self.verify_file(save_path, download_info.checksum):
                            info(f"File downloaded successfully: {save_path}")
                            return True, "Download successful"
                        else:
                            raise RequestException("File verification failed")
                except RequestException as e:
                    if attempt < self.retries - 1:
                        delay = self.retry_delay * (2 ** attempt)
                        warning(f"Download failed ({e}), retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        raise
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            error(error_msg)
            
            # Clean up incomplete file
            if save_path.exists():
                try:
                    save_path.unlink()
                    info("Cleaned up incomplete file")
                except PermissionError:
                    warning("Unable to clean up incomplete file, may be in use by another process")
            return False, error_msg
        return False, "Unknown error"
        
    
    def download_files(self, download_infos: List[DownloaderInfo]) -> Dict[str, Tuple[bool, str]]:
        """
        Download multiple files
        
        Args:
            download_infos: List of download information objects
            
        Returns:
            Dict[str, Tuple[bool, str]]: Download results dictionary {component_name: (success_status, message)}
        """
        result = {}
        for info in download_infos:
            info(f"\nProcessing: {info.name} {info.version}")
            success, message = self.download_file(info)
            result[info.name] = (success, message)
            info("-"*60)
        return result