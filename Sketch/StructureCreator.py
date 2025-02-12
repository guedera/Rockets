import os

def create_structure(base_path="meu_jogo"):
    structure = [
        "assets/images",
        "assets/sounds",
        "assets/fonts",
        "src/scenes",
        "src/entities",
        "src/utils",
    ]
    
    files = [
        "src/scenes/main_menu.py",
        "src/scenes/game.py",
        "src/scenes/game_over.py",
        "src/entities/rocket.py",
        "src/entities/platform.py",
        "src/utils/config.py",
        "src/utils/helpers.py",
        "src/utils/sound_manager.py",
        "src/game_loop.py",
        "src/settings.py",
        "main.py",
        "requirements.txt",
        "README.md"
    ]
    
    # Criando diretórios
    for folder in structure:
        os.makedirs(os.path.join(base_path, folder), exist_ok=True)
    
    # Criando arquivos vazios
    for file in files:
        file_path = os.path.join(base_path, file)
        with open(file_path, "w") as f:
            pass
    
    print(f"Estrutura do jogo criada em: {base_path}")

# Executando a função
create_structure()
