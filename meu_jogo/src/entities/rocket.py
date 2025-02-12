import math

class Rocket:
    GRAVIDADE = 10.0  # m/s²

    def __init__(self, posicao_x: float, posicao_y: float, orientacao: float, velocidade: float, angulo_motor: float, potencia_motor: float, massa: float):
        self.posicao = [posicao_x, posicao_y]
        self.orientacao = orientacao
        self.velocidade = [0, velocidade]
        self.angulo_motor = angulo_motor
        self.potencia_motor = max(0, min(potencia_motor, 100))  # Garante que a potência esteja entre 0 e 100%
        self.massa = massa

    def aplicar_forca(self, delta_time):
        """Aplica a força do motor e a gravidade ao foguete"""
        if self.potencia_motor > 0:
            empuxo = (self.potencia_motor / 100) * 1000  # Empuxo arbitrário proporcional à potência
            angulo_rads = math.radians(self.orientacao + self.angulo_motor)
            forca_x = empuxo * math.cos(angulo_rads)
            forca_y = empuxo * math.sin(angulo_rads) - (self.massa * self.GRAVIDADE)
            
            aceleracao_x = forca_x / self.massa
            aceleracao_y = forca_y / self.massa

            self.velocidade[0] += aceleracao_x * delta_time
            self.velocidade[1] += aceleracao_y * delta_time

    def atualizar(self, delta_time):
        """Atualiza a posição do foguete considerando a velocidade e a força aplicada"""
        self.aplicar_forca(delta_time)
        self.posicao[0] += self.velocidade[0] * delta_time
        self.posicao[1] += self.velocidade[1] * delta_time

    def girar(self, angulo):
        """Gira a nave para um novo ângulo"""
        self.orientacao += angulo

    def mudar_vetoracao(self, angulo):
        """Muda o ângulo do motor dentro de um limite"""
        self.angulo_motor = max(-45, min(45, angulo))  # Limitamos a vetorção entre -45 e 45 graus

    def limitar_potencia(self, valor):
        """Garante que a potência fique entre 0% e 100%"""
        self.potencia_motor = max(0, min(valor, 100))
