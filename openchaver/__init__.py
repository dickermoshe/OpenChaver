from pathlib import Path
BASE_DIR = Path(__file__).parent
image_database_path = BASE_DIR / "images.db"
image_database_url = "sqlite:///" + str(image_database_path)