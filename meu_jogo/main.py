# main.py
import pygame
import math
from src.entities.rocket import Rocket
from src.entities.platform import Platform

# Configurações da tela e da simulação
WIDTH, HEIGHT = 800, 600
FPS = 60

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Criação da plataforma (chão)
platform_width = 200
# Centraliza a plataforma na tela; em nossa simulação, o chão é y = 0
platform = Platform(posicao_x=(WIDTH - platform_width) // 2, comprimento=platform_width, altura=0)

# Definições do foguete
rocket_width, rocket_height = 20, 40
# Coloca o foguete centralizado horizontalmente sobre a plataforma;
# define a posição inicial y como metade da altura do foguete (centro de massa acima do chão)
rocket_initial_x = platform.posicao[0] + platform.comprimento / 2
rocket_initial_y = rocket_height / 2
foguete = Rocket(posicao_x=rocket_initial_x, posicao_y=rocket_initial_y, massa=50)

def draw_rocket(surface, rocket):
    """Desenha o foguete com rotação e indicador do ângulo do motor."""
    # Cria uma surface com transparência para desenhar o foguete
    rocket_surf = pygame.Surface((rocket_width, rocket_height), pygame.SRCALPHA)
    
    # Corpo do foguete:
    # - Corpo retangular (parte inferior)
    body_rect = pygame.Rect(0, 10, rocket_width, rocket_height - 10)
    pygame.draw.rect(rocket_surf, (200, 0, 0), body_rect)
    # - Nariz triangular
    pygame.draw.polygon(rocket_surf, (255, 0, 0), [(0, 10), (rocket_width, 10), (rocket_width/2, 0)])
    # - Aletas (finas) na base
    pygame.draw.polygon(rocket_surf, (150, 150, 150), [(0, rocket_height), (5, rocket_height - 10), (0, rocket_height - 10)])
    pygame.draw.polygon(rocket_surf, (150, 150, 150), [(rocket_width, rocket_height), (rocket_width - 5, rocket_height - 10), (rocket_width, rocket_height - 10)])
    
    # Indicação visual do ângulo do motor: uma linha verde partindo da base central
    engine_start = (rocket_width/2, rocket_height - 5)
    gimbal_angle = math.radians(rocket.angulo_motor)
    line_length = 15
    engine_end = (rocket_width/2 + line_length * math.sin(gimbal_angle),
                  rocket_height - 5 - line_length * math.cos(gimbal_angle))
    pygame.draw.line(rocket_surf, (0, 255, 0), engine_start, engine_end, 3)
    
    # Rotaciona a imagem do foguete compensando os 90° iniciais
    rotated_surf = pygame.transform.rotate(rocket_surf, -(rocket.orientacao - 90))
    # Converte as coordenadas da simulação para a tela:
    # Na simulação, y = 0 é o chão; na tela, y aumenta para baixo.
    rotated_rect = rotated_surf.get_rect(center=(int(rocket.posicao[0]), HEIGHT - int(rocket.posicao[1])))
    surface.blit(rotated_surf, rotated_rect.topleft)

running = True
while running:
    # Use tick() para obter delta_time consistente
    delta_time = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Controles do foguete:
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        foguete.alterar_potencia(Rocket.POTENCIA_INCREMENTO)
    if keys[pygame.K_s]:
        foguete.alterar_potencia(-Rocket.POTENCIA_INCREMENTO)
    if keys[pygame.K_a]:
        foguete.girar_motor(-1)  # Gira o gimbal para a esquerda
    if keys[pygame.K_d]:
        foguete.girar_motor(1)   # Gira o gimbal para a direita

    # Atualiza a física do foguete
    foguete.atualizar(delta_time)

    # Colisão com o chão: garante que o foguete não desça abaixo do chão (y = 0)
    rocket_half_height = rocket_height / 2
    if foguete.posicao[1] < rocket_half_height:
        foguete.posicao[1] = rocket_half_height
        foguete.velocidade[1] = 0
        foguete.angular_velocity = 0

    # Desenhos
    screen.fill((0, 0, 30))  # Fundo escuro
    # Desenha a plataforma (chão)
    platform_rect = pygame.Rect(platform.posicao[0], HEIGHT - 10, platform.comprimento, 10)
    pygame.draw.rect(screen, (100, 100, 100), platform_rect)
    # Desenha o foguete
    draw_rocket(screen, foguete)
    # Desenha a barra de potência (lado direito)
    bar_x, bar_y, bar_width, bar_height = WIDTH - 40, HEIGHT - 150, 20, 100
    pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
    filled_height = (foguete.potencia_motor / 100.0) * bar_height
    pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y + (bar_height - filled_height), bar_width, filled_height))

    pygame.display.flip()

pygame.quit()
