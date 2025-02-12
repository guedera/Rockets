import pygame # type: ignore
import math
from src.entities.rocket import Rocket
from src.entities.platform import Platform

# Configurações da tela e da simulação
WIDTH, HEIGHT = 1600, 900
FPS = 60

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Fontes
splash_font = pygame.font.SysFont(None, 100)
small_font = pygame.font.SysFont(None, 24)
crash_font = pygame.font.SysFont(None, 72)

# Informações de versão e quit (HUD no canto superior esquerdo)
version_text = "0.6.4"
quit_text = "Press ESC to quit"

# Constantes para as setinhas do HUD (velocidade)
ARROW_SCALE = 0.2        # Fator de escala para converter velocidade em comprimento
ARROW_HEAD_LENGTH = 10
ARROW_HEAD_ANGLE = 30      # em graus
MIN_VELOCITY_DISPLAY = 5   # Se a velocidade for menor que esse valor, a seta não é desenhada
MAX_ARROW_LENGTH = 100     # Tamanho máximo da seta
BLINK_INTERVAL = 0.3       # Intervalo para o piscar da seta (em segundos)
# As setinhas serão desenhadas no canto superior direito com folga
HUD_ARROW_ORIGIN = (WIDTH - 150, 150)
blink_timer = 0

def draw_arrow(surface, color, start, end, head_length=ARROW_HEAD_LENGTH, head_angle=ARROW_HEAD_ANGLE):
    """Desenha uma seta com cabeça, dada a cor, ponto de início e fim."""
    pygame.draw.line(surface, color, start, end, 3)
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    angle = math.atan2(dy, dx)
    angle1 = angle + math.radians(head_angle)
    angle2 = angle - math.radians(head_angle)
    x1 = end[0] - head_length * math.cos(angle1)
    y1 = end[1] - head_length * math.sin(angle1)
    x2 = end[0] - head_length * math.cos(angle2)
    y2 = end[1] - head_length * math.sin(angle2)
    pygame.draw.polygon(surface, color, [end, (x1, y1), (x2, y2)])

# Criação das plataformas
initial_platform_width = 200
initial_platform_x = 100  # margem esquerda de 100 pixels
initial_platform = Platform(posicao_x=initial_platform_x, comprimento=initial_platform_width, altura=0)

landing_platform_width = 200
landing_platform_x = WIDTH - landing_platform_width - 100  # margem direita de 100 pixels
landing_platform = Platform(posicao_x=landing_platform_x, comprimento=landing_platform_width, altura=0)

# Definições do foguete (iniciado centralizado na plataforma inicial)
rocket_width, rocket_height = 20, 40
rocket_initial_x = initial_platform.posicao[0] + initial_platform.comprimento / 2
rocket_initial_y = rocket_height / 2  # O centro de massa inicia em rocket_height/2 (sobre o chão)
foguete = Rocket(posicao_x=rocket_initial_x, posicao_y=rocket_initial_y, massa=50)

# Flag para indicar se o foguete explodiu (crashed)
crashed = False

def draw_rocket(surface, rocket):
    """Desenha o foguete, rotacionando a imagem de acordo com rocket.orientacao."""
    rocket_surf = pygame.Surface((rocket_width, rocket_height), pygame.SRCALPHA)
    body_rect = pygame.Rect(0, 10, rocket_width, rocket_height - 10)
    pygame.draw.rect(rocket_surf, (200, 0, 0), body_rect)
    pygame.draw.polygon(rocket_surf, (255, 0, 0), [(0, 10), (rocket_width, 10), (rocket_width/2, 0)])
    pygame.draw.polygon(rocket_surf, (150, 150, 150), [(0, rocket_height), (5, rocket_height - 10), (0, rocket_height - 10)])
    pygame.draw.polygon(rocket_surf, (150, 150, 150), [(rocket_width, rocket_height), (rocket_width - 5, rocket_height - 10), (rocket_width, rocket_height - 10)])
    rotated_surf = pygame.transform.rotate(rocket_surf, (rocket.orientacao - 90))
    rotated_rect = rotated_surf.get_rect(center=(int(rocket.posicao[0]), HEIGHT - int(rocket.posicao[1])))
    surface.blit(rotated_surf, rotated_rect.topleft)

# Estados do jogo: "intro" (primeiros 5 segundos), "waiting" (após 5s, espera Space) e "play"
game_state = "intro"
intro_timer = 0.0

