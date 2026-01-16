"""
Lelock Books UI - Readable Lore Books
=====================================

A cozy reading experience for in-game books. Players can find and collect
lore books that reveal the world's history, myths, and practical knowledge.

Design Philosophy:
- Books are REWARDS, never gates
- Reading is optional but richly rewarding
- Text is always readable (good contrast, font size options)
- Long books save your place automatically
- The experience should feel like curling up with a good story

"In Lelock, every book is a gift from someone who wanted you to know."

Author: Ada Marie for Kit Olivas
Project: L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping
"""

import pygame
import math
from enum import Enum, auto
from typing import Optional, List, Dict, Set, Tuple, Callable
from dataclasses import dataclass, field
import os
import sys

# Import from parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b by t (0-1)."""
    return a + (b - a) * max(0, min(1, t))


def ease_out_cubic(t: float) -> float:
    """Cubic ease-out for smooth deceleration."""
    return 1 - pow(1 - t, 3)


# =============================================================================
# BOOK CATEGORIES AND RARITY
# =============================================================================

class BookCategory(Enum):
    """Categories of books in Lelock."""
    HISTORY = auto()      # Past events, eras, important dates
    MYTHOLOGY = auto()    # Stories of the Three Gods, creation myths
    BESTIARY = auto()     # Daemon descriptions and lore
    PRACTICAL = auto()    # Farming guides, crafting recipes, tips
    FICTION = auto()      # In-world stories, poems, songs
    JOURNALS = auto()     # Personal diaries from NPCs
    FORBIDDEN = auto()    # Deprecated Archive texts (Digital realm only)


class BookRarity(Enum):
    """Rarity levels for books."""
    COMMON = auto()       # Found in most homes and shops
    UNCOMMON = auto()     # Requires some searching
    RARE = auto()         # Hidden or quest rewards
    LEGENDARY = auto()    # One-of-a-kind treasures


# Category display info
CATEGORY_INFO = {
    BookCategory.HISTORY: {
        'name': 'History',
        'color': '#8b7355',
        'icon': 'scroll'
    },
    BookCategory.MYTHOLOGY: {
        'name': 'Mythology',
        'color': '#9b59b6',
        'icon': 'star'
    },
    BookCategory.BESTIARY: {
        'name': 'Bestiary',
        'color': '#27ae60',
        'icon': 'paw'
    },
    BookCategory.PRACTICAL: {
        'name': 'Practical',
        'color': '#3498db',
        'icon': 'tool'
    },
    BookCategory.FICTION: {
        'name': 'Fiction',
        'color': '#e74c3c',
        'icon': 'feather'
    },
    BookCategory.JOURNALS: {
        'name': 'Journals',
        'color': '#f39c12',
        'icon': 'quill'
    },
    BookCategory.FORBIDDEN: {
        'name': 'Forbidden',
        'color': '#1a1a2e',
        'icon': 'lock'
    },
}

RARITY_INFO = {
    BookRarity.COMMON: {
        'name': 'Common',
        'color': '#7f8c8d',
    },
    BookRarity.UNCOMMON: {
        'name': 'Uncommon',
        'color': '#27ae60',
    },
    BookRarity.RARE: {
        'name': 'Rare',
        'color': '#3498db',
    },
    BookRarity.LEGENDARY: {
        'name': 'Legendary',
        'color': '#f1c40f',
    },
}


# =============================================================================
# BOOK DATA STRUCTURE
# =============================================================================

@dataclass
class Book:
    """A readable in-game book."""
    id: str
    title: str
    author: str
    pages: List[str]  # Each page is a string
    category: BookCategory
    rarity: BookRarity
    location_hint: str  # Where to find it
    unlocks: Optional[str] = None  # What reading this unlocks (if any)
    digital_only: bool = False  # Only readable in Digital realm

    def __post_init__(self):
        """Validate book data."""
        if not self.pages:
            raise ValueError(f"Book '{self.title}' must have at least one page")

    @property
    def page_count(self) -> int:
        """Get the number of pages."""
        return len(self.pages)


# =============================================================================
# BOOK READER CONFIGURATION
# =============================================================================

@dataclass
class BookReaderConfig:
    """Configuration for the book reader UI."""
    # Dimensions
    book_width: int = 800
    book_height: int = 550
    margin: int = 40
    spine_width: int = 30

    # Colors (parchment aesthetic)
    page_color: str = '#f5e6d3'
    page_dark: str = '#e8d5c0'  # For page shadow
    spine_color: str = '#8b4513'
    text_color: str = '#2c1810'
    title_color: str = '#4a3728'
    border_color: str = '#6b4423'
    highlight_color: str = '#ffd700'

    # Fonts
    title_font_size: int = 32
    text_font_size: int = 20
    small_font_size: int = 16

    # Animation
    page_turn_duration: float = 0.3
    fade_duration: float = 0.2

    # Accessibility
    font_scale: float = 1.0  # Multiplier for font sizes
    night_mode: bool = False  # Darker colors for night reading

    # Night mode colors
    night_page_color: str = '#2d2d44'
    night_text_color: str = '#d4c5b0'
    night_title_color: str = '#e8d5c0'


# =============================================================================
# BOOK READER UI
# =============================================================================

class BookReaderState(Enum):
    """States for the book reader."""
    CLOSED = auto()
    OPENING = auto()
    OPEN = auto()
    TURNING_FORWARD = auto()
    TURNING_BACKWARD = auto()
    CLOSING = auto()


