class Platform:
    def __init__(self, posicao_x: float, comprimento: float, altura: float = 0):
        self.posicao = (posicao_x, altura)
        self.comprimento = comprimento
        self.altura = altura  # altura do chão (y = 0 na simulação)