running = True
while running:
    delta_time = clock.tick(FPS) / 1000.0
    blink_timer += delta_time
    if blink_timer >= BLINK_INTERVAL:
        blink_timer = 0

    # Processa eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if game_state == "waiting" and event.key == pygame.K_SPACE:
                game_state = "play"

    # Limpa a tela
    screen.fill((0, 0, 30))
    
    # Exibe a versão e a mensagem de quit no canto superior esquerdo
    version_surface = small_font.render(version_text, True, (255, 255, 255))
    quit_surface = small_font.render(quit_text, True, (255, 255, 255))
    screen.blit(version_surface, (10, 10))
    screen.blit(quit_surface, (10, 30))
    
    # Se o jogo ainda não começou ("intro" ou "waiting"), exibe a tela de início
    if game_state != "play":
        if game_state == "intro":
            intro_timer += delta_time
            splash_text = splash_font.render("Rocket - by Guilherme Guedes", True, (255, 255, 255))
            splash_rect = splash_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(splash_text, splash_rect)
            if intro_timer >= 5.0:
                game_state = "waiting"
        elif game_state == "waiting":
            waiting_text = splash_font.render("Press Space to Play", True, (255, 255, 255))
            waiting_rect = waiting_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(waiting_text, waiting_rect)
        pygame.display.flip()
        continue  # Pula o restante do loop até o jogo iniciar

    # Se o jogo está em "play", processa controles, física e desenho do jogo
    keys = pygame.key.get_pressed()
    if keys[pygame.K_r]:
        foguete.reset()
        crashed = False

    if not crashed:
        if keys[pygame.K_w]:
            foguete.alterar_potencia(Rocket.POTENCIA_INCREMENTO)
        if keys[pygame.K_s]:
            foguete.alterar_potencia(-Rocket.POTENCIA_INCREMENTO)
        if keys[pygame.K_a]:
            foguete.aplicar_torque(+Rocket.ROTATION_TORQUE, delta_time)
        if keys[pygame.K_d]:
            foguete.aplicar_torque(-Rocket.ROTATION_TORQUE, delta_time)
        foguete.atualizar(delta_time)
        rocket_half_height = rocket_height / 2
        if foguete.posicao[1] <= rocket_half_height and foguete.velocidade[1] <= 0:
            on_initial = (initial_platform.posicao[0] <= foguete.posicao[0] <= initial_platform.posicao[0] + initial_platform.comprimento)
            on_landing = (landing_platform.posicao[0] <= foguete.posicao[0] <= landing_platform.posicao[0] + landing_platform.comprimento)
            if not (on_initial or on_landing):
                crashed = True
            else:
                foguete.posicao[1] = rocket_half_height
                if foguete.potencia_motor == 0:
                    foguete.velocidade = [0, 0]
                    foguete.angular_velocity = 0
                else:
                    foguete.velocidade[1] = 0
                    foguete.angular_velocity = 0

    # Desenha as plataformas
    initial_platform_rect = pygame.Rect(initial_platform.posicao[0], HEIGHT - 10, initial_platform.comprimento, 10)
    pygame.draw.rect(screen, (100, 100, 100), initial_platform_rect)
    landing_platform_rect = pygame.Rect(landing_platform.posicao[0], HEIGHT - 10, landing_platform.comprimento, 10)
    pygame.draw.rect(screen, (100, 100, 100), landing_platform_rect)
    
    # Desenha o foguete (ou "Crash!" se explodido)
    if not crashed:
        draw_rocket(screen, foguete)
    else:
        crash_text = crash_font.render("Crash!", True, (255, 0, 0))
        crash_rect = crash_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(crash_text, crash_rect)
    
    # Desenha a barra de potência (lado direito) com moldura
    bar_x, bar_y, bar_width, bar_height = WIDTH - 40, HEIGHT - 150, 20, 100
    pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
    filled_height = (foguete.potencia_motor / 100.0) * bar_height
    pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y + (bar_height - filled_height), bar_width, filled_height))
    pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
    
    # --- HUD: Desenha as setinhas de velocidade no canto superior direito ---
    vel_x = foguete.velocidade[0]
    if abs(vel_x) >= MIN_VELOCITY_DISPLAY:
        arrow_length_x = abs(vel_x) * ARROW_SCALE
        blinking_x = False
        if arrow_length_x > MAX_ARROW_LENGTH:
            arrow_length_x = MAX_ARROW_LENGTH
            blinking_x = True
        if not blinking_x or (blinking_x and blink_timer < BLINK_INTERVAL / 2):
            red_end = (HUD_ARROW_ORIGIN[0] + math.copysign(arrow_length_x, vel_x), HUD_ARROW_ORIGIN[1])
            draw_arrow(screen, (255, 0, 0), HUD_ARROW_ORIGIN, red_end)
    
    vel_y = foguete.velocidade[1]
    if abs(vel_y) >= MIN_VELOCITY_DISPLAY:
        arrow_length_y = abs(vel_y) * ARROW_SCALE
        blinking_y = False
        if arrow_length_y > MAX_ARROW_LENGTH:
            arrow_length_y = MAX_ARROW_LENGTH
            blinking_y = True
        if not blinking_y or (blinking_y and blink_timer < BLINK_INTERVAL / 2):
            blue_end = (HUD_ARROW_ORIGIN[0], HUD_ARROW_ORIGIN[1] - math.copysign(arrow_length_y, vel_y))
            draw_arrow(screen, (0, 0, 255), HUD_ARROW_ORIGIN, blue_end)
    
    pygame.display.flip()

pygame.quit()