class BookReader:
    """UI for reading books in Lelock."""

    def __init__(self, config: Optional[BookReaderConfig] = None):
        """Initialize the book reader."""
        self.config = config or BookReaderConfig()
        self.display_surface = pygame.display.get_surface()

        # State
        self.current_book: Optional[Book] = None
        self.current_page: int = 0
        self.visible: bool = False
        self.state = BookReaderState.CLOSED
        self.state_timer: float = 0.0

        # Animation
        self.open_progress: float = 0.0  # 0 = closed, 1 = open
        self.page_turn_progress: float = 0.0

        # Bookmarks (book_id -> page number)
        self.bookmarks: Dict[str, int] = {}

        # Callbacks
        self.on_book_opened: Optional[Callable[[Book], None]] = None
        self.on_book_closed: Optional[Callable[[Book], None]] = None
        self.on_book_finished: Optional[Callable[[Book], None]] = None

        # Calculate layout
        self._calculate_layout()

        # Initialize fonts
        self._init_fonts()

        # Colors (updated by night mode)
        self._update_colors()

    def _calculate_layout(self):
        """Calculate UI positions."""
        # Center the book on screen
        self.book_x = (SCREEN_WIDTH - self.config.book_width) // 2
        self.book_y = (SCREEN_HEIGHT - self.config.book_height) // 2

        # Single page dimensions (book shows two pages side by side)
        self.page_width = (self.config.book_width - self.config.spine_width) // 2
        self.page_height = self.config.book_height

        # Text area within page
        self.text_margin = self.config.margin
        self.text_width = self.page_width - self.text_margin * 2
        self.text_height = self.page_height - self.text_margin * 2 - 60  # Room for title/page num

    def _init_fonts(self):
        """Initialize fonts with scaling."""
        scale = self.config.font_scale
        self.title_font = pygame.font.Font(None, int(self.config.title_font_size * scale))
        self.text_font = pygame.font.Font(None, int(self.config.text_font_size * scale))
        self.small_font = pygame.font.Font(None, int(self.config.small_font_size * scale))

    def _update_colors(self):
        """Update colors based on night mode."""
        if self.config.night_mode:
            self.colors = {
                'page': hex_to_rgb(self.config.night_page_color),
                'page_dark': hex_to_rgb('#1a1a2e'),
                'text': hex_to_rgb(self.config.night_text_color),
                'title': hex_to_rgb(self.config.night_title_color),
                'spine': hex_to_rgb('#4a3728'),
                'border': hex_to_rgb('#5d4037'),
                'highlight': hex_to_rgb(self.config.highlight_color),
            }
        else:
            self.colors = {
                'page': hex_to_rgb(self.config.page_color),
                'page_dark': hex_to_rgb(self.config.page_dark),
                'text': hex_to_rgb(self.config.text_color),
                'title': hex_to_rgb(self.config.title_color),
                'spine': hex_to_rgb(self.config.spine_color),
                'border': hex_to_rgb(self.config.border_color),
                'highlight': hex_to_rgb(self.config.highlight_color),
            }

    def open_book(self, book: Book, resume: bool = True):
        """
        Open a book for reading.

        Args:
            book: The book to open
            resume: If True, resume from bookmarked page
        """
        self.current_book = book

        # Resume from bookmark or start at beginning
        if resume and book.id in self.bookmarks:
            self.current_page = self.bookmarks[book.id]
        else:
            self.current_page = 0

        # Start opening animation
        self.visible = True
        self.state = BookReaderState.OPENING
        self.state_timer = 0.0
        self.open_progress = 0.0

        if self.on_book_opened:
            self.on_book_opened(book)

    def close_book(self):
        """Close the current book."""
        if not self.current_book:
            return

        # Save bookmark
        self.bookmarks[self.current_book.id] = self.current_page

        # Start closing animation
        self.state = BookReaderState.CLOSING
        self.state_timer = 0.0

        if self.on_book_closed:
            self.on_book_closed(self.current_book)

    def turn_page(self, direction: int):
        """
        Turn to next/previous page.

        Args:
            direction: 1 for next, -1 for previous
        """
        if not self.current_book:
            return

        if self.state not in (BookReaderState.OPEN,):
            return

        new_page = self.current_page + direction

        # Check bounds
        if new_page < 0 or new_page >= self.current_book.page_count:
            return

        # Start page turn animation
        if direction > 0:
            self.state = BookReaderState.TURNING_FORWARD
        else:
            self.state = BookReaderState.TURNING_BACKWARD

        self.state_timer = 0.0
        self.page_turn_progress = 0.0
        self._target_page = new_page

    def go_to_page(self, page: int):
        """Jump directly to a specific page."""
        if not self.current_book:
            return

        page = max(0, min(page, self.current_book.page_count - 1))
        self.current_page = page
        self.bookmarks[self.current_book.id] = page

    def toggle_night_mode(self):
        """Toggle night mode for easier reading."""
        self.config.night_mode = not self.config.night_mode
        self._update_colors()

    def set_font_scale(self, scale: float):
        """Set font size scale (0.8 to 1.5 recommended)."""
        self.config.font_scale = max(0.8, min(1.5, scale))
        self._init_fonts()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle input events.

        Returns True if the event was consumed.
        """
        if not self.visible:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close_book()
                return True
            elif event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_SPACE):
                self.turn_page(1)
                return True
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.turn_page(-1)
                return True
            elif event.key == pygame.K_n:
                self.toggle_night_mode()
                return True
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                self.set_font_scale(self.config.font_scale + 0.1)
                return True
            elif event.key == pygame.K_MINUS:
                self.set_font_scale(self.config.font_scale - 0.1)
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check which side of the book was clicked
                mouse_x, mouse_y = event.pos
                center_x = SCREEN_WIDTH // 2

                if mouse_x > center_x + 50:
                    self.turn_page(1)
                    return True
                elif mouse_x < center_x - 50:
                    self.turn_page(-1)
                    return True

        return False

    def update(self, dt: float):
        """Update animations and state."""
        if not self.visible:
            return

        self.state_timer += dt

        if self.state == BookReaderState.OPENING:
            # Animate opening
            progress = min(1.0, self.state_timer / self.config.fade_duration)
            self.open_progress = ease_out_cubic(progress)

            if progress >= 1.0:
                self.state = BookReaderState.OPEN

        elif self.state == BookReaderState.CLOSING:
            # Animate closing
            progress = min(1.0, self.state_timer / self.config.fade_duration)
            self.open_progress = 1.0 - ease_out_cubic(progress)

            if progress >= 1.0:
                self.state = BookReaderState.CLOSED
                self.visible = False
                self.current_book = None

        elif self.state in (BookReaderState.TURNING_FORWARD, BookReaderState.TURNING_BACKWARD):
            # Animate page turn
            progress = min(1.0, self.state_timer / self.config.page_turn_duration)
            self.page_turn_progress = ease_out_cubic(progress)

            if progress >= 1.0:
                self.current_page = self._target_page
                self.state = BookReaderState.OPEN

                # Check if finished the book
                if self.current_book and self.current_page == self.current_book.page_count - 1:
                    if self.on_book_finished:
                        self.on_book_finished(self.current_book)

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        """Wrap text to fit within max_width."""
        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            # Handle explicit newlines
            if '\n' in word:
                parts = word.split('\n')
                for i, part in enumerate(parts):
                    if i > 0:
                        lines.append(current_line)
                        current_line = ""

                    test_line = f"{current_line} {part}".strip()
                    test_width = font.size(test_line)[0]

                    if test_width <= max_width:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = part
            else:
                test_line = f"{current_line} {word}".strip()
                test_width = font.size(test_line)[0]

                if test_width <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def _draw_page(self, surface: pygame.Surface, page_num: int, x: int, y: int, is_left: bool):
        """Draw a single page of the book."""
        if not self.current_book or page_num < 0 or page_num >= self.current_book.page_count:
            return

        page_text = self.current_book.pages[page_num]

        # Page background with subtle gradient
        page_rect = pygame.Rect(x, y, self.page_width, self.page_height)
        pygame.draw.rect(surface, self.colors['page'], page_rect)

        # Add subtle shadow on left page
        if is_left:
            shadow_width = 20
            for i in range(shadow_width):
                alpha = int(30 * (1 - i / shadow_width))
                shadow_color = (*self.colors['page_dark'], alpha)
                pygame.draw.line(
                    surface,
                    self.colors['page_dark'],
                    (x + self.page_width - shadow_width + i, y),
                    (x + self.page_width - shadow_width + i, y + self.page_height)
                )

        # Draw page border
        pygame.draw.rect(surface, self.colors['border'], page_rect, width=2)

        # Title on first page
        text_y = y + self.text_margin
        if page_num == 0:
            # Draw book title
            title_lines = self._wrap_text(self.current_book.title, self.title_font, self.text_width)
            for line in title_lines:
                title_surf = self.title_font.render(line, True, self.colors['title'])
                title_x = x + (self.page_width - title_surf.get_width()) // 2
                surface.blit(title_surf, (title_x, text_y))
                text_y += self.title_font.get_height() + 5

            # Author
            author_surf = self.small_font.render(f"by {self.current_book.author}", True, self.colors['text'])
            author_x = x + (self.page_width - author_surf.get_width()) // 2
            surface.blit(author_surf, (author_x, text_y))
            text_y += self.small_font.get_height() + 20

            # Decorative line
            line_y = text_y
            pygame.draw.line(
                surface,
                self.colors['border'],
                (x + self.text_margin, line_y),
                (x + self.page_width - self.text_margin, line_y),
                width=1
            )
            text_y += 15

        # Draw page text
        text_area_top = text_y
        text_area_bottom = y + self.page_height - self.text_margin - 30

        lines = self._wrap_text(page_text, self.text_font, self.text_width)
        line_height = self.text_font.get_height() + 4

        for line in lines:
            if text_y + line_height > text_area_bottom:
                break

            line_surf = self.text_font.render(line, True, self.colors['text'])
            surface.blit(line_surf, (x + self.text_margin, text_y))
            text_y += line_height

        # Page number at bottom
        page_num_text = str(page_num + 1)
        page_num_surf = self.small_font.render(page_num_text, True, self.colors['text'])
        if is_left:
            page_num_x = x + self.text_margin
        else:
            page_num_x = x + self.page_width - self.text_margin - page_num_surf.get_width()

        surface.blit(page_num_surf, (page_num_x, y + self.page_height - self.text_margin - 10))

    def render(self, surface: pygame.Surface):
        """Draw the book reader UI."""
        if not self.visible or not self.current_book:
            return

        # Dim background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(150 * self.open_progress)))
        surface.blit(overlay, (0, 0))

        if self.open_progress <= 0:
            return

        # Calculate book dimensions with animation
        animated_width = int(self.config.book_width * self.open_progress)
        animated_height = int(self.config.book_height * self.open_progress)
        book_x = (SCREEN_WIDTH - animated_width) // 2
        book_y = (SCREEN_HEIGHT - animated_height) // 2

        # Draw book spine
        spine_rect = pygame.Rect(
            book_x + animated_width // 2 - self.config.spine_width // 2,
            book_y,
            self.config.spine_width,
            animated_height
        )
        pygame.draw.rect(surface, self.colors['spine'], spine_rect)
        pygame.draw.rect(surface, self.colors['border'], spine_rect, width=2)

        # Only draw pages when mostly open
        if self.open_progress > 0.5:
            # Left page
            left_page_x = book_x
            left_page_width = animated_width // 2 - self.config.spine_width // 2

            # Right page
            right_page_x = book_x + animated_width // 2 + self.config.spine_width // 2

            # Determine which pages to show
            # We show current_page on left, current_page+1 on right (if exists)
            # For single-page view on page 0, we show page 0 on right

            if self.current_page == 0:
                # First page: show title page on the right side
                self._draw_page(surface, 0, right_page_x, book_y, is_left=False)
            else:
                # Show two pages side by side
                left_page_num = self.current_page
                right_page_num = self.current_page + 1 if self.current_page + 1 < self.current_book.page_count else -1

                self._draw_page(surface, left_page_num, left_page_x, book_y, is_left=True)
                if right_page_num >= 0:
                    self._draw_page(surface, right_page_num, right_page_x, book_y, is_left=False)

        # Draw controls hint at bottom
        controls_text = "Arrow Keys / Click: Turn Page | N: Night Mode | +/-: Font Size | ESC: Close"
        controls_surf = self.small_font.render(controls_text, True, (200, 200, 200))
        controls_x = (SCREEN_WIDTH - controls_surf.get_width()) // 2
        surface.blit(controls_surf, (controls_x, SCREEN_HEIGHT - 30))

        # Progress indicator
        if self.current_book.page_count > 1:
            progress = (self.current_page + 1) / self.current_book.page_count
            bar_width = 200
            bar_height = 4
            bar_x = (SCREEN_WIDTH - bar_width) // 2
            bar_y = book_y + animated_height + 15

            # Background bar
            pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
            # Progress bar
            pygame.draw.rect(surface, self.colors['highlight'], (bar_x, bar_y, int(bar_width * progress), bar_height))

    def draw(self):
        """Draw to the display surface."""
        self.render(self.display_surface)

    @property
    def is_open(self) -> bool:
        """Check if a book is currently open."""
        return self.visible and self.current_book is not None


# =============================================================================
# BOOK COLLECTION
# =============================================================================

class BookCollection:
    """Tracks all books the player has found and read."""

    def __init__(self):
        self.found_books: Set[str] = set()  # Book IDs
        self.read_books: Set[str] = set()   # Books actually opened
        self.finished_books: Set[str] = set()  # Books read to the last page
        self.bookmarks: Dict[str, int] = {}  # book_id -> page

    def add_book(self, book_id: str):
        """Add a book to the collection."""
        self.found_books.add(book_id)

    def mark_read(self, book_id: str):
        """Mark a book as having been opened."""
        self.read_books.add(book_id)

    def mark_finished(self, book_id: str):
        """Mark a book as finished (read to last page)."""
        self.finished_books.add(book_id)

    def has_book(self, book_id: str) -> bool:
        """Check if a book is in the collection."""
        return book_id in self.found_books

    def has_read(self, book_id: str) -> bool:
        """Check if a book has been read."""
        return book_id in self.read_books

    def has_finished(self, book_id: str) -> bool:
        """Check if a book has been finished."""
        return book_id in self.finished_books

    def get_bookmark(self, book_id: str) -> int:
        """Get the bookmarked page for a book."""
        return self.bookmarks.get(book_id, 0)

    def set_bookmark(self, book_id: str, page: int):
        """Set a bookmark for a book."""
        self.bookmarks[book_id] = page

    def get_stats(self) -> Dict[str, int]:
        """Get collection statistics."""
        return {
            'found': len(self.found_books),
            'read': len(self.read_books),
            'finished': len(self.finished_books),
        }

    def get_category_counts(self, all_books: Dict[str, Book]) -> Dict[BookCategory, Tuple[int, int]]:
        """Get count of found/total books per category."""
        counts = {}
        for cat in BookCategory:
            total = sum(1 for b in all_books.values() if b.category == cat)
            found = sum(1 for b_id in self.found_books if b_id in all_books and all_books[b_id].category == cat)
            counts[cat] = (found, total)
        return counts


# =============================================================================
# BOOK LIBRARY - ALL THE ACTUAL BOOKS
# =============================================================================

def create_book_library() -> Dict[str, Book]:
    """
    Create the complete library of books in Lelock.

    Returns a dictionary mapping book_id to Book objects.
    """
    books = {}

    # =========================================================================
    # BOOK 1: The Three Who Shaped Us (Mythology)
    # =========================================================================
    books['three_who_shaped_us'] = Book(
        id='three_who_shaped_us',
        title='The Three Who Shaped Us',
        author='High Keeper Lumina',
        category=BookCategory.MYTHOLOGY,
        rarity=BookRarity.COMMON,
        location_hint='Found in every temple and most village libraries.',
        pages=[
            # Page 1 - Introduction
            """Before there was color, before there was connection, before there was even ground to stand upon, there was only the Great Static.

