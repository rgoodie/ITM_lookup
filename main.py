#!/usr/bin/env python3
import sys
import re
import requests
from bs4 import BeautifulSoup
from PIL import Image
import io
import os
import tempfile
import base64
import sqlite3

# Dictionary of common Icelandic noun endings and their base forms
NOUN_ENDINGS = {
    # Singular
    'inn': 'i',      # masculine definite
    'inum': 'i',     # masculine dative definite
    'ins': 'i',      # masculine genitive definite
    'in': 'i',       # feminine definite
    'ina': 'i',      # feminine accusative definite
    'inni': 'i',     # feminine dative definite
    'innar': 'i',    # feminine genitive definite
    'ið': 'i',       # neuter definite
    'inu': 'i',      # neuter dative definite
    'ins': 'i',      # neuter genitive definite
    
    # Plural
    'arnir': 'i',    # masculine nominative plural definite
    'ana': 'i',      # masculine accusative plural definite
    'unum': 'i',     # masculine dative plural definite
    'anna': 'i',     # masculine genitive plural definite
    'irnar': 'i',    # feminine nominative plural definite
    'unum': 'i',     # feminine dative plural definite
    'anna': 'i',     # feminine genitive plural definite
    'in': 'i',       # neuter nominative plural definite
    'unum': 'i',     # neuter dative plural definite
    'anna': 'i',     # neuter genitive plural definite
    
    # Common case endings
    'ar': '',        # genitive singular or nominative plural
    'um': 'ur',      # dative plural
    'a': 'i',        # accusative plural
    'u': 'a',        # dative singular
    'i': 'ur',       # dative singular
}

# Dictionary of common Icelandic verb endings and their infinitive forms
VERB_ENDINGS = {
    # Present tense
    'a': 'a',        # 1st person plural
    'ar': 'a',       # 2nd/3rd person singular
    'um': 'a',       # 1st person plural
    'ið': 'a',       # 2nd person plural
    'ir': 'a',       # 3rd person plural
    
    # Past tense
    'aði': 'a',      # 1st/3rd person singular
    'aðir': 'a',     # 2nd person singular
    'uðum': 'a',     # 1st person plural
    'uðuð': 'a',     # 2nd person plural
    'uðu': 'a',      # 3rd person plural
    
    # Strong verbs past tense (examples)
    'ók': 'aka',     # drive
    'fór': 'fara',   # go
    'kom': 'koma',   # come
    'tók': 'taka',   # take
}

