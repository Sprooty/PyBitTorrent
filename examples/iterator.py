import os
import subprocess
import logging
from glob import glob
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
torrent_directory = r'C:\Syncthing\Personal\Git\PyBitTorrent\examples\torrents'
output_directory = r'C:\Syncthing\Personal\Git\PyBitTorrent\examples\download'
max_instances = 25

def run_torrent_client(torrent_file):
    command = [
        'python', 'Client.py',
        '--torrent', torrent_file,
        '--output-directory', output_directory
    ]
    logging.info(f"Starting torrent client for {torrent_file}")
    return subprocess.Popen(command)  # Return the process

def main():
    torrent_files = glob(os.path.join(torrent_directory, '*.torrent'))

    if not torrent_files:
        logging.warning("No torrent files found in the specified directory.")
        return

    running_processes = []
    for torrent_file in torrent_files:
        if len(running_processes) < max_instances:
            process = run_torrent_client(torrent_file)
            running_processes.append((torrent_file, process))  # Keep track of the file and process
        else:
            # Wait for any process to complete and replace it with a new one
            while True:
                for i, (file, process) in enumerate(running_processes):
                    if process.poll() is not None:  # Check if the process has completed
                        logging.info(f"Torrent client for {file} completed")
                        running_processes.pop(i)  # Remove the completed process
                        break
                else:
                    time.sleep(1)  # Wait a bit before checking again
                    continue  # No process was completed yet, continue waiting
                break  # Exit the while loop to add a new process
        
        # At this point, there's room to add a new process or all torrents have been processed

    # Wait for all remaining processes to complete
    for file, process in running_processes:
        logging.info(f"Waiting for {file} to complete")
        process.wait()  # Wait for the process to complete

if __name__ == '__main__':
    main()
