import os
import sys
# Adiciona o diretório raiz do projeto ao sys.path para que os módulos do Game sejam encontrados
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

import gym
import numpy as np
from gym import spaces
import math
import random

from Game.src.entities.rocket import Rocket
from Game.src.entities.platform import Platform
from Game.src.entities.target import Target

# Constantes do jogo (iguais aos usados na main)
WIDTH = 1600
HEIGHT = 900
PIXELS_PER_METER = 100
LANDING_SPEED_THRESHOLD = 50

class RocketEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        super(RocketEnv, self).__init__()
        # Ações: 0: nada, 1: aumentar empuxo, 2: diminuir empuxo,
        # 3: girar para esquerda, 4: girar para direita
        self.action_space = spaces.Discrete(5)

        # Observação (15 dimensões):
        # [rocket_pos_x, rocket_pos_y, rocket_width, rocket_height,
        #  target_pos_x, target_pos_y,
        #  landing_platform_pos_x, landing_platform_pos_y,
        #  engine_power, fuel_consumed,
        #  rocket_vel_x, rocket_vel_y,
        #  rocket_orientation, target_passed, landed]
        low = np.array([
            0, 0, 20, 40,      # rocket posição e tamanho
            0, 0,              # target posição
            0, 0,              # landing platform (y = 0)
            0, 0,              # engine power e fuel
            -1000, -1000,      # velocidades
            -720,             # orientação
            0, 0              # target_passed, landed
        ], dtype=np.float32)
        high = np.array([
            WIDTH, HEIGHT, 20, 40,
            WIDTH, HEIGHT,
            WIDTH, 0,         # landing platform y fixo em 0
            100, 10000,
            1000, 1000,
            720,
            1, 1
        ], dtype=np.float32)
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)

        # Parâmetros de simulação
        self.dt = 1 / 60.0
        self.max_steps = 1000
        self.current_step = 0

        # Plataformas: inicial e de pouso
        self.initial_platform = Platform(posicao_x=100, comprimento=200, altura=0)
        self.landing_platform = Platform(posicao_x=WIDTH - 200 - 100, comprimento=200, altura=0)

        # Foguete: inicializado na plataforma inicial
        rocket_initial_x = self.initial_platform.posicao[0] + self.initial_platform.comprimento / 2
        # No main.py, o foguete inicia no solo: rocket_height/2 = 20 pixels.
        rocket_initial_y = 40 / 2  
        self.rocket = Rocket(posicao_x=rocket_initial_x, posicao_y=rocket_initial_y, massa=50)

        # Target: posição y sempre maior que 1 metro (100 pixels)
        self.TARGET_DIAMETER = 50
        self._spawn_target()

        # Outras variáveis de estado
        self.fuel_consumed = 0.0
        self.target_passed = False
        self.landed = False
        self.crashed = False

    def _spawn_target(self):
        self.target = Target(
            random.randint(self.TARGET_DIAMETER // 2, WIDTH - self.TARGET_DIAMETER // 2),
            random.randint(PIXELS_PER_METER, HEIGHT - self.TARGET_DIAMETER // 2),
            self.TARGET_DIAMETER,
            self.TARGET_DIAMETER
        )

    def _get_obs(self):
        obs = np.array([
            self.rocket.posicao[0],
            self.rocket.posicao[1],
            20, 40,  # tamanho do foguete (constante)
            self.target.posicao[0],
            self.target.posicao[1],
            self.landing_platform.posicao[0],
            self.landing_platform.altura,  # que é 0
            self.rocket.potencia_motor,
            self.fuel_consumed,
            self.rocket.velocidade[0],
            self.rocket.velocidade[1],
            self.rocket.orientacao,
            1.0 if self.target_passed else 0.0,
            1.0 if self.landed else 0.0
        ], dtype=np.float32)
        return obs

    def reset(self):
        self.current_step = 0
        self.fuel_consumed = 0.0
        self.target_passed = False
        self.landed = False
        self.crashed = False

        rocket_initial_x = self.initial_platform.posicao[0] + self.initial_platform.comprimento / 2
        # Para iniciar no solo, usamos rocket_height/2 = 20 pixels.
        rocket_initial_y = 40 / 2  
        self.rocket = Rocket(posicao_x=rocket_initial_x, posicao_y=rocket_initial_y, massa=50)
        self._spawn_target()
        return self._get_obs()

    def step(self, action):
        reward = 0.0
        done = False
        info = {}

        # Mapeamento da ação:
        # 0: nada, 1: aumentar empuxo, 2: diminuir empuxo,
        # 3: girar para esquerda, 4: girar para direita
        if action == 1:
            self.rocket.alterar_potencia(Rocket.POTENCIA_INCREMENTO)
        elif action == 2:
            self.rocket.alterar_potencia(-Rocket.POTENCIA_INCREMENTO)
        elif action == 3:
            self.rocket.aplicar_torque(+Rocket.ROTATION_TORQUE, self.dt)
        elif action == 4:
            self.rocket.aplicar_torque(-Rocket.ROTATION_TORQUE, self.dt)
        # ação 0 não faz nada

        # Atualiza a simulação (dinâmica do foguete)
        self.rocket.atualizar(self.dt)
        self.fuel_consumed += (self.rocket.potencia_motor / 100.0) * self.dt

        # Verifica se o foguete passou pelo target
        dx = self.rocket.posicao[0] - self.target.posicao[0]
        dy = self.rocket.posicao[1] - self.target.posicao[1]
        if not self.target_passed and math.sqrt(dx**2 + dy**2) <= self.target.altura / 2:
            self.target_passed = True
            reward += 50  # bônus por passar pelo target

        # Verifica se o foguete toca o solo (usamos rocket_half_height = 40/2 = 20)
        rocket_half_height = 40 / 2
        if self.rocket.posicao[1] <= rocket_half_height and self.rocket.velocidade[1] <= 0:
            landing_speed = math.sqrt(self.rocket.velocidade[0]**2 + self.rocket.velocidade[1]**2)
            if landing_speed > LANDING_SPEED_THRESHOLD:
                self.crashed = True
            else:
                # Verifica se está sobre a plataforma de pouso
                if (self.landing_platform.posicao[0] <= self.rocket.posicao[0] <= 
                    self.landing_platform.posicao[0] + self.landing_platform.comprimento):
                    self.landed = True
                else:
                    self.crashed = True

            # Zera velocidades para evitar acumulação
            self.rocket.velocidade = [0, 0]
            self.rocket.angular_velocity = 0

        # Define fim de episódio
        if self.landed:
            reward += 100 - self.fuel_consumed * 0.01  # recompensa por pousar com segurança, penalizando combustível
            done = True
        if self.crashed:
            reward -= 100
            done = True

        # Penalidade de tempo
        reward -= 0.1

        self.current_step += 1
        if self.current_step >= self.max_steps:
            done = True

        obs = self._get_obs()
        return obs, reward, done, info

    def render(self, mode='human'):
        # Renderização simplificada: imprime a observação (para debug)
        obs = self._get_obs()
        print("Observation:", obs)

    def close(self):
        pass