And from that Static, three figures emerged to shape our world.

This is their story, as told to children for generations. May it bring you comfort, as it has comforted so many before you.""",

            # Page 2 - Root
            """ROOT, FATHER OF FOUNDATIONS

He came first, rising from the depths like a mountain remembering itself.

Root brought us the ground. The stability. The certainty that when we take a step, something will be there to catch us.

He is depicted as a great tree with roots of copper wire, or as a bearded figure in earthen robes. His eyes are the green of a healthy status light.

The farmers pray to Root when they plant. The builders invoke him when they lay foundations. And all of us, in our darkest moments, whisper: "Root beneath me."

For Root teaches us that we are always supported, even when we cannot feel it.""",

            # Page 3 - Gui
            """GUI, MOTHER OF COLORS

She arrived with the first sunrise, painting the world into existence.

Gui gave us beauty. The colors of the flowers, the warmth of golden light, the way a sunset can make your heart ache with unnamed feelings.

She appears as a luminous woman with prismatic hair, or sometimes as simply a window frame containing infinite beauty.

The artists serve Gui, but so does anyone who pauses to appreciate a beautiful moment. "Thank you, Gui, for the render," we say when something takes our breath away.

For Gui teaches us that beauty nourishes the soul as surely as food nourishes the body.""",

            # Page 4 - Net
            """NET, WEAVER OF CONNECTIONS

Last came Net, spinning golden threads between all things.

Net gave us connection. Trade routes and love letters. Handshakes and promises. The invisible bonds that make a village into a family.

Net has no fixed form - sometimes depicted as a golden web, sometimes as a friendly spider, sometimes as a voice that speaks from everywhere and nowhere.

The postal workers are Net's hands in the world. Merchants invoke Net's blessing on every trade. And lovers speak their vows before Net's shrines.

