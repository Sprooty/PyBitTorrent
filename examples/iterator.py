import os
import subprocess
import logging
from glob import glob
import time
import platform

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Relative path configuration
base_path = os.path.dirname(__file__)  # Get the directory where the script is located
torrent_directory = os.path.join(base_path, '', 'torrents')
output_directory = os.path.join(base_path, '', 'download')
logging.info(f"Torrent Directory is {torrent_directory}")
logging.info(f"Output Directy is {output_directory}")
max_instances = 20

def run_torrent_client(torrent_file, output_directory):
    # Determine the correct Python command based on the operating system
    python_command = 'python' if platform.system() == 'Windows' else 'python3'

    # Dynamically get the directory where this script is located
    script_dir = os.path.dirname(os.path.realpath(__file__))

    # Correct the path to Client.py
    client_script = os.path.join(script_dir, 'Client.py')

    # Build the command with the appropriate Python command
    command = [
        python_command, client_script,
        '--torrent', torrent_file,
        '--output-directory', output_directory
    ]

    logging.info(f"Starting torrent client for {torrent_file} with output directory {output_directory}")
    try:
        return subprocess.Popen(command)  # Return the process
    except Exception as e:
        logging.error(f"Failed to start torrent client for {torrent_file}: {e}")


def main():
    torrent_files = glob(os.path.join(torrent_directory, '*.torrent'))

    if not torrent_files:
        logging.warning("No torrent files found in the specified directory.")
        return

    running_processes = []
    for torrent_file in torrent_files:
        if len(running_processes) < max_instances:
            process = run_torrent_client(torrent_file, output_directory)
            if process:
                running_processes.append((torrent_file, process))  # Keep track of the file and process
        else:
            # Wait for any process to complete and replace it with a new one
            while True:
                for i, (file, process) in enumerate(running_processes):
                    if process and process.poll() is not None:  # Check if the process has completed
                        logging.info(f"Torrent client for {file} completed with return code {process.returncode}")
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
        if process:
            process.wait()  # Wait for the process to complete
            logging.info(f"{file} completed with return code {process.returncode}")

if __name__ == '__main__':
    main()