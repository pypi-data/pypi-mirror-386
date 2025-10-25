"""Core catpic functionality and constants."""

import os
from enum import Enum
from typing import Dict, List, Optional, Tuple

# MEOW v0.6 format constants
MEOW_VERSION = "0.6"
MEOW_OSC_NUMBER = 9876
MEOW_OSC_PREFIX = f"\x1b]{MEOW_OSC_NUMBER};"
MEOW_OSC_SUFFIX = "\x07"

# Default values for MEOW format
DEFAULT_BASIS = (2, 2)
DEFAULT_CANVAS_SIZE = (80, 24)
DEFAULT_ALPHA = 1.0
DEFAULT_FRAME_DELAY = 100  # milliseconds
DEFAULT_CHAR_ASPECT = 2.0  # Terminal characters are roughly 2:1 (height:width)

# Exit codes (MEOW v0.6 spec)
EXIT_SUCCESS = 0
EXIT_ERROR_GENERAL = 1
EXIT_ERROR_PARSE = 2
EXIT_ERROR_NO_CANVAS_SIZE = 3
EXIT_ERROR_INVALID_METADATA = 4
EXIT_ERROR_FILE_NOT_FOUND = 5
EXIT_ERROR_WRITE_ERROR = 6


class BASIS(Enum):
    """BASIS system for catpic quality levels."""
    
    BASIS_1_2 = (1, 2)  # 4 patterns - Universal compatibility
    BASIS_2_2 = (2, 2)  # 16 patterns - Balanced
    BASIS_2_3 = (2, 3)  # 64 patterns - High quality  
    BASIS_2_4 = (2, 4)  # 256 patterns - Ultra quality


def get_default_basis() -> BASIS:
    """
    Get default BASIS from environment variable or fallback.
    
    Reads CATPIC_BASIS environment variable (format: "2,2" or "2x2" or "2_2")
    Falls back to BASIS_2_2 if not set or invalid.
    
    Examples:
        export CATPIC_BASIS=2,4  # Use ultra quality
        export CATPIC_BASIS=1,2  # Use universal compatibility
    """
    env_basis = os.environ.get('CATPIC_BASIS', '').strip()
    
    if not env_basis:
        return BASIS.BASIS_2_2  # Default
    
    # Parse various formats: "2,2" or "2x2" or "2_2"
    for sep in [',', 'x', '_', ' ']:
        if sep in env_basis:
            parts = env_basis.split(sep)
            if len(parts) == 2:
                try:
                    x, y = int(parts[0]), int(parts[1])
                    # Map to BASIS enum
                    basis_map = {
                        (1, 2): BASIS.BASIS_1_2,
                        (2, 2): BASIS.BASIS_2_2,
                        (2, 3): BASIS.BASIS_2_3,
                        (2, 4): BASIS.BASIS_2_4,
                    }
                    if (x, y) in basis_map:
                        return basis_map[(x, y)]
                except ValueError:
                    pass
    
    # Invalid format, fall back to default
    return BASIS.BASIS_2_2


def get_char_aspect() -> float:
    """
    Get terminal character aspect ratio from environment or default.
    
    Terminal characters are typically taller than wide. Common values:
    - 2.0: Most terminals (default)
    - 1.8: Some wider fonts
    - 2.2: Some narrower fonts
    
    Environment:
        CATPIC_CHAR_ASPECT: Float value (e.g., "2.0", "1.8")
    
    Returns:
        Character aspect ratio (height / width)
    """
    aspect_env = os.getenv('CATPIC_CHAR_ASPECT')
    if not aspect_env:
        return DEFAULT_CHAR_ASPECT
    
    try:
        aspect = float(aspect_env)
        # Sanity check: reasonable range
        if 1.0 <= aspect <= 3.0:
            return aspect
    except (ValueError, TypeError):
        pass
    
    return DEFAULT_CHAR_ASPECT


