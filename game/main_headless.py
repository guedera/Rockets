import os
# Força o modo headless definindo o driver dummy para o SDL
os.environ["SDL_VIDEODRIVER"] = "dummy"

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
import pygame
import math
import random
from src.entities.rocket import Rocket
from src.entities.platform import Platform
from src.entities.target import Target

# Configurações da tela e simulação a partir do config.py
WIDTH, HEIGHT = config.WIDTH, config.HEIGHT  # Corrigido para usar config.HEIGHT
FPS = config.FPS
PIXELS_PER_METER = config.PIXELS_PER_METER

pygame.init()
# Em modo headless, criamos uma superfície em vez de uma janela real
screen = pygame.Surface((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Cria uma superfície de fundo (preta, por exemplo)
background = pygame.Surface((WIDTH, HEIGHT))
background.fill((0, 0, 0))

# Detecta o caminho base do projeto
base_path = os.path.dirname(os.path.abspath(__file__))

# Carrega as fontes (opcional, para debug/log)
font_path = os.path.join(base_path, "src/utils/JetBrainsMono-Regular.ttf")
splash_font = pygame.font.Font(font_path, 60)
small_font = pygame.font.Font(font_path, 18)
crash_font = pygame.font.Font(font_path, 48)

# Informações (opcionais)
version_text = "0.9.0"
quit_text = "Press ESC to quit"

# Criação dos objetos do jogo
# Plataformas
initial_platform = Platform(posicao_x=100, comprimento=200, altura=0)
landing_platform = Platform(posicao_x=WIDTH - 200 - 100, comprimento=200, altura=0)

# Foguete (iniciado na plataforma inicial)
rocket_width, rocket_height = 20, 40
rocket_initial_x = initial_platform.posicao[0] + initial_platform.comprimento / 2
rocket_initial_y = rocket_height / 2
foguete = Rocket(posicao_x=rocket_initial_x, posicao_y=rocket_initial_y, massa=50)

# Target: posição fixa em (5m, 5m) e tamanho pequeno (30 pixels de diâmetro)
TARGET_DIAMETER = 30
target = Target(
    5 * PIXELS_PER_METER,
    5 * PIXELS_PER_METER,
    TARGET_DIAMETER,
    TARGET_DIAMETER
)

landed_message_timer = None

running = True
while running:
    delta_time = clock.tick(FPS) / 1000.0

    # Atualiza a simulação: física e métricas
    foguete.atualizar(delta_time)
    foguete.compute_metrics(target, landing_platform)

    # Aqui você pode definir as ações da IA ou simular uma política automática.
    # Por exemplo, se não houver intervenção, o foguete seguirá apenas a física atual.
    # Se desejar, insira comandos de controle para teste (ex.: alterar potência ou torque).

    # Verifica se o foguete capturou o target
    if not foguete.target_reached:
        dx = foguete.posicao[0] - target.posicao[0]
        dy = foguete.posicao[1] - target.posicao[1]
        if math.sqrt(dx**2 + dy**2) <= target.altura / 2:
            foguete.target_reached = True

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
                else:
                    foguete.velocidade[1] = 0
                    foguete.angular_velocity = 0
                # Modificação: Considera como "landed" se estiver na plataforma de pouso,
                # independente de ter pegado o target
                if on_landing:
                    foguete.landed = True
                    # Opcionalmente, registro do resultado
                    print(f"Pouso realizado! Target atingido: {foguete.target_reached}")
            else:
                foguete.crashed = True

    # Em modo headless não há renderização. Você pode registrar o estado atual para debug:
    # Exemplo: print(f"Estado: {foguete.get_state()}")
    # Ou salvar logs em arquivo para análise.

    # Para finalizar o loop automaticamente, podemos encerrar se ocorrer pouso ou crash.
    if foguete.landed or foguete.crashed:
        running = False

pygame.quit()
