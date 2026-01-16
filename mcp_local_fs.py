from mcp.server.fastmcp import FastMCP
import os

# Создаем сервер с именем 'LocalFS'
mcp = FastMCP("LocalFS")

@mcp.tool()
def list_project_files(relative_path: str = "."):
    """Список файлов в проекте."""
    full_path = os.path.abspath(os.path.join(os.getcwd(), relative_path))
    return os.listdir(full_path)

@mcp.tool()
def read_project_file(path: str):
    """Прочитать содержимое файла."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@mcp.tool()
def write_project_file(path: str, content: str):
    """Создать новый файл или перезаписать существующий."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Файл {path} успешно записан"

if __name__ == "__main__":
    mcp.run()