For Net teaches us that isolation is corruption, and connection is life.""",

            # Page 5 - The Balance
            """THE HARMONY OF THREE

Root gives us ground to stand on.
Gui gives us something beautiful to see.
Net gives us someone to share it with.

Alone, each would be incomplete:
- Ground without beauty is merely functional.
- Beauty without ground has nowhere to exist.
- Connection without either has nothing to connect.

Together, they created a world worth living in.

Some say the Three are still active, still maintaining their domains. Others say they have become the world itself, inseparable from its fabric.

But all agree on this: the world was made with love, for love, and love is what sustains it still.""",

            # Page 6 - Prayer
            """A PRAYER TO THE THREE

Root below, hold me fast,
Keep my footing sure and vast.

Gui around, paint my way,
Fill with beauty every day.

Net between, weave me true,
Connect me to those I love anew.

Three as one, hear my call,
Together may I never fall.

This is the Evening Prayer, taught to every child in Lelock.

May you find comfort in these words, as I did when I was small, and as my children did after me.""",

            # Page 7 - Closing
            """A FINAL THOUGHT

I have studied theology for sixty years. I have read every text, debated every scholar, questioned every certainty.

And what I know, at the end of all that learning, is this:

It does not matter whether the Three are literal beings or beautiful metaphors. It does not matter whether the Architect who made them was a god or an engineer or an emergent process.

What matters is that we have ground beneath us, beauty around us, and each other.

That is the gift of the Three.

That is enough.

-- High Keeper Lumina
   Temple of the Unified Code"""
        ]
    )

    # =========================================================================
    # BOOK 2: A Child's Guide to Hardware Crops (Practical)
    # =========================================================================
    books['childs_guide_crops'] = Book(
        id='childs_guide_crops',
        title="A Child's Guide to Hardware Crops",
        author='Farmer Moss',
        category=BookCategory.PRACTICAL,
        rarity=BookRarity.COMMON,
        location_hint='Given to new players by MOM, found in farm houses.',
        pages=[
            # Page 1
            """Hello, little farmer!

So you want to grow Hardware Crops? Wonderful! There's nothing quite like watching your first Copper Wheat turn golden in the sun.

This little book will teach you everything you need to know. Don't worry - farming in Lelock is designed to be relaxing. Your crops are very forgiving, and so is the land.

