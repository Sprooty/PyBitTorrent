import logging
import socket
import time
from threading import Thread
from typing import List
from PyBitTorrent.torwoldTrackerdb import insert_into_ips_table
from PyBitTorrent.torwoldTrackerdb import insert_into_torrent_ips_table
from PyBitTorrent.torwoldTrackerdb import insert_into_torrents_table
from PyBitTorrent.torwoldTrackerdb import search_infohash


from PyBitTorrent import Utils
from PyBitTorrent.Block import BlockStatus
from PyBitTorrent.Exceptions import (
    PieceIsPending,
    NoPeersHavePiece,
    NoPieceFound,
    PeerDisconnected,
    PieceIsFull,
    OutOfPeers,
    AllPeersChocked,
)
from PyBitTorrent.Message import (
    Handshake,
    KeepAlive,
    BitField,
    Unchoke,
    Request,
    PieceMessage,
    HaveMessage,
    Choke,
)
from PyBitTorrent.PeersManager import PeersManager
from PyBitTorrent.Piece import Piece, create_pieces
from PyBitTorrent.PiecesManager import DiskManager
from PyBitTorrent.TorrentFile import TorrentFile
from PyBitTorrent.TrackerFactory import TrackerFactory
from PyBitTorrent.TrackerManager import TrackerManager
from PyBitTorrent.Utils import generate_peer_id, read_peers_from_file


LISTENING_PORT = 43706
MAX_LISTENING_PORT = 43706
MAX_PEERS = 20000
REQUEST_INTERVAL = 0.2
ITERATION_SLEEP_INTERVAL = 0.001
LOGGING_NONE = 100


DEFAULT_TRACKER_URLS = [
    "udp://tracker.coppersurfer.tk:6969/announce",
    "udp://9.rarbg.to:2920/announce",
    "udp://tracker.opentrackr.org:1337",
    "udp://tracker.internetwarriors.net:1337/announce",
    "udp://tracker.leechers-paradise.org:6969/announce",
    "udp://tracker.coppersurfer.tk:6969/announce",
    "udp://tracker.pirateparty.gr:6969/announce",
    "udp://tracker.cyberia.is:6969/announce"
    "udp://47.ip-51-68-199.eu:6969/announce",
    "udp://9.rarbg.me:2780/announce",
    "udp://9.rarbg.to:2710/announce",
    "udp://9.rarbg.to:2730/announce",
    "udp://9.rarbg.to:2920/announce",
    "udp://open.stealth.si:80/announce",
    "udp://opentracker.i2p.rocks:6969/announce",
    "udp://tracker.coppersurfer.tk:6969/announce",
    "udp://tracker.cyberia.is:6969/announce",
    "udp://tracker.dler.org:6969/announce",
    "udp://tracker.internetwarriors.net:1337/announce",
    "udp://tracker.leechers-paradise.org:6969/announce",
    "udp://tracker.openbittorrent.com:6969/announce",
    "udp://tracker.opentrackr.org:1337",
    "udp://tracker.pirateparty.gr:6969/announce",
    "udp://tracker.tiny-vps.com:6969/announce",
    "udp://tracker.torrent.eu.org:451/announce"
    ]

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                    )


