import math

class Rocket:
    GRAVIDADE = 500.0            # pixels/s² (para a simulação)
    POTENCIA_INCREMENTO = 1      # Incremento da potência por comando (1% por tecla)
    MAX_THRUST = 30000           # Empuxo máximo (N) para potência de 100%
    ROTATION_TORQUE = 3000.0     # Torque aplicado quando se pressiona A ou D (unidade arbitrária)
    DRAG_COEFFICIENT = 7.0       # Coeficiente de arrasto (força de drag = -DRAG_COEFFICIENT * v)

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

        # Atributos já existentes para HUD
        self.fuel_consumed = 0.0
        self.target_reached = False
        self.landed = False
        self.crashed = False

        # NOVOS ATRIBUTOS:
        # Distância do foguete até o target (em pixels)
        self.distance_to_target = None
        # Diferença (em graus) entre o ângulo do foguete e o ângulo da reta que une o foguete ao target
        self.angle_difference = None
        # Distância entre o foguete e a plataforma de pouso em x e y (em pixels)
        self.distance_to_landing_platform_x = None
        self.distance_to_landing_platform_y = None

    def reset(self):
        """
        Reseta o foguete para a posição e estado iniciais.
        """
        self.posicao = self.initial_position.copy()
        self.orientacao = self.initial_orientation
        self.velocidade = [0.0, 0.0]
        self.angular_velocity = 0.0
        self.potencia_motor = 0

        # Reset dos atributos do HUD e das métricas
        self.fuel_consumed = 0.0
        self.target_reached = False
        self.landed = False
        self.crashed = False
        self.distance_to_target = None
        self.angle_difference = None
        self.distance_to_landing_platform_x = None
        self.distance_to_landing_platform_y = None

    def aplicar_forca(self, delta_time):
        """
        Aplica a força do motor (sempre ao longo do eixo do foguete), a gravidade
        e a força de arrasto (drag) que se opõe à velocidade.

        :param delta_time: tempo decorrido (s)
        """
        thrust = (self.potencia_motor / 100.0) * self.MAX_THRUST
        total_angle_rad = math.radians(self.orientacao)
        thrust_force_x = thrust * math.cos(total_angle_rad)
        thrust_force_y = thrust * math.sin(total_angle_rad)
        
        gravity_force = self.massa * self.GRAVIDADE

        drag_force_x = - self.DRAG_COEFFICIENT * self.velocidade[0]
        drag_force_y = - self.DRAG_COEFFICIENT * self.velocidade[1]

        net_force_x = thrust_force_x + drag_force_x
        net_force_y = thrust_force_y + drag_force_y - gravity_force

        ax = net_force_x / self.massa
        ay = net_force_y / self.massa
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
        Atualiza também o combustível consumido.
        
        :param delta_time: tempo decorrido (s)
        """
        self.aplicar_forca(delta_time)
        self.posicao[0] += self.velocidade[0] * delta_time
        self.posicao[1] += self.velocidade[1] * delta_time
        self.orientacao += self.angular_velocity * delta_time

        self.fuel_consumed += (self.potencia_motor / 100.0) * delta_time

    def alterar_potencia(self, incremento):
        """
        Ajusta a potência do motor.

        :param incremento: valor a ser somado à potência atual (pode ser negativo)
        """
        self.potencia_motor += incremento
        self.potencia_motor = max(0, min(100, self.potencia_motor))

    def compute_metrics(self, target, landing_platform):
        """
        Atualiza as métricas relativas ao target e à plataforma de pouso:
         - Distância até o target.
         - Diferença entre o ângulo do foguete e o ângulo da reta que liga o foguete ao target.
         - Distância em x e y até a plataforma de pouso (usando o centro da plataforma).
         
        :param target: instância de Target.
        :param landing_platform: instância de Platform.
        """
        # Distância ao target:
        dx = target.posicao[0] - self.posicao[0]
        dy = target.posicao[1] - self.posicao[1]
        self.distance_to_target = math.sqrt(dx**2 + dy**2)

        # Ângulo formado pela reta que une o foguete ao target
        angle_to_target = math.degrees(math.atan2(dy, dx))
        # Diferença entre o ângulo do foguete e o ângulo até o target (valor absoluto)
        self.angle_difference = abs((self.orientacao - angle_to_target + 180) % 360 - 180)

        # Distância em x e y até a plataforma de pouso (usando o centro da plataforma)
        landing_center_x = landing_platform.posicao[0] + landing_platform.comprimento / 2
        landing_center_y = landing_platform.altura  # Supondo que a plataforma esteja na altura 0
        self.distance_to_landing_platform_x = abs(self.posicao[0] - landing_center_x)
        self.distance_to_landing_platform_y = abs(self.posicao[1] - landing_center_y)
