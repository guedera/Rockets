import os
import sys
import math
import numpy as np

# Adiciona o caminho do jogo para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import game.config
import pygame

from game.src.entities.rocket import Rocket
from game.src.entities.platform import Platform
from game.src.entities.target import Target

class RocketEnvironment:
    def __init__(self):
        """
        Ambiente para o treinamento do agente RL
        """
        # Inicializa o pygame em modo headless
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.init()
        
        # Parâmetros básicos
        self.WIDTH = game.config.WIDTH
        self.HEIGHT = game.config.HEIGHT
        self.FPS = game.config.FPS
        self.PIXELS_PER_METER = game.config.PIXELS_PER_METER
        
        # Surface para o modo headless
        self.screen = pygame.Surface((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()
        
        # Definição das ações
        # Formato: [potência_motor, torque]
        self.actions = [
            [0.0, 0.0],   # Sem ação
            [0.5, 0.0],   # Potência média, sem torque
            [1.0, 0.0],   # Potência total, sem torque
            [0.5, -1.0],  # Potência média, torque para esquerda
            [0.5, 1.0],   # Potência média, torque para direita
            [1.0, -1.0],  # Potência total, torque para esquerda
            [1.0, 1.0]    # Potência total, torque para direita
        ]
        
        self.action_space_size = len(self.actions)
        
        # Tamanho do espaço de estado (posição x,y, velocidade x,y, ângulo, vel. angular,
        # distância ao target, distância à plataforma, combustível restante)
        self.state_space_size = 9
        
        # Reseta o ambiente para iniciar
        self.reset()
    
    def reset(self):
        """
        Reseta o ambiente para um novo episódio
        :return: estado inicial
        """
        # Criação das plataformas
        self.initial_platform = Platform(posicao_x=100, comprimento=200, altura=0)
        self.landing_platform = Platform(posicao_x=self.WIDTH - 200 - 100, comprimento=200, altura=0)
        
        # Criação do foguete
        rocket_width, rocket_height = 20, 40
        rocket_initial_x = self.initial_platform.posicao[0] + self.initial_platform.comprimento / 2
        rocket_initial_y = rocket_height / 2
        self.foguete = Rocket(posicao_x=rocket_initial_x, posicao_y=rocket_initial_y, massa=50)
        
        # Criação do target
        TARGET_DIAMETER = 30
        self.target = Target(
            5 * self.PIXELS_PER_METER,
            5 * self.PIXELS_PER_METER,
            TARGET_DIAMETER,
            TARGET_DIAMETER
        )
        
        # Outras variáveis de estado
        self.done = False
        self.steps = 0
        self.max_steps = 1000  # Limite para evitar episódios muito longos
        
        # Inicializar métricas do foguete
        self.foguete.compute_metrics(self.target, self.landing_platform)
        self.foguete.target_reached = False
        
        # Retorna o estado inicial
        return self._get_state()
    
    def step(self, action_idx):
        """
        Executa uma ação e avança a simulação
        :param action_idx: índice da ação a ser tomada
        :return: (novo_estado, recompensa, terminado, info)
        """
        # Obtém a ação correspondente ao índice
        action = self.actions[action_idx]
        
        # Define a potência do motor (0-100%)
        self.foguete.potencia_motor = action[0] * 100.0
        
        # Aplica o torque usando o método apropriado do foguete
        delta_time = 1.0 / self.FPS
        torque_value = action[1] * game.config.ROTATION_TORQUE
        self.foguete.aplicar_torque(torque_value, delta_time)
        
        # Executa um passo de simulação
        self.foguete.atualizar(delta_time)
        self.steps += 1
        
        # Verifica se o target foi atingido
        if not self.foguete.target_reached:
            dx = self.foguete.posicao[0] - self.target.posicao[0]
            dy = self.foguete.posicao[1] - self.target.posicao[1]
            if math.sqrt(dx**2 + dy**2) <= self.target.altura / 2:
                self.foguete.target_reached = True
        
        # Atualiza as métricas do foguete
        self.foguete.compute_metrics(self.target, self.landing_platform)
        
        # Verifica condições de pouso ou colisão
        self._check_landing_conditions()
        
        # Obtém o novo estado
        new_state = self._get_state()
        
        # Calcula a recompensa
        reward = self._calculate_reward()
        
        # Verifica se o episódio terminou
        self.done = (self.foguete.landed or self.foguete.crashed or 
                     self.steps >= self.max_steps or 
                     self.foguete.posicao[1] >= self.HEIGHT)
        
        # Informações adicionais
        info = {
            "landed": self.foguete.landed,
            "crashed": self.foguete.crashed,
            "target_reached": self.foguete.target_reached,
            "fuel_used": self.foguete.fuel_consumed,
            "steps": self.steps
        }
        
        return new_state, reward, self.done, info
    
    def _get_state(self):
        """
        Obtém o estado atual normalizado para treinamento
        :return: array numpy com o estado
        """
        # Posição normalizada pelo tamanho da tela
        pos_x = self.foguete.posicao[0] / self.WIDTH
        pos_y = self.foguete.posicao[1] / self.HEIGHT
        
        # Velocidade normalizada (valor arbitrário de 10 m/s como máximo)
        vel_x = self.foguete.velocidade[0] / (10 * self.PIXELS_PER_METER)
        vel_y = self.foguete.velocidade[1] / (10 * self.PIXELS_PER_METER)
        
        # Ângulo e velocidade angular normalizados
        angle = self.foguete.orientacao / 360.0  # Normalizado por 360 graus
        ang_vel = self.foguete.angular_velocity / 10.0  # normalizado por valor arbitrário
        
        # Distância ao target
        dx_target = (self.foguete.posicao[0] - self.target.posicao[0]) / self.WIDTH
        dy_target = (self.foguete.posicao[1] - self.target.posicao[1]) / self.HEIGHT
        dist_target = math.sqrt(dx_target**2 + dy_target**2)
        
        # Distância à plataforma de pouso
        platform_center_x = self.landing_platform.posicao[0] + self.landing_platform.comprimento / 2
        dx_platform = (self.foguete.posicao[0] - platform_center_x) / self.WIDTH
        
        # Combustível normalizado (inverso do fuel_consumed)
        fuel = max(0, 1.0 - self.foguete.fuel_consumed / 100.0)
        
        return np.array([pos_x, pos_y, vel_x, vel_y, angle, ang_vel, 
                         dist_target, dx_platform, fuel])
    
    def _check_landing_conditions(self):
        """
        Verifica as condições de pouso ou crash
        """
        rocket_half_height = 20  # metade da altura do foguete
        if self.foguete.posicao[1] <= rocket_half_height and self.foguete.velocidade[1] <= 0:
            landing_speed = math.sqrt(self.foguete.velocidade[0]**2 + self.foguete.velocidade[1]**2)
            on_initial = (self.initial_platform.posicao[0] <= self.foguete.posicao[0] <= 
                         self.initial_platform.posicao[0] + self.initial_platform.comprimento)
            on_landing = (self.landing_platform.posicao[0] <= self.foguete.posicao[0] <= 
                         self.landing_platform.posicao[0] + self.landing_platform.comprimento)
            
            if landing_speed > game.config.LANDING_SPEED_THRESHOLD:
                self.foguete.crashed = True
            else:
                if on_initial or on_landing:
                    self.foguete.posicao[1] = rocket_half_height
                    if self.foguete.potencia_motor == 0:
                        self.foguete.velocidade = [0.0, 0.0]
                        self.foguete.angular_velocity = 0.0
                    else:
                        self.foguete.velocidade[1] = 0.0
                        self.foguete.angular_velocity = 0.0
                    if on_landing:
                        self.foguete.landed = True
                else:
                    self.foguete.crashed = True
    
    def _calculate_reward(self):
        """
        Calcula a recompensa para o estado atual
        :return: valor da recompensa
        """
        reward = 0
        
        # Penalidade por consumo de combustível
        fuel_penalty = -0.01 * self.foguete.fuel_consumed / 100.0
        reward += fuel_penalty
        
        # Recompensa por se aproximar do target (se ainda não alcançado)
        if not self.foguete.target_reached:
            target_reward = -0.01 * self.foguete.distance_to_target / self.PIXELS_PER_METER
            reward += target_reward
        
        # Grande recompensa por atingir o target
        if self.foguete.target_reached and not hasattr(self, '_target_reached_before'):
            reward += 100  # Recompensa única quando o target é atingido
            self._target_reached_before = True
        
        # Recompensa/Penalidades para pouso ou crash
        if self.foguete.landed:
            if self.foguete.target_reached:
                reward += 200  # Pouso bem sucedido após passar pelo target
            else:
                reward += 50   # Pouso bem sucedido mas sem passar pelo target
        
        if self.foguete.crashed:
            reward -= 100  # Grande penalidade por crash
        
        # Penalidade por inclinar demais o foguete (dificulta o pouso)
        angle_rad = math.radians(self.foguete.orientacao)
        angle_penalty = -0.1 * abs(math.sin(angle_rad))
        reward += angle_penalty
        
        # Penalidade por estar muito longe da plataforma de pouso
        # quanto mais próximo do final do episódio
        if self.steps > self.max_steps / 2:
            platform_penalty = -0.1 * self.foguete.distance_to_landing_platform_x / self.WIDTH * (self.steps / self.max_steps)
            reward += platform_penalty
        
        return reward
