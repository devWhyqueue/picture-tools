import argparse
import os


# Define a function to recursively search for files to delete
def delete_files(dir_a, dir_b):
    for item in os.listdir(dir_b):
        item_path = os.path.join(dir_b, item)
        if os.path.isfile(item_path):
            item_filename = os.path.basename(item_path)
            for root, dirs, files in os.walk(dir_a):
                for file in files:
                    if os.path.basename(file) == item_filename:
                        file_path = os.path.join(root, file)
                        os.remove(item_path)
                        break
        elif os.path.isdir(item_path):
            delete_files(dir_a, item_path)


# Define the CLI using argparse
parser = argparse.ArgumentParser(
    description="Delete all files from a directory b recursively which are in folder a (searched recursively)")
parser.add_argument("dir-a", help=f"Path to directory a")
parser.add_argument("dir_b", help="Path to directory b")

# Parse the CLI arguments and call the delete_files function
args = parser.parse_args()
dir_a = args.dir_a
dir_b = args.dir_b
delete_files(dir_a, dir_b)
print("Done.")
