import logging
from argparse import ArgumentParser
from PyBitTorrent.Bittorrent import TorrentClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Script for downloading torrent files
    """

    parser = ArgumentParser(main.__doc__)
    parser.add_argument('--torrent', type=str, help='Path of the Torrent file', required=True)
    parser.add_argument('--peers', type=str, help='Path to file contain peers (in the format ip:port for each line)')
    parser.add_argument('--output-directory', default='.', type=str, help='Path to the output directory')
    parser.add_argument('--use-progress-bar', action='store_true', default=False, help='should show progress bar')
    parser.add_argument('--max-peers', type=int, default=2000, help='Max connected peers')
    args = parser.parse_args()

    # Log the received arguments
    logging.info(f"Received arguments: Torrent file: {args.torrent}, Peers: {args.peers}, "
                 f"Output directory: {args.output_directory}, Use progress bar: {args.use_progress_bar}, "
                 f"Max peers: {args.max_peers}")

    # Create client from the BitTorrent Meta File
    torrent_client = TorrentClient(torrent=args.torrent, max_peers=args.max_peers,
                                   use_progress_bar=args.use_progress_bar, peers_file=args.peers,
                                   output_dir=args.output_directory)

    # Start downloading the file
    torrent_client.start()

if __name__ == '__main__':
    main()
