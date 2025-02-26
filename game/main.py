import sys
import pygame
import math
import random
from src.entities.rocket import Rocket
from src.entities.platform import Platform
from src.entities.target import Target

# Configurações da tela e da simulação
WIDTH, HEIGHT = 1600, 900
FPS = 60

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Carrega e redimensiona a imagem de fundo
background = pygame.image.load("game/src/images/Fundo.png").convert()
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# Carrega a fonte personalizada (tamanhos reduzidos)
splash_font = pygame.font.Font("game/src/utils/JetBrainsMono-Regular.ttf", 60)
small_font = pygame.font.Font("game/src/utils/JetBrainsMono-Regular.ttf", 18)
crash_font = pygame.font.Font("game/src/utils/JetBrainsMono-Regular.ttf", 48)

# Informações de versão e quit (HUD no canto superior esquerdo)
version_text = "0.9.0"
quit_text = "Press ESC to quit"

# Constantes para as setinhas do HUD (usadas para Speed e Orientation)
ARROW_SCALE = 0.2        # Fator de escala para converter velocidade em comprimento
ARROW_HEAD_LENGTH = 10
ARROW_HEAD_ANGLE = 30      # em graus
MIN_VELOCITY_DISPLAY = 5   # Se a velocidade for menor que esse valor, a seta não é desenhada
MAX_ARROW_LENGTH = 50     # Tamanho máximo da seta
BLINK_INTERVAL = 0.3       # Intervalo para o piscar da seta (em segundos)
blink_timer = 0

def draw_arrow(surface, color, start, end, head_length=ARROW_HEAD_LENGTH, head_angle=ARROW_HEAD_ANGLE):
    """
    Desenha uma seta com cabeça, dada a cor, ponto de início e fim.
    """
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

