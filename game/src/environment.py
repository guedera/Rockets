import math
import numpy as np
from .entities.rocket import Rocket
from .entities.platform import Platform
from .entities.target import Target
import sys
import os

# Ajusta o caminho para importar o config corretamente
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class RocketEnvironment:
    """Ambiente para simulação do jogo de foguetes compatível com RL."""
    
    # Número de ações possíveis
    ACTION_SPACE_SIZE = 9
    
    def __init__(self, width=config.WIDTH, height=config.HEIGHT, render_mode=None):
        """
        Inicializa o ambiente para o agente DQN.
        
        Args:
            width: Largura da tela (pixels)
            height: Altura da tela (pixels)
            render_mode: None para headless, 'human' para renderização visual
        """
        self.width = width
        self.height = height
        self.render_mode = render_mode
        self.pixels_per_meter = config.PIXELS_PER_METER
        
        # Criação das plataformas
        self.initial_platform_width = 200
        self.initial_platform_x = 100
        self.initial_platform = Platform(
            posicao_x=self.initial_platform_x, 
            comprimento=self.initial_platform_width, 
            altura=0
        )
        
        self.landing_platform_width = 200
        self.landing_platform_x = width - self.landing_platform_width - 100
        self.landing_platform = Platform(
            posicao_x=self.landing_platform_x, 
            comprimento=self.landing_platform_width, 
            altura=0
        )
        
        # Parâmetros do foguete
        self.rocket_width, self.rocket_height = 20, 40
        self.rocket_initial_x = self.initial_platform.posicao[0] + self.initial_platform.comprimento / 2
        self.rocket_initial_y = self.rocket_height / 2
        
        # Target
        self.target_diameter = 30
        
        # Inicialização dos elementos do jogo
        self.rocket = None
        self.target = None
        self.reset()
        
        # Controle da simulação
        self.done = False
        self.reward = 0
        self.landing_speed_threshold = config.LANDING_SPEED_THRESHOLD
        self.total_steps = 0
        self.max_steps = 2000  # Limite de passos por episódio
        
    def get_state_size(self):
        """Retorna o tamanho do espaço de estados para a rede neural."""
        return len(self._get_state())
    
    def reset(self):
        """
        Reinicia o ambiente para um novo episódio.
        
        Returns:
            O estado inicial do ambiente.
        """
        # Reinicia o foguete
        self.rocket = Rocket(
            posicao_x=self.rocket_initial_x, 
            posicao_y=self.rocket_initial_y, 
            massa=50
        )
        
        # Reinicia o target
        self.target = Target(
            5 * self.pixels_per_meter,
            5 * self.pixels_per_meter,
            self.target_diameter,
            self.target_diameter
        )
        
        # Reinicia estados
        self.done = False
        self.reward = 0
        self.total_steps = 0
        
        # Calcula as métricas iniciais
        self.rocket.compute_metrics(self.target, self.landing_platform)
        
        return self._get_state()
    
    def step(self, action):
        """
        Executa uma ação no ambiente e retorna o próximo estado, recompensa e flag de término.
        
        Args:
            action: Um inteiro representando a ação a ser tomada:
                   0: Não fazer nada
                   1: Aumentar potência
                   2: Diminuir potência
                   3: Girar no sentido anti-horário
                   4: Girar no sentido horário
                   5: Aumentar potência + Girar anti-horário
                   6: Aumentar potência + Girar horário
                   7: Diminuir potência + Girar anti-horário
                   8: Diminuir potência + Girar horário
        
        Returns:
            Uma tupla (estado, recompensa, finalizado, info) onde:
            - estado é o novo estado do ambiente
            - recompensa é a recompensa obtida pela ação
            - finalizado indica se o episódio terminou
            - info é um dicionário com informações adicionais
        """
        if self.done:
            return self._get_state(), 0, True, {"status": "already_done"}
        
        # Incrementa contador de passos
        self.total_steps += 1
        if self.total_steps >= self.max_steps:
            self.done = True
            return self._get_state(), -50, True, {"status": "timeout"}
            
        # Aplica a ação escolhida
        delta_time = 1.0/config.FPS  # Simulação de um frame
        
        # Armazena métricas antigas para calcular recompensas
        old_distance = self.rocket.distance_to_target
        old_angle_diff = self.rocket.angle_difference
        old_landing_dist_x = self.rocket.distance_to_landing_platform_x
        old_landing_dist_y = self.rocket.distance_to_landing_platform_y
        
        # Decodifica a ação
        if action == 0:  # Não fazer nada
            pass
        elif action == 1:  # Aumentar potência
            self.rocket.alterar_potencia(Rocket.POTENCIA_INCREMENTO)
        elif action == 2:  # Diminuir potência
            self.rocket.alterar_potencia(-Rocket.POTENCIA_INCREMENTO)
        elif action == 3:  # Girar no sentido anti-horário
            self.rocket.aplicar_torque(+Rocket.ROTATION_TORQUE, delta_time)
        elif action == 4:  # Girar no sentido horário
            self.rocket.aplicar_torque(-Rocket.ROTATION_TORQUE, delta_time)
        elif action == 5:  # Aumentar potência + Girar anti-horário
            self.rocket.alterar_potencia(Rocket.POTENCIA_INCREMENTO)
            self.rocket.aplicar_torque(+Rocket.ROTATION_TORQUE, delta_time)
        elif action == 6:  # Aumentar potência + Girar horário
            self.rocket.alterar_potencia(Rocket.POTENCIA_INCREMENTO)
            self.rocket.aplicar_torque(-Rocket.ROTATION_TORQUE, delta_time)
        elif action == 7:  # Diminuir potência + Girar anti-horário
            self.rocket.alterar_potencia(-Rocket.POTENCIA_INCREMENTO)
            self.rocket.aplicar_torque(+Rocket.ROTATION_TORQUE, delta_time)
        elif action == 8:  # Diminuir potência + Girar horário
            self.rocket.alterar_potencia(-Rocket.POTENCIA_INCREMENTO)
            self.rocket.aplicar_torque(-Rocket.ROTATION_TORQUE, delta_time)
        
        # Atualiza a física do foguete
        self.rocket.atualizar(delta_time)
        
        # Atualiza métricas
        self.rocket.compute_metrics(self.target, self.landing_platform)
        
        # Inicia com recompensa zerada para este passo
        step_reward = 0
        
        # Verifica captura do target
        if not self.rocket.target_reached:
            dx = self.rocket.posicao[0] - self.target.posicao[0]
            dy = self.rocket.posicao[1] - self.target.posicao[1]
            if math.sqrt(dx**2 + dy**2) <= self.target.altura / 2:
                self.rocket.target_reached = True
                # Recompensa por pegar o target
                step_reward += 100
        
        # Verifica pouso ou colisão
        rocket_half_height = self.rocket_height / 2
        if self.rocket.posicao[1] <= rocket_half_height and self.rocket.velocidade[1] <= 0:
            landing_speed = math.sqrt(self.rocket.velocidade[0]**2 + self.rocket.velocidade[1]**2)
            on_initial = (self.initial_platform.posicao[0] <= self.rocket.posicao[0] <= 
                         self.initial_platform.posicao[0] + self.initial_platform.comprimento)
            on_landing = (self.landing_platform.posicao[0] <= self.rocket.posicao[0] <= 
                         self.landing_platform.posicao[0] + self.landing_platform.comprimento)
            
            # Inicializar target_reached se não existir
            if not hasattr(self.rocket, 'target_reached'):
                self.rocket.target_reached = False
                
            if landing_speed > self.landing_speed_threshold:
                self.rocket.crashed = True
                self.done = True
                # Penalidade por crash
                step_reward -= 100
            else:
                if on_initial or on_landing:
                    # Ajusta posição para ficar exatamente na plataforma
                    self.rocket.posicao[1] = rocket_half_height
                    
                    # Se a potência for zero, para o foguete completamente
                    if self.rocket.potencia_motor == 0:
                        self.rocket.velocidade = [0.0, 0.0]  # Importante: usar 0.0 para garantir tipo float
                        self.rocket.angular_velocity = 0.0
                        
                        # Marca como pousado se estiver na plataforma de pouso
                        if on_landing:
                            self.rocket.landed = True
                            # Só finaliza a simulação se tiver pegado o target
                            if self.rocket.target_reached:
                                self.done = True
                                landing_reward = 200 - self.rocket.fuel_consumed
                                landing_reward += 300  # Extra por ter completado com o target
                                step_reward += max(0, landing_reward)
                            else:
                                # Pequena recompensa por pousar sem o target
                                step_reward += 20
                    else:
                        # Se ainda tem potência, só para o movimento vertical mas permite continuar
                        self.rocket.velocidade[1] = 0.0
                        # Não marca como pousado se tiver potência
                else:
                    # Bateu no chão fora da plataforma
                    self.rocket.crashed = True
                    self.done = True
                    step_reward -= 100
        
        # Recompensas incrementais
        # Melhorou a distância até o target?
        if old_distance > self.rocket.distance_to_target:
            step_reward += 0.1
        else:
            step_reward -= 0.05
        
        # Melhorou o ângulo em relação ao target?
        if old_angle_diff > self.rocket.angle_difference:
            step_reward += 0.1
        
        # Se já pegou o target, recompensa por melhorar a posição em relação à plataforma de pouso
        if self.rocket.target_reached:
            if old_landing_dist_x > self.rocket.distance_to_landing_platform_x:
                step_reward += 0.2
            if old_landing_dist_y > self.rocket.distance_to_landing_platform_y:
                step_reward += 0.2
        
        # Penalidade por consumo de combustível (pequena)
        step_reward -= 0.01 * self.rocket.potencia_motor / 100.0
        
        # Verifica se saiu da tela
        # Removido: Não deve haver penalização ou fim de jogo por sair da tela
        # O foguete deve poder viajar livremente pelo espaço
        # if (self.rocket.posicao[0] < 0 or self.rocket.posicao[0] > self.width or 
        #    self.rocket.posicao[1] < 0 or self.rocket.posicao[1] > self.height):
        #    self.done = True
        #    step_reward -= 100
        
        return self._get_state(), step_reward, self.done, {"status": "in_progress"}
    
    def _get_state(self):
        """
        Retorna o estado atual do ambiente em um formato que pode ser usado
        como entrada para uma rede neural.
        """
        # Normalização dos valores para range adequado para rede neural
        pos_x_norm = self.rocket.posicao[0] / self.width
        pos_y_norm = self.rocket.posicao[1] / self.height
        vel_x_norm = self.rocket.velocidade[0] / 1000.0  # Normaliza para valor máximo esperado
        vel_y_norm = self.rocket.velocidade[1] / 1000.0
        orientation_norm = self.rocket.orientacao / 360.0
        angular_vel_norm = self.rocket.angular_velocity / 360.0
        power_norm = self.rocket.potencia_motor / 100.0
        
        target_x_norm = self.target.posicao[0] / self.width
        target_y_norm = self.target.posicao[1] / self.height
        target_reached = 1.0 if self.rocket.target_reached else 0.0
        
        dist_to_target_norm = self.rocket.distance_to_target / math.sqrt(self.width**2 + self.height**2)
        angle_diff_norm = self.rocket.angle_difference / 180.0
        
        landing_x_norm = self.landing_platform.posicao[0] / self.width
        landing_width_norm = self.landing_platform.comprimento / self.width
        dist_landing_x_norm = self.rocket.distance_to_landing_platform_x / self.width
        dist_landing_y_norm = self.rocket.distance_to_landing_platform_y / self.height
        
        return np.array([
            pos_x_norm, pos_y_norm,
            vel_x_norm, vel_y_norm,
            orientation_norm, angular_vel_norm,
            power_norm,
            target_x_norm, target_y_norm, target_reached,
            dist_to_target_norm, angle_diff_norm,
            landing_x_norm, landing_width_norm,
            dist_landing_x_norm, dist_landing_y_norm
        ])
    
    def render(self, screen=None):
        """
        Renderiza o estado atual do ambiente, se render_mode='human'.
        Pode ser conectado com a função de renderização do Pygame.
        
        Args:
            screen: A superfície do Pygame onde renderizar (opcional)
        """
        if self.render_mode != 'human' or screen is None:
            return
        
        # Esta função deixa a renderização para o código main.py
        # Aqui fornecemos apenas os objetos atualizados
        return {
            'rocket': self.rocket,
            'target': self.target,
            'initial_platform': self.initial_platform,
            'landing_platform': self.landing_platform
        }
