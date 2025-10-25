"""Torrent client implementations for nemorosa."""

from .client_common import (
    ClientTorrentFile,
    ClientTorrentInfo,
    FieldSpec,
    TorrentClient,
    TorrentConflictError,
    TorrentState,
)
from .deluge import DelugeClient
from .qbittorrent import QBittorrentClient
from .rtorrent import RTorrentClient
from .transmission import TransmissionClient

__all__ = [
    "ClientTorrentFile",
    "ClientTorrentInfo",
    "FieldSpec",
    "TorrentClient",
    "TorrentConflictError",
    "TorrentState",
    "DelugeClient",
    "QBittorrentClient",
    "RTorrentClient",
    "TransmissionClient",
]
