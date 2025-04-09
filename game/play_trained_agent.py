import os
import sys
import pygame
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.losses import MeanSquaredError
import math

# Garantir que o diretório atual está no path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.environment import RocketEnvironment
import config

def play_with_trained_agent(model_path):
    """
    Carrega um modelo treinado e o utiliza para jogar o jogo.
    
    Args:
        model_path: Caminho para o arquivo do modelo (.h5)
    """
    # Configurações do jogo
    WIDTH, HEIGHT = config.WIDTH, config.HEIGHT
    FPS = config.FPS
    
    # Carrega o modelo treinado com objetos personalizados para resolver o problema do 'mse'
    try:
        # Tenta carregar o modelo com objetos personalizados
        custom_objects = {
            'mse': MeanSquaredError(),
            'mean_squared_error': MeanSquaredError()
        }
        model = load_model(model_path, custom_objects=custom_objects)
        print(f"Modelo carregado com sucesso: {model_path}")
    except Exception as e:
        print(f"Erro ao carregar o modelo: {e}")
        print("Tentando método alternativo de carregamento...")
        
        try:
            # Tenta o método alternativo
            model = tf.keras.models.load_model(model_path, compile=False)
            # Compila o modelo manualmente
            model.compile(loss='mse', optimizer='adam')
            print("Modelo carregado com método alternativo")
        except Exception as e:
            print(f"Falha no carregamento alternativo: {e}")
            sys.exit(1)
    
    # Inicializa pygame
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Rocket Landing - Agente Treinado")
    clock = pygame.time.Clock()
    
    # Detecta o caminho base do projeto
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Carrega recursos visuais
    try:
        background = pygame.image.load(os.path.join(base_path, "src/images/Fundo.png")).convert()
    except FileNotFoundError:
        # Cria um fundo preto de backup caso a imagem não seja encontrada
        background = pygame.Surface((WIDTH, HEIGHT))
        background.fill((0, 0, 0))
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))
    
    # Carrega fontes
    font_path = os.path.join(base_path, "src/utils/JetBrainsMono-Regular.ttf")
    font = pygame.font.Font(font_path, 18)
    
    # Inicializa o ambiente
    env = RocketEnvironment(render_mode='human')
    state = env.reset()
    
    # Variáveis para desenho do foguete
    rocket_width, rocket_height = env.rocket_width, env.rocket_height
    
    def draw_rocket(surface, rocket):
        rocket_surf = pygame.Surface((rocket_width, rocket_height), pygame.SRCALPHA)
        body_rect = pygame.Rect(0, 10, rocket_width, rocket_height - 10)
        pygame.draw.rect(rocket_surf, (200, 0, 0), body_rect)
        pygame.draw.polygon(rocket_surf, (255, 0, 0), [(0, 10), (rocket_width, 10), (rocket_width/2, 0)])
        pygame.draw.polygon(rocket_surf, (150, 150, 150), [(0, rocket_height), (5, rocket_height - 10), (0, rocket_height - 10)])
        pygame.draw.polygon(rocket_surf, (150, 150, 150), [(rocket_width, rocket_height), (rocket_width - 5, rocket_height - 10), (rocket_width, rocket_height - 10)])
        rotated_surf = pygame.transform.rotate(rocket_surf, (rocket.orientacao - 90))
        rotated_rect = rotated_surf.get_rect(center=(int(rocket.posicao[0]), HEIGHT - int(rocket.posicao[1])))
        surface.blit(rotated_surf, rotated_rect.topleft)
    
    running = True
    step_counter = 0
    
    # Loop principal
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r:
                    state = env.reset()
                    step_counter = 0
        
        # Determina a ação usando o modelo treinado
        action = np.argmax(model.predict(state.reshape(1, -1), verbose=0)[0])
        
        # Executa a ação no ambiente
        next_state, reward, done, info = env.step(action)
        state = next_state
        step_counter += 1
        
        # Renderização
        screen.blit(background, (0, 0))
        
        # Desenha plataformas
        initial_platform = env.initial_platform
        landing_platform = env.landing_platform
        pygame.draw.rect(screen, (100, 100, 100), 
                        (initial_platform.posicao[0], HEIGHT - 10, 
                        initial_platform.comprimento, 10))
        pygame.draw.rect(screen, (100, 100, 100), 
                        (landing_platform.posicao[0], HEIGHT - 10, 
                        landing_platform.comprimento, 10))
        
        # Desenha target se ainda não foi alcançado
        target = env.target
        foguete = env.rocket
        if not foguete.target_reached:
            pygame.draw.circle(
                screen,
                (255, 0, 0),
                (int(target.posicao[0]), HEIGHT - int(target.posicao[1])),
                int(target.altura / 2),
                4
            )
        
        # Desenha o foguete
        if not foguete.crashed:
            draw_rocket(screen, foguete)
        
        # Exibe informações
        info_text = font.render(
            f"Action: {action} | Reward: {reward:.2f} | Steps: {step_counter}", 
            True, (255, 255, 255)
        )
        screen.blit(info_text, (10, 10))
        
        # Exibe mensagens de estado
        if foguete.landed:
            msg = font.render("Missão cumprida! Pouso perfeito!", True, (0, 255, 0))
            screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2))
        elif foguete.crashed:
            msg = font.render("Foguete destruído!", True, (255, 0, 0))
            screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2))
        
        pygame.display.flip()
        clock.tick(FPS)
        
        # Reinicia se terminou
        if done:
            pygame.time.wait(2000)  # Pausa por 2 segundos
            state = env.reset()
            step_counter = 0
    
    pygame.quit()

if __name__ == "__main__":
    # Verifica se foi fornecido um caminho para o modelo
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
    else:
        model_path = "dqn_model_final.h5"  # Usa o modelo final por padrão
    
    if not os.path.exists(model_path):
        print(f"Erro: Modelo não encontrado em {model_path}")
        sys.exit(1)
    
    play_with_trained_agent(model_path)
