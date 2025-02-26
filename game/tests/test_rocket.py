import unittest
import math
from game.src.entities.rocket import Rocket
from game.src.entities.target import Target
from game.src.entities.platform import Platform
import config

class TestRocketPhysics(unittest.TestCase):
    def setUp(self):
        # Cria uma instância de foguete e instâncias para target e plataforma
        self.rocket = Rocket(100, 100, 50)
        self.target = Target(200, 200, 30, 30)
        self.platform = Platform(posicao_x=400, comprimento=200, altura=0)

    def test_compute_metrics(self):
        # Define posições conhecidas e verifica se os cálculos estão corretos
        self.rocket.posicao = [100, 100]
        self.target.posicao = (200, 200)
        self.rocket.orientacao = 45  # apontando em direção de 45°

        self.rocket.compute_metrics(self.target, self.platform)
        expected_distance = math.sqrt((200-100)**2 + (200-100)**2)
        self.assertAlmostEqual(self.rocket.distance_to_target, expected_distance)

        # Como o ângulo até o target é 45° e o foguete está apontando para 45°, a diferença deve ser zero
        self.assertAlmostEqual(self.rocket.angle_difference, 0)

        landing_center_x = 400 + 200 / 2  # 400 + 100 = 500
        self.assertAlmostEqual(self.rocket.distance_to_landing_platform_x, abs(100 - 500))
        self.assertAlmostEqual(self.rocket.distance_to_landing_platform_y, abs(100 - 0))

    def test_update_physics(self):
        # Testa se a atualização da física altera posição, velocidade e orientação
        initial_position = self.rocket.posicao.copy()
        initial_velocity = self.rocket.velocidade.copy()
        delta_time = 1.0

        # Define uma potência e torque para o teste
        self.rocket.potencia_motor = 50  # 50%
        self.rocket.angular_velocity = 10  # graus/s

        self.rocket.update_physics(delta_time)

        self.assertNotEqual(self.rocket.posicao, initial_position)
        self.assertNotEqual(self.rocket.velocidade, initial_velocity)
        self.assertEqual(self.rocket.orientacao, 90 + 10 * delta_time)

if __name__ == '__main__':
    unittest.main()
