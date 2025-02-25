class Platform:
    def __init__(self, posicao_x: float, comprimento: float, altura: float = 0):
        """
        posicao_x: coordenada x (em pixels) da esquerda da plataforma;
        comprimento: largura da plataforma (em pixels);
        altura: nível do solo na simulação (normalmente 0).
        """
        self.posicao = (posicao_x, altura)
        self.comprimento = comprimento
        self.altura = altura  # altura do chão (y = 0 na simulação)
