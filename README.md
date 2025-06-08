# Icelandic Sign Language Lookup Tool

This script processes Icelandic text and displays corresponding sign language images from SignWiki.is.


![Icelandic Sign Language Lookup Tool Screenshot](screenshot.png)


## Features 

- Processes Icelandic words to their dictionary/infinitive forms
- Fetches sign language images from SignWiki.is
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

Example:
```
python main.py "Ég tala íslensku"
```

## How it works

1. The script processes each word in the input sentence to its dictionary form
2. For each processed word, it fetches the corresponding sign language image from SignWiki.is
3. It displays the image in the terminal (if using iTerm2) or opens it in the default image viewer

## Notes

- The word processing is based on pattern matching and may not handle all Icelandic word forms correctly
- Image display in the terminal works best in iTerm2 on macOS
- If an image cannot be displayed in the terminal, it will be opened in the default image viewer