import os

def split_file(input_file, chunk_size, output_dir):
    """
    Splits the file at input_file into chunks of chunk_size (in bytes),
    and saves them in output_dir.
    
    :param input_file: Path to the input file.
    :param chunk_size: Chunk size in bytes (e.g., 1024 for 1KB).
    :param output_dir: Directory where chunk files will be saved.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' not found.")

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.basename(input_file)
    with open(input_file, 'rb') as f:
        i = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            chunk_filename = os.path.join(output_dir, f"{base_name}.part{i}")
            with open(chunk_filename, 'wb') as chunk_file:
                chunk_file.write(chunk)
            i += 1