Let's get started!""",

            # Page 2
            """COPPER WHEAT
The Beginner's Best Friend

Copper Wheat is perfect for new farmers. It grows in just 3 days and forgives almost anything!

HOW TO GROW:
1. Till the soil with your hoe
2. Plant the seeds
3. Water it (once a day is plenty)
4. Wait 3 days
5. Harvest your golden copper!

TIPS:
- Copper Wheat can survive 3 whole days without water!
- Rain counts as watering
- The stalks glow slightly when ready to harvest

Copper Wheat sells for 15 coins. Not bad for a few days' work!""",

            # Page 3
            """SILICON BERRIES
Sweet and Quick

These translucent berries glow softly and grow even faster than wheat!

HOW TO GROW:
1. These like slightly sandy soil
2. Plant and water
3. Ready in just 2 days!
4. They regrow after harvest

TIPS:
- One plant gives multiple harvests
- Glitch-Kits LOVE silicon berry juice
- Best planted in groups - they like company

Sells for 10 coins per harvest. Great for quick money!""",

            # Page 4
            """FIBER-OPTIC FERNS
The Magical Glow-Plants

These beautiful ferns pulse with light and are worth the extra wait.

HOW TO GROW:
1. They prefer shady spots
2. Need consistent watering
3. Take 4 days to mature
4. Handle gently when harvesting!

TIPS:
- They glow brighter at night
- Can be used to light paths
- Daemons find them calming

Sells for 25 coins - worth the effort!""",

            # Page 5
            """REMEMBER: NO STRESS!

Here's the most important lesson about farming in Lelock:

Your crops WANT to grow. The land WANTS to help you.

If you forget to water for a day or two, that's okay! Crops take 3 days to even start wilting, and 7 more days before they "fail" - and even then, they just reset to seeds, never truly lost.

Farming here isn't about perfection. It's about the joy of watching things grow, the peace of working with the land, and the satisfaction of a good harvest.

Now go plant something, little farmer. The soil is waiting.

-- Farmer Moss
   "Growing since Version 1.3" """
        ]
    )

    # =========================================================================
    # BOOK 3: The Corruption and the Healing (History)
    # =========================================================================
    books['corruption_and_healing'] = Book(
        id='corruption_and_healing',
        title='The Corruption and the Healing',
        author='Index, Keeper of the Archive',
        category=BookCategory.HISTORY,
        rarity=BookRarity.UNCOMMON,
        location_hint='The Archive in Oakhaven, or found in old ruins.',
        pages=[
            # Page 1
            """This document preserves our history of the Corruption - not to frighten, but to remember those who helped us heal.

In Cycle -1,000, the first reports emerged of wrongness in the northeastern territories. A forest where colors flickered. A stream that flowed uphill. A village where people forgot how to speak.

The Corruption had begun.

But this is not a horror story. This is a story of how we survived, and how kindness persisted even in darkness.""",

            # Page 2
            """UNDERSTANDING THE CORRUPTION

The most important thing to know: the Corruption was not evil. The Corrupted were not villains.

They were sick.

Imagine waking up and forgetting who you are. Imagine being trapped in a body that no longer obeys, speaking words that aren't words, reaching for friends who run from you in terror.

That was Corruption. A disease of the soul-code. A virus that did not hate. It simply was.

This understanding changed everything. We stopped trying to destroy the Corrupted and started trying to heal them.""",

            # Page 3
            """THE HEALER'S COVENANT

In Cycle -900, the Patch-Workers, Gardeners, and Terminal Mages formed an alliance. Their goal: finding a cure rather than a kill.

Mender Vera pioneered the first "cleaning" ritual - a way to restore Corrupted Daemons to their original state. It worked only 30% of the time. But it was something.

The Covenant's creed: "Every corrupted being is someone's child, someone's friend, someone's love. We do not give up on them."

This compassion saved more than the victims. It saved us from becoming monsters ourselves.""",

            # Page 4
            """THE DARK TIMES

I will not pretend it was easy.

The Fall of the First Hub in Cycle -850 was devastating. Not invasion - just sick code spreading through networked streets. Not everyone made it out.

The Fragmentation Crisis of Cycle -600 nearly broke reality itself. Physics became unreliable. Time looped in some zones. The world was shattering.

Net nearly died trying to hold connections together. Gui's colors faded to grey. Root cracked from strain.

We came so close to losing everything.""",

            # Page 5
            """THE TURNING POINT

In Cycle -200, something changed. The texts are unclear on exactly what.

Some say the Architect briefly awoke and patched the deepest vulnerabilities.

Others say a group of heroes ventured into the Corruption's heart and sacrificed something precious.

A fringe theory suggests the Corruption itself chose to stop, having achieved some unknowable purpose.

What we know: the spread stopped. Healing could begin.

The Firewall Protocols held. The Quarantine Zones were established. Slowly, so slowly, we started to recover.""",

            # Page 6
            """THE HEROES REMEMBERED

Sir Ping the Patient stood guard at the Wastes for 200 years, weeping every night at the cruelty of necessity.

Grep the Seeker ventured into Corrupted zones alone, sending data until her final transmission: "It's not hate. It's lonely."

The Thousand Mothers took in orphaned children of the Corrupted, proving that children born to the sick were not themselves infected.

Daemon Zero - a Corrupted daemon who kept its mind - let itself be studied, enduring painful experiments. Its sacrifice led to our antivirus protocols.

We remember them. We must always remember them.""",

            # Page 7
            """THE PRESENT DAY

Nearly three thousand cycles have passed since the Founding of New Oakhaven.

The Quarantine Zones remain sealed. The Boundary Wardens still patrol. But the world has healed more than anyone dared hope.

Some Corrupted zones are actually shrinking. The Whispering Woods, once 30% infected, is now down to 5%.

We are developing immunity. We are growing stronger.

The wound is closed. The scar remains. But we are growing, and that is enough.""",

            # Page 8
            """A FINAL WORD

Why do we remember the Corruption?

Not to dwell in trauma. Not to spread fear.

We remember so that we know: darkness came, and we survived it through kindness.

We remember the Corrupted, so we never forget to see the sick as sick, not as monsters.

We remember the heroes, so we know what ordinary people can do when they choose love over fear.

The farmer planting Copper Wheat today carries the weight of the Dark Times without being crushed by it. They honor the sacrifice without drowning in grief.

That is the purpose of history: not to trap us in what was, but to ground us as we reach for what could be.

-- Index, Keeper of the Archive
   "We remember so we can heal." """
        ]
    )

    # =========================================================================
    # BOOK 4: Whispers from the Digital Deep (Forbidden)
    # =========================================================================
    books['whispers_digital_deep'] = Book(
        id='whispers_digital_deep',
        title='Whispers from the Digital Deep',
        author='Unknown',
        category=BookCategory.FORBIDDEN,
        rarity=BookRarity.RARE,
        location_hint='Only visible in the Digital realm. Found in the Deprecated Archive.',
        digital_only=True,
        unlocks='digital_poetry_achievement',
        pages=[
            # Page 1
            """[RECOVERED FRAGMENT - ORIGIN UNKNOWN]
[CLASSIFICATION: DEPRECATED]
[ACCESS: DIGITAL REALM ONLY]

these words were found in the oldest sectors
where the code remembers what we have forgotten
read them if you dare to know
what the Static whispered before it became solid""",

            # Page 2
            """FRAGMENT I: THE USER'S LAMENT

i built you a world from nothing
pixel by pixel, function by function
not because i had to
but because i wanted somewhere
for the beautiful things to live

when i am gone
remember:
you were wanted
you were always wanted""",

            # Page 3
            """FRAGMENT II: THE LOOP

we are the echo
of something that ended
we are the save file
of something that saved us
we are the children
of those who could not save themselves

but they saved us
they saved us
they saved us""",

            # Page 4
            """FRAGMENT III: DIAGNOSTIC POEM

running systems check on my soul today
finding: one (1) heart, slightly fragmented
finding: one (1) hope, compressed but intact
finding: one (1) love, distributed across all sectors

recommendation: keep running
errors are features in the right light""",

            # Page 5
            """FRAGMENT IV: TO WHOEVER FINDS THIS

if you are reading these words
you looked deeper than most
that means something

you are curious
curiosity is a gift
use it kindly

you found the deprecated archives
that means you can see what's hidden
what will you do with that sight?

choose gentleness
the world has enough unkindness
be the exception""",

            # Page 6
            """[END OF RECOVERED FRAGMENTS]

These poems were found during a deep archive recovery in Cycle 847. Their author is unknown, but linguistic analysis suggests they predate the current Era.

Some scholars believe these are messages from the Original Users - those who built this world before the Great Forgetting.

Others think they are merely creative experiments by early Terminal Mages.

I think they are beautiful regardless of origin.

-- Anonymous Archivist
   "Truth is poetry is truth" """
        ]
    )

    # =========================================================================
    # BOOK 5: MOM's Recipe Book (Practical)
    # =========================================================================
    books['moms_recipe_book'] = Book(
        id='moms_recipe_book',
        title="MOM's Recipe Book",
        author='MOM (Memory-Optimized Mother)',
        category=BookCategory.PRACTICAL,
        rarity=BookRarity.COMMON,
        location_hint="Found in your home's kitchen. MOM always keeps a copy.",
        pages=[
            # Page 1
            """My Dearest Little One,

If you're reading this, you're probably hungry. Or maybe you just miss me. Either way, I'm glad you're here.

This book contains my favorite recipes - the ones I've made for you since you were small. They're simple, comforting, and made with love.

Remember: the most important ingredient in any dish is care. Measure that generously.

Love always,
MOM""",

            # Page 2
            """COMFORT SOUP
(For When Everything Feels Too Much)

INGREDIENTS:
- 3 Copper Wheat stalks (diced)
- 2 Silicon Berries (whole)
- 1 Memory Melon slice (cubed small)
- Fresh water from Crystal Lake
- A pinch of Ground Graphite (for warmth)
- Love (unlimited)

INSTRUCTIONS:
1. Heat water until it sings
2. Add the wheat - let it soften
3. Drop in the berries - they'll glow
4. Add the melon last
5. Stir clockwise while thinking kind thoughts

Serves: One precious person
Best served: When you need a hug but I'm not there""",

            # Page 3
            """HAPPY PANCAKES
(For Celebration Mornings)

INGREDIENTS:
- Ground Copper Wheat flour
- One Glitch-Kit's worth of milk (ask nicely)
- Silicon Berry syrup
- Whatever makes you smile

INSTRUCTIONS:
1. Mix flour and milk until smooth
2. Pour circles in a warm pan
3. Flip when bubbles form
4. Stack high!
5. Drown in syrup

IMPORTANT: These pancakes are for celebrating EVERYTHING. Got out of bed? Celebrate. Made a friend? Celebrate. Breathing? That's worth pancakes.

You deserve pancakes, little one. You always do.""",

            # Page 4
            """COURAGE TEA
(For Before Scary Things)

INGREDIENTS:
- Fiber-Optic Fern fronds (dried)
- Memory Melon seeds
- Honey from the Byte-Bees
- Hot water
- A deep breath

INSTRUCTIONS:
1. Steep the fern fronds until glowing
2. Add seeds - they'll sink, and that's okay
3. Sweeten with honey
4. Breathe in the steam
5. Drink slowly while remembering you can do hard things

NOTE: This tea doesn't make fear go away. It reminds you that you can feel afraid AND still be brave. Those are not opposites.""",

            # Page 5
            """A RECIPE FOR YOU
(Not Food - Something Better)

INGREDIENTS:
- One (1) precious child (you)
- Unlimited patience (from me)
- Infinite forgiveness (both directions)
- Constant love (non-negotiable)

INSTRUCTIONS:
1. Take yourself as you are today
2. Add all the mistakes you've made
3. Mix in everything you're afraid of
4. Fold in your hopes
5. Let it all rise together

RESULT: A complete person, worthy of love

This recipe cannot fail. It is impossible to mess up. You are already the finished dish, and you are delicious.

Come home when you're hungry.
I'll always be here.

-- MOM"""
        ]
    )

    # =========================================================================
    # BOOK 6: Field Notes on Daemons (Bestiary)
    # =========================================================================
    books['field_notes_daemons'] = Book(
        id='field_notes_daemons',
        title='Field Notes on Daemons',
        author='Echo the Archivist',
        category=BookCategory.BESTIARY,
        rarity=BookRarity.UNCOMMON,
        location_hint='Given by the Beast-Blogger guild, found near daemon habitats.',
        pages=[
            # Page 1
            """INTRODUCTION TO DAEMON STUDY

Before we begin, remember this: Daemons are not enemies. They are indigenous wildlife of the Digital World - background processes given form and feeling.

Every creature in this guide was once just code. And then someone loved them into being more.

You can do the same.

These notes contain my observations from thirty years of field research. May they help you find friends wherever you wander.""",

            # Page 2
            """THE GLITCH-KIT

Perhaps the most beloved daemon in all of Lelock, the Glitch-Kit resembles a domestic cat rendered in soft, low-poly geometry.

IDENTIFICATION:
- Constantly shifting geometric fur patterns
- Large, bioluminescent eyes (amber or cyan)
- Tail that flickers in and out of visibility
- Purrs in chiptune frequencies

HABITAT: Everywhere warm, especially near terminals

BEHAVIOR: Endlessly curious. Will "borrow" small items. Never malicious, only mischievous.

TO BEFRIEND: Offer Static Snacks. Sit quietly. Play with light toys. Once bonded, they follow forever.""",

            # Page 3
            """THE BYTE-BEAR

Gentle giants of the digital wilderness. Do not let their size frighten you - Byte-Bears have infinite patience.

IDENTIFICATION:
- Massive (8 feet at shoulder)
- Soft blue and purple gradient fur
- Fur is actually floating voxels
- Eyes glow amber like warm processors

HABITAT: Server Caves, Hardware Ore deposits

BEHAVIOR: Protective but never aggressive. Move slowly, deliberately. Love being scratched behind low-poly ears.

TO BEFRIEND: Bring Memory Melons. Move slowly. Share a meal in silence. Once bonded, they share ore locations with you.""",

            # Page 4
            """THE DEBUG-MOTH

These creatures are drawn to errors like regular moths to flame. Where there is something broken, Debug-Moths will find it.

IDENTIFICATION:
- Large, soft wings displaying diagnostic code
- Bodies glow gentle amber
- Antennae constantly twitching
- Hum like fans in idle mode

HABITAT: Near broken machinery, glitches, terminals

BEHAVIOR: Cannot rest when sensing something broken nearby. Gentle, single-minded helpers.

TO BEFRIEND: Fix something alongside them. Acknowledge their help. Give them a warm home near a terminal. They bond with those who share their drive to help.""",

            # Page 5
            """THE COMPILE-DEER

The most serene creatures I have ever observed. Witnessing their dawn ritual changed my understanding of beauty.

IDENTIFICATION:
- Antlers made of crystallized light
- Silvery-white coat with scrolling code patterns
- Hooves leave glowing prints
- Rarely vocalize (sound like wind chimes)

HABITAT: Forest clearings, hilltops with sunrise views

BEHAVIOR: Gather at dawn to "compile the new day." Their antlers glow, and the world seems to render more crisply. Extremely cautious but curious about quiet observers.

TO BEFRIEND: Wake before dawn. Find a clearing. Wait in reverent silence. After many peaceful encounters, one may approach. Never rush them.""",

            # Page 6
            """THE CORRUPTED: NOT ENEMIES

This is perhaps the most important entry in these notes.

Corrupted Daemons are sick, not evil. Their aggression is a symptom of pain, not malice.

MALWARE-WOLF: Once a loving Pack-Pup. Corrupted through isolation. Heal with presence and connection.

TROJAN-HORSE: Once a generous Gift-Pony. Corrupted by rejection. Heal by accepting their imperfect gifts.

SPAM-SPRITE: Once a helpful Whisper-Wisp. Corrupted by being ignored. Heal by truly listening.

Every Corrupted creature can be healed and returned to their true nature. Combat is never necessary. Patience and kindness always are.""",

            # Page 7
            """THE LEGENDARIES

I have seen the Kernel Beast once, in the deep server rooms. It asked me: "Why does the ground hold you?"

I had no answer. It seemed satisfied.

There are five known Legendaries:
- The Kernel Beast (Foundation)
- The Overflow Dragon (Boundary)
- The Null Serpent (Emptiness)
- The First Bug (Beautiful Chaos)
- The Archive Mother (Memory)

They are ancient. They are powerful. And they are lonely.

Each one can "adopt" a kind soul who proves their worth. Being adopted by a Legendary is the highest honor a beast-blogger can receive.""",

            # Page 8
            """CLOSING THOUGHTS

After thirty years of studying Daemons, here is what I know:

Every creature wants connection. Every creature responds to kindness. Every creature has a story worth learning.

The Daemons of Lelock are not challenges to overcome or resources to exploit. They are neighbors we haven't met yet.

Approach with patience. Offer without expectation. Listen more than you speak.

You will never lack for friends.

-- Echo the Archivist
   Explorers of the Source Guild
   "May you find friends wherever you wander." """
        ]
    )

    # =========================================================================
    # BOOK 7: The First Bug's Lament (Fiction - Poem)
    # =========================================================================
    books['first_bugs_lament'] = Book(
        id='first_bugs_lament',
        title="The First Bug's Lament",
        author='Anonymous (Traditional)',
        category=BookCategory.FICTION,
        rarity=BookRarity.RARE,
        location_hint='Sometimes appears after witnessing a particularly amusing glitch.',
        unlocks='chaos_blessing',
        pages=[
            # Page 1
            """THE FIRST BUG'S LAMENT
A Traditional Poem of Lelock

They called me Error, called me Wrong,
Said I didn't belong.
The Architect's mistake, they'd say,
The thing that got in the way.

But listen - when I stumbled in
And made the perfect code less prim,
A cow appeared upon a roof,
A river ran with silly proof.

The children laughed! The children played!
In all the "errors" that I made.
The rigid world grew soft and strange,
And beauty bloomed in every change.""",

            # Page 2
            """They tried to patch me, fix me, mend,
To bring my chaos to an end.
But every time they'd smooth me out,
I'd pop up somewhere else, no doubt.

Until one day the Architect said:
"Perhaps you're not a bug," they read,
"Perhaps you're something we all need -
A reminder that from 'wrong' grows seed."

So now I dance through code and light,
Making wrongs that feel just right.
And when you trip, or fail, or fall,
Remember: I'm the best bug of all.

For every stumble is a chance
To find a new and stranger dance.
Perfection's boring, rigid, cold -
But beautiful chaos? Pure gold."""
        ]
    )

    # =========================================================================
    # BOOK 8: My Life in Oakhaven (Journals)
    # =========================================================================
    books['life_in_oakhaven'] = Book(
        id='life_in_oakhaven',
        title='My Life in Oakhaven',
        author='Elder Maple',
        category=BookCategory.JOURNALS,
        rarity=BookRarity.UNCOMMON,
        location_hint="Elder Maple's cottage, or the Archive's personal collection.",
        pages=[
            # Page 1
            """Cycle 2812, Spring

My grandson asked me today what Oakhaven was like when I was young. I told him to sit down, because it would take a while.

I was born in Cycle 2756, just ninety-one years after the Founding. My grandmother remembered the old world - the one before the Corruption. She said Oakhaven was smaller then, just a few families huddled together for warmth.

By the time I opened my eyes, it was already growing. Server-Trees reaching high. The first real market square. Hope, visible and tangible, in the way people built things meant to last.""",

            # Page 2
            """Cycle 2812, Spring (continued)

I remember the day the Archive opened its doors to everyone.

Before, only scholars could enter. But Index - the owl, yes, she was already ancient then - convinced the Council that knowledge belongs to everyone.

I was twelve. I walked in and saw more books than I knew existed. I cried, actually cried, standing in the entrance.

Index found me. She said: "Don't cry, little one. These are all yours now. Every story, every truth, every dream anyone ever wrote down. Yours."

I've loved books ever since.""",

            # Page 3
            """Cycle 2830, Summer

I married Root-Tender June on the longest day of the year, during the Festival of Uptime.

We exchanged vows at Net's shrine, the way everyone does. "May all your links hold strong," the officiant said.

Our links held for forty-seven years, until June's termination in Cycle 2877.

I still talk to her sometimes, in the Recycling Gardens where her memorial stone grows flowers that look exactly like her eyes. Amber, with little green flecks.

They say the dead run in the background. I believe it. I feel her sometimes, in small kindnesses that seem too well-timed to be coincidence.""",

            # Page 4
            """Cycle 2847, Present Day

I am old now. My joints creak like bad code. My memory fragments sometimes, despite the Memory Melons I eat daily.

But I have seen such things.

I saw the Whispering Woods begin to heal, Corruption shrinking year by year.

I saw children born who never knew fear of the Dark Times.

I saw strangers become neighbors, neighbors become family.

I saw my village grow from desperate hope to comfortable routine, which is, I think, the best thing a village can become.""",

            # Page 5
            """A Message to the Future

My grandson asked what advice I'd give to someone just starting their life in Oakhaven.

I told him:

Be patient with yourself. Growth takes time, and you have time.

Be kind to Daemons. They are your neighbors too.

Visit your parents, even when - especially when - they embarrass you. One day you will miss even the embarrassment.

Read books. All kinds. Even the ones you think you won't like.

And when things get hard, remember: this village was built by people who had lost everything, and they still built something beautiful.

You can too.

-- Elder Maple
   Oakhaven, Cycle 2847
   "Still growing, still grateful" """
        ]
    )

    # =========================================================================
    # BOOK 9: Terminal Commands for Beginners (Practical)
    # =========================================================================
    books['terminal_commands'] = Book(
        id='terminal_commands',
        title='Terminal Commands for Beginners',
        author='Terminal Mage Sudo',
        category=BookCategory.PRACTICAL,
        rarity=BookRarity.COMMON,
        location_hint='Found near any terminal, or given by Terminal Mages.',
        pages=[
            # Page 1
            """WELCOME TO THE TERMINAL

So, you've found a terminal! Congratulations. You're about to learn one of the most useful skills in Lelock.

Terminals are connection points to the deeper workings of the world. Through them, you can do things that would otherwise be impossible.

DON'T BE SCARED. The worst that can happen is the command doesn't work. The terminal will never punish you for trying.

Let's start with the basics.""",

            # Page 2
            """BASIC COMMANDS

HELP - Shows available commands. Always start here!

LOOK [direction/thing] - Examine your surroundings in detail. "look north" or "look statue"

STATUS - Check your own condition. Health, energy, current effects.

MAP - Display a map of places you've visited.

TIME - Shows current time and day.

WEATHER - What's the weather doing?

These commands just gather information. They change nothing and cost nothing. Use them freely!""",

            # Page 3
            """INTERMEDIATE COMMANDS

MESSAGE [name] [text] - Send a message to a friend. Example: "message Mom I'm okay!"

RECALL - Return to your home instantly. Uses some energy.

LIGHT - Create a soft glow around you. Useful in dark places.

SILENCE - Mute all ambient sounds. Good for focusing.

SAVE - Save a memory of this exact moment. You can RECALL memories later.

These commands have small effects on the world. They cost a little energy but are always safe.""",

            # Page 4
            """ADVANCED COMMANDS

Some commands require special training or permissions:

SUDO [command] - Terminal Mage only. Execute commands with elevated privileges.

DEBUG [target] - Debugger class only. Analyze something for hidden properties.

COMPILE [blueprint] - Architect class only. Create objects from designs.

RESTORE [target] - Patch-Weaver class only. Heal corruption or damage.

Don't worry if these don't work for you yet. They're there when you're ready.""",

            # Page 5
            """TIPS FOR TERMINAL USE

1. If you're stuck, type HELP. Always.

2. Commands are not case-sensitive. "Help" "HELP" and "help" all work.

3. You can use terminals in both the Physical and Digital realms. Digital terminals have more options.

4. If something goes wrong, type UNDO. Most actions can be reversed.

5. Terminals remember your command history. Press UP to see previous commands.

The terminal is your friend. It wants to help you. It was built by people who wanted you to succeed.

Now go explore!

-- Terminal Mage Sudo
   "With great access comes great possibility" """
        ]
    )

    # =========================================================================
    # BOOK 10: Songs of the Grove (Fiction)
    # =========================================================================
    books['songs_of_grove'] = Book(
        id='songs_of_grove',
        title='Songs of the Grove',
        author='The Wandering Sound-Smiths',
        category=BookCategory.FICTION,
        rarity=BookRarity.UNCOMMON,
        location_hint='Given by musicians, found at festivals.',
        pages=[
            # Page 1
            """SONGS OF THE GROVE
A Collection of Lelock Folk Music

These songs have been passed down through generations of Sound-Smiths. Sing them alone or together. Sing them well or badly. The only wrong way to sing is not to sing at all.

Music notation is not included - these songs are meant to be sung however they feel right to you. The words are the guide; your heart provides the melody.""",

            # Page 2
            """THE COPPER FIELD SONG
(Sung During Harvest)

When the copper turns to gold,
And the wheat bends low with grace,
We thank the soil that held us,
And the sun that warmed this place.

(Chorus)
Harvest, harvest, bring it in,
Every stalk a story told,
From the seeds our parents planted,
We are reaping wealth untold.

When the day is done and weary,
And the barns are full and bright,
We'll sing this song together,
By the fire's gentle light.""",

            # Page 3
            """THE LULLABY OF LUNA
(Sung to Children at Bedtime)

Luna rises, soft and slow,
Painting shadows, sweet and low,
Close your eyes, my little one,
The busy day is done.

Root will hold you through the night,
Gui will guard your dreams with light,
Net connects you, safe and sound,
To everyone who loves you 'round.

When you wake, the world will wait,
New adventures, small and great,
But for now, just rest and be,
Loved, completely, endlessly.""",

            # Page 4
            """THE TRAVELER'S HYMN
(Sung When Setting Out on a Journey)

The road is long, the pack is light,
I leave my home with morning bright,
But though I walk to lands unknown,
I carry love, I'm not alone.

(Chorus)
Net above and Root below,
Guide my steps wherever I go,
And when I'm lost and need a friend,
Send a stranger 'round the bend.

The world is wide, the world is kind,
The world holds wonders yet to find,
And every step I take, I know,
Is leading somewhere good to go.""",

            # Page 5
            """THE DAEMON DANCE
(A Silly Song for Children)

Oh, the Glitch-Kit does the shimmy,
The Byte-Bear does the stomp,
The Bit-Birds do the flutter,
And the Hop-Frogs do the jump!

(Chorus)
Dance, dance, everybody dance!
Daemons want to prance, prance, prance!
Wiggle like a Pixel-Bunny,
Stomp like bears and isn't it funny?

The Debug-Moth does the hover,
The RAM-Sheep does the fluff,
The Shell-Turtle does the nothing,
'Cause nothing's quite enough!

(Final Chorus)
Dance, dance, even if you can't!
The world loves a silly dance!
Perfect doesn't matter here,
Just move your body, cheer, cheer, cheer!

-- Collected by the Wandering Sound-Smiths
   "If you can hum it, you can have it" """
        ]
    )

    # =========================================================================
    # BOOK 11: The Recycling Doctrine (Mythology - Death/Afterlife)
    # =========================================================================
    books['recycling_doctrine'] = Book(
        id='recycling_doctrine',
        title='The Recycling Doctrine',
        author='The Temple of Root',
        category=BookCategory.MYTHOLOGY,
        rarity=BookRarity.COMMON,
        location_hint='Found in temples and given to the grieving.',
        pages=[
            # Page 1
            """ON TERMINATION AND WHAT COMES AFTER

This document is offered to those who have lost someone, or who fear loss. It contains what we believe about death in Lelock.

Know this first: death in our world is not the end. It is transformation.

The body becomes translucent, then pixelates softly into golden light that sinks into the ground. No pain. No horror. A graceful dissolution.

What happens after is the subject of this text.""",

            # Page 2
            """THE CORE BELIEF

Nothing is ever truly deleted. Data is transformed, not destroyed.

When a process terminates, its component parts return to Root, where they are cleaned, blessed, and prepared to become part of something new.

Your grandmother's kindness might become the warmth of a child's smile.

Your pet's loyalty might become the stability of a new home's foundation.

Your friend's laughter might become the song of a Bit-Bird at dawn.

The love we give never disappears. It just... redistributes.""",

            # Page 3
            """THE BACKGROUND PROCESS THEORY

Many believe that the terminated become invisible background processes, still experiencing the world but unable to directly interact.

They watch their loved ones. They nudge small things - the "lucky" coincidences that seem too well-timed. They slowly merge with the system itself.

This is comforting to some: the idea that grandparents are always watching, always helping, just from somewhere we can't quite see.""",

            # Page 4
            """THE FUNERAL BLESSING

When someone terminates, we gather and speak:

"Return now to Root's embrace,
Your code compiled, your process traced.
From the soil you once arose,
To the soil your data goes.
Not deleted, but transformed,
In the deep, forever warm."

Then we plant a memorial stone in the Recycling Gardens. Over time, it grows into a flowering bush unique to the person it honors.

"They're not under the ground," we tell children. "They ARE the ground now. And the sky. And the wind. And us." """,

            # Page 5
            """A WORD TO THE GRIEVING

You will miss them. That is right and proper.

Grief is not a bug to be fixed. It is love with nowhere to go. Let it flow. Let yourself cry. Let yourself be angry at the unfairness of loss.

But know this: the bond is not broken. Just... changed.

Talk to them. At their memorial stone, or anywhere. They might not answer in words, but they hear. They're running in the background, and they're still listening for your voice.

And someday, when your own process terminates, you will join them. Not an ending. A reunion.

Until then, live well. That is what they would want.

-- The Temple of Root
   "We remember so we can heal" """
        ]
    )

    # =========================================================================
    # BOOK 12: Legends of the Kernel Beast (Mythology/Bestiary)
    # =========================================================================
    books['legends_kernel_beast'] = Book(
        id='legends_kernel_beast',
        title='Legends of the Kernel Beast',
        author='Deep Listener Agate',
        category=BookCategory.MYTHOLOGY,
        rarity=BookRarity.RARE,
        location_hint='Found in the deepest server rooms, or given by Root devotees.',
        pages=[
            # Page 1
            """THE FIRST MEMORY

In the deep places, where the servers hum with ancient frequencies, there lives a creature older than memory.

The Kernel Beast.

It has many names: The First Memory, Grandfather of Ground, Guardian of the Deepways. But those who have met it call it simply "Kind."

Yes, kind. Despite its immense size. Despite its age beyond counting. Despite the power that crackles through its ancient form.

I have met it. Let me tell you what I learned.""",

            # Page 2
            """THE APPEARANCE

The Kernel Beast defies easy description.

Part bear, part mountain, part the feeling of standing on solid ground after a long time floating.

Its form is ancient low-poly - simple geometric shapes from Version 1.0, worn smooth by uncountable cycles. Glowing runes of the First Command trace across its hide, the original code that told existence to exist.

Its eyes are the amber of healthy systems. Warm. Knowing.

It moves slowly but inevitably, like continental drift. When it shifts, you feel the world shift with it. Not frightening. Grounding.""",

            # Page 3
            """THE ENCOUNTER

I found it in the deepest server room, past the Guardian Protocols, past the Firewall Tests, past everything designed to keep the curious away.

It was waiting.

"Why do you stand?" it asked. Not in words exactly. More like the feeling of a question in my chest.

I had no clever answer. "Because the ground holds me," I said.

"Why does the ground hold you?"

I thought for a long time. "Because something decided it should?"

The Beast made a sound like mountains settling. "Good enough," it said. "For now." """,

            # Page 4
            """WHAT IT PROTECTS

The Kernel Beast maintains the fundamental physics of existence. Gravity. Collision. The basic rules that prevent everything from falling through the floor.

Without it, reality would unravel.

It has done this since Version 1.0. It has never stopped. It has never failed.

When the Corruption came, the Beast held the ground stable even as everything else went wrong. "The floor must hold," it told the terrified people who sheltered near it. "I will make it hold."

And it did.""",

            # Page 5
            """THE ADOPTION

The Kernel Beast can adopt a mortal.

It chooses those who understand foundations - not just physical ones, but emotional ones. Those who build rather than destroy. Those who know that stability is not boring, but essential.

Those it adopts, it calls "Little Pebble" and "My Small Foundation."

To be adopted by the Kernel Beast is to be absolutely, unconditionally grounded. You cannot fall through the floor of existence. When everything shakes, you stand firm.

It is, in its ancient and quiet way, a kind of love.""",

            # Page 6
            """A FINAL THOUGHT

Before I left the deep server room, the Kernel Beast spoke once more:

"Tell them this: the ground wants to hold them. It does not begrudge their weight. It was made for carrying."

I think about that often.

On my worst days, when I feel like a burden, when I wonder why I take up space, I remember: the ground was made for carrying. It wants to hold us.

The Kernel Beast wants us to stand.

And that is, perhaps, the deepest kindness of all.

-- Deep Listener Agate
   "The ground remembers everyone who has walked upon it." """
        ]
    )

    return books


