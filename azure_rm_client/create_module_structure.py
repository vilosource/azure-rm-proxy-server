import os

def create_files_and_directories():
    base_path = os.path.dirname(os.path.abspath(__file__))

    # Define the structure
    structure = {
        "cmd.py": "",
        "client.py": "",
        "worker.py": "",
        "formatter.py": "",
        "commands": {
            "__init__.py": "",
            "base_command.py": "",
        },
        "formatters": {
            "__init__.py": "",
            "formatter_interface.py": "",
            "rich_formatter.py": "",
            "markdown_formatter.py": "",
            "mediawiki_formatter.py": "",
            "json_formatter.py": "",
            "text_formatter.py": "",
        },
    }

    def create_structure(base, structure):
        for name, content in structure.items():
            path = os.path.join(base, name)
            if isinstance(content, dict):
                os.makedirs(path, exist_ok=True)
                create_structure(path, content)
            else:
                with open(path, "w") as f:
                    f.write(content)

    # Create the structure
    create_structure(base_path, structure)

if __name__ == "__main__":
    create_files_and_directories()