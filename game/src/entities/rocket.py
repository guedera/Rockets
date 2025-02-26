import math

class Rocket:
    GRAVIDADE = 500.0            # pixels/s²
    POTENCIA_INCREMENTO = 1      # Incremento da potência (1% por tecla)
    MAX_THRUST = 30000           # Empuxo máximo (N) para potência de 100%
    ROTATION_TORQUE = 3000.0     # Torque aplicado (valor arbitrário)
    DRAG_COEFFICIENT = 7.0       # Coeficiente de arrasto

    def __init__(self, posicao_x: float, posicao_y: float, massa: float):
        self.posicao = [posicao_x, posicao_y]
        self.initial_position = [posicao_x, posicao_y]
        self.orientacao = 90.0          
        self.initial_orientation = 90.0 
        self.velocidade = [0.0, 0.0]    
        self.angular_velocity = 0.0     
        self.massa = massa
        self.potencia_motor = 0         
        self.moment_of_inercia = self.massa * 50  

        self.fuel_consumed = 0.0
        self.target_reached = False
        self.landed = False
        self.crashed = False

        self.distance_to_target = None
        self.angle_difference = None
        self.distance_to_landing_platform_x = None
        self.distance_to_landing_platform_y = None

    def reset(self):
        self.posicao = self.initial_position.copy()
        self.orientacao = self.initial_orientation
        self.velocidade = [0.0, 0.0]
        self.angular_velocity = 0.0
        self.potencia_motor = 0

        self.fuel_consumed = 0.0
        self.target_reached = False
        self.landed = False
        self.crashed = False
        self.distance_to_target = None
        self.angle_difference = None
        self.distance_to_landing_platform_x = None
        self.distance_to_landing_platform_y = None

    def aplicar_forca(self, delta_time):
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
        return ax, ay

    def update_physics(self, delta_time):
        ax, ay = self.aplicar_forca(delta_time)
        self.velocidade[0] += ax * delta_time
        self.velocidade[1] += ay * delta_time
        self.posicao[0] += self.velocidade[0] * delta_time
        self.posicao[1] += self.velocidade[1] * delta_time
        self.orientacao += self.angular_velocity * delta_time

    def atualizar(self, delta_time):
        self.update_physics(delta_time)
        self.fuel_consumed += (self.potencia_motor / 100.0) * delta_time

    def alterar_potencia(self, incremento):
        self.potencia_motor += incremento
        self.potencia_motor = max(0, min(100, self.potencia_motor))

    def aplicar_torque(self, torque, delta_time):
        """
        Aplica torque para alterar a velocidade angular.
        """
        angular_acc_rad = torque / self.moment_of_inercia
        angular_acc_deg = math.degrees(angular_acc_rad)
        self.angular_velocity += angular_acc_deg * delta_time

    def compute_metrics(self, target, landing_platform):
        dx = target.posicao[0] - self.posicao[0]
        dy = target.posicao[1] - self.posicao[1]
        self.distance_to_target = math.sqrt(dx**2 + dy**2)

        angle_to_target = math.degrees(math.atan2(dy, dx))
        self.angle_difference = abs((self.orientacao - angle_to_target + 180) % 360 - 180)

        landing_center_x = landing_platform.posicao[0] + landing_platform.comprimento / 2
        landing_center_y = landing_platform.altura
        self.distance_to_landing_platform_x = abs(self.posicao[0] - landing_center_x)
        self.distance_to_landing_platform_y = abs(self.posicao[1] - landing_center_y)

    def get_state(self):
        return {
            'position': self.posicao.copy(),
            'velocity': self.velocidade.copy(),
            'orientation': self.orientacao,
            'fuel_consumed': self.fuel_consumed,
            'distance_to_target': self.distance_to_target,
            'angle_difference': self.angle_difference,
            'distance_to_landing_platform_x': self.distance_to_landing_platform_x,
            'distance_to_landing_platform_y': self.distance_to_landing_platform_y,
            'target_reached': self.target_reached,
            'landed': self.landed,
            'crashed': self.crashed
        }