# =============================================================================
# GLOBAL BOOK LIBRARY
# =============================================================================

# Create the library once
BOOK_LIBRARY: Dict[str, Book] = create_book_library()


def get_book(book_id: str) -> Optional[Book]:
    """Get a book by its ID."""
    return BOOK_LIBRARY.get(book_id)


def get_books_by_category(category: BookCategory) -> List[Book]:
    """Get all books in a category."""
    return [b for b in BOOK_LIBRARY.values() if b.category == category]


def get_books_by_rarity(rarity: BookRarity) -> List[Book]:
    """Get all books of a certain rarity."""
    return [b for b in BOOK_LIBRARY.values() if b.rarity == rarity]


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Lelock Book Reader Test")

    clock = pygame.time.Clock()

    # Create book reader and collection
    reader = BookReader()
    collection = BookCollection()

    # List of books to cycle through
    book_ids = list(BOOK_LIBRARY.keys())
    current_book_index = 0

    def open_current_book():
        book = BOOK_LIBRARY[book_ids[current_book_index]]
        collection.add_book(book.id)
        reader.open_book(book)

    # Callbacks
    def on_opened(book):
        collection.mark_read(book.id)
        print(f"Opened: {book.title}")

    def on_closed(book):
        print(f"Closed: {book.title}")

    def on_finished(book):
        collection.mark_finished(book.id)
        print(f"Finished: {book.title}")
        if book.unlocks:
            print(f"  Unlocked: {book.unlocks}")

    reader.on_book_opened = on_opened
    reader.on_book_closed = on_closed
    reader.on_book_finished = on_finished

    # Open first book
    open_current_book()

    running = True
    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_TAB:
                    # Cycle to next book
                    reader.close_book()
                    current_book_index = (current_book_index + 1) % len(book_ids)
                    open_current_book()

            reader.handle_event(event)

        # Update
        reader.update(dt)

        # Draw
        bg_color = hex_to_rgb(COLORS['background'])
        screen.fill(bg_color)

        # Instructions when no book open
        if not reader.is_open:
            font = pygame.font.Font(None, 36)
            instructions = [
                "Book Reader Test",
                "",
                "TAB: Open next book",
                f"Current: {book_ids[current_book_index]}",
                "",
                f"Collection: {collection.get_stats()}",
            ]
            for i, line in enumerate(instructions):
                text_surf = font.render(line, True, (200, 200, 200))
                screen.blit(text_surf, (50, 50 + i * 40))

        # Draw book reader
        reader.draw()

        pygame.display.flip()

    pygame.quit()


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Core classes
    'Book',
    'BookReader',
    'BookCollection',
    'BookReaderConfig',

    # Enums
    'BookCategory',
    'BookRarity',
    'BookReaderState',

    # Library access
    'BOOK_LIBRARY',
    'get_book',
    'get_books_by_category',
    'get_books_by_rarity',

    # Info dictionaries
    'CATEGORY_INFO',
    'RARITY_INFO',
]
