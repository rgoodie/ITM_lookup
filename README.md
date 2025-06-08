# Icelandic Sign Language Lookup Tool

This script processes Icelandic text and displays corresponding sign language images from SignWiki.is.

## Features

- Processes Icelandic words to their dictionary/infinitive forms
- Fetches sign language images from SignWiki.is
- Caches images in a local SQLite database to reduce web requests
- Displays images directly in the terminal (if using iTerm2) or opens them in the default image viewer

## Setup

1. Create a virtual environment and install dependencies:
```
python3 -m venv venv
source venv/bin/activate
pip install requests beautifulsoup4 pillow
```

## Usage

```
source venv/bin/activate
python main.py "Icelandic sentence here"
```

Or use the provided shell script:
```
./run.sh "Icelandic sentence here"
```

Example:
```
./run.sh "Ég tala íslensku"
```

## How it works

1. The script processes each word in the input sentence to its dictionary form
2. It checks if the sign image is already in the local cache database
3. If cached, it uses the stored image; otherwise, it fetches from SignWiki.is and caches it
4. It displays the image in the terminal (if using iTerm2) or opens it in the default image viewer

## Cache System

The script uses a SQLite database (`signwiki.is.db`) to cache sign images:
- Table: `signcache`
- Columns: 
  - `ord`: The Icelandic word (primary key)
  - `base64`: The base64-encoded image data

This reduces network requests and speeds up repeated lookups.