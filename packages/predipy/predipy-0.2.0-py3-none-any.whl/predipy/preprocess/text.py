# Text preprocessing sederhana
import re
from typing import List, Union

def clean_text(texts: Union[str, List[str]]) -> Union[str, List[str]]:
    """Clean: lowercase, remove non-alphanum, remove @mentions and #hashtags."""
    def clean_single(text: str) -> str:
        if not isinstance(text, str):
            return ""
        text = text.lower()
        # Remove @mentions and #hashtags first (entire tokens)
        text = re.sub(r'\s+[@#][a-zA-Z0-9_]+', '', text)  # Remove " @user" or " #hashtag"
        # Remove other non-alphanum
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    if isinstance(texts, str):
        return clean_single(texts)
    else:
        return [clean_single(text) for text in texts]
