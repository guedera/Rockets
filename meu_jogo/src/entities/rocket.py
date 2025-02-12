import math

class Rocket:
    GRAVIDADE = 500.0            # pixels/s² (para a simulação)
    POTENCIA_INCREMENTO = 1      # Incremento da potência por comando (1% por tecla)
    MAX_THRUST = 30000           # Empuxo máximo (N) para potência de 100%
    ROTATION_TORQUE = 1000.0     # Torque aplicado quando se pressiona A ou D (unidade arbitrária)

    def __init__(self, posicao_x: float, posicao_y: float, massa: float):
        """
        Inicializa o foguete.

        :param posicao_x: posição inicial em x do centro de massa (em pixels)
        :param posicao_y: posição inicial em y do centro de massa (em pixels)
        :param massa: massa do foguete
        """
        self.posicao = [posicao_x, posicao_y]
        self.initial_position = [posicao_x, posicao_y]  # Para reset
        self.orientacao = 90.0          # 90° = foguete "de pé" (apontando para cima)
        self.initial_orientation = 90.0 # Para reset
        self.velocidade = [0.0, 0.0]    # Velocidade linear (pixels/s)
        self.angular_velocity = 0.0     # Velocidade angular (graus/s)
        self.massa = massa
        self.potencia_motor = 0         # Potência do motor (0 a 100)
        self.moment_of_inercia = self.massa * 50  # Valor arbitrário para a inércia rotacional

    def reset(self):
        """
        Reseta o foguete para a posição e estado iniciais.
        """
        self.posicao = self.initial_position.copy()
        self.orientacao = self.initial_orientation
        self.velocidade = [0.0, 0.0]
        self.angular_velocity = 0.0
        self.potencia_motor = 0

    def aplicar_forca(self, delta_time):
        """
        Aplica a força do motor (sempre ao longo do eixo do foguete) e a gravidade.

        :param delta_time: tempo decorrido (s)
        """
        # A força do motor é proporcional à potência e age na direção de self.orientacao
        thrust = (self.potencia_motor / 100.0) * self.MAX_THRUST
        total_angle_rad = math.radians(self.orientacao)
        force_x = thrust * math.cos(total_angle_rad)
        force_y = thrust * math.sin(total_angle_rad) - self.massa * self.GRAVIDADE

        # Atualiza a velocidade linear
        ax = force_x / self.massa
        ay = force_y / self.massa
        self.velocidade[0] += ax * delta_time
        self.velocidade[1] += ay * delta_time

    def aplicar_torque(self, torque, delta_time):
        """
        Aplica um torque que gera aceleração angular.

        :param torque: valor do torque (positivo para girar no sentido antihorário)
        :param delta_time: tempo decorrido (s)
        """
        angular_acc_rad = torque / self.moment_of_inercia
        angular_acc_deg = math.degrees(angular_acc_rad)
        self.angular_velocity += angular_acc_deg * delta_time

    def atualizar(self, delta_time):
        """
        Atualiza a posição e a orientação do foguete com base nas velocidades linear e angular.

        :param delta_time: tempo decorrido (s)
        """
        self.aplicar_forca(delta_time)
        self.posicao[0] += self.velocidade[0] * delta_time
        self.posicao[1] += self.velocidade[1] * delta_time
        self.orientacao += self.angular_velocity * delta_time

    def alterar_potencia(self, incremento):
        """
        Ajusta a potência do motor.

        :param incremento: valor a ser somado à potência atual (pode ser negativo)
        """
        self.potencia_motor += incremento
        self.potencia_motor = max(0, min(100, self.potencia_motor))
