import os

def display(filename: str):
    """
    Displays the contents of a .txt file from folder 'a' or 'b'.

    Example:
        display("a1.txt") -> shows text from saplexer/a/1.txt
        display("b3.txt") -> shows text from saplexer/b/3.txt
    """

    base_path = os.path.dirname(__file__)

    # Validate input
    if not filename.endswith(".txt") or len(filename) < 3:
        print("Invalid filename. Use format like 'a1.txt' or 'b2.txt'.")
        return

    folder = filename[0].lower()  # 'a' or 'b'
    file_number = filename[1:-4]  # e.g., '1', '2', etc.

    if folder not in ["a", "b"]:
        print("Invalid folder. Use 'a' or 'b' at the start of the filename.")
        return

    file_path = os.path.join(base_path, folder, f"{file_number}.txt")

    if not os.path.exists(file_path):
        print(f"File '{filename}' not found in folder '{folder}'.")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
            print(f"\n--- Displaying: {filename} ---\n{content}\n")
    except Exception as e:
        print(f"Error reading {filename}: {e}")
