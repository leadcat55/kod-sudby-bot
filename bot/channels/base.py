from abc import ABC, abstractmethod
from typing import List, Tuple, Optional


class Incoming(ABC):
    """Abstract incoming message interface"""
    
    @property
    @abstractmethod
    def text(self) -> str:
        """Get text from incoming message"""
        pass
    
    @abstractmethod
    def photo_bytes(self) -> Optional[bytes]:
        """Get photo bytes from incoming message"""
        pass


class Channel(ABC):
    """Abstract channel interface for multi-platform support"""
    
    @property
    @abstractmethod
    def user_key(self) -> str:
        """Unique user identifier (e.g., 'tg:123', 'vk:456')"""
        pass
    
    @property
    @abstractmethod
    def incoming(self) -> Incoming:
        """Get incoming message object"""
        pass
    
    @abstractmethod
    def send_text(self, text: str) -> None:
        """Send text message"""
        pass
    
    @abstractmethod
    def send_buttons(self, text: str, options: List[Tuple[str, str]]) -> None:
        """Send message with buttons. Options: [(payload, label), ...]"""
        pass
    
    @abstractmethod
    def send_photos(self, urls: List[str], caption: str) -> None:
        """Send photos with caption"""
        pass

    def send_document(self, file, filename: str) -> None:
        """Send document file"""
        pass

    def send_start_keyboard(self) -> None:
        """Show start keyboard (optional, platform-specific)"""
        pass