# --- HUD PANEL: define o retângulo do HUD ---
hud_panel_rect = pygame.Rect(WIDTH//2 - 300, HEIGHT - 220, 600, 200)
HUD_BG_COLOR = (0, 0, 0, 150)         # Fundo preto com transparência (alpha 150)
HUD_BORDER_COLOR = (200, 200, 200)      # Borda cinza claro
HUD_BORDER_RADIUS = 15                # Raio para cantos arredondados

# --- HUD GRUPO: posições para os itens do painel ---
hud_center = hud_panel_rect.center
THRUST_GROUP_CENTER = (hud_center[0] - 150, hud_panel_rect.centery + 20)
SPEED_GROUP_CENTER  = (hud_center[0], hud_panel_rect.centery + 20)
ORIENTATION_GROUP_CENTER = (hud_center[0] + 150, hud_panel_rect.centery + 20)
# Posição do texto de posição (um pouco mais acima dentro do painel)
POSITION_TEXT_CENTER = (hud_panel_rect.centerx, hud_panel_rect.top + 15)

# Constante para velocidade de pouso segura (em pixels/segundo)
LANDING_SPEED_THRESHOLD = 50

# Criação das plataformas
initial_platform_width = 200
initial_platform_x = 100
initial_platform = Platform(posicao_x=initial_platform_x, comprimento=initial_platform_width, altura=0)

landing_platform_width = 200
landing_platform_x = WIDTH - landing_platform_width - 100
landing_platform = Platform(posicao_x=landing_platform_x, comprimento=landing_platform_width, altura=0)

# Definições do foguete (iniciado na plataforma inicial)
rocket_width, rocket_height = 20, 40
rocket_initial_x = initial_platform.posicao[0] + initial_platform.comprimento / 2
rocket_initial_y = rocket_height / 2
foguete = Rocket(posicao_x=rocket_initial_x, posicao_y=rocket_initial_y, massa=50)

# Constante de conversão: quantos pixels equivalem a 1 metro
PIXELS_PER_METER = 100

# Nova variável para contabilizar o combustível gasto
fuel_consumed = 0.0

# Nova variável oculta para indicar vitória (pouso seguro na plataforma de pouso)
win = 0

# Variável para controlar o tempo de exibição da mensagem de vitória
landed_message_timer = None

# --- IMPLEMENTAÇÃO DO TARGET ---
# O target agora terá sua posição y sempre maior que 1 metro (100 pixels)
TARGET_DIAMETER = 50
target = Target(
    random.randint(TARGET_DIAMETER//2, WIDTH - TARGET_DIAMETER//2),
    random.randint(PIXELS_PER_METER, HEIGHT - TARGET_DIAMETER//2),
    TARGET_DIAMETER,
    TARGET_DIAMETER
)
target_passed = False

# Estados do jogo: "intro", "waiting", "play"
game_state = "intro"
intro_timer = 0.0

# Flag de crash
crashed = False

def draw_rocket(surface, rocket):
    """
    Desenha o foguete, rotacionado conforme rocket.orientacao.
    """
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
while running:
    delta_time = clock.tick(FPS) / 1000.0
    blink_timer += delta_time

    # Se já venceu, atualiza o timer da mensagem de vitória e fecha após 3 segundos.
    if win == 1:
        if landed_message_timer is None:
            landed_message_timer = 0
        else:
            landed_message_timer += delta_time
            if landed_message_timer >= 3:
                pygame.quit()
                sys.exit()

    if blink_timer >= BLINK_INTERVAL:
        blink_timer = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            if game_state == "waiting" and event.key == pygame.K_SPACE:
                game_state = "play"

    screen.blit(background, (0, 0))

    version_surface = small_font.render(version_text, True, (255, 255, 255))
    quit_surface = small_font.render(quit_text, True, (255, 255, 255))
    screen.blit(version_surface, (10, 10))
    screen.blit(quit_surface, (10, 30))

    if game_state != "play":
        if game_state == "intro":
            intro_timer += delta_time
            splash_text = splash_font.render("Rocket - by Guilherme Guedes", True, (255, 255, 255))
            splash_rect = splash_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(splash_text, splash_rect)
            if intro_timer >= 2.0:
                game_state = "waiting"
        elif game_state == "waiting":
            waiting_text = splash_font.render("Press Space to Play", True, (255, 255, 255))
            waiting_rect = waiting_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(waiting_text, waiting_rect)
        pygame.display.flip()
        continue

    keys = pygame.key.get_pressed()
    if keys[pygame.K_r]:
        foguete.reset()
        crashed = False
        fuel_consumed = 0.0
        win = 0
        landed_message_timer = None
        # Reposiciona o target aleatoriamente e reseta a flag,
        # garantindo que sua posição y seja maior que 1 metro.
        target = Target(
            random.randint(TARGET_DIAMETER//2, WIDTH - TARGET_DIAMETER//2),
            random.randint(PIXELS_PER_METER, HEIGHT - TARGET_DIAMETER//2),
            TARGET_DIAMETER,
            TARGET_DIAMETER
        )
        target_passed = False
    if keys[pygame.K_x]:
        foguete.potencia_motor = 0

    if game_state == "play" and not crashed:
        fuel_consumed += (foguete.potencia_motor / 100.0) * delta_time

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

        # Verifica se o foguete passou pelo target (checa se o centro do foguete está dentro do círculo)
        if not target_passed:
            dx = foguete.posicao[0] - target.posicao[0]
            dy = foguete.posicao[1] - target.posicao[1]
            if math.sqrt(dx**2 + dy**2) <= target.altura / 2:
                target_passed = True

        rocket_half_height = rocket_height / 2
        if foguete.posicao[1] <= rocket_half_height and foguete.velocidade[1] <= 0:
            landing_speed = math.sqrt(foguete.velocidade[0]**2 + foguete.velocidade[1]**2)
            on_initial = (initial_platform.posicao[0] <= foguete.posicao[0] <= initial_platform.posicao[0] + initial_platform.comprimento)
            on_landing = (landing_platform.posicao[0] <= foguete.posicao[0] <= landing_platform.posicao[0] + landing_platform.comprimento)
            if landing_speed > LANDING_SPEED_THRESHOLD:
                crashed = True
            else:
                if on_initial or on_landing:
                    foguete.posicao[1] = rocket_half_height
                    if foguete.potencia_motor == 0:
                        foguete.velocidade = [0, 0]
                        foguete.angular_velocity = 0
                    else:
                        foguete.velocidade[1] = 0
                        foguete.angular_velocity = 0
                    # Marca vitória somente se pousar na plataforma de pouso E tiver passado pelo target
                    if on_landing and target_passed:
                        win = 1
                else:
                    crashed = True

    # Desenha as plataformas
    initial_platform_rect = pygame.Rect(initial_platform.posicao[0], HEIGHT - 10, initial_platform.comprimento, 10)
    pygame.draw.rect(screen, (100, 100, 100), initial_platform_rect)
    landing_platform_rect = pygame.Rect(landing_platform.posicao[0], HEIGHT - 10, landing_platform.comprimento, 10)
    pygame.draw.rect(screen, (100, 100, 100), landing_platform_rect)

    # Desenha o target se ainda não foi atravessado (agora em vermelho)
    if not target_passed:
        pygame.draw.circle(
            screen,
            (255, 0, 0),
            (int(target.posicao[0]), HEIGHT - int(target.posicao[1])),
            int(target.altura / 2),
            2
        )

    if not crashed:
        draw_rocket(screen, foguete)
    else:
        crash_text = crash_font.render("Crash!", True, (255, 0, 0))
        crash_rect = crash_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(crash_text, crash_rect)

    # --- HUD PANEL: Desenha o painel do HUD com fundo transparente e bordas arredondadas ---
    hud_surface = pygame.Surface((hud_panel_rect.width, hud_panel_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(hud_surface, HUD_BG_COLOR, hud_surface.get_rect(), border_radius=HUD_BORDER_RADIUS)
    pygame.draw.rect(hud_surface, HUD_BORDER_COLOR, hud_surface.get_rect(), 2, border_radius=HUD_BORDER_RADIUS)
    screen.blit(hud_surface, hud_panel_rect.topleft)

    dx_pixels = foguete.posicao[0] - rocket_initial_x
    dy_pixels = foguete.posicao[1] - rocket_initial_y
    pos_x_m = dx_pixels / PIXELS_PER_METER
    pos_y_m = dy_pixels / PIXELS_PER_METER
    position_text = small_font.render(f"Pos: {pos_x_m:.2f}:{pos_y_m:.2f} m", True, (255, 255, 255))
    position_text_rect = position_text.get_rect(center=(hud_panel_rect.centerx, hud_panel_rect.top + 15))
    screen.blit(position_text, position_text_rect)

    fuel_text = small_font.render(f"Fuel: {fuel_consumed:.2f}", True, (255, 255, 255))
    fuel_text_rect = fuel_text.get_rect(center=(hud_panel_rect.centerx - 100, hud_panel_rect.bottom - 20))
    screen.blit(fuel_text, fuel_text_rect)

    speed_value_text = small_font.render(f"v: { (math.sqrt(foguete.velocidade[0]**2 + foguete.velocidade[1]**2)) / PIXELS_PER_METER:.2f} m/s", True, (255, 255, 255))
    speed_value_rect = speed_value_text.get_rect(center=(hud_panel_rect.centerx + 100, hud_panel_rect.bottom - 20))
    screen.blit(speed_value_text, speed_value_rect)

    # --- HUD: Grupo de indicadores no painel ---
    # 1. Thrust (Barra de potência) com rótulo acima
    thrust_bar_width = 20
    thrust_bar_height = 100
    thrust_bar_x = THRUST_GROUP_CENTER[0] - thrust_bar_width // 2
    thrust_bar_y = THRUST_GROUP_CENTER[1] - thrust_bar_height // 2
    pygame.draw.rect(screen, (50, 50, 50), (thrust_bar_x, thrust_bar_y, thrust_bar_width, thrust_bar_height))
    filled_height = (foguete.potencia_motor / 100.0) * thrust_bar_height
    pygame.draw.rect(screen, (0, 255, 0), (thrust_bar_x, thrust_bar_y + (thrust_bar_height - filled_height), thrust_bar_width, filled_height))
    pygame.draw.rect(screen, (255, 255, 255), (thrust_bar_x, thrust_bar_y, thrust_bar_width, thrust_bar_height), 2)
    thrust_label = small_font.render("Thrust", True, (255, 255, 255))
    thrust_label_rect = thrust_label.get_rect(center=(THRUST_GROUP_CENTER[0], thrust_bar_y - 15))
    screen.blit(thrust_label, thrust_label_rect)

    # 2. Speed (Setas de velocidade) com rótulo acima
    if abs(foguete.velocidade[0]) >= MIN_VELOCITY_DISPLAY:
        arrow_length_x = abs(foguete.velocidade[0]) * ARROW_SCALE
        blinking_x = False
        if arrow_length_x > MAX_ARROW_LENGTH:
            arrow_length_x = MAX_ARROW_LENGTH
            blinking_x = True
        if not blinking_x or (blinking_x and blink_timer < BLINK_INTERVAL / 2):
            speed_red_end = (SPEED_GROUP_CENTER[0] + math.copysign(arrow_length_x, foguete.velocidade[0]), SPEED_GROUP_CENTER[1])
            draw_arrow(screen, (255, 0, 0), SPEED_GROUP_CENTER, speed_red_end)
    if abs(foguete.velocidade[1]) >= MIN_VELOCITY_DISPLAY:
        arrow_length_y = abs(foguete.velocidade[1]) * ARROW_SCALE
        blinking_y = False
        if arrow_length_y > MAX_ARROW_LENGTH:
            arrow_length_y = MAX_ARROW_LENGTH
            blinking_y = True
        if not blinking_y or (blinking_y and blink_timer < BLINK_INTERVAL / 2):
            speed_blue_end = (SPEED_GROUP_CENTER[0], SPEED_GROUP_CENTER[1] - math.copysign(arrow_length_y, foguete.velocidade[1]))
            draw_arrow(screen, (0, 0, 255), SPEED_GROUP_CENTER, speed_blue_end)
    speed_label = small_font.render("Speed", True, (255, 255, 255))
    speed_label_rect = speed_label.get_rect(center=(SPEED_GROUP_CENTER[0], SPEED_GROUP_CENTER[1] - 65))
    screen.blit(speed_label, speed_label_rect)

    # 3. Orientation (Seta de orientação fixa) com rótulo acima
    ORIENTATION_ARROW_LENGTH = 80
    rad = math.radians(foguete.orientacao)
    dir_x = math.cos(rad)
    dir_y = -math.sin(rad)
    half_length = ORIENTATION_ARROW_LENGTH / 2
    orientation_start = (ORIENTATION_GROUP_CENTER[0] - half_length * dir_x,
                           ORIENTATION_GROUP_CENTER[1] - half_length * dir_y)
    orientation_end = (ORIENTATION_GROUP_CENTER[0] + half_length * dir_x,
                         ORIENTATION_GROUP_CENTER[1] + half_length * dir_y)
    draw_arrow(screen, (255, 255, 0), orientation_start, orientation_end)
    orientation_label = small_font.render("Orientation", True, (255, 255, 255))
    orientation_label_rect = orientation_label.get_rect(center=(ORIENTATION_GROUP_CENTER[0], ORIENTATION_GROUP_CENTER[1] - 65))
    screen.blit(orientation_label, orientation_label_rect)

    # Se o foguete pousou com sucesso na plataforma de pouso e passou pelo target, exibe mensagem de vitória
    if win == 1:
        landed_text = small_font.render("Houston, we Landed.", True, (0, 255, 0))
        landed_rect = landed_text.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(landed_text, landed_rect)

    pygame.display.flip()

pygame.quit()
