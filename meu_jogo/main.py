import pygame
from src.entities.rocket import Rocket
from src.entities.platform import Platform

# Configurações iniciais
WIDTH, HEIGHT = 800, 600
FPS = 60

# Inicializar o Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Criar objetos
foguete = Rocket(posicao_x=400, posicao_y=50, massa=50)
plataforma = Platform(posicao_x=350, comprimento=100)

# Loop principal
going = True
while going:
    delta_time = clock.get_time() / 1000  # Tempo entre frames
    screen.fill((0, 0, 0))  # Fundo preto
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            going = False
    
    # Controles do foguete
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        foguete.alterar_potencia(1)
    if keys[pygame.K_s]:
        foguete.alterar_potencia(-1)
    if keys[pygame.K_a]:
        foguete.girar_motor(-1)
    if keys[pygame.K_d]:
        foguete.girar_motor(1)
    
    # Atualizar foguete
    foguete.atualizar(delta_time)
    
    # Desenhar elementos (placeholder)
    pygame.draw.rect(screen, (255, 255, 255), (plataforma.posicao[0], HEIGHT - 20, plataforma.comprimento, 10))  # Plataforma
    pygame.draw.circle(screen, (255, 0, 0), (int(foguete.posicao[0]), HEIGHT - int(foguete.posicao[1]) - 50), 10)  # Foguete
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
