import os
import subprocess
import logging
from glob import glob

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
torrent_directory = 'examples/torrents'  # Change this to your directory with torrent files
output_directory = '~/Downloads'  # Change this if you want a different output directory
max_instances = 5  # Maximum number of instances to run

def run_torrent_client(torrent_file):
    # Construct the command to run your script
    command = [
        'python', 'examples\Client.py',  # Adjust if your script's name or python command is different
        '--torrent', torrent_file,
        '--output-directory', output_directory
    ]
    
    logging.info(f"Starting torrent client for {torrent_file}")
    # Run the command
    subprocess.Popen(command)

def main():
    # Find all torrent files in the specified directory
    torrent_files = glob(os.path.join(torrent_directory, '*.torrent'))
    
    if not torrent_files:
        logging.warning("No torrent files found in the specified directory.")
        return
    
    # Run up to max_instances of your script with different torrent files
    for torrent_file in torrent_files[:max_instances]:
        run_torrent_client(torrent_file)

if __name__ == '__main__':
    main()
