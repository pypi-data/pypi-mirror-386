import os
from filesplitter import split_file

def test_split():
    input_file = "sample.txt"
    output_dir = "output_chunks"
    chunk_size = 10  # bytes

    with open(input_file, "w") as f:
        f.write("This is a test file. It will be split into parts.")

    split_file(input_file, chunk_size, output_dir)

    chunks = sorted(os.listdir(output_dir))
    print(f"Created {len(chunks)} chunks:")
    for chunk in chunks:
        with open(os.path.join(output_dir, chunk), 'r') as f:
            print(f"{chunk}: {f.read()}")

    os.remove(input_file)
    for chunk in chunks:
        os.remove(os.path.join(output_dir, chunk))
    os.rmdir(output_dir)

if __name__ == "__main__":
    test_split()