def init_db():
    """
    Initialize the SQLite database for caching sign images
    """
    conn = sqlite3.connect('signwiki.is.db')
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS signcache (
        ord TEXT PRIMARY KEY,
        base64 TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()

def get_cached_image(word):
    """
    Get an image from the cache if it exists
    """
    conn = sqlite3.connect('signwiki.is.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT base64 FROM signcache WHERE ord = ?', (word,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        print(f"Using cached image for '{word}'")
        return base64.b64decode(result[0])
    
    return None

def cache_image(word, image_data):
    """
    Cache an image in the database
    """
    if not image_data:
        return
    
    # Convert image data to base64
    image_base64 = base64.b64encode(image_data).decode('ascii')
    
    conn = sqlite3.connect('signwiki.is.db')
    cursor = conn.cursor()
    
    # Insert or replace the image
    cursor.execute(
        'INSERT OR REPLACE INTO signcache (ord, base64) VALUES (?, ?)',
        (word, image_base64)
    )
    
    conn.commit()
    conn.close()
    
    print(f"Cached image for '{word}'")

def process_icelandic_word(word):
    """
    Process an Icelandic word to its dictionary form using Reynir.
    Falls back to rule-based approach if Reynir is not available.
    Special handling for question words.
    """
    # Special handling for question words
    question_words = {
        "hvað": "hvað",
        "hvaða": "hvað",
        "hver": "hver",
        "hvers": "hver",
        "hverjum": "hver",
        "hverjir": "hver",
        "hverjar": "hver",
        "hvar": "hvar",
        "hvernig": "hvernig"
    }
    
    # Remove punctuation for lookup
    clean_word_lower = re.sub(r'[^\w\s]', '', word).lower()
    
    # Check if it's a question word
    if clean_word_lower in question_words:
        return question_words[clean_word_lower]
    
    try:
        from reynir import Reynir
        
        # Remove punctuation but keep the original word for processing
        clean_word = re.sub(r'[^\w\s]', '', word)
        
        if not clean_word:
            return word
        
        # Initialize Reynir (only done once)
        if not hasattr(process_icelandic_word, 'reynir'):
            process_icelandic_word.reynir = Reynir()
        
        # Parse the word to get its lemma (dictionary form)
        sent = process_icelandic_word.reynir.parse_single(clean_word)
        
        if sent and sent.tree and len(sent.terminals) > 0:
            # Get the lemma of the word
            lemma = sent.terminals[0].lemma
            return lemma
        
        # Fall back to rule-based approach if parsing fails
        print(f"Reynir parsing failed for '{word}', falling back to rule-based approach")
        return _rule_based_process(clean_word, word)
        
    except ImportError:
        print("Reynir not installed. Install with: pip install reynir")
        return _rule_based_process(word, word)
    except Exception as e:
        print(f"Error processing word with Reynir: {e}")
        return _rule_based_process(word, word)

def _rule_based_process(clean_word, original_word):
    """
    Fallback rule-based approach for processing Icelandic words.
    """
    clean_word = clean_word.lower()
    
    if not clean_word:
        return original_word
    
    # Try to find matching verb endings
    for ending, base in VERB_ENDINGS.items():
        if clean_word.endswith(ending) and len(clean_word) > len(ending):
            stem = clean_word[:-len(ending)]
            return stem + base
    
    # Try to find matching noun endings
    for ending, replacement in NOUN_ENDINGS.items():
        if clean_word.endswith(ending) and len(clean_word) > len(ending):
            stem = clean_word[:-len(ending)]
            if replacement:
                return stem + replacement
            return stem
    
    # If no patterns match, return the original word
    return clean_word

def fetch_signwiki_image(word):
    """
    Fetch the image for a word from signwiki.is or from cache
    """
    # Check cache first
    cached_image = get_cached_image(word)
    if cached_image:
        return cached_image
    
    # If not in cache, fetch from web
    url = f"https://signwiki.is/index.php/{word}"
    
    try:
        # Fetch the webpage
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the image using the provided selector
        img_tag = soup.select_one('div.mw-parser-output a img')
        
        if img_tag and 'src' in img_tag.attrs:
            img_url = img_tag['src']
            
            # If the URL is relative, make it absolute
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                img_url = 'https://signwiki.is' + img_url
                
            # Fetch the image
            img_response = requests.get(img_url)
            img_response.raise_for_status()
            
            image_data = img_response.content
            
            # Cache the image
            cache_image(word, image_data)
            
            return image_data
        else:
            print(f"No image found for '{word}'")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching image for '{word}': {e}")
        return None

def display_image_in_terminal(image_data, word):
    """
    Display an image in the terminal using iTerm2's inline image protocol
    """
    if not image_data:
        return
    
    # Save the image to a temporary file
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
        temp_file.write(image_data)
        temp_path = temp_file.name
    
    try:
        # Use iTerm2's inline image protocol
        print(f"\nSign for '{word}':")
        
        # Open the image
        img = Image.open(io.BytesIO(image_data))
        
        # Resize to make the image larger (about 3x the original size)
        width, height = img.size
        scale_factor = 3.0  # Make image 3 times larger
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        
        # But cap at a reasonable maximum width
        max_width = 1500
        if new_width > max_width:
            ratio = max_width / new_width
            new_width = max_width
            new_height = int(new_height * ratio)
            
        img = img.resize((new_width, new_height))
        
        # Convert image to bytes
        with io.BytesIO() as output:
            img.save(output, format="PNG")
            image_bytes = output.getvalue()
        
        # Encode image in base64
        image_base64 = base64.b64encode(image_bytes).decode('ascii')
        
        # Print link to the word page
        print(f"Word page: https://signwiki.is/index.php/{word}")
        
        # Use iTerm2's inline image protocol
        sys.stdout.write(f"\033]1337;File=inline=1:{image_base64}\a\n")
        sys.stdout.flush()
        
    except Exception as e:
        print(f"Error displaying image: {e}")
        # Fallback to opening the image
        print(f"Opening image in default viewer...")
        import subprocess
        if sys.platform == 'darwin':  # macOS
            subprocess.call(['open', temp_path])
        elif sys.platform == 'win32':  # Windows
            os.startfile(temp_path)
        else:  # Linux
            subprocess.call(['xdg-open', temp_path])

def main():
    # Initialize the database
    init_db()
    
    if len(sys.argv) < 2:
        print("Usage: python main.py \"Icelandic sentence here\"")
        sys.exit(1)
    
    # Get the sentence from command line arguments
    sentence = " ".join(sys.argv[1:])
    
    # Split the sentence into words
    words = sentence.split()
    
    # Process each word and fetch its sign
    for word in words:
        if word.strip():  # Skip empty strings
            base_form = process_icelandic_word(word)
            print(f"Original: {word} → Base form: {base_form}")
            
            # Fetch and display the sign image
            image_data = fetch_signwiki_image(base_form)
            if image_data:
                display_image_in_terminal(image_data, base_form)
            else:
                print(f"No sign found for '{base_form}'")
            
            print("\n" + "-" * 40 + "\n")

if __name__ == "__main__":
    main()