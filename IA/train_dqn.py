import time
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback, CallbackList
from rocket_env import RocketEnv
import os
import numpy as np
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.env_checker import check_env
import torch

# Create directories for models and logs
model_dir = "models"
log_dir = "logs"
os.makedirs(model_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)

# Create and check environment
def make_env():
    env = RocketEnv(headless=True)
    return Monitor(env)

# Check environment for compatibility with stable-baselines3
print("Checking environment compatibility...")
check_env(RocketEnv())
print("Environment check passed!")

# Create vectorized environment
env = DummyVecEnv([make_env])

# Normalize observations and rewards
env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.0)

# Set up callbacks
eval_callback = EvalCallback(
    env,
    best_model_save_path=f"{model_dir}/best_model",
    log_path=log_dir,
    eval_freq=10000,
    deterministic=True,
    render=False
)

checkpoint_callback = CheckpointCallback(
    save_freq=50000,
    save_path=model_dir,
    name_prefix="rocket_dqn_model"
)

callback = CallbackList([checkpoint_callback, eval_callback])

# Configure DQN hyperparameters
policy_kwargs = dict(
    net_arch=[256, 256],  # Two hidden layers with 256 neurons each
)

# Initialize the DQN agent
print("Creating and training DQN agent...")
model = DQN(
    "MlpPolicy",
    env,
    policy_kwargs=policy_kwargs,
    learning_rate=0.0001,
    buffer_size=100000,
    learning_starts=1000,
    batch_size=64,
    gamma=0.99,
    train_freq=4,
    gradient_steps=1,
    target_update_interval=1000,
    exploration_fraction=0.1,
    exploration_initial_eps=1.0,
    exploration_final_eps=0.05,
    verbose=1,
    tensorboard_log=log_dir,
    device='cuda' if torch.cuda.is_available() else 'cpu'
)

# Train the agent
total_timesteps = 1000000
start_time = time.time()
model.learn(
    total_timesteps=total_timesteps, 
    callback=callback, 
    tb_log_name="dqn_rocket"
)

training_time = time.time() - start_time
print(f"Training completed in {training_time:.2f} seconds")

# Save the final model
model.save(f"{model_dir}/final_model")

# Save the normalization parameters
env.save(f"{model_dir}/vec_normalize.pkl")

print(f"Training complete! Model saved to {model_dir}/final_model")