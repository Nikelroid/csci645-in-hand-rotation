# mjlab 1.6.0 port (CSCI 645 HW1, Part 4)

This branch ports the in-hand cube rotation task from mjlab 1.1.1 to mjlab 1.6.0, the latest mjlab release before the HW1 assignment date (2026-08-27). The `main` branch keeps the course's pinned versions, as the handout requires.

## Versions

| Package | `main` | `mjlab-1.6` |
|---|---|---|
| mjlab | 1.1.1 | 1.6.0 |
| mujoco | 3.5.0 | 3.11.0 |
| mujoco-warp | git `fc91589` | 3.11.0 |
| warp-lang | 1.12.0.dev20260206 | 1.16.0 |
| rsl-rl-lib | 4.0.1 | 5.4.2 |
| torch | 2.9.0 (CUDA 12.6) | 2.9.0 (CUDA 12.6) |

`pyproject.toml` also sets `exclude-newer = "2026-08-28T00:00:00Z"`, so uv resolves every other package as it was on the assignment date. MuJoCo 3.11 is the newest line that mjlab 1.6.0 allows.

## Usage

The commands and flags are the same as on `main` (see `README_CSCI645.md`).

```bash
uv sync
uv run python scripts/train.py Mjlab-Leap-Left-HandCube-Rotate \
  --env.scene.num-envs 4096 --agent.max-iterations 5000 --agent.upload-model False
uv run python scripts/play.py Mjlab-Leap-Left-Custom-HandCube-Rotate \
  --checkpoint-file ckpts/leap_left_custom_model_4900.pt
```

By default, mjlab 1.6.0 uploads every checkpoint to W&B. The flag `--agent.upload-model False` turns this off and does not change training.

## What changed

- Actuators. mjlab 1.3 removed `DelayedActuatorCfg`, so the LEAP actuators set the command delay (0 to 20 physics steps, held for the episode) directly on `IdealPdActuatorCfg` (`robots/leap_hand/leap_right_constants.py`). The effort-limit event and the sim2sim action term no longer unwrap a delayed actuator.
- Lag event. The per-episode lag event `sync_actuator_delays` (25 to 75 ms) left mjlab with the same release, so the task has its own copy on top of `Actuator.set_lags` (`tasks/hand_cube/mdp/events.py`).
- Domain randomization. mjlab 1.2 removed `randomize_field`, so the COM, joint friction, joint damping, armature and PD-gain events use `dr.body_com_offset`, `dr.joint_friction`, `dr.joint_damping`, `dr.joint_armature` and `dr.pd_gains` with the same ranges (`tasks/hand_cube/hand_cube_env_cfg.py`).
- PPO config. The actor's `stochastic` and `init_noise_std` became a `distribution_cfg` (Gaussian, initial std 0.7, scalar std), and the critic's became `None` (`tasks/hand_cube/config/*/rl_cfg.py`).
- Runner. `scripts/train.py` and `scripts/play.py` use `MjlabOnPolicyRunner`, which also loads RSL-RL 4 checkpoints such as the course's pretrained model.
- Smaller API changes. Command terms take `env_ids` in `_update_command`, and `TerrainImporterCfg` is now `TerrainEntityCfg`. The removed `update_assets` helper is vendored in `robots/leap_hand/assets.py`, and the frame debug drawing passes float64 arrays to MuJoCo 3.11 (`tasks/hand_cube/mdp/commands.py`).

## Checks

- The compiled MuJoCo model is identical to `main` in all 28 fields I compared (collision filtering, contact parameters, masses, inertias, armature, damping, friction loss, joint and actuator limits, solver options). The PPO settings are identical too.
- The course's pretrained checkpoint loads on this branch and spins the cube at 0.323 [0.311, 0.334] rad/s over 16 episodes, against 0.318 [0.301, 0.336] rad/s on `main`. Both keep 16 of 16 cubes.
- On `main`, the pose-deviation termination and the drift metrics store the reset pose before mjlab updates the body poses, so their reference is 0.40 to 0.58 m off right after a reset. On this branch the reference is the true cube pose. At iteration 0, the logged position error drops from 0.493 m to 0.006 m, and the pose-deviation terminations from 135.6 to 0.5 per reset event.
- On an A40 with 4,096 environments, training runs at 29,884 to 32,763 steps/s, against 15,767 to 16,186 on `main`. A 5,000-iteration run takes 5.5 to 6.3 hours.

## Results (seed 42)

I retrained the HW1 baseline and both modifications on this branch with the same budget, 4,096 environments, 32 steps per environment and 5,000 iterations. Each value is a mean over 1,024 evaluation episodes, under the training randomization (train) or with hand-cube friction 0.35 to 0.55 (slippery). Kept is the share of episodes that reach the 20 s limit.

| Configuration | Spin, train (rad/s) | Kept, train (%) | Tilt error, train (rad) | Kept, slippery (%) | W&B run |
|---|---|---|---|---|---|
| Baseline | 0.360 | 96.9 | 0.177 | 88.3 | [pkly9o7y](https://wandb.ai/kelidari-usc/csci645-hw1/runs/pkly9o7y) |
| Wider friction and mass randomization (Track C) | 0.341 | 96.1 | 0.180 | 94.7 | [0fjgmc6x](https://wandb.ai/kelidari-usc/csci645-hw1/runs/0fjgmc6x) |
| Proportional drift gate (Track A) | 0.254 | 96.4 | 0.152 | 84.3 | [7uk611kj](https://wandb.ai/kelidari-usc/csci645-hw1/runs/7uk611kj) |

The two modifications add these flags to the training command.

```bash
# Wider friction and mass randomization
--env.events.dr-shared-contact-friction.params.friction-range 0.4 1.6 \
--env.events.dr-cube-mass.params.mass-range 0.5 2.0

# Proportional drift gate
--env.rewards.rotate-finite-diff.params.drift-mode exp \
--env.rewards.rotate-finite-diff.params.drift-position-threshold 0.0 \
--env.rewards.rotate-finite-diff.params.drift-tilt-threshold 0.0
```
