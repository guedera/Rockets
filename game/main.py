import sys
import os
import pygame
import math
import random

# Garantir que o diretório atual está no path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.environment import RocketEnvironment
import config

# Configurações da tela e da simulação
WIDTH, HEIGHT = config.WIDTH, config.HEIGHT
FPS = config.FPS

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Corrige os caminhos para arquivos de recursos
# Detecta o caminho base do projeto
base_path = os.path.dirname(os.path.abspath(__file__))

# Carrega e redimensiona a imagem de fundo
try:
    image_path = os.path.join(base_path, "src/images/Fundo.png")
    
    if os.path.exists(image_path):
        background = pygame.image.load(image_path).convert()
    else:
        # Cria um fundo preto de backup caso a imagem não seja encontrada
        background = pygame.Surface((WIDTH, HEIGHT))
        background.fill((0, 0, 0))
except Exception as e:
    # Cria um fundo preto de backup em caso de erro
    background = pygame.Surface((WIDTH, HEIGHT))
    background.fill((0, 0, 0))

background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# Carrega as fontes
font_path = os.path.join(base_path, "src/utils/JetBrainsMono-Regular.ttf")
splash_font = pygame.font.Font(font_path, 60)
small_font = pygame.font.Font(font_path, 18)
crash_font = pygame.font.Font(font_path, 48)

# Informações do HUD
version_text = "0.9.5"
quit_text = "Press ESC to quit"

# Constantes para as setinhas do HUD
ARROW_SCALE = 0.2
ARROW_HEAD_LENGTH = 10
ARROW_HEAD_ANGLE = 30
MIN_VELOCITY_DISPLAY = 5
MAX_ARROW_LENGTH = 50
BLINK_INTERVAL = 0.3
blink_timer = 0

def draw_arrow(surface, color, start, end, head_length=ARROW_HEAD_LENGTH, head_angle=ARROW_HEAD_ANGLE):
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

