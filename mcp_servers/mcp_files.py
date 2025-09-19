import os

WORKSPACE = "workspace"
os.makedirs(WORKSPACE, exist_ok=True)

def create_file(filename: str, content: str) -> str:
    """Crea un archivo en el workspace"""
    file_path = os.path.join(WORKSPACE, filename)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ Archivo creado: {file_path}"
    except Exception as e:
        return f"❌ Error creando archivo: {str(e)}"
