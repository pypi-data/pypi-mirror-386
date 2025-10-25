def reverse_string(s):
    return s[::-1]

def camel_to_snake(s):
    import re
    return re.sub(r'(?<!^)(?=[A-Z])', '_', s).lower()

def snake_to_camel(s):
    return ''.join(word.title() for word in s.split('_'))

def is_palindrome(s):
    s_clean = ''.join(c.lower() for c in s if c.isalnum())
    return s_clean == s_clean[::-1]
def count_vowels(s):
    return sum(1 for c in s.lower() if c in "aeiou")

def count_consonants(s):
    return sum(1 for c in s.lower() if c.isalpha() and c not in "aeiou")

def truncate(s, length):
    return s[:length]

def capitalize_sentences(text):
    return ". ".join(sentence.strip().capitalize() for sentence in text.split("."))

def mask_email(email):
    parts = email.split("@")
    return parts[0][0] + "****@" + parts[1]

def is_anagram(s1, s2):
    return sorted(s1.replace(" ","").lower()) == sorted(s2.replace(" ","").lower())