class CatpicCore:
    """Core catpic constants and Unicode character sets for mosaic encoding."""
    
    # Unicode block characters for different BASIS levels
    BLOCKS: Dict[BASIS, List[str]] = {
        BASIS.BASIS_1_2: [
            " ",  # Empty
            "▀",  # Upper half
            "▄",  # Lower half  
            "█",  # Full block
        ],
        
        BASIS.BASIS_2_2: [
            " ", "▘", "▝", "▀",  # 0000, 0001, 0010, 0011
            "▖", "▌", "▞", "▛",  # 0100, 0101, 0110, 0111
            "▗", "▚", "▐", "▜",  # 1000, 1001, 1010, 1011
            "▄", "▙", "▟", "█",  # 1100, 1101, 1110, 1111
        ],
        
        BASIS.BASIS_2_3: [
            " ", "🬀", "🬁", "🬂", "🬃", "🬄", "🬅", "🬆",
            "🬇", "🬈", "🬉", "🬊", "🬋", "🬌", "🬍", "🬎",
            "🬏", "🬐", "🬑", "🬒", "🬓", "🬔", "🬕", "🬖",
            "🬗", "🬘", "🬙", "🬚", "🬛", "🬜", "🬝", "🬞",
            "🬟", "🬠", "🬡", "🬢", "🬣", "🬤", "🬥", "🬦",
            "🬧", "🬨", "🬩", "🬪", "🬫", "🬬", "🬭", "🬮",
            "🬯", "🬰", "🬱", "🬲", "🬳", "🬴", "🬵", "🬶",
            "🬷", "🬸", "🬹", "🬺", "🬻", "▀", "▄", "█",
        ],
        
        # Sextant blocks (64 glyphs)
        BASIS.BASIS_2_3: list(
            " 🬀🬁🬂🬃🬄🬅🬆🬇🬈🬉🬊🬋🬌🬍🬎🬏🬐🬑🬒🬓▌🬔🬕🬖🬗🬘🬙🬚🬛🬜🬝🬞🬟🬠🬡🬢🬣🬤🬥🬦🬧▐🬨🬩🬪🬫🬬🬭🬮🬯🬰🬱🬲🬳🬴🬵🬶🬷🬸🬹🬺🬻█"
        ),

        # Octant blocks (256 glyphs)
        BASIS.BASIS_2_4: list(
            " 𜺨𜺫🮂𜴀▘𜴁𜴂𜴃𜴄▝𜴅𜴆𜴇𜴈▀𜴉𜴊𜴋𜴌🯦𜴍𜴎𜴏𜴐𜴑𜴒𜴓𜴔𜴕𜴖𜴗𜴘𜴙𜴚𜴛𜴜𜴝𜴞𜴟🯧𜴠𜴡𜴢𜴣𜴤𜴥𜴦𜴧𜴨𜴩𜴪𜴫𜴬𜴭𜴮𜴯𜴰𜴱𜴲𜴳𜴴𜴵🮅"
            "𜺣𜴶𜴷𜴸𜴹𜴺𜴻𜴼𜴽𜴾𜴿𜵀𜵁𜵂𜵃𜵄▖𜵅𜵆𜵇𜵈▌𜵉𜵊𜵋𜵌▞𜵍𜵎𜵏𜵐▛𜵑𜵒𜵓𜵔𜵕𜵖𜵗𜵘𜵙𜵚𜵛𜵜𜵝𜵞𜵟𜵠𜵡𜵢𜵣𜵤𜵥𜵦𜵧𜵨𜵩𜵪𜵫𜵬𜵭𜵮𜵯𜵰"
            "𜺠𜵱𜵲𜵳𜵴𜵵𜵶𜵷𜵸𜵹𜵺𜵻𜵼𜵽𜵾𜵿𜶀𜶁𜶂𜶃𜶄𜶅𜶆𜶇𜶈𜶉𜶊𜶋𜶌𜶍𜶎▗𜶏𜶐𜶑𜶒▚𜶓𜶔𜶕𜶖▐𜶗𜶘𜶙𜶚▜𜶛𜶜𜶝𜶞𜶟𜶠𜶡𜶢𜶣𜶤𜶥𜶦𜶧𜶨𜶩𜶪𜶫"
            "▂𜶬𜶭𜶮𜶯𜶰𜶱𜶲𜶳𜶴𜶵𜶶𜶷𜶸𜶹𜶺𜶻𜶼𜶽𜶾𜶿𜷀𜷁𜷂𜷃𜷄𜷅𜷆𜷇𜷈𜷉𜷊𜷋𜷌𜷍𜷎𜷏𜷐𜷑𜷒𜷓𜷔𜷕𜷖𜷗𜷘𜷙𜷚▄𜷛𜷜𜷝𜷞▙𜷟𜷠𜷡𜷢▟𜷣▆𜷤𜷥█"
        ),
    }
    
    # ANSI color format strings
    RESET = "\x1b[0m"
    FG_COLOR = "\x1b[38;2;{r};{g};{b}m"
    BG_COLOR = "\x1b[48;2;{r};{g};{b}m"
    
    @staticmethod
    def format_cell(char: str, fg_rgb: Tuple[int, int, int], bg_rgb: Tuple[int, int, int]) -> str:
        """Format a single cell with foreground/background colors."""
        fg_r, fg_g, fg_b = fg_rgb
        bg_r, bg_g, bg_b = bg_rgb
        
        return (
            f"\x1b[38;2;{fg_r};{fg_g};{fg_b}m"
            f"\x1b[48;2;{bg_r};{bg_g};{bg_b}m"
            f"{char}"
            f"\x1b[0m"
        )
    
    @staticmethod
    def get_basis_dimensions(basis: BASIS) -> Tuple[int, int]:
        """Get pixel dimensions for a BASIS level."""
        return basis.value
