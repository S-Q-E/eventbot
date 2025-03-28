MAX_MESSAGE_LENGTH = 4096

def split_message(text, max_length=MAX_MESSAGE_LENGTH):
    """Функция для разбиения длинного текста на части"""
    lines = text.split("\n")
    chunks = []
    current_chunk = ""

    for line in lines:
        if len(current_chunk) + len(line) + 1 > max_length:
            chunks.append(current_chunk)
            current_chunk = line
        else:
            current_chunk += "\n" + line if current_chunk else line

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
