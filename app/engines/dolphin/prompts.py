LAYOUT_PROMPT = "Parse the reading order of this document."

ELEMENT_PROMPTS = {
    "tab": "Parse the table in the image.",
    "equ": "Read formula in the image.",
    "code": "Read code in the image.",
    "text": "Read text in the image.",
    "para": "Read text in the image.",
    "title": "Read text in the image.",
    "distorted_page": "Read text in the image.",
}


def get_element_prompt(label: str) -> str:
    return ELEMENT_PROMPTS.get(label, ELEMENT_PROMPTS["text"])
