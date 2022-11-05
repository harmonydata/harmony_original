import re

language_code_regex = re.compile(r'(?i)[a-z][a-z]')

def get_clean_language_code(language_string: str) -> str:
    matches = language_code_regex.findall(language_string)
    if len(matches) > 0:
        return matches[0].lower()
    return "en"
