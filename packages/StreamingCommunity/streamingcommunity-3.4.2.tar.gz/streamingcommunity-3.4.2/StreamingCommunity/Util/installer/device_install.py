# 18.07.25

import os
import struct
import logging
from typing import Optional


# External library
from rich.console import Console


# Internal utilities
from .binary_paths import binary_paths


# Variable
console = Console()


class DeviceDownloader:
    def __init__(self):
        self.base_dir = binary_paths.ensure_binary_directory()

    def extract_png_chunk(self, png_with_wvd: str, out_wvd_path: str) -> bool:
        """Extract WVD data"""
        try:
            with open(png_with_wvd, "rb") as f: 
                data = f.read()
            pos = 8
            
            while pos < len(data):
                length = struct.unpack(">I", data[pos:pos+4])[0]
                chunk_type = data[pos+4:pos+8]
                chunk_data = data[pos+8:pos+8+length]

                if chunk_type == b"stEg":
                    with open(out_wvd_path, "wb") as f: 
                        f.write(chunk_data)
                    return True
                
                pos += 12 + length
            
            return False
            
        except Exception as e:
            logging.error(f"Error extracting PNG chunk: {e}")
            return False

    def _check_existing_wvd(self) -> Optional[str]:
        """Check for existing WVD files in binary directory."""
        try:
            if not os.path.exists(self.base_dir):
                return None

            # Look for any .wvd file first
            for file in os.listdir(self.base_dir):
                if file.lower().endswith('.wvd'):
                    wvd_path = os.path.join(self.base_dir, file)
                    if os.path.exists(wvd_path) and os.path.getsize(wvd_path) > 0:
                        logging.info(f"Found existing .wvd file: {file}")
                        return wvd_path
                
            return None
            
        except Exception as e:
            logging.error(f"Error checking existing WVD files: {e}")
            return None

    def _find_png_recursively(self, start_dir: str = ".") -> Optional[str]:
        """Find crunchyroll_etp_rt.png recursively starting from start_dir."""
        target_filename = "crunchyroll_etp_rt.png"
        
        try:
            for root, dirs, files in os.walk(start_dir):
                if target_filename in files:
                    png_path = os.path.join(root, target_filename)
                    logging.info(f"Found PNG file at: {png_path}")
                    return png_path
                    
            logging.warning(f"PNG file '{target_filename}' not found in '{start_dir}' and subdirectories")
            return None
            
        except Exception as e:
            logging.error(f"Error during recursive PNG search: {e}")
            return None

    def download(self) -> Optional[str]:
        """
        Main method to extract WVD file from PNG.
        """
        try:
            png_path = self._find_png_recursively()
            if not png_path:
                logging.error("PNG file not found, cannot extract device.wvd")
                return None

            device_wvd_path = os.path.join(self.base_dir, 'device.wvd')
            
            if self.extract_png_chunk(png_path, device_wvd_path):
                if os.path.exists(device_wvd_path) and os.path.getsize(device_wvd_path) > 0:
                    logging.info("Successfully extracted device.wvd from PNG")
                    return device_wvd_path
                else:
                    logging.error("Extraction completed but resulting file is invalid")
                    return None
            else:
                logging.error("Failed to extract device.wvd from PNG")
                return None
                
        except Exception as e:
            logging.error(f"Error during WVD extraction: {e}")
            return None


def check_device_wvd_path() -> Optional[str]:
    """
    Check for device.wvd file in binary directory and extract from PNG if not found.
    """
    try:
        downloader = DeviceDownloader()
        
        existing_wvd = downloader._check_existing_wvd()
        if existing_wvd:
            return existing_wvd
        
        logging.info("device.wvd not found, attempting extraction from PNG")
        return downloader.download()

    except Exception as e:
        logging.error(f"Error checking for device.wvd: {e}")
        return None