# --- HUD PANEL ---
hud_panel_rect = pygame.Rect(WIDTH//2 - 300, HEIGHT - 220, 600, 200)
HUD_BG_COLOR = (0, 0, 0, 150)
HUD_BORDER_COLOR = (200, 200, 200)
HUD_BORDER_RADIUS = 15

hud_center = hud_panel_rect.center
THRUST_GROUP_CENTER = (hud_center[0] - 150, hud_panel_rect.centery + 20)
SPEED_GROUP_CENTER  = (hud_center[0], hud_panel_rect.centery + 20)
ORIENTATION_GROUP_CENTER = (hud_center[0] + 150, hud_panel_rect.centery + 20)
POSITION_TEXT_CENTER = (hud_panel_rect.centerx, hud_panel_rect.top + 15)

# Inicialização do ambiente
env = RocketEnvironment(width=WIDTH, height=HEIGHT, render_mode='human')
PIXELS_PER_METER = env.pixels_per_meter

# Variáveis do jogo
landed_message_timer = None
rocket_width, rocket_height = env.rocket_width, env.rocket_height
game_shutdown = False

running = True
while running:
    # Limpa a tela com o fundo antes de cada novo frame
    screen.blit(background, (0, 0))
    
    delta_time = clock.tick(FPS) / 1000.0
    blink_timer += delta_time

    # Resetar o timer de piscar quando ele ultrapassar um ciclo completo
    if blink_timer >= BLINK_INTERVAL:
        blink_timer = blink_timer % BLINK_INTERVAL

    foguete = env.rocket
    # Mudança: só finaliza o jogo se o foguete pousou E pegou o target OU se crashou
    if foguete.landed and foguete.target_reached and not game_shutdown:
        if landed_message_timer is None:
            landed_message_timer = 0
        else:
            landed_message_timer += delta_time
            if landed_message_timer >= 3:
                game_shutdown = True
                # Não chamamos pygame.quit() e sys.exit() imediatamente
                # Em vez disso, definimos uma flag para sair do loop principal

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # Se o jogo está marcado para encerrar, saímos do loop
    if game_shutdown:
        running = False
        break

    keys = pygame.key.get_pressed()
    if keys[pygame.K_r]:
        env.reset()
        landed_message_timer = None
    
    # Converte teclas pressionadas em ações para o ambiente
    action = None
    # Importante: permitir controle se estiver pousado mas não tiver pego o target ainda
    if not foguete.crashed and (not foguete.landed or (foguete.landed and not foguete.target_reached)):
        if keys[pygame.K_x]:
            # Modificação: só alterar o valor da potência, sem enviar como ação para o ambiente
            # Isso evita efeitos colaterais indesejados na simulação
            foguete.potencia_motor = 0
            action = 0  # Definir ação para "não fazer nada" em vez de deixar None
        elif keys[pygame.K_w] and keys[pygame.K_a]:
            action = 5  # Aumentar potência + Girar anti-horário
        elif keys[pygame.K_w] and keys[pygame.K_d]:
            action = 6  # Aumentar potência + Girar horário
        elif keys[pygame.K_s] and keys[pygame.K_a]:
            action = 7  # Diminuir potência + Girar anti-horário
        elif keys[pygame.K_s] and keys[pygame.K_d]:
            action = 8  # Diminuir potência + Girar horário
        elif keys[pygame.K_w]:
            action = 1  # Aumentar potência
        elif keys[pygame.K_s]:
            action = 2  # Diminuir potência
        elif keys[pygame.K_a]:
            action = 3  # Girar anti-horário
        elif keys[pygame.K_d]:
            action = 4  # Girar horário
        else:
            action = 0  # Não fazer nada
        
        if action is not None:
            state, reward, done, info = env.step(action)
    
    # Desenha as plataformas
    initial_platform = env.initial_platform
    landing_platform = env.landing_platform
    initial_platform_rect = pygame.Rect(initial_platform.posicao[0], HEIGHT - 10, initial_platform.comprimento, 10)
    pygame.draw.rect(screen, (100, 100, 100), initial_platform_rect)
    landing_platform_rect = pygame.Rect(landing_platform.posicao[0], HEIGHT - 10, landing_platform.comprimento, 10)
    pygame.draw.rect(screen, (100, 100, 100), landing_platform_rect)

    # Desenha o target com aro de espessura maior (4)
    target = env.target
    if not foguete.target_reached:
        pygame.draw.circle(
            screen,
            (255, 0, 0),
            (int(target.posicao[0]), HEIGHT - int(target.posicao[1])),
            int(target.altura / 2),
            4
        )

    if not foguete.crashed:
        def draw_rocket(surface, rocket):
            # Criamos a superfície do foguete com transparência
            rocket_surf = pygame.Surface((rocket_width, rocket_height), pygame.SRCALPHA)
            # Limpa a superfície do foguete antes de desenhar
            rocket_surf.fill((0, 0, 0, 0))  # Completamente transparente
            
            # Desenha o corpo do foguete
            body_rect = pygame.Rect(0, 10, rocket_width, rocket_height - 10)
            pygame.draw.rect(rocket_surf, (200, 0, 0), body_rect)
            pygame.draw.polygon(rocket_surf, (255, 0, 0), [(0, 10), (rocket_width, 10), (rocket_width/2, 0)])
            pygame.draw.polygon(rocket_surf, (150, 150, 150), [(0, rocket_height), (5, rocket_height - 10), (0, rocket_height - 10)])
            pygame.draw.polygon(rocket_surf, (150, 150, 150), [(rocket_width, rocket_height), (rocket_width - 5, rocket_height - 10), (rocket_width, rocket_height - 10)])
            
            # Rotaciona a superfície
            rotated_surf = pygame.transform.rotate(rocket_surf, (rocket.orientacao - 90))
            rotated_rect = rotated_surf.get_rect(center=(int(rocket.posicao[0]), HEIGHT - int(rocket.posicao[1])))
            
            # Desenha no destino
            surface.blit(rotated_surf, rotated_rect.topleft)
        
        draw_rocket(screen, foguete)
    else:
        crash_text = crash_font.render("Crash!", True, (255, 0, 0))
        crash_rect = crash_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(crash_text, crash_rect)

    # Verifica as condições de pouso ou crash
    rocket_half_height = rocket_height / 2
    if foguete.posicao[1] <= rocket_half_height and foguete.velocidade[1] <= 0:
        landing_speed = math.sqrt(foguete.velocidade[0]**2 + foguete.velocidade[1]**2)
        on_initial = (initial_platform.posicao[0] <= foguete.posicao[0] <= initial_platform.posicao[0] + initial_platform.comprimento)
        on_landing = (landing_platform.posicao[0] <= foguete.posicao[0] <= landing_platform.posicao[0] + landing_platform.comprimento)
        if landing_speed > config.LANDING_SPEED_THRESHOLD:
            foguete.crashed = True
        else:
            if on_initial or on_landing:
                foguete.posicao[1] = rocket_half_height
                if foguete.potencia_motor == 0:
                    foguete.velocidade = [0, 0]
                    foguete.angular_velocity = 0
                    
                    # Marca como pousado mas não encerra o jogo, a não ser que tenha pegado o target
                    if on_landing:
                        # Apenas marca como pousado, mas o jogo continua
                        foguete.landed = True
                        # Não marcamos game_shutdown aqui - o jogo continua mesmo após pousar
                else:
                    foguete.velocidade[1] = 0
                    foguete.angular_velocity = 0
                    # Não marca como landed se a potência não for zero
            else:
                foguete.crashed = True

    # --- HUD Panel ---
    hud_surface = pygame.Surface((hud_panel_rect.width, hud_panel_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(hud_surface, HUD_BG_COLOR, hud_surface.get_rect(), border_radius=HUD_BORDER_RADIUS)
    pygame.draw.rect(hud_surface, HUD_BORDER_COLOR, hud_surface.get_rect(), 2, border_radius=HUD_BORDER_RADIUS)
    screen.blit(hud_surface, hud_panel_rect.topleft)

    rocket_initial_x = env.rocket_initial_x
    rocket_initial_y = env.rocket_initial_y
    dx_pixels = foguete.posicao[0] - rocket_initial_x
    dy_pixels = foguete.posicao[1] - rocket_initial_y
    pos_x_m = dx_pixels / PIXELS_PER_METER
    pos_y_m = dy_pixels / PIXELS_PER_METER
    position_text = small_font.render(f"Pos: {pos_x_m:.2f}:{pos_y_m:.2f} m", True, (255, 255, 255))
    position_text_rect = position_text.get_rect(center=(hud_panel_rect.centerx, hud_panel_rect.top + 15))
    screen.blit(position_text, position_text_rect)

    fuel_text = small_font.render(f"Fuel: {foguete.fuel_consumed:.2f}", True, (255, 255, 255))
    fuel_text_rect = fuel_text.get_rect(center=(hud_panel_rect.centerx - 100, hud_panel_rect.bottom - 20))
    screen.blit(fuel_text, fuel_text_rect)

    speed_result = math.sqrt(foguete.velocidade[0]**2 + foguete.velocidade[1]**2) / PIXELS_PER_METER
    speed_text = small_font.render(f"Speed: {speed_result:.2f} m/s", True, (255, 255, 255))
    speed_text_rect = speed_text.get_rect(center=(hud_panel_rect.centerx + 100, hud_panel_rect.bottom - 20))
    screen.blit(speed_text, speed_text_rect)

    # Exibe apenas as informações do thrust e da orientação
    thrust_text = small_font.render(f"Thrust: {foguete.potencia_motor}%", True, (255, 255, 255))
    thrust_rect = thrust_text.get_rect(center=(hud_panel_rect.centerx - 200, hud_panel_rect.top + 40))
    screen.blit(thrust_text, thrust_rect)

    orientation_text = small_font.render(f"Angle: {foguete.orientacao:.2f}", True, (255, 255, 255))
    orientation_rect = orientation_text.get_rect(center=(hud_panel_rect.centerx + 200, hud_panel_rect.top + 40))
    screen.blit(orientation_text, orientation_rect)

    # --- HUD: Indicadores gráficos ---
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

    if abs(foguete.velocidade[0]) >= MIN_VELOCITY_DISPLAY:
        arrow_length_x = abs(foguete.velocidade[0]) * ARROW_SCALE
        blinking_x = False
        if arrow_length_x > MAX_ARROW_LENGTH:
            arrow_length_x = MAX_ARROW_LENGTH
            blinking_x = True
        
        # Corrigido: usar o módulo para garantir que o blink_timer cicla corretamente
        should_draw = not blinking_x or (blink_timer <= BLINK_INTERVAL / 2)
        if should_draw:
            speed_red_end = (SPEED_GROUP_CENTER[0] + math.copysign(arrow_length_x, foguete.velocidade[0]), SPEED_GROUP_CENTER[1])
            draw_arrow(screen, (255, 0, 0), SPEED_GROUP_CENTER, speed_red_end)
    
    if abs(foguete.velocidade[1]) >= MIN_VELOCITY_DISPLAY:
        arrow_length_y = abs(foguete.velocidade[1]) * ARROW_SCALE
        blinking_y = False
        if arrow_length_y > MAX_ARROW_LENGTH:
            arrow_length_y = MAX_ARROW_LENGTH
            blinking_y = True
        
        # Corrigido: usar o módulo para garantir que o blink_timer cicla corretamente
        should_draw = not blinking_y or (blink_timer <= BLINK_INTERVAL / 2)
        if should_draw:
            speed_blue_end = (SPEED_GROUP_CENTER[0], SPEED_GROUP_CENTER[1] - math.copysign(arrow_length_y, foguete.velocidade[1]))
            draw_arrow(screen, (0, 0, 255), SPEED_GROUP_CENTER, speed_blue_end)
    speed_label = small_font.render("Speed", True, (255, 255, 255))
    speed_label_rect = speed_label.get_rect(center=(SPEED_GROUP_CENTER[0], SPEED_GROUP_CENTER[1] - 65))
    screen.blit(speed_label, speed_label_rect)

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

    # Exibir mensagens de estado em um único lugar no código para evitar sobreposição
    if foguete.landed:
        # Caixa de fundo para a mensagem para melhor legibilidade
        if hasattr(foguete, 'target_reached') and foguete.target_reached:
            msg_text = "Houston, we have a perfect landing!"
            msg_color = (0, 255, 0)  # Verde para sucesso completo
            # Adiciona um fundo semi-transparente para melhorar a legibilidade
            landed_msg = small_font.render(msg_text, True, msg_color)
            msg_rect = landed_msg.get_rect(center=(WIDTH//2, HEIGHT//2))
            bg_rect = msg_rect.inflate(20, 10)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            bg_surface.fill((0, 0, 0, 180))  # Preto com 70% de opacidade
            screen.blit(bg_surface, bg_rect.topleft)
            screen.blit(landed_msg, msg_rect)
        else:
            # Se pousou sem o target, mostra uma mensagem temporária no canto superior
            msg_text = "Landed. Get the target and land again to complete mission."
            msg_color = (255, 255, 0)  # Amarelo para pouso parcial
            landed_msg = small_font.render(msg_text, True, msg_color)
            msg_rect = landed_msg.get_rect(center=(WIDTH//2, 30))
            screen.blit(landed_msg, msg_rect)
            
            # Reinicia o pouso - permite levantar novamente
            if foguete.potencia_motor > 0:
                foguete.landed = False
    
    elif foguete.crashed:
        crash_text = crash_font.render("Crash!", True, (255, 0, 0))
        crash_rect = crash_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        
        # Fundo para a mensagem de crash
        bg_rect = crash_rect.inflate(20, 10)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180))
        screen.blit(bg_surface, bg_rect.topleft)
        
        screen.blit(crash_text, crash_rect)
        
        # Se crashou, encerra o jogo após 3 segundos
        if landed_message_timer is None:
            landed_message_timer = 0
        else:
            landed_message_timer += delta_time
            if landed_message_timer >= 3:
                game_shutdown = True

    pygame.display.flip()

# Garantir que o pygame é encerrado corretamente fora do loop principal
pygame.quit()
sys.exit()
