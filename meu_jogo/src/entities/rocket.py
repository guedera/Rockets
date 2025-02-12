import math

class Rocket:
    GRAVIDADE = 10.0  # m/s²
    MAX_VETORACAO = 45  # Limite de inclinação do motor
    POTENCIA_INCREMENTO = 10  # Quanto a potência muda por comando

    def __init__(self, posicao_x: float, posicao_y: float, massa: float):
        self.posicao = [posicao_x, posicao_y]
        self.orientacao = 90  # Inicia de pé (graus)
        self.velocidade = [0, 0]
        self.angulo_motor = 0  # Inicialmente alinhado
        self.potencia_motor = 0
        self.massa = massa

    def aplicar_forca(self, delta_time):
        """Aplica a força do motor e a gravidade ao foguete"""
        empuxo = (self.potencia_motor / 100) * 1000  # Empuxo proporcional à potência
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

    def girar_motor(self, angulo):
        """Ajusta o ângulo do motor dentro do limite"""
        self.angulo_motor = max(-self.MAX_VETORACAO, min(self.MAX_VETORACAO, self.angulo_motor + angulo))

    def alterar_potencia(self, incremento):
        """Ajusta a potência do motor dentro do limite"""
        self.potencia_motor = max(0, min(100, self.potencia_motor + incremento))
