"""
Barcode linking functionality - integrates with external API to get linked data.
"""

import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# External API configuration
BARCODE_LINK_API_URL = "http://10.100.10.83:5000/api/ProcessLock/FA/GetLinkData"
BARCODE_LINK_TIMEOUT = 3  # seconds
BARCODE_LINK_ENABLED = True  # Set to False to disable linking

def get_linked_barcode(scanned_barcode: str) -> Optional[str]:
    """
    Get linked barcode data from external API.
    
    Args:
        scanned_barcode: The barcode scanned from the device
        
    Returns:
        Linked barcode data from API, or None if API call fails
        
    Example:
        >>> get_linked_barcode("20003548-0000003-1019720-101")
        "20003548-0000003-1019720-101"
    """
    if not BARCODE_LINK_ENABLED:
        logger.debug("Barcode linking is disabled")
        return None
    
    if not scanned_barcode or not scanned_barcode.strip():
        logger.warning("Empty barcode provided for linking")
        return None
    
    try:
        # Clean the barcode
        clean_barcode = scanned_barcode.strip()
        
        # Call external API
        # POST body is a JSON string (quoted string)
        logger.info(f"Calling barcode link API for: {clean_barcode}")
        
        response = requests.post(
            BARCODE_LINK_API_URL,
            json=clean_barcode,  # Send as JSON string (will be quoted automatically)
            headers={
                'accept': '*/*',
                'Content-Type': 'application/json'
            },
            timeout=BARCODE_LINK_TIMEOUT
        )
        
        # Check if request was successful
        if response.status_code == 200:
            # API returns plain text response (may be quoted)
            linked_data = response.text.strip()
            
            # Remove surrounding quotes if present (API returns "value")
            if linked_data.startswith('"') and linked_data.endswith('"'):
                linked_data = linked_data[1:-1]
            
            # Handle "null" response (invalid barcode)
            if linked_data.lower() == 'null' or not linked_data:
                logger.warning(
                    f"Barcode link API returned null/empty for: "
                    f"{scanned_barcode}"
                )
                return None
            
            logger.info(f"Barcode link API returned: {linked_data}")
            return linked_data
        else:
            logger.warning(f"Barcode link API returned status {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        logger.warning(f"Barcode link API timeout after {BARCODE_LINK_TIMEOUT}s for barcode: {scanned_barcode}")
        return None
    except requests.exceptions.ConnectionError:
        logger.warning(f"Barcode link API connection error for barcode: {scanned_barcode}")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Barcode link API request failed for {scanned_barcode}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in barcode linking for {scanned_barcode}: {e}")
        return None

def get_linked_barcode_with_fallback(scanned_barcode: str) -> tuple[str, bool]:
    """
    Get linked barcode data with fallback to original barcode.
    
    Args:
        scanned_barcode: The barcode scanned from the device
        
    Returns:
        Tuple of (barcode_to_use, is_linked):
        - barcode_to_use: The linked barcode or original if linking failed
        - is_linked: True if linking was successful, False if using original
        
    Example:
        >>> get_linked_barcode_with_fallback("20003548-0000003-1019720-101")
        ("20003548-0000003-1019720-101", True)
        
        >>> get_linked_barcode_with_fallback("INVALID")  # API fails
        ("INVALID", False)
    """
    if not scanned_barcode or not scanned_barcode.strip():
        return (scanned_barcode, False)
    
    # Try to get linked data
    linked_data = get_linked_barcode(scanned_barcode)
    
    if linked_data:
        logger.info(f"Using linked barcode: {scanned_barcode} -> {linked_data}")
        return (linked_data, True)
    else:
        logger.info(f"Using original barcode (linking failed): {scanned_barcode}")
        return (scanned_barcode, False)

def set_barcode_link_enabled(enabled: bool):
    """Enable or disable barcode linking globally."""
    global BARCODE_LINK_ENABLED
    BARCODE_LINK_ENABLED = enabled
    logger.info(f"Barcode linking {'enabled' if enabled else 'disabled'}")

def set_barcode_link_api_url(url: str):
    """Set the barcode linking API URL."""
    global BARCODE_LINK_API_URL
    BARCODE_LINK_API_URL = url
    logger.info(f"Barcode link API URL set to: {url}")

def set_barcode_link_timeout(timeout: int):
    """Set the barcode linking API timeout in seconds."""
    global BARCODE_LINK_TIMEOUT
    BARCODE_LINK_TIMEOUT = timeout
    logger.info(f"Barcode link API timeout set to: {timeout}s")