class TorrentClient:
    def __init__(self, torrent: str, max_peers: int = MAX_PEERS, use_progress_bar: bool = True, peers_file: str = None, output_dir: str = '.'):
        # Initial setup
        self.tracker_manager = None
        self.initialized = False  # Flag to indicate if initialization was successful

        self.peer_manager: PeersManager = PeersManager(max_peers)
        self.tracker_manager: TrackerManager
        self.id: bytes = generate_peer_id()
        self.listener_socket: socket.socket = socket.socket()
        self.port: int = LISTENING_PORT
        self.peers_file: str = peers_file
        self.pieces: List[Piece] = []
        self.should_continue = True
        self.use_progress_bar = use_progress_bar
        if use_progress_bar:
            logging.getLogger("BitTorrent").setLevel(LOGGING_NONE)

        logging.getLogger("BitTorrent").info(f"OUTPUT DIR IS {output_dir}")
        # decode the config file and assign it
        self.torrent = TorrentFile(torrent)
        logging.getLogger("BitTorrent").info(f"FILE NAME {self.torrent.file_name}")
        print(self.torrent.file_name)
        logging.getLogger("BitTorrent").info(f"Infohash is {self.torrent.hash}")
        self.piece_manager = DiskManager(output_dir, self.torrent)


        logging.getLogger("BitTorrent").info(f"CHECKING IF EXISTS IN DB")
        # This could be set based on a configuration file, command-line argument, or some other means
        check_infohash_existence = True  # Set this to False to disable checking

        self.torrent = TorrentFile(torrent)
        logging.getLogger("BitTorrent").info(f"FILE NAME {self.torrent.file_name}")
        print(self.torrent.file_name)
        logging.getLogger("BitTorrent").info(f"Infohash is {self.torrent.hash}")

        # Before initiating the check
        if check_infohash_existence:
            try:
                existing_torrent = search_infohash(self.torrent.hash)
                if existing_torrent:
                    logging.info(f"Infohash {self.torrent.hash} already exists in the database with details: {existing_torrent}. Skipping insertion.")
                    return  # Skip further processing
                else:
                    logging.info(f"Infohash {self.torrent.hash} does not exist in the database. Proceeding with insertion.")

            except Exception as e:
                logging.error(f"Error occurred while checking for info_hash: {e}")
                return  # Optionally return early in case of errors

        # Continue with initialization only if the early return hasn't happened
        # ... [rest of your initialization code, including setting up trackers] ...

        self.initialized = True  # Mark as successfully initialized
        self.piece_manager = DiskManager(output_dir, self.torrent)
        # ... [rest of your code for creating trackers and so on] ..
                # create tracker for each url of tracker in the config file
        trackers = []
        if "announce" in self.torrent.config:
            tracker = TrackerFactory.create_tracker(self.torrent.config["announce"])
            trackers.append(tracker)

        if "announce-list" in self.torrent.config:
            new_trackers = TrackerFactory.create_trackers(
                self.torrent.config["announce-list"]
            )
            trackers += new_trackers

         # If no trackers were added, use the default list
        if not trackers:
            for url in DEFAULT_TRACKER_URLS:
                tracker = TrackerFactory.create_tracker(url)
                trackers.append(tracker)    

        self.tracker_manager = TrackerManager(trackers)
        file_size, piece_size = self.torrent.length, self.torrent.piece_size
        self.pieces = create_pieces(file_size, piece_size)
        self.number_of_pieces = len(self.pieces)

    def start(self):
        if not self.initialized:
            logging.error("TorrentClient instance was not fully initialized.")
            return  # Do not proceed further

        if self.peers_file:
            logging.getLogger("BitTorrent").info("Reading peers from file")
            peers = read_peers_from_file(self.peers_file)
        else:
            peers = self.tracker_manager.get_peers(self.id, self.port, self.torrent)
            if len(peers) == 0:
                raise Exception("No peers found")

        logging.getLogger("BitTorrent").info(f"Number of peers: {len(peers)}")

        
        self.peer_manager.add_peers(peers)
        handshakes = Thread(
            target=self.peer_manager.send_handshakes, args=(self.id, self.torrent.hash)
        )
        requester = Thread(target=self.piece_requester)

        # Assuming self.peer_manager is an instance of PeersManager and is accessible in this scope

        # Get all IP values from peers
        all_ips = self.peer_manager.get_all_ips()
        logging.getLogger("BitTorrent").info(f"ALL IPS {all_ips}")

        # # Loop through each IP and check if it exists in the database, insert if it doesn't
        # for ip in all_ips:
        #     if not check_record_exists('IPs', f"ip = '{ip}'"):
        #         # IP does not exist, so insert it
        #         insert_into_ips_table(ip, 'NULL')  # Ensure 'NULL' is appropriate for your database schema
        #         logging.getLogger("BitTorrent").info(f'Inserted new IP into the database: {ip}')
        #     else:
        #         # IP already exists
        #         logging.getLogger("BitTorrent").info(f'This IP already exists in the database: {ip}')

     
        # Insert the torrent information and retrieve the TorrentID
        torrent_id = insert_into_torrents_table(self.torrent.file_name,self.torrent.hash)
        
        # Loop through each IP
        for ip in all_ips:
         # Insert or update IP information
         insert_into_ips_table(ip)  # Assuming country is unknown or handled elsewhere

         # Insert or update the relationship between the torrent and the IP
        for ip in all_ips:
            insert_into_torrent_ips_table(torrent_id, ip)


        #logging.getLogger("BitTorrent").info(f'Processed IP: {ip}')
        #handshakes.start()
        #requester.start()
        #self.progress_download()
        #handshakes.join()
        #requester.join()
        Utils.console.print("[green]GoodBye!")
        

        

    def progress_download(self):
        if self.use_progress_bar:
            for _ in progress.track(
                    range(len(self.pieces)),
                    description=f"Downloading {self.torrent.file_name}",
            ):
                self.handle_messages()
        else:
            for _ in range(len(self.pieces)):
                self.handle_messages()

    def handle_messages(self):
        while not self._all_pieces_full():
            try:
                # Utils.console.print.f'[purple]Waiting for message...')
                messages = self.peer_manager.receive_messages()
            except OutOfPeers:
                logging.getLogger("BitTorrent").error(
                    f"No peers found, sleep for 2 seconds"
                )
                time.sleep(2)
                continue
            except socket.error as e:
                logging.getLogger("BitTorrent").info(f"Unknown socket error: {e}")
                continue

            for peer, message in messages.items():
                if type(message) is Handshake:
                    peer.verify_handshake(message)

                elif type(message) is BitField:
                    logging.getLogger("BitTorrent").info(f"Got bitfield from {peer}")
                    peer.set_bitfield(message)

                elif type(message) is HaveMessage:
                    peer.set_have(message)

                elif type(message) is KeepAlive:
                    logging.getLogger("BitTorrent").debug(f"Got keep alive from {peer}")

                elif type(message) is Choke:
                    peer.set_choked()

                elif type(message) is Unchoke:
                    logging.getLogger("BitTorrent").debug(f"Received unchoke from {peer}")
                    peer.set_unchoked()

                elif type(message) is PieceMessage:
                    # "Got piece!", message)
                    if self.handle_piece(message):
                        return

                else:
                    logging.getLogger("BitTorrent").error(
                        f"Unknown message: {message.id}"
                    )  # should be error

    def piece_requester(self):
        """
        This function will run as different thread.
        Iterate over all the blocks of all the pieces
        in chronological order, and see if one of them is free.
        is yes - request it from random peer.
        """

        while self.should_continue:
            self.request_current_block()
            time.sleep(ITERATION_SLEEP_INTERVAL)  # wait between each piece request

        logging.getLogger("BitTorrent").info(f"Exiting the requesting loop...")
        self.piece_manager.close()

    def request_current_block(self):
        for piece in self.pieces:
            try:
                block = piece.get_free_block()
                peer = self.peer_manager.get_random_peer_by_piece(piece)
                request = Request(piece.index, block.offset, block.size)
                peer.send_message(request)
                block.set_requested()
                return

            except PieceIsPending:
                continue

            except PieceIsFull:
                continue

            except NoPeersHavePiece:
                logging.getLogger("BitTorrent").debug(
                    f"No peers have piece {piece.index}"
                )
                time.sleep(2.5)

            except AllPeersChocked:
                logging.getLogger("BitTorrent").debug(
                    f"All of "
                    f"{len(self.peer_manager.connected_peers)} peers is chocked"
                )
                time.sleep(2.5)

            except PeerDisconnected:
                logging.getLogger("BitTorrent").error(
                    f"Peer {peer} disconnected when requesting for piece"
                )
                self.peer_manager.remove_peer(peer)

        if self._all_pieces_full():
            self.should_continue = False

    def _all_pieces_full(self) -> bool:
        for piece in self.pieces:
            if not piece.is_full():
                return False

        return True

    def _get_piece_by_index(self, index):
        for piece in self.pieces:
            if piece.index == index:
                return piece

        raise NoPieceFound

    def handle_piece(self, pieceMessage: PieceMessage):
        try:
            if not len(pieceMessage.data):
                logging.getLogger("BitTorrent").debug("Empty piece:", pieceMessage.index)
                return

            piece = self._get_piece_by_index(pieceMessage.index)
            block = piece.get_block_by_offset(pieceMessage.offset)
            block.data = pieceMessage.data
            block.status = BlockStatus.FULL

            if piece.is_full():
                self.piece_manager.write_piece(piece, self.torrent.piece_size)
                self.pieces.remove(piece)
                if not self.use_progress_bar:
                    logging.getLogger("BitTorrent").info(
                        "Progress: {have}/{total} Unchoked peers: {peers_have}/{total_peers}".format(
                            have=self.piece_manager.written,
                            total=self.number_of_pieces,
                            peers_have=self.peer_manager.num_of_unchoked,
                            total_peers=len(self.peer_manager.connected_peers),
                        )
                    )

                del piece
                return True

        except PieceIsPending:
            logging.getLogger("BitTorrent").debug(
                f"Piece {pieceMessage.index} is pending"
            )

        except NoPieceFound:
            pass

        return False
