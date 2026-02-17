import os

def combine_python_files(folder_path, output_file):
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for filename in os.listdir(folder_path):
            if filename.endswith(".py"):
                file_path = os.path.join(folder_path, filename)
                
                with open(file_path, 'r', encoding='utf-8') as infile:
                    outfile.write(f"# ===== {filename} =====\n")
                    outfile.write(infile.read())
                    outfile.write("\n\n")

if __name__ == "__main__":
    combine_python_files("src/routes", "combined.py")
