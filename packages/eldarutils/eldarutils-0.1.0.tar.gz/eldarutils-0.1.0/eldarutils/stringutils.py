def reverse(text):
    """Return the reversed version of the text."""
    return text[::-1]

def capitalize_words(text):
    """Capitalize the first letter of every word."""
    return " ".join(word.capitalize() for word in text.split())

def remove_vowels(text):
    """Remove all vowels from the given text."""
    vowels = "aeiouAEIOU"
    return "".join(ch for ch in text if ch not in vowels)

def count_vowels(text):
    """Count how many vowels are in the text."""
    vowels = "aeiouAEIOU"
    return sum(1 for ch in text if ch in vowels)

def is_palindrome(text):
    """Check if a text is a palindrome."""
    cleaned = "".join(ch.lower() for ch in text if ch.isalnum())
    return cleaned == cleaned[::-1]

def remove_specials(text):
    """Remove special characters (keep letters, digits, and spaces)."""
    return "".join(ch for ch in text if ch.isalnum() or ch.isspace())

def word_count(text):
    """Count how many words are in the text."""
    return len(text.split())

def extract_digits(text):
    """Return only digits from the text."""
    return "".join(ch for ch in text if ch.isdigit())

def char_frequency(text):
    """Return a dictionary with frequency of each character."""
    freq = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    return freq
