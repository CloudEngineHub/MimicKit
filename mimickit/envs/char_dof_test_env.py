import envs.char_env as char_env

import numpy as np
import torch

class CharDofTestEnv(char_env.CharEnv):
    def __init__(self, config, num_envs, device, visualize):
        self._time_per_dof = 4.0

        super().__init__(config=config, num_envs=num_envs, device=device,
                         visualize=visualize)

        self._episode_length = self._time_per_dof * self._pd_low.shape[0]
        return
    
    def _build_sim_tensors(self, config):
        super()._build_sim_tensors(config)
        
        pd_low = self._action_space.low
        pd_high = self._action_space.high
        self._pd_low = torch.tensor(pd_low, device=self._device, dtype=torch.float32)
        self._pd_high = torch.tensor(pd_high, device=self._device, dtype=torch.float32)
        return

    def _apply_action(self, actions):
        test_actions = self._calc_test_action(actions)
        super()._apply_action(test_actions)
        return

    def _calc_test_action(self, actions):
        test_actions = torch.zeros_like(actions)

        num_envs = self._engine.get_num_envs()
        num_dofs = self._pd_low.shape[0]
        env_ids = torch.arange(num_envs, device=self._device, dtype=torch.long)

        phase = self._time_buf / self._time_per_dof
        dof_id = phase.type(torch.long)
        dof_id = dof_id + env_ids
        dof_id = torch.remainder(dof_id, num_dofs)

        curr_low = self._pd_low[dof_id]
        curr_high = self._pd_high[dof_id]
        
        joint_phase = phase - torch.floor(phase)
        lerp = torch.sin(2 * np.pi * joint_phase)
        lim_val = torch.where(lerp < 0.0, curr_low, curr_high)
        abs_lerp = torch.abs(lerp)
        dof_val = abs_lerp * lim_val

        test_actions[torch.arange(actions.shape[0]), dof_id] = dof_val

        return test_actions
    
    def _ig_load_char_asset(self, config):
        char_file = config["env"]["char_file"]
        self._char_asset = self._engine.load_asset(char_file, fix_base=True)
        return

    def _ig_build_character(self, env_id, config, color=None):
        col_group = env_id
        col_filter = 1
        segmentation_id = 0
        char_id = self._engine.create_actor(env_id=env_id, 
                                             asset=self._char_asset,
                                             name="character", 
                                             col_group=col_group, 
                                             col_filter=col_filter, 
                                             segmentation_id=segmentation_id,
                                             color=color)
        return char_id
