
def reverse_string(text: str) -> str:
    if len(text) == 1:
        return text

    text_to_list = list(text)
    left, right = 0, len(text_to_list) - 1
    while left <= right:
        if text_to_list[left].isalnum() and text_to_list[right].isalnum():
            text_to_list[left], text_to_list[right] = text_to_list[right], text_to_list[left]
            left += 1
            right -= 1
        if not text_to_list[left].isalnum():
            left += 1
        if not text_to_list[right].isalnum():
            right -= 1
    return ''.join(text_to_list)