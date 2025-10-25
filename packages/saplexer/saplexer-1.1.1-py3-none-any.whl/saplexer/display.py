import os

def display(filename: str):
    """
    Display the contents of a .txt file inside folder 'a' or 'b'.

    Example:
        display("a1.txt")  # Reads saplexer/a/1.txt
        display("b3.txt")  # Reads saplexer/b/3.txt
    """
    folder = filename[0].lower()  # e.g. 'a' or 'b'

    if not filename.endswith(".txt") or folder not in ["a", "b"]:
        print("❌ Use correct format like 'a1.txt' or 'b3.txt'")
        return

    # Build path inside package
    base_path = os.path.join(os.path.dirname(__file__), folder)
    file_number = filename[1:-4]  # remove first letter and '.txt'
    file_path = os.path.join(base_path, f"{file_number}.txt")

    if not os.path.exists(file_path):
        print(f"❌ File '{filename}' not found in folder '{folder}'.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    print(f"\n📄 Displaying {filename}\n{'-'*30}\n{content}\n")
