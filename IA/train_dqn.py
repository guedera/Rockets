import time
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback, CallbackList
from rocket_env import RocketEnv

def main():
    # Cria o ambiente de treinamento
    env = RocketEnv()

    # Cria o modelo DQN com política MLP e habilita logging para TensorBoard
    model = DQN("MlpPolicy", env, verbose=1, tensorboard_log="./tensorboard_log/")

    # Cria um ambiente para avaliação (usado pelo EvalCallback)
    eval_env = RocketEnv()

    # Callback de avaliação:
    # - A cada 5000 timesteps, o ambiente é avaliado em 10 episódios.
    # - Se o desempenho médio for melhor do que o melhor registrado, o modelo é salvo em './logs/best_model/'.
    # - As métricas de avaliação (recompensa média, etc.) são registradas em './logs/'.
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path='./logs/best_model/',
        log_path='./logs/',
        eval_freq=5000,
        n_eval_episodes=10,
        deterministic=True,
        render=False
    )

    # Callback de checkpoint: salva periodicamente o modelo a cada 5000 timesteps.
    # Assim, você tem backups intermediários, mas o melhor modelo será aquele salvo pelo EvalCallback.
    checkpoint_callback = CheckpointCallback(
        save_freq=5000,
        save_path='./checkpoints/',
        name_prefix='dqn_rocket_model'
    )

    # Combina os callbacks
    callback = CallbackList([eval_callback, checkpoint_callback])

    # Inicia o treinamento por 100000 timesteps (ajuste conforme necessário)
    model.learn(total_timesteps=100000, callback=callback)

    # Salva o modelo final
    model.save("dqn_rocket_model_final")
    print("Treinamento concluído e modelo salvo em dqn_rocket_model_final.zip")

    # Testa o modelo treinado
    obs = env.reset()
    for _ in range(1000):
        action, _states = model.predict(obs)
        obs, reward, done, info = env.step(action)
        env.render()  # No nosso ambiente, render() imprime a observação
        time.sleep(0.02)  # Pausa para facilitar a visualização
        if done:
            obs = env.reset()

if __name__ == '__main__':
    main()
