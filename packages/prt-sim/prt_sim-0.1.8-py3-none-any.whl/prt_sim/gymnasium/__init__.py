"""Custom Gymnasium API environments
"""
from gymnasium.envs.registration import register

register(
    id="prt-sim/ImagePipeline-v0",
    entry_point="prt_sim.gymnasium.image_pipeline:ImagePipeline",
    disable_env_checker=True,
)