"""
Download frequency data files on demand from GitHub.
"""
import os
import urllib.request
import sys

# Base URL for frequency data
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018"

def get_data_path():
    """Get the path where language data is stored."""
    package_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(package_dir, 'language_data', 'hermitdave', '2018')

def download_language_data(language_code):
    """
    Download frequency data for a language if not already present.

    Args:
        language_code: Two-letter language code (e.g., 'da', 'en')

    Returns:
        Path to the downloaded file
    """
    data_path = get_data_path()
    lang_dir = os.path.join(data_path, language_code)
    file_path = os.path.join(lang_dir, f"{language_code}_full.txt")

    # If file already exists, return it
    if os.path.exists(file_path):
        return file_path

    # Create directory if needed
    os.makedirs(lang_dir, exist_ok=True)

    # Download from GitHub
    url = f"{GITHUB_RAW_BASE}/{language_code}/{language_code}_full.txt"

    print(f"Downloading {language_code} frequency data from {url}...", file=sys.stderr)

    try:
        urllib.request.urlretrieve(url, file_path)
        print(f"✓ Downloaded {language_code} data", file=sys.stderr)
        return file_path
    except Exception as e:
        print(f"✗ Failed to download {language_code} data: {e}", file=sys.stderr)
        raise FileNotFoundError(f"Could not download frequency data for '{language_code}'. "
                              f"Please check your internet connection and try again.")

def ensure_language_data(language_code):
    """
    Ensure language data is available, downloading if necessary.

    Args:
        language_code: Two-letter language code (e.g., 'da', 'en')

    Returns:
        Path to the language data file
    """
    return download_language_data(language_code)
