# rocket.py
import math

class Rocket:
    GRAVIDADE = 500.0         # pixels/s² (ajustado para simulação em pixels)
    MAX_GIMBAL_ANGLE = 45     # Ângulo máximo de gimbal (graus)
    POTENCIA_INCREMENTO = 1   # Incremento da potência por comando (1% por tecla)
    MAX_THRUST = 15000        # Empuxo máximo (N) para potência de 100%
    ENGINE_OFFSET = 20        # Distância (pixels) do centro de massa até a montagem do motor

    def __init__(self, posicao_x: float, posicao_y: float, massa: float):
        """
        Inicializa o foguete.
        
        :param posicao_x: posição inicial em x do centro de massa (em pixels)
        :param posicao_y: posição inicial em y do centro de massa (em pixels)
        :param massa: massa do foguete
        """
        self.posicao = [posicao_x, posicao_y]
        self.orientacao = 90.0       # Inicia com 90° (de pé, apontando para cima)
        self.velocidade = [0.0, 0.0] # Velocidade linear (pixels/s)
        self.angular_velocity = 0.0  # Velocidade angular (graus/s)
        self.massa = massa
        self.angulo_motor = 0.0      # Ângulo de gimbal do motor (graus, relativo à orientação)
        self.potencia_motor = 0      # Potência do motor (0 a 100)
        self.moment_of_inercia = self.massa * 50  # Valor arbitrário para a inércia rotacional

    def aplicar_forca(self, delta_time):
        """
        Aplica as forças atuantes no foguete (empuxo do motor e gravidade) e calcula
        o torque para a rotação com base no ângulo do motor.
        """
        # Calcula o empuxo baseado na potência atual do motor
        thrust = (self.potencia_motor / 100.0) * self.MAX_THRUST

        # Calcula o ângulo total do empuxo.
        # Se o motor for inclinado para a direita (ângulo positivo),
        # subtrair o angulo_motor da orientacao fará com que o vetor de empuxo seja dirigido para a direita.
        total_angle_rad = math.radians(self.orientacao - self.angulo_motor)
        force_x = thrust * math.cos(total_angle_rad)
        force_y = thrust * math.sin(total_angle_rad) - self.massa * self.GRAVIDADE

        # Calcula as acelerações lineares
        ax = force_x / self.massa
        ay = force_y / self.massa

        self.velocidade[0] += ax * delta_time
        self.velocidade[1] += ay * delta_time

        # Calcula o torque: se o motor for inclinado para a direita (angulo_motor positivo),
        # o torque deve ser positivo, fazendo com que a orientacao aumente (rotação no sentido horário).
        torque = self.ENGINE_OFFSET * thrust * math.sin(math.radians(self.angulo_motor))
        angular_acceleration_rad = torque / self.moment_of_inercia  # em rad/s²
        angular_acceleration_deg = math.degrees(angular_acceleration_rad)  # converte para graus/s²
        self.angular_velocity += angular_acceleration_deg * delta_time

    def atualizar(self, delta_time):
        """
        Atualiza a posição e a orientação do foguete com base nas velocidades linear e angular.
        """
        self.aplicar_forca(delta_time)
        self.posicao[0] += self.velocidade[0] * delta_time
        self.posicao[1] += self.velocidade[1] * delta_time
        self.orientacao += self.angular_velocity * delta_time

    def girar_motor(self, delta_angle):
        """
        Ajusta o ângulo de gimbal do motor.
        
        :param delta_angle: incremento no ângulo (graus), positivo para a direita e negativo para a esquerda.
        """
        self.angulo_motor += delta_angle
        # Limita o ângulo de gimbal para o intervalo [-MAX_GIMBAL_ANGLE, MAX_GIMBAL_ANGLE]
        self.angulo_motor = max(-self.MAX_GIMBAL_ANGLE, min(self.MAX_GIMBAL_ANGLE, self.angulo_motor))

    def alterar_potencia(self, incremento):
        """
        Ajusta a potência do motor.
        
        :param incremento: valor a ser adicionado à potência atual.
        """
        self.potencia_motor += incremento
        self.potencia_motor = max(0, min(100, self.potencia_motor))
