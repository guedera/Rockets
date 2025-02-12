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
platform = Platform(posicao_x=(WIDTH - platform_width) // 2, comprimento=platform_width, altura=0)

# Definições do foguete
rocket_width, rocket_height = 20, 40
rocket_initial_x = platform.posicao[0] + platform.comprimento / 2
rocket_initial_y = rocket_height / 2  # O centro de massa inicia em rocket_height/2
foguete = Rocket(posicao_x=rocket_initial_x, posicao_y=rocket_initial_y, massa=50)

def draw_rocket(surface, rocket):
    """
    Desenha o foguete.
    
    A imagem é rotacionada de forma que:
      - Quando rocket.orientacao == 90, o foguete aparece "de pé" (apontando para cima);
      - Valores maiores que 90 resultam em uma rotação antihorária (inclinação para a esquerda);
      - Valores menores que 90 resultam em uma rotação horária (inclinação para a direita).
    """
    rocket_surf = pygame.Surface((rocket_width, rocket_height), pygame.SRCALPHA)
    # Corpo do foguete: retângulo, nariz triangular e aletas
    body_rect = pygame.Rect(0, 10, rocket_width, rocket_height - 10)
    pygame.draw.rect(rocket_surf, (200, 0, 0), body_rect)
    pygame.draw.polygon(rocket_surf, (255, 0, 0), [(0, 10), (rocket_width, 10), (rocket_width/2, 0)])
    pygame.draw.polygon(rocket_surf, (150, 150, 150), [(0, rocket_height), (5, rocket_height - 10), (0, rocket_height - 10)])
    pygame.draw.polygon(rocket_surf, (150, 150, 150), [(rocket_width, rocket_height), (rocket_width - 5, rocket_height - 10), (rocket_width, rocket_height - 10)])
    
    # Rotaciona a imagem usando a rotação direta:
    # Quando rocket.orientacao == 90, nenhuma rotação é aplicada.
    rotated_surf = pygame.transform.rotate(rocket_surf, (rocket.orientacao - 90))
    rotated_rect = rotated_surf.get_rect(center=(int(rocket.posicao[0]), HEIGHT - int(rocket.posicao[1])))
    surface.blit(rotated_surf, rotated_rect.topleft)

running = True
while running:
    delta_time = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    # Controle de potência do motor
    if keys[pygame.K_w]:
        foguete.alterar_potencia(Rocket.POTENCIA_INCREMENTO)
    if keys[pygame.K_s]:
        foguete.alterar_potencia(-Rocket.POTENCIA_INCREMENTO)
    # Controle de rotação: A para girar no sentido antihorário, D para girar no sentido horário
    if keys[pygame.K_a]:
        foguete.aplicar_torque(+Rocket.ROTATION_TORQUE, delta_time)
    if keys[pygame.K_d]:
        foguete.aplicar_torque(-Rocket.ROTATION_TORQUE, delta_time)
    # Reset do foguete
    if keys[pygame.K_r]:
        foguete.reset()

    # Atualiza a física do foguete
    foguete.atualizar(delta_time)

    # Impede que o foguete penetre o chão:
    # Se o centro de massa estiver abaixo de rocket_height/2 e se movendo para baixo, "prende-o" ao chão.
    rocket_half_height = rocket_height / 2
    if foguete.posicao[1] < rocket_half_height and foguete.velocidade[1] <= 0:
        foguete.posicao[1] = rocket_half_height
        foguete.velocidade[1] = 0
        foguete.angular_velocity = 0

    screen.fill((0, 0, 30))
    # Desenha a plataforma (chão)
    platform_rect = pygame.Rect(platform.posicao[0], HEIGHT - 10, platform.comprimento, 10)
    pygame.draw.rect(screen, (100, 100, 100), platform_rect)
    # Desenha o foguete
    draw_rocket(screen, foguete)
    # Desenha a barra de potência (lado direito) com moldura
    bar_x, bar_y, bar_width, bar_height = WIDTH - 40, HEIGHT - 150, 20, 100
    pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
    filled_height = (foguete.potencia_motor / 100.0) * bar_height
    pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y + (bar_height - filled_height), bar_width, filled_height))
    pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)

    pygame.display.flip()

pygame.quit()
