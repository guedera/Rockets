import time
import pygame
from stable_baselines3 import DQN
from rocket_env import RocketEnv

# Inicializa o Pygame e cria a janela de visualização
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 900
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Rocket IA - Teste")
clock = pygame.time.Clock()

# Carrega o background do jogo
# Como test_dqn.py está em IA, o caminho relativo para o fundo é:
background = pygame.image.load("Game/src/images/Fundo.png").convert()
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))

def draw_rocket(surface, rocket):
    rocket_width = 20
    rocket_height = 40
    rocket_surf = pygame.Surface((rocket_width, rocket_height), pygame.SRCALPHA)
    # Desenha o corpo
    body_rect = pygame.Rect(0, 10, rocket_width, rocket_height - 10)
    pygame.draw.rect(rocket_surf, (200, 0, 0), body_rect)
    # Desenha a ponta (triângulo)
    pygame.draw.polygon(rocket_surf, (255, 0, 0), [(0, 10), (rocket_width, 10), (rocket_width/2, 0)])
    # Desenha as aletas (esquerda)
    pygame.draw.polygon(rocket_surf, (150, 150, 150), [(0, rocket_height), (5, rocket_height - 10), (0, rocket_height - 10)])
    # Desenha as aletas (direita)
    pygame.draw.polygon(rocket_surf, (150, 150, 150), [(rocket_width, rocket_height), (rocket_width - 5, rocket_height - 10), (rocket_width, rocket_height - 10)])
    # Aplica a rotação
    rotated_surf = pygame.transform.rotate(rocket_surf, (rocket.orientacao - 90))
    rotated_rect = rotated_surf.get_rect(center=(int(rocket.posicao[0]), SCREEN_HEIGHT - int(rocket.posicao[1])))
    surface.blit(rotated_surf, rotated_rect.topleft)

def draw_environment(env):
    # Desenha o fundo
    screen.blit(background, (0, 0))
    
    # Desenha a plataforma de decolagem (initial platform) em uma cor diferenciada (ex: verde escuro)
    init_plat_x = int(env.initial_platform.posicao[0])
    init_plat_width = int(env.initial_platform.comprimento)
    init_plat_height = 10
    init_plat_y = SCREEN_HEIGHT - init_plat_height
    pygame.draw.rect(screen, (0, 100, 0), (init_plat_x, init_plat_y, init_plat_width, init_plat_height))
    
    # Desenha a plataforma de pouso (landing platform) (retângulo cinza)
    land_plat_x = int(env.landing_platform.posicao[0])
    land_plat_width = int(env.landing_platform.comprimento)
    land_plat_height = 10
    land_plat_y = SCREEN_HEIGHT - land_plat_height
    pygame.draw.rect(screen, (100, 100, 100), (land_plat_x, land_plat_y, land_plat_width, land_plat_height))
    
    # Desenha o target (círculo vermelho) se ainda não foi alcançado
    if not env.target_passed:
        target_x = int(env.target.posicao[0])
        target_y = SCREEN_HEIGHT - int(env.target.posicao[1])
        target_radius = int(env.target.altura / 2)
        pygame.draw.circle(screen, (255, 0, 0), (target_x, target_y), target_radius, 2)
    
    # Desenha o foguete
    draw_rocket(screen, env.rocket)
    
    pygame.display.flip()

def main():
    # Cria o ambiente
    env = RocketEnv()
    
    # Reinicia o ambiente (o foguete iniciará no solo, conforme definido em rocket_env.py)
    obs = env.reset()
    
    # Carrega o modelo treinado (ajuste o caminho se necessário)
    model = DQN.load("dqn_rocket_model_final")
    
    running = True
    while running:
        # Processa eventos para permitir fechar a janela
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # O modelo predita a ação com base na observação
        action, _states = model.predict(obs)
        obs, reward, done, info = env.step(action)
        
        # Atualiza a renderização do ambiente
        draw_environment(env)
        
        clock.tick(60)  # Limita a 60 FPS
        time.sleep(0.02)
        
        if done:
            obs = env.reset()
    
    pygame.quit()

if __name__ == '__main__':
    main()
