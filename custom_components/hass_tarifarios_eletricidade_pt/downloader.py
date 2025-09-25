"""Download and extraction utilities for ERSE data."""
import asyncio
import logging
import zipfile
import re
from datetime import datetime, timedelta
from io import BytesIO
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

# ERSE simulator page URL
ERSE_SIMULATOR_URL = "https://simuladorprecos.erse.pt"
# Fallback URL if all methods fail
FALLBACK_ZIP_URL = "https://simuladorprecos.erse.pt/Admin/csvs/20250919%20100313%20CSV.zip"

def _analyze_page_content(html_content: str) -> list[str]:
    """Analyze page content for CSV URLs using multiple patterns."""
    found_urls = []
    
    # Pattern 1: Direct Admin/csvs paths
    admin_paths = re.findall(r'/Admin/csvs/[^"\'>\s]*\.zip', html_content)
    for path in admin_paths:
        found_urls.append(f"https://simuladorprecos.erse.pt{path}")
    
    # Pattern 2: Full URLs with .zip
    zip_urls = re.findall(r'https://simuladorprecos\.erse\.pt/Admin/csvs/[^"\'>\s]*\.zip', html_content)
    found_urls.extend(zip_urls)
    
    # Pattern 3: Date patterns that might be CSV filenames
    date_patterns = re.findall(r'\d{8}[%\s]\d{6}[%\s]CSV\.zip', html_content)
    for pattern in date_patterns:
        # Convert spaces to %20 for URL encoding
        encoded_pattern = pattern.replace(' ', '%20')
        found_urls.append(f"https://simuladorprecos.erse.pt/Admin/csvs/{encoded_pattern}")
    
    # Pattern 4: JavaScript variables with CSV paths
    js_vars = re.findall(r'["\']([^"\']*Admin/csvs/[^"\']*\.zip)["\']', html_content)
    for var in js_vars:
        if var.startswith('/'):
            found_urls.append(f"https://simuladorprecos.erse.pt{var}")
        elif not var.startswith('http'):
            found_urls.append(f"https://simuladorprecos.erse.pt/{var}")
        else:
            found_urls.append(var)
    
    _LOGGER.debug("Found potential CSV URLs in page: %s", found_urls)
    return list(set(found_urls))  # Remove duplicates

async def _try_date_patterns(hass: HomeAssistant) -> str:
    """Try date-based URL patterns using known working format."""
    session = async_get_clientsession(hass)
    base_url = "https://simuladorprecos.erse.pt/Admin/csvs"
    
    # Try recent dates with common time patterns
    today = datetime.now()
    
    # Time patterns based on known working format (100313 from fallback)
    time_patterns = [
        "100313",  # Known working time
        "100000", "110000", "120000", "090000",
        "100300", "100330", "100315", "100310"
    ]
    
    for days_back in range(0, 10):  # Try last 10 days
        date = today - timedelta(days=days_back)
        date_str = date.strftime('%Y%m%d')
        
        for time_str in time_patterns:
            url = f"{base_url}/{date_str}%20{time_str}%20CSV.zip"
            
            try:
                async with session.head(url, timeout=5) as resp:
                    if resp.status == 200:
                        _LOGGER.info("Found working CSV URL via date pattern: %s", url)
                        return url
            except:
                continue
    
    return None

async def _test_extracted_urls(hass: HomeAssistant, urls: list[str]) -> str:
    """Test extracted URLs to find working ones."""
    session = async_get_clientsession(hass)
    
    for url in urls:
        try:
            async with session.head(url, timeout=5) as resp:
                if resp.status == 200:
                    _LOGGER.info("Found working CSV URL from page analysis: %s", url)
                    return url
        except:
            continue
    
    return None

async def async_get_latest_csv_url(hass: HomeAssistant) -> str:
    """Get the latest CSV ZIP URL using multiple strategies."""
    session = async_get_clientsession(hass)
    
    try:
        _LOGGER.debug("Fetching ERSE simulator page...")
        async with session.get(ERSE_SIMULATOR_URL, timeout=30) as resp:
            resp.raise_for_status()
            html_content = await resp.text()
        
        # Strategy 1: Analyze page content for CSV URLs
        _LOGGER.debug("Analyzing page content for CSV URLs...")
        extracted_urls = _analyze_page_content(html_content)
        if extracted_urls:
            working_url = await _test_extracted_urls(hass, extracted_urls)
            if working_url:
                return working_url
        
        # Strategy 2: Try recent date patterns
        _LOGGER.debug("Trying date-based URL patterns...")
        pattern_url = await _try_date_patterns(hass)
        if pattern_url:
            return pattern_url
        
        # Strategy 3: Fallback to known working URL
        _LOGGER.warning("All discovery methods failed, using fallback URL")
        return FALLBACK_ZIP_URL
        
    except Exception as e:
        _LOGGER.error("Failed to get latest CSV URL: %s", e)
        _LOGGER.info("Using fallback CSV URL: %s", FALLBACK_ZIP_URL)
        return FALLBACK_ZIP_URL

async def async_download_erse_zip(hass: HomeAssistant, url: str = None) -> bytes:
    """Download ERSE ZIP file."""
    if not url:
        url = await async_get_latest_csv_url(hass)
    
    _LOGGER.debug("Starting download from %s", url)
    session = async_get_clientsession(hass)
    
    async with session.get(url, timeout=60) as resp:
        content = await resp.read()
        _LOGGER.debug("Downloaded ZIP size=%d bytes status=%s", len(content), resp.status)
        resp.raise_for_status()
        return content

async def async_extract_csv_from_zip(zip_content: bytes, filename: str) -> str:
    """Extract specific CSV file from ZIP content."""
    def _extract():
        with zipfile.ZipFile(BytesIO(zip_content)) as zf:
            file_list = zf.namelist()
            _LOGGER.debug("ZIP contains files: %s", file_list)
            
            # Find the target file
            target_file = None
            for file in file_list:
                if file.endswith(filename) or filename in file:
                    target_file = file
                    break
            
            if not target_file:
                raise FileNotFoundError(f"File '{filename}' not found in ZIP. Available files: {file_list}")
            
            _LOGGER.debug("Extracting '%s' from ZIP", target_file)
            return zf.read(target_file).decode('utf-8-sig')
    
    return await asyncio.to_thread(_extract)

async def async_download_and_extract_csvs(hass: HomeAssistant) -> tuple[str, str]:
    """Download ERSE ZIP and extract both CSV files."""
    try:
        _LOGGER.info("Finding latest ERSE CSV URL...")
        csv_url = await async_get_latest_csv_url(hass)
        
        _LOGGER.info("Downloading ERSE data from: %s", csv_url)
        zip_content = await async_download_erse_zip(hass, csv_url)
        
        _LOGGER.info("Extracting CSV files...")
        cond_txt, precos_txt = await asyncio.gather(
            async_extract_csv_from_zip(zip_content, "CondComerciais.csv"),
            async_extract_csv_from_zip(zip_content, "Precos_ELEGN.csv"),
        )
        
        _LOGGER.info("Successfully extracted CSV files: CondComerciais (%d chars), Precos_ELEGN (%d chars)", 
                     len(cond_txt), len(precos_txt))
        
        return cond_txt, precos_txt
        
    except Exception as e:
        _LOGGER.error("Download or extraction failed: %s", e)
        raise