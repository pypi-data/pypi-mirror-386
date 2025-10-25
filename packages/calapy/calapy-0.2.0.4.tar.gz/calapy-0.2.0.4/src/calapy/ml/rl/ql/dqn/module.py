

import os
import copy
import math
import random
import torch
import numpy as np
from ..... import clock as cp_clock
from ..... import strings as cp_strings
from ..... import txt as cp_txt
from ....rl import utilities as cp_rl_utilities
from .....ml import utilities as cp_ml_utilities
from ....sl.dl.output_methods.general import *
from ....sl.dl.tensors import unsqueeze as cp_unsqueeze


__all__ = ['DQNMethods', 'TimedDQNMethods']


class DQNMethods(OutputMethods):

    def __init__(
            self, model, axis_features_outs, axis_models_losses,
            possible_actions, action_selection_type='active', same_indexes_actions=None,
            gamma=0.999, reward_bias=0.0, loss_scales_actors=None, is_recurrent=False):

        """
        :type model:
        :type axis_features_outs: int
        :type axis_models_losses: int
        :type possible_actions: list[list[int | float] | tuple[int | float]] |
                                tuple[list[int | float] | tuple[int | float]]
        :type action_selection_type: str
        :type same_indexes_actions: int | list | tuple | np.ndarray | torch.Tensor | None
        :type gamma: int | float | None
        :type reward_bias: int | float | None
        :type loss_scales_actors: list[int | float] | tuple[int | float] |
                                  np.ndarray[int | float] | torch.Tensor[int | float] | float | int | None
        :type is_recurrent: bool | None
        """

        superclass = DQNMethods
        try:
            # noinspection PyUnresolvedReferences
            self.superclasses_initiated
        except AttributeError:
            self.superclasses_initiated = []
        except NameError:
            self.superclasses_initiated = []

        self.model = model

        self.device = model.device
        self.dtype = model.dtype

        if isinstance(possible_actions, list):
            self.possible_actions = possible_actions
        elif isinstance(possible_actions, tuple):
            self.possible_actions = list(possible_actions)
        elif isinstance(possible_actions, np.ndarray):
            self.possible_actions = possible_actions.tolist()
        else:
            raise TypeError('n_possible_actions')

        self.n_agents = self.A = len(self.possible_actions)
        self.loss_scales_actors = _set_loss_scales(M=self.A, loss_scales=loss_scales_actors)

        self.n_possible_actions = [-1 for a in range(0, self.A, 1)]  # type: list

        for a in range(0, self.A, 1):
            if isinstance(self.possible_actions[a], (list, tuple)):
                self.possible_actions[a] = torch.tensor(self.possible_actions[a], device=self.device)
            elif isinstance(self.possible_actions[a], np.ndarray):
                self.possible_actions[a] = torch.from_numpy(self.possible_actions[a]).to(device=self.device)
            elif isinstance(self.possible_actions[a], torch.Tensor):
                self.possible_actions[a].to(device=self.device)
            else:
                raise TypeError('n_possible_actions')

            self.n_possible_actions[a] = len(self.possible_actions[a])

        self.possible_actions = tuple(self.possible_actions)
        self.n_possible_actions = tuple(self.n_possible_actions)

        if TimedOutputMethods not in self.superclasses_initiated:
            OutputMethods.__init__(
                self=self, axis_features_outs=axis_features_outs,
                axis_models_losses=axis_models_losses, M=self.A, loss_scales=self.loss_scales_actors)
            if TimedOutputMethods not in self.superclasses_initiated:
                self.superclasses_initiated.append(TimedOutputMethods)

        if isinstance(action_selection_type, str):
            if action_selection_type.lower() in ['active', 'random', 'same']:
                self.action_selection_type = action_selection_type.lower()
            else:
                raise ValueError('action_selection_type')
        else:
            raise TypeError('action_selection_type')

        if self.action_selection_type == 'same':
            if isinstance(same_indexes_actions, int):
                self.same_indexes_actions = [same_indexes_actions]  # type: list
            elif isinstance(same_indexes_actions, list):
                self.same_indexes_actions = same_indexes_actions
            elif isinstance(same_indexes_actions, tuple):
                self.same_indexes_actions = list(same_indexes_actions)
            elif isinstance(same_indexes_actions, (np.ndarray, torch.Tensor)):
                self.same_indexes_actions = same_indexes_actions.tolist()
            else:
                raise TypeError('same_indexes_actions')
        else:
            self.same_indexes_actions = same_indexes_actions

        if is_recurrent is None:
            self.is_recurrent = False
        elif isinstance(is_recurrent, bool):
            self.is_recurrent = is_recurrent
        else:
            raise TypeError('is_recurrent')

        if gamma is None:
            self.gamma = 0.999
        elif isinstance(gamma, float):
            self.gamma = gamma
        elif isinstance(gamma, int):
            self.gamma = float(gamma)
        else:
            raise TypeError('gamma')

        if reward_bias is None:
            self.reward_bias = 0.0
        elif isinstance(reward_bias, float):
            self.reward_bias = reward_bias
        elif isinstance(reward_bias, int):
            self.reward_bias = float(reward_bias)
        else:
            raise TypeError('reward_bias')

        if reward_bias is None:
            self.reward_bias = 0.0
        elif isinstance(reward_bias, float):
            self.reward_bias = reward_bias
        elif isinstance(reward_bias, int):
            self.reward_bias = float(reward_bias)
        else:
            raise TypeError('reward_bias')

        self.criterion_values_actions = torch.nn.SmoothL1Loss(reduction='none')
        self.criterion_values_actions_reduction = torch.nn.SmoothL1Loss(reduction='mean')

        if superclass not in self.superclasses_initiated:
            self.superclasses_initiated.append(superclass)

    def q_values_to_actions(self, values_actions):

        """

        :type values_actions: list | torch.Tensor
        """

        # todo: forward only n non-random actions

        if isinstance(values_actions, torch.Tensor):
            device = values_actions.device
        else:
            device = values_actions[0].device

        A = len(values_actions)
        shape_actions = self.compute_shape_losses(values_actions)

        indexes_actions = [
            slice(0, shape_actions[a], 1) if a != self.axis_models_losses else None
            for a in range(0, values_actions[0].ndim, 1)]  # type: list

        actions = torch.empty(shape_actions, dtype=torch.int64, device=device, requires_grad=False)

        for a in range(0, A, 1):

            indexes_actions[self.axis_models_losses] = a
            tuple_indexes_actions = tuple(indexes_actions)

            # actions[tuple_indexes_actions] = values_actions[a].max(dim=self.axis_features_outs, keepdim=True)[1]
            actions[tuple_indexes_actions] = values_actions[a].max(dim=self.axis_features_outs, keepdim=False)[1]

        return actions

    def sample_action(self, values_actions, epsilon=.1):

        """

        :type values_actions: list | torch.Tensor
        :type epsilon: list[float]
        """

        # todo: forward only n non-random actions

        if isinstance(values_actions, torch.Tensor):
            device = values_actions.device
        else:
            device = values_actions[0].device

        A = len(values_actions)
        shape_actions = self.compute_shape_losses(values_actions)

        indexes_actions = [
            slice(0, shape_actions[a], 1) if a != self.axis_models_losses else None
            for a in range(0, values_actions[0].ndim, 1)]  # type: list

        shape_actions_a = [
            shape_actions[a] for a in range(0, values_actions[0].ndim, 1) if a != self.axis_models_losses]

        actions = torch.empty(shape_actions, dtype=torch.int64, device=device, requires_grad=False)

        if self.action_selection_type == 'active':

            # mask_randoms = torch.rand(
            #     shape_actions_a, out=None, dtype=None, layout=torch.strided,
            #     device=device, requires_grad=False) < epsilon
            #
            # n_randoms = mask_randoms.sum(dtype=None).item()
            #
            # mask_greedy = torch.logical_not(mask_randoms, out=None)

            for a in range(0, A, 1):

                indexes_actions[self.axis_models_losses] = a
                tuple_indexes_actions = tuple(indexes_actions)

                mask_randoms_a = torch.rand(
                    shape_actions_a, out=None, dtype=None, layout=torch.strided,
                    device=device, requires_grad=False) < epsilon[a]  # type: torch.Tensor

                n_randoms_a = mask_randoms_a.sum(dtype=None).item()

                mask_greedy_a = torch.logical_not(mask_randoms_a, out=None)

                random_action_a = torch.randint(
                    low=0, high=self.n_possible_actions[a], size=(n_randoms_a,),
                    generator=None, dtype=torch.int64, device=device, requires_grad=False)

                actions[tuple_indexes_actions][mask_randoms_a] = random_action_a

                actions[tuple_indexes_actions][mask_greedy_a] = (
                    # values_actions[a].max(dim=self.axis_features_outs, keepdim=True)[1][mask_greedy_a])
                    values_actions[a].max(dim=self.axis_features_outs, keepdim=False)[1][mask_greedy_a])

        elif self.action_selection_type == 'random':

            for a in range(0, A, 1):

                indexes_actions[self.axis_models_losses] = a
                tuple_indexes_actions = tuple(indexes_actions)

                actions[tuple_indexes_actions] = torch.randint(
                    low=0, high=self.n_possible_actions[a], size=shape_actions_a,
                    generator=None, dtype=torch.int64, device=device, requires_grad=False)

        elif self.action_selection_type == 'same':

            for a in range(0, A, 1):

                indexes_actions[self.axis_models_losses] = a
                tuple_indexes_actions = tuple(indexes_actions)

                actions[tuple_indexes_actions] = torch.full(
                    size=shape_actions_a, fill_value=self.same_indexes_actions[a],
                    dtype=torch.int64, device=device, requires_grad=False)
        else:
            raise ValueError('self.action_selection_type')

        return actions

    def gather_values_selected_actions(self, values_actions, actions):

        A = len(values_actions)
        shape_actions = actions.shape

        device = values_actions[0].device

        values_selected_actions = torch.empty(shape_actions, dtype=torch.float32, device=device, requires_grad=False)
        indexes_actions = [
            slice(0, values_selected_actions.shape[a], 1)
            for a in range(0, values_selected_actions.ndim, 1)]  # type: list

        for a in range(0, A, 1):

            indexes_actions[self.axis_models_losses] = a
            tuple_indexes_actions = tuple(indexes_actions)

            values_selected_actions[tuple_indexes_actions] = values_actions[a].gather(
                self.axis_features_outs, actions[tuple_indexes_actions].unsqueeze(
                    dim=self.axis_features_outs)).squeeze(dim=self.axis_features_outs)

        # values_selected_actions = [values_actions[a].gather(self.axis_features_outs, actions[a]).squeeze(
        #     dim=self.axis_features_outs) for a in range(0, self.A, 1)]
        # values_selected_actions = [values_actions[a].gather(self.axis_features_outs, actions[a].unsqueeze(
        #     dim=self.axis_features_outs)).squeeze(dim=self.axis_features_outs) for a in range(0, self.A, 1)]

        return values_selected_actions

    def compute_expected_values_actions(self, next_values_actions, rewards):

        A = len(next_values_actions)
        shape_actions = self.compute_shape_losses(next_values_actions)

        device = next_values_actions[0].device

        expected_values_actions = torch.empty(shape_actions, dtype=torch.float32, device=device, requires_grad=False)
        indexes_actions = [
            slice(0, expected_values_actions.shape[a], 1)
            for a in range(0, expected_values_actions.ndim, 1)]  # type: list

        biased_rewards = rewards + self.reward_bias

        for a in range(0, A, 1):

            indexes_actions[self.axis_models_losses] = a
            tuple_indexes_actions = tuple(indexes_actions)

            max_next_values_actions_a = next_values_actions[a].max(
                dim=self.axis_features_outs, keepdim=False)[0].detach()

            expected_values_actions[tuple_indexes_actions] = biased_rewards + (self.gamma * max_next_values_actions_a)

        return expected_values_actions.detach()

    def compute_value_action_losses(self, values_selected_actions, expected_values_actions):

        value_action_losses = self.criterion_values_actions(values_selected_actions, expected_values_actions.detach())

        return value_action_losses

    def reduce_value_action_losses(
            self, value_action_losses, axes_not_included=None,
            scaled=False, loss_scales_actors=None, format_scales=True):

        """


        :type value_action_losses: torch.Tensor | np.ndarray
        :type axes_not_included: int | list | tuple | np.ndarray | torch.Tensor | None
        :type scaled: bool
        :type loss_scales_actors: list | tuple | np.ndarray | torch.Tensor | None
        :type format_scales: bool

        :rtype:
        """

        if scaled and (loss_scales_actors is None):
            loss_scales_actors = self.loss_scales_actors
            format_scales = False

        reduced_value_action_losses = self.reduce_losses(
            losses=value_action_losses, axes_not_included=axes_not_included,
            scaled=scaled, loss_scales=loss_scales_actors, format_scales=format_scales)

        return reduced_value_action_losses

    def compute_n_selected_actions(self, selected_actions, axes_not_included=None):

        """

        :type selected_actions: np.ndarray | torch.Tensor
        :type axes_not_included: int | list | tuple | np.ndarray | torch.Tensor | None

        :rtype:
        """

        n_selected_actions = self.compute_n_losses(losses=selected_actions, axes_not_included=axes_not_included)

        return n_selected_actions

    def compute_deltas(self, actions: torch.Tensor, to_numpy: bool = False):

        indexes_actions = [
            slice(0, actions.shape[a], 1) if a != self.axis_models_losses else None
            for a in range(0, actions.ndim, 1)]  # type: list

        # deltas = copy.deepcopy(actions)
        # for a in range(0, self.A, 1):
        #     indexes_actions[self.axis_models_losses] = a
        #     tup_indexes_actions = tuple(indexes_actions)
        #     deltas[tup_indexes_actions] = self.possible_actions[a][actions[tup_indexes_actions]]
        # if to_numpy:
        #     if deltas.is_cuda:
        #         deltas = deltas.cpu().numpy()
        #     else:
        #         deltas = deltas.numpy()

        deltas = [None for a in range(0, self.A, 1)]  # type: list[torch.Tensor] | list[None]

        for a in range(0, self.A, 1):
            indexes_actions[self.axis_models_losses] = a
            tup_indexes_actions = tuple(indexes_actions)
            deltas[a] = self.possible_actions[a][actions[tup_indexes_actions]]

            if to_numpy:
                if deltas[a].is_cuda:
                    deltas[a] = deltas[a].cpu().numpy()
                else:
                    deltas[a] = deltas[a].numpy()

        return deltas

    def train_from_ind_agents(
            self, environment, optimizer,
            is_without_state_batch_axis, is_without_state_time_axis,
            is_without_reward_batch_axis, is_without_reward_time_axis,
            state_batch_axis, state_time_axis, action_batch_axis, action_time_axis, reward_batch_axis, reward_time_axis,
            U=10, E=None, n_batches_per_train_phase=100, batch_size_of_train=100, time_size=10, T_train=None,
            epsilon_start=.95, epsilon_end=.01, epsilon_step=-.05,  capacity=100000,
            min_n_episodes_for_optim=2, min_n_samples_for_optim=1000, prob_last=0.0,
            n_episodes_per_val_phase=1000, T_val=None, directory_outputs=None):

        """

        :type environment:

        :type optimizer:

        :type is_without_state_batch_axis: bool

        :type is_without_state_time_axis: bool

        :type is_without_reward_batch_axis: bool

        :type is_without_reward_time_axis: bool

        :type state_batch_axis: int

        :type state_time_axis: int

        :type action_batch_axis: int

        :type action_time_axis: int

        :type reward_batch_axis: int

        :type reward_time_axis: int

        :type U: int | float | None

        :type E: int | float | None

        :type n_batches_per_train_phase: int

        :type batch_size_of_train: int

        :type time_size: int

        :type T_train: int | float | None

        :type epsilon_start: np.ndarray[float]

        :type epsilon_end: np.ndarray[float]

        :type epsilon_step: np.ndarray[float]

        :type capacity: int

        :type min_n_episodes_for_optim: int

        :type min_n_samples_for_optim: int

        :type n_episodes_per_val_phase: int

        :type T_val: int | float | None

        :type directory_outputs: str | None
        """

        cp_timer = cp_clock.Timer()

        phases_names = ('training', 'validation')
        n_phases = len(phases_names)
        phases_titles = tuple(phase_name_p.title() for phase_name_p in phases_names)
        for key_environment_k in environment.keys():
            if key_environment_k in phases_names:
                pass
            else:
                raise ValueError('Unknown keys in environment')

        if n_batches_per_train_phase is None:
            n_batches_per_train_phase = 100
        elif isinstance(n_batches_per_train_phase, int):
            pass
        else:
            raise TypeError('n_batches_per_train_phase')

        if batch_size_of_train is None:
            batch_size_of_train = 100
        elif isinstance(batch_size_of_train, int):
            pass
        else:
            raise TypeError('batch_size_of_train')

        tot_observations_per_train_phase = n_batches_per_train_phase * batch_size_of_train
        if self.is_recurrent:
            tot_observations_per_train_phase *= time_size

        T = {'training': T_train, 'validation': T_val}
        if T['training'] is None:
            T['training'] = math.inf
        elif isinstance(T['training'], int):
            pass
        elif isinstance(T['training'], float):
            if T['training'] == math.inf:
                pass
            else:
                raise ValueError('T_train')
        else:
            raise TypeError('T_train')

        if T['validation'] is None:
            T['validation'] = math.inf
        elif isinstance(T['validation'], int):
            pass
        elif isinstance(T['validation'], float):
            if T['validation'] == math.inf:
                pass
            else:
                raise ValueError('T_val')
        else:
            raise TypeError('T_val')

        self.model.freeze()
        torch.set_grad_enabled(False)

        headers = [
            'Epoch', 'Unsuccessful_Epochs', 'Epsilons',
            # 'Start_Date', 'Start_Time' 'Epoch_Duration', 'Elapsed_Time',

            'Training_Time_Length_Per_Episode', 'Training_Scores_Per_Episode',
            'Training_Cumulative_Reward_Per_Episode', 'Training_Reward_Per_Observation', 'Training_Loss',

            'Validation_Time_Length_Per_Episode',

            'Validation_Scores_Per_Episode',
            'Highest_Validation_Scores_Per_Episode', 'Is_Highest_Validation_Scores_Per_Episode',

            'Validation_Cumulative_Reward_Per_Episode',
            'Highest_Validation_Cumulative_Reward_Per_Episode', 'Is_Highest_Validation_Cumulative_Reward_Per_Episode',

            'Validation_Reward_Per_Observation',
            'Highest_Validation_Reward_Per_Observation', 'Is_Highest_Validation_Reward_Per_Observation',

            'Validation_Loss', 'Lowest_Validation_Loss', 'Is_Lowest_Validation_Loss'
        ]

        n_columns = len(headers)
        new_line_stats = [None for i in range(0, n_columns, 1)]  # type: list

        stats = {
            'headers': {headers[k]: k for k in range(n_columns)},
            'n_columns': n_columns,
            'lines': []}

        if directory_outputs is None:
            directory_outputs = 'outputs'
        os.makedirs(directory_outputs, exist_ok=True)

        directory_model_at_last_epoch = os.path.join(directory_outputs, 'model_at_last_epoch.pth')

        directory_model_with_highest_score_per_episode = os.path.join(
            directory_outputs, 'model_with_highest_score_per_episode.pth')

        directory_model_with_highest_cum_reward_per_episode = os.path.join(
            directory_outputs, 'model_with_highest_cumulative_reward_per_episode.pth')

        directory_model_with_highest_reward_per_obs = os.path.join(
            directory_outputs, 'model_with_highest_reward_per_observation.pth')

        directory_model_with_lowest_loss = os.path.join(directory_outputs, 'model_with_lowest_loss.pth')

        directory_stats = os.path.join(directory_outputs, 'stats.csv')

        n_decimals_for_printing = 6
        n_dashes = 150
        dashes = '-' * n_dashes
        print(dashes)

        if self.is_recurrent:

            memory = EpisodeMemory(
                capacity=capacity, add_timepoints_as='l', batch_size=batch_size_of_train, time_size=time_size,
                is_without_state_batch_axis=False, is_without_state_time_axis=False,
                is_without_reward_batch_axis=is_without_reward_batch_axis,
                is_without_reward_time_axis=is_without_reward_time_axis,
                state_batch_axis=state_batch_axis, state_time_axis=state_time_axis,
                action_batch_axis=action_batch_axis, action_time_axis=action_time_axis,
                reward_batch_axis=reward_batch_axis, reward_time_axis=reward_time_axis,
                prob_last=prob_last)

            sorted_state_bt_axes = memory.sorted_state_bt_axes
        else:
            memory = TimePointMemory(
                capacity=capacity, add_timepoints_as='l', batch_size=batch_size_of_train,
                is_without_state_batch_axis=False, is_without_reward_batch_axis=is_without_reward_batch_axis,
                state_batch_axis=state_batch_axis, action_batch_axis=action_batch_axis,
                reward_batch_axis=reward_batch_axis)
            sorted_state_bt_axes = None

        score_per_episode_ep = -math.inf
        highest_score_per_episode = score_per_episode_ep
        highest_score_per_episode_str = str(highest_score_per_episode)

        cum_reward_per_episode_ep = -math.inf
        highest_cum_reward_per_episode = cum_reward_per_episode_ep
        highest_cum_reward_per_episode_str = str(highest_cum_reward_per_episode)

        reward_per_observation_ep = -math.inf
        highest_reward_per_obs = reward_per_observation_ep
        highest_reward_per_obs_str = str(highest_reward_per_obs)

        loss_ep = math.inf
        lowest_loss = loss_ep
        lowest_loss_str = str(lowest_loss)

        epsilon = epsilon_start  # todo to the model
        ind_bool = epsilon < epsilon_end
        if np.any(ind_bool):
            epsilon[ind_bool] = copy.deepcopy(epsilon_end[ind_bool])

        epochs = cp_ml_utilities.EpochsIterator(U=U, E=E)
        e = 0
        u = 0

        for e, u in epochs:

            print('Epoch {e} ...'.format(e=e))

            stats['lines'].append(new_line_stats.copy())
            stats['lines'][e][stats['headers']['Epoch']] = e
            stats['lines'][e][stats['headers']['Epsilons']] = epsilon.tolist()

            # Each Training Epoch has a training and a validation phase
            for p in range(0, n_phases, 1):

                phase_name_p = phases_names[p]
                phase_title_p = phases_titles[p]

                running_n_selected_actions_ep = 0
                running_loss_ep = 0.0
                running_n_episodes_ep = 0
                running_sum_time_lengths_ep = 0
                running_sum_scores_ep = 0
                running_sum_cum_rewards_ep = 0

                i = 0
                s = 0
                b = 0
                j = 0

                if phase_name_p == 'training':
                    self.model.train()
                    are_more_episodes_needed = s < tot_observations_per_train_phase
                elif phase_name_p == 'validation':
                    self.model.eval()
                    are_more_episodes_needed = i < n_episodes_per_val_phase
                else:
                    raise ValueError('phase_name_p')

                while are_more_episodes_needed:

                    observation_epit = copy.deepcopy(environment[phase_name_p].reset())

                    if is_without_state_batch_axis or (self.is_recurrent and is_without_state_time_axis):
                        for a in range(0, environment[phase_name_p].n_agents, 1):
                            if observation_epit[a] is not None:
                                if is_without_state_batch_axis:
                                    if self.is_recurrent and is_without_state_time_axis:
                                        observation_epit[a] = cp_unsqueeze(
                                            data=observation_epit[a], dims=sorted_state_bt_axes, sort=False)
                                    else:
                                        observation_epit[a] = torch.unsqueeze(
                                            input=observation_epit[a], dim=state_batch_axis)
                                elif self.is_recurrent and is_without_state_time_axis:
                                    observation_epit[a] = torch.unsqueeze(
                                        input=observation_epit[a], dim=state_time_axis)

                    state_epit = copy.deepcopy(observation_epit)

                    if self.is_recurrent:
                        if phase_name_p == 'training':
                            memory.init_episode_vars(n_agents=environment[phase_name_p].n_agents)

                        hc_epit = [None for a in range(0, environment[phase_name_p].n_agents, 1)]  # type: list | None

                        values_actions_epit = [
                            None for a in range(0, environment[phase_name_p].n_agents, 1)]  # type: list
                        for a in range(0, environment[phase_name_p].n_agents, 1):
                            if state_epit[a] is not None:
                                values_actions_epit[a], hc_epit[a] = self.model(x=state_epit[a], h=hc_epit[a])
                    else:
                        hc_epit = None

                        values_actions_epit = [
                            None if state_epit[a] is None else self.model(x=state_epit[a])
                            for a in range(0, environment[phase_name_p].n_agents, 1)]  # type: list

                    cum_rewards_epi = [0.0 for a in range(0, environment[phase_name_p].n_agents, 1)]  # type: list
                    time_lengths_epi = [0 for a in range(0, environment[phase_name_p].n_agents, 1)]  # type: list

                    obs_iterator = cp_rl_utilities.ObservationsIterator(T=T[phase_name_p])

                    for t in obs_iterator:

                        if phase_name_p == 'training':
                            action_epit = [
                                None if values_actions_epit[a] is None
                                else self.sample_action(values_actions=values_actions_epit[a], epsilon=epsilon)
                                for a in range(0, environment[phase_name_p].n_agents, 1)]  # type: list
                        elif phase_name_p == 'validation':
                            action_epit = [
                                None if values_actions_epit[a] is None
                                else self.q_values_to_actions(values_actions=values_actions_epit[a])
                                for a in range(0, environment[phase_name_p].n_agents, 1)]  # type: list
                        else:
                            raise ValueError('phase_name_p')

                        delta_epit = [
                            None if action_epit[a] is None else self.compute_deltas(action_epit[a])
                            for a in range(0, environment[phase_name_p].n_agents, 1)]  # type: list

                        next_observation_epit, reward_epit, obs_iterator.not_over = copy.deepcopy(
                            environment[phase_name_p].step(deltas=delta_epit))

                        for a in range(0, environment[phase_name_p].n_agents, 1):
                            if state_epit[a] is not None:
                                time_lengths_epi[a] += 1
                                if isinstance(reward_epit[a], (torch.Tensor, np.ndarray)):
                                    cum_rewards_epi[a] += reward_epit[a].item()
                                else:
                                    cum_rewards_epi[a] += reward_epit[a]

                        if is_without_state_batch_axis or (self.is_recurrent and is_without_state_time_axis):
                            for a in range(0, environment[phase_name_p].n_agents, 1):
                                if next_observation_epit[a] is not None:
                                    if is_without_state_batch_axis:
                                        if self.is_recurrent and is_without_state_time_axis:
                                            next_observation_epit[a] = cp_unsqueeze(
                                                data=next_observation_epit[a], dims=sorted_state_bt_axes, sort=False)
                                        else:
                                            next_observation_epit[a] = torch.unsqueeze(
                                                input=next_observation_epit[a], dim=state_batch_axis)
                                    elif self.is_recurrent and is_without_state_time_axis:
                                        next_observation_epit[a] = torch.unsqueeze(
                                            input=next_observation_epit[a], dim=state_time_axis)

                        next_observation_with_zeros_epit = [
                            None if observation_epit[a] is None
                            else torch.zeros(
                                size=observation_epit[a].shape, device=observation_epit[a].device,
                                dtype=observation_epit[a].dtype, requires_grad=False)
                            if next_observation_epit[a] is None else next_observation_epit[a]
                            for a in range(0, environment[phase_name_p].n_agents, 1)]

                        next_state_epit = copy.deepcopy(next_observation_with_zeros_epit)

                        if self.is_recurrent:
                            next_values_actions_epit = [
                                None for a in range(0, environment[phase_name_p].n_agents, 1)]  # type: list
                            for a in range(0, environment[phase_name_p].n_agents, 1):
                                if next_state_epit[a] is not None:
                                    next_values_actions_epit[a], hc_epit[a] = self.model(
                                        x=next_state_epit[a], h=hc_epit[a])
                        else:
                            next_values_actions_epit = [
                                None if next_state_epit[a] is None else self.model(x=next_state_epit[a])
                                for a in range(0, environment[phase_name_p].n_agents, 1)]  # type: list

                        values_selected_actions_epit = torch.cat([
                            self.gather_values_selected_actions(
                                values_actions=values_actions_epit[a], actions=action_epit[a])
                            for a in range(0, environment[phase_name_p].n_agents, 1)
                            if values_actions_epit[a] is not None],
                            dim=action_batch_axis)

                        expected_values_actions_epit = torch.cat([
                            self.compute_expected_values_actions(
                                next_values_actions=next_values_actions_epit[a], rewards=reward_epit[a])
                            for a in range(0, environment[phase_name_p].n_agents, 1)
                            if next_values_actions_epit[a] is not None],
                            dim=action_batch_axis)

                        value_action_losses_epit = self.compute_value_action_losses(
                            values_selected_actions=values_selected_actions_epit,
                            expected_values_actions=expected_values_actions_epit)

                        scaled_value_action_loss_epit = self.reduce_value_action_losses(
                            value_action_losses=value_action_losses_epit, axes_not_included=None,
                            scaled=True, loss_scales_actors=None, format_scales=False)

                        n_selected_actions_epit = self.compute_n_selected_actions(
                            selected_actions=value_action_losses_epit, axes_not_included=None)

                        running_n_selected_actions_ep += n_selected_actions_epit
                        running_loss_ep += (scaled_value_action_loss_epit.item() * n_selected_actions_epit)

                        if phase_name_p == 'training':
                            memory.add(states=state_epit, actions=action_epit, rewards=reward_epit,
                                       next_states=next_state_epit)

                        observation_epit = copy.deepcopy(next_observation_epit)
                        state_epit = copy.deepcopy(observation_epit)

                        values_actions_epit = [
                            None if state_epit[a] is None else copy.deepcopy(next_values_actions_epit[a])
                            for a in range(0, environment[phase_name_p].n_agents, 1)]  # type: list

                    n_episodes_epi = sum([1 for len_i in time_lengths_epi if len_i > 0])

                    running_n_episodes_ep += n_episodes_epi
                    running_sum_time_lengths_ep = sum(time_lengths_epi, start=running_sum_time_lengths_ep)

                    running_sum_scores_ep = sum(environment[phase_name_p].get_scores(), start=running_sum_scores_ep)
                    running_sum_cum_rewards_ep = sum(cum_rewards_epi, start=running_sum_cum_rewards_ep)

                    i += n_episodes_epi
                    j += n_episodes_epi

                    if phase_name_p == 'training':
                        if self.is_recurrent:
                            memory.add_episodes()
                            memory_tot_episodes = memory.get_tot_episodes()
                            memory_tot_time_points = memory.get_tot_observations()
                            memory_has_enough_samples_for_optim = (
                                    (memory_tot_episodes >= min_n_episodes_for_optim) and
                                    (memory_tot_time_points >= min_n_samples_for_optim) and
                                    (memory_tot_episodes >= batch_size_of_train))
                        else:
                            memory_tot_time_points = memory.get_tot_observations()
                            memory_has_enough_samples_for_optim = (
                                    (j >= min_n_episodes_for_optim) and
                                    (memory_tot_time_points >= min_n_samples_for_optim) and
                                    (memory_tot_time_points >= batch_size_of_train))

                        if memory_has_enough_samples_for_optim:

                            samples_epb = memory.sample()
                            states_epb = samples_epb['states']
                            actions_epb = samples_epb['actions']
                            rewards_epb = samples_epb['rewards']
                            next_states_epb = samples_epb['next_states']

                            if self.is_recurrent:
                                next_values_actions_epb, next_hc_epb = self.model(x=next_states_epb, h=None)
                            else:
                                next_values_actions_epb = self.model(x=next_states_epb)

                            expected_values_actions_epb = self.compute_expected_values_actions(
                                next_values_actions=next_values_actions_epb, rewards=rewards_epb)

                            optimizer.zero_grad()

                            # forward
                            # track history
                            torch.set_grad_enabled(True)
                            self.model.unfreeze()

                            if self.is_recurrent:
                                values_actions_epb, hc_epb = self.model(x=states_epb, h=None)
                            else:
                                values_actions_epb = self.model(x=states_epb)

                            values_selected_actions_epb = self.gather_values_selected_actions(
                                values_actions=values_actions_epb, actions=actions_epb)

                            value_action_losses_epb = self.compute_value_action_losses(
                                values_selected_actions=values_selected_actions_epb,
                                expected_values_actions=expected_values_actions_epb)

                            scaled_value_action_loss_epb = self.reduce_value_action_losses(
                                value_action_losses=value_action_losses_epb, axes_not_included=None,
                                scaled=True, loss_scales_actors=None, format_scales=False)

                            scaled_value_action_loss_epb.backward()
                            optimizer.step()

                            self.model.freeze()
                            torch.set_grad_enabled(False)

                            if self.is_recurrent:
                                s += (states_epb.shape[state_batch_axis] * states_epb.shape[state_time_axis])
                            else:
                                s += states_epb.shape[state_batch_axis]

                            b += 1
                            j = 0

                            are_more_episodes_needed = s < tot_observations_per_train_phase

                    elif phase_name_p == 'validation':
                        are_more_episodes_needed = i < n_episodes_per_val_phase
                    else:
                        raise ValueError('phase_name_p')

                time_length_per_episode_ep = running_sum_time_lengths_ep / running_n_episodes_ep
                score_per_episode_ep = running_sum_scores_ep / running_n_episodes_ep
                cum_reward_per_episode_ep = running_sum_cum_rewards_ep / running_n_episodes_ep

                reward_per_observation_ep = running_sum_cum_rewards_ep / running_sum_time_lengths_ep
                loss_ep = running_loss_ep / running_n_selected_actions_ep

                stats['lines'][e][stats['headers']['{phase:s}_Time_Length_Per_Episode'.format(
                    phase=phase_title_p)]] = time_length_per_episode_ep

                stats['lines'][e][stats['headers']['{phase:s}_Scores_Per_Episode'.format(
                    phase=phase_title_p)]] = score_per_episode_ep

                stats['lines'][e][stats['headers']['{phase:s}_Cumulative_Reward_Per_Episode'.format(
                    phase=phase_title_p)]] = cum_reward_per_episode_ep

                stats['lines'][e][stats['headers']['{phase:s}_Reward_Per_Observation'.format(
                    phase=phase_title_p)]] = reward_per_observation_ep

                stats['lines'][e][stats['headers']['{phase:s}_Loss'.format(phase=phase_title_p)]] = loss_ep

                environment[phase_name_p].step_difficulty()

                if phase_name_p == 'training':
                    epsilon = epsilon + epsilon_step
                    ind_bool = epsilon < epsilon_end
                    if np.any(ind_bool):
                        epsilon[ind_bool] = copy.deepcopy(epsilon_end[ind_bool])
                elif phase_name_p == 'validation':
                    model_dict = copy.deepcopy(self.model.state_dict())
                    if os.path.isfile(directory_model_at_last_epoch):
                        os.remove(directory_model_at_last_epoch)
                    torch.save(model_dict, directory_model_at_last_epoch)

                    is_successful_epoch = False

                    if score_per_episode_ep >= highest_score_per_episode:
                        highest_score_per_episode = score_per_episode_ep
                        highest_score_per_episode_str = cp_strings.format_float_to_str(
                            highest_score_per_episode, n_decimals=n_decimals_for_printing)

                        stats['lines'][e][stats['headers']['Is_Highest_Validation_Scores_Per_Episode']] = 1
                        is_successful_epoch = True

                        if os.path.isfile(directory_model_with_highest_score_per_episode):
                            os.remove(directory_model_with_highest_score_per_episode)
                        torch.save(model_dict, directory_model_with_highest_score_per_episode)
                    else:
                        stats['lines'][e][stats['headers']['Is_Highest_Validation_Scores_Per_Episode']] = 0

                    stats['lines'][e][stats['headers'][
                        'Highest_Validation_Scores_Per_Episode']] = highest_score_per_episode

                    if cum_reward_per_episode_ep >= highest_cum_reward_per_episode:
                        highest_cum_reward_per_episode = cum_reward_per_episode_ep
                        highest_cum_reward_per_episode_str = cp_strings.format_float_to_str(
                            highest_cum_reward_per_episode, n_decimals=n_decimals_for_printing)

                        stats['lines'][e][stats['headers']['Is_Highest_Validation_Cumulative_Reward_Per_Episode']] = 1
                        is_successful_epoch = True

                        if os.path.isfile(directory_model_with_highest_cum_reward_per_episode):
                            os.remove(directory_model_with_highest_cum_reward_per_episode)
                        torch.save(model_dict, directory_model_with_highest_cum_reward_per_episode)
                    else:
                        stats['lines'][e][stats['headers']['Is_Highest_Validation_Cumulative_Reward_Per_Episode']] = 0

                    stats['lines'][e][stats['headers'][
                        'Highest_Validation_Cumulative_Reward_Per_Episode']] = highest_cum_reward_per_episode

                    if reward_per_observation_ep >= highest_reward_per_obs:
                        highest_reward_per_obs = reward_per_observation_ep
                        highest_reward_per_obs_str = cp_strings.format_float_to_str(
                            highest_reward_per_obs, n_decimals=n_decimals_for_printing)

                        stats['lines'][e][stats['headers']['Is_Highest_Validation_Reward_Per_Observation']] = 1
                        is_successful_epoch = True

                        if os.path.isfile(directory_model_with_highest_reward_per_obs):
                            os.remove(directory_model_with_highest_reward_per_obs)
                        torch.save(model_dict, directory_model_with_highest_reward_per_obs)
                    else:
                        stats['lines'][e][stats['headers']['Is_Highest_Validation_Reward_Per_Observation']] = 0

                    stats['lines'][e][stats['headers'][
                        'Highest_Validation_Reward_Per_Observation']] = highest_reward_per_obs

                    if loss_ep <= lowest_loss:

                        lowest_loss = loss_ep
                        lowest_loss_str = cp_strings.format_float_to_str(
                            lowest_loss, n_decimals=n_decimals_for_printing)

                        stats['lines'][e][stats['headers']['Is_Lowest_Validation_Loss']] = 1
                        is_successful_epoch = True

                        if os.path.isfile(directory_model_with_lowest_loss):
                            os.remove(directory_model_with_lowest_loss)
                        torch.save(model_dict, directory_model_with_lowest_loss)
                    else:
                        stats['lines'][e][stats['headers']['Is_Lowest_Validation_Loss']] = 0

                    stats['lines'][e][stats['headers']['Lowest_Validation_Loss']] = lowest_loss

                    epochs.count_unsuccessful_epochs(is_successful_epoch=is_successful_epoch)
                    stats['lines'][e][stats['headers']['Unsuccessful_Epochs']] = epochs.u

                    if os.path.isfile(directory_stats):
                        os.remove(directory_stats)
                    cp_txt.lines_to_csv_file(stats['lines'], directory_stats, stats['headers'])
                else:
                    raise ValueError('phase_name_p')

                time_length_per_episode_str_ep = cp_strings.format_float_to_str(
                    time_length_per_episode_ep, n_decimals=n_decimals_for_printing)

                score_per_episode_str_ep = cp_strings.format_float_to_str(
                    score_per_episode_ep, n_decimals=n_decimals_for_printing)

                cum_reward_per_episode_str_ep = cp_strings.format_float_to_str(
                    cum_reward_per_episode_ep, n_decimals=n_decimals_for_printing)

                reward_per_observation_str_ep = cp_strings.format_float_to_str(
                    reward_per_observation_ep, n_decimals=n_decimals_for_printing)

                loss_str_ep = cp_strings.format_float_to_str(loss_ep, n_decimals=n_decimals_for_printing)

                print(
                    'Epoch: {e:d}. Phase: {phase:s}. Time Length per Episode: {ep_time:s}. '
                    'Score per Episode {ep_score:s}. Cumulative Reward per Episode {ep_reward:s}. '
                    'Reward per Observation {ob_reward:s}. Loss per Observation: {ob_loss:s}.'.format(
                        e=e, phase=phase_title_p, ep_time=time_length_per_episode_str_ep,
                        ep_score=score_per_episode_str_ep, ep_reward=cum_reward_per_episode_str_ep,
                        ob_reward=reward_per_observation_str_ep, ob_loss=loss_str_ep))

            print('Epoch {e:d} - Unsuccessful Epochs {u:d}.'.format(e=e, u=epochs.u))

            print(dashes)

        print()

        n_completed_epochs = E = e + 1

        time_training = cp_timer.get_delta_time_total()

        print('Training completed in {d} days {h} hours {m} minutes {s} seconds'.format(
            d=time_training.days, h=time_training.hours,
            m=time_training.minutes, s=time_training.seconds))
        print('Number of Epochs: {E:d}'.format(E=E))

        print('Highest Score per Episode: {:s}'.format(highest_score_per_episode_str))
        print('Highest Cumulative Reward per Episode: {:s}'.format(highest_cum_reward_per_episode_str))
        print('Highest Reward per Observation: {:s}'.format(highest_reward_per_obs_str))
        print('Lowest Loss: {:s}'.format(lowest_loss_str))

        return self.model


class _Memory:
    def __init__(
            self, capacity, add_timepoints_as, batch_size,
            is_without_state_batch_axis, is_without_reward_batch_axis,
            state_batch_axis, action_batch_axis, reward_batch_axis):

        """


        :type capacity: int

        :param add_timepoints_as: "s" for single observation, "l" for list or tuple of observation, "t" for tensor or
            array of some batched observations
        :type add_timepoints_as: str

        :type batch_size: int

        :type is_without_state_batch_axis: bool

        :type is_without_reward_batch_axis: bool

        :type state_batch_axis: int

        :type action_batch_axis: int

        :type reward_batch_axis: int
        """

        self.states = []
        self.actions = []
        self.rewards = []
        self.next_states = []

        if isinstance(capacity, int):
            self.capacity = capacity
        else:
            raise TypeError('capacity')

        if isinstance(batch_size, int):
            self.batch_size = batch_size
        else:
            raise TypeError('batch_size')

        if isinstance(state_batch_axis, int):
            self.state_batch_axis = state_batch_axis
        else:
            raise TypeError('state_batch_axis')

        if isinstance(action_batch_axis, int):
            self.action_batch_axis = action_batch_axis
        else:
            raise TypeError('action_batch_axis')

        if isinstance(reward_batch_axis, int):
            self.reward_batch_axis = reward_batch_axis
        else:
            raise TypeError('reward_batch_axis')

        if isinstance(add_timepoints_as, str):
            self.add_timepoints_as = add_timepoints_as.lower()
            if self.add_timepoints_as in 'slt':
                pass
            else:
                raise ValueError('add_timepoints_as')
        else:
            raise TypeError('add_timepoints_as')

        if isinstance(is_without_state_batch_axis, bool):
            self.is_without_state_batch_axis = is_without_state_batch_axis
        else:
            raise TypeError('is_without_state_batch_axis')

        if isinstance(is_without_reward_batch_axis, bool):
            self.is_without_reward_batch_axis = is_without_reward_batch_axis
        else:
            raise TypeError('is_without_reward_batch_axis')

        self.rng = np.random.default_rng()

        self.current_len = 0

    def __len__(self) -> int:
        self.current_len = len(self.states)
        return self.current_len

    def add(self, states, actions, rewards, next_states):
        return None

    def add_list(self, states, actions, rewards, next_states):
        return None

    def add_batch(self, states, actions, rewards, next_states):

        self.add_list(
            states=self.unbatch_states(states=states), actions=self.unbatch_actions(actions=actions),
            rewards=self.unbatch_rewards(rewards=rewards), next_states=self.unbatch_states(states=next_states))

        return None

    def unbatch_states(self, states):
        if self.is_without_state_batch_axis:
            raise ValueError(type(self).__name__ + '.is_without_state_batch_axis')
        else:
            return self._unbatch(samples=states, batch_axis=self.state_batch_axis)

    def unbatch_actions(self, actions):
        # if self.is_without_action_batch_axis:
        #     raise ValueError(type(self).__name__ + '.is_without_action_batch_axis')
        # else:
        #     return self._unbatch(samples=actions, batch_axis=self.action_batch_axis)
        return self._unbatch(samples=actions, batch_axis=self.action_batch_axis)

    def unbatch_rewards(self, rewards):
        if self.is_without_reward_batch_axis:
            raise ValueError(type(self).__name__ + '.is_without_reward_batch_axis')
        else:
            return self._unbatch(samples=rewards, batch_axis=self.reward_batch_axis)

    def _unbatch(self, samples, batch_axis):

        n_new_samples = samples.shape[batch_axis]
        new_samples = [None for i in range(0, n_new_samples, 1)]
        idx = [slice(0, samples.shape[a], 1) for a in range(0, samples.ndim, 1)]
        for i in range(0, n_new_samples, 1):
            idx[batch_axis] = slice(i, i + 1, 1)
            new_samples[i] = samples[tuple(idx)]
        return samples


class TimePointMemory(_Memory):
    """A simple replay buffer."""

    def __init__(
            self, capacity, add_timepoints_as, batch_size,
            is_without_state_batch_axis, is_without_reward_batch_axis,
            state_batch_axis, action_batch_axis, reward_batch_axis):

        _Memory.__init__(
            self=self, capacity=capacity, add_timepoints_as=add_timepoints_as, batch_size=batch_size,
            is_without_state_batch_axis=is_without_state_batch_axis,
            is_without_reward_batch_axis=is_without_reward_batch_axis,
            state_batch_axis=state_batch_axis, action_batch_axis=action_batch_axis, reward_batch_axis=reward_batch_axis)

        if self.add_timepoints_as == 's':
            self.add = self.add_element
        elif self.add_timepoints_as == 'l':
            self.add = self.add_list
        elif self.add_timepoints_as == 't':
            self.add = self.add_batch
        else:
            raise ValueError('add_timepoints_as')

    def clear(self):
        self.__init__(
            capacity=self.capacity, add_timepoints_as=self.add_timepoints_as, batch_size=self.batch_size,
            is_without_state_batch_axis=self.is_without_state_batch_axis,
            is_without_reward_batch_axis=self.is_without_reward_batch_axis,
            state_batch_axis=self.state_batch_axis, action_batch_axis=self.action_batch_axis,
            reward_batch_axis=self.reward_batch_axis)
        return None

    def get_tot_observations(self):
        return len(self)

    def add_element(self, states, actions, rewards, next_states):

        if states is not None:

            if self.is_without_state_batch_axis:
                self.states.append(torch.unsqueeze(input=states, dim=self.state_batch_axis))
                if next_states is None:
                    self.next_states.append(None)
                else:
                    self.next_states.append(torch.unsqueeze(input=next_states, dim=self.state_batch_axis))
            else:
                self.states.append(states)
                self.next_states.append(next_states)

            # if self.is_without_action_batch_axis:
            #     self.actions.append(torch.unsqueeze(input=actions, dim=self.action_batch_axis))
            # else:
            #     self.actions.append(actions)
            self.actions.append(actions)

            if not isinstance(rewards, torch.Tensor):
                rewards_f = torch.tensor(data=rewards, dtype=states.dtype, device=states.device, requires_grad=False)
            else:
                rewards_f = rewards

            if self.is_without_reward_batch_axis:
                self.rewards.append(torch.unsqueeze(input=rewards_f, dim=self.reward_batch_axis))
            else:
                self.rewards.append(rewards_f)

            self.current_len = len(self)
            self.remove_extras()

        return None

    def add_list(self, states, actions, rewards, next_states):

        for a in range(0, len(states), 1):
            self.add_element(states=states[a], actions=actions[a], rewards=rewards[a], next_states=next_states[a])
        return None

    def remove_extras(self):

        n_extras = self.current_len - self.capacity

        if n_extras > 0:
            self.states = self.states[slice(n_extras, self.current_len, 1)]

            self.actions = self.actions[slice(n_extras, self.current_len, 1)]

            self.rewards = self.rewards[slice(n_extras, self.current_len, 1)]

            self.next_states = self.next_states[slice(n_extras, self.current_len, 1)]

            self.current_len = len(self)

        return None

    def sample(self):

        tot_time_points = self.get_tot_observations()

        if self.batch_size > tot_time_points:
            raise ValueError('self.batch_size > tot_time_points')

        indexes = self.rng.choice(
            a=tot_time_points, size=tuple([self.batch_size]), replace=False, p=None, axis=0, shuffle=True).tolist()

        states = []
        actions = []
        rewards = []
        next_states = []
        for i in range(0, self.batch_size, 1):

            states.append(self.states[indexes[i]])
            actions.append(self.actions[indexes[i]])
            rewards.append(self.rewards[indexes[i]])
            next_states.append(self.next_states[indexes[i]])

            # index = np.random.randint(low=0, high=self.current_len, size=None, dtype='i').tolist()
            # states.append(self.states.pop(index))
            # actions.append(self.actions.pop(index))
            # rewards.append(self.rewards.pop(index))
            # next_states.append(self.next_states.pop(index))
            # self.current_len = len(self)

            if next_states[i] is None:
                next_states[i] = torch.zeros(
                    size=states[i].shape, device=states[i].device, dtype=states[i].dtype, requires_grad=False)

        states = torch.cat(states, dim=self.state_batch_axis)
        next_states = torch.cat(next_states, dim=self.state_batch_axis)
        actions = torch.cat(actions, dim=self.action_batch_axis)
        rewards = torch.cat(rewards, dim=self.reward_batch_axis)

        return dict(states=states, actions=actions, rewards=rewards, next_states=next_states)


class EpisodeMemory(_Memory):
    """A simple replay buffer for recurrent models."""

    def __init__(
            self, capacity, add_timepoints_as, batch_size, time_size,
            is_without_state_batch_axis, is_without_state_time_axis,
            is_without_reward_batch_axis, is_without_reward_time_axis,
            state_batch_axis, state_time_axis,
            action_batch_axis, action_time_axis,
            reward_batch_axis, reward_time_axis,
            prob_last=0.0):

        """

        :type capacity: int

        :param add_timepoints_as: "s" for single observation, "l" for list or tuple of observation, "t" for tensor or
            array of some batched observations
        :type add_timepoints_as: str

        :type batch_size: int

        :type time_size: int

        :type is_without_state_batch_axis: bool

        :type is_without_state_time_axis: bool

        :type is_without_reward_batch_axis: bool

        :type is_without_reward_time_axis: bool

        :type state_batch_axis: int

        :type state_time_axis: int

        :type action_batch_axis: int

        :type action_time_axis: int

        :type reward_batch_axis: int

        :type reward_time_axis: int

        :type prob_last: float | int | None
        """

        _Memory.__init__(
            self=self, capacity=capacity, add_timepoints_as=add_timepoints_as, batch_size=batch_size,
            is_without_state_batch_axis=is_without_state_batch_axis,
            is_without_reward_batch_axis=is_without_reward_batch_axis,
            state_batch_axis=state_batch_axis, action_batch_axis=action_batch_axis, reward_batch_axis=reward_batch_axis)

        self.n_agents = None
        self.tmp_states = None
        self.tmp_actions = None
        self.tmp_rewards = None
        self.tmp_next_states = None

        if isinstance(time_size, int):
            self.time_size = time_size
        else:
            raise TypeError('time_size')

        if isinstance(state_time_axis, int):
            self.state_time_axis = state_time_axis
        else:
            raise TypeError('state_time_axis')

        if isinstance(action_time_axis, int):
            self.action_time_axis = action_time_axis
        else:
            raise TypeError('action_time_axis')

        if isinstance(reward_time_axis, int):
            self.reward_time_axis = reward_time_axis
        else:
            raise TypeError('reward_time_axis')

        if isinstance(is_without_state_time_axis, bool):
            self.is_without_state_time_axis = is_without_state_time_axis
        else:
            raise TypeError('is_without_state_time_axis')

        if isinstance(is_without_reward_time_axis, bool):
            self.is_without_reward_time_axis = is_without_reward_time_axis
        else:
            raise TypeError('is_without_reward_time_axis')

        if prob_last is None:
            self.prob_last = 0.0
        elif isinstance(prob_last, float):
            self.prob_last = prob_last
        elif isinstance(prob_last, int):
            self.prob_last = float(prob_last)
        else:
            raise TypeError('prob_last')

        if (self.prob_last < 0.0) or (self.prob_last > 1.0):
            raise ValueError('prob_last')

        self.is_prob_last_greater_than_0 = self.prob_last > 0.0

        if self.state_batch_axis < self.state_time_axis:
            self.is_batch_axis_first = True
        elif self.state_batch_axis > self.state_time_axis:
            self.is_batch_axis_first = False

        else:
            raise ValueError('state_batch_axis == state_time_axis')

        self.sorted_state_bt_axes = sorted([self.state_batch_axis, self.state_time_axis])
        self.sorted_action_bt_axes = sorted([self.action_batch_axis, self.action_time_axis])
        self.sorted_reward_bt_axes = sorted([self.reward_batch_axis, self.reward_time_axis])

        if self.add_timepoints_as == 's':
            self.add = self.add_element
        elif self.add_timepoints_as == 'l':
            self.add = self.add_list
        elif self.add_timepoints_as == 't':
            self.add = self.add_batch
        else:
            raise ValueError('add_timepoints_as')

    def clear(self):

        self.__init__(
            capacity=self.capacity, add_timepoints_as=self.add_timepoints_as,
            batch_size=self.batch_size, time_size=self.time_size,
            is_without_state_batch_axis=self.is_without_state_batch_axis,
            is_without_state_time_axis=self.is_without_state_time_axis,
            is_without_reward_batch_axis=self.is_without_reward_batch_axis,
            is_without_reward_time_axis=self.is_without_reward_time_axis,
            state_batch_axis=self.state_batch_axis, state_time_axis=self.state_time_axis,
            action_batch_axis=self.action_batch_axis, action_time_axis=self.action_time_axis,
            reward_batch_axis=self.reward_batch_axis, reward_time_axis=self.reward_time_axis)

        return None

    def __len__(self):
        self.current_len = sum(
            [self.states[i].shape[self.state_time_axis] for i in range(0, self.get_tot_episodes(), 1)])
        return self.current_len

    def get_tot_episodes(self):
        return len(self.states)

    def get_tot_observations(self):
        return len(self)

    def init_episode_vars(self, n_agents=None):

        if self.add_timepoints_as == 's':
            if n_agents is None or n_agents == 1:
                self.n_agents = 1
                self.tmp_states = []
                self.tmp_actions = []
                self.tmp_rewards = []
                self.tmp_next_states = []

            else:
                raise ValueError('add_timepoints_as and n_agents are not compatible')
        else:
            self.n_agents = n_agents
            self.tmp_states = [[] for a in range(0, self.n_agents, 1)]
            self.tmp_actions = [[] for a in range(0, self.n_agents, 1)]
            self.tmp_rewards = [[] for a in range(0, self.n_agents, 1)]
            self.tmp_next_states = [[] for a in range(0, self.n_agents, 1)]

        return None

    def add_element(self, states, actions, rewards, next_states, index=None):

        if states is not None:

            if self.is_without_state_batch_axis:
                if self.is_without_state_time_axis:
                    states_f = cp_unsqueeze(data=states, dims=self.sorted_state_bt_axes, sort=False)

                    if next_states is None:
                        next_states_f = torch.zeros(
                            size=states_f.shape, device=states_f.device, dtype=states_f.dtype, requires_grad=False)
                    else:
                        next_states_f = cp_unsqueeze(data=next_states, dims=self.sorted_state_bt_axes, sort=False)
                else:
                    states_f = torch.unsqueeze(input=states, dim=self.state_batch_axis)
                    if next_states is None:
                        next_states_f = torch.zeros(
                            size=states_f.shape, device=states_f.device, dtype=states_f.dtype, requires_grad=False)
                    else:
                        next_states_f = torch.unsqueeze(input=next_states, dim=self.state_batch_axis)
            else:
                if self.is_without_state_time_axis:
                    states_f = torch.unsqueeze(input=states, dim=self.state_time_axis)
                    if next_states is None:
                        next_states_f = torch.zeros(
                            size=states_f.shape, device=states_f.device, dtype=states_f.dtype, requires_grad=False)
                    else:
                        next_states_f = torch.unsqueeze(input=next_states, dim=self.state_time_axis)
                else:
                    states_f = states
                    if next_states is None:
                        next_states_f = torch.zeros(
                            size=states_f.shape, device=states_f.device, dtype=states_f.dtype, requires_grad=False)
                    else:
                        next_states_f = next_states

            # if self.is_without_action_batch_axis:
            #     if self.is_without_action_time_axis:
            #         actions_f = cp_unsqueeze(data=actions, dims=self.sorted_action_bt_axes, sort=False)
            #     else:
            #         actions_f = torch.unsqueeze(input=actions, dim=self.action_batch_axis)
            # else:
            #     if self.is_without_action_time_axis:
            #         actions_f = torch.unsqueeze(input=actions, dim=self.action_time_axis)
            #     else:
            #         actions_f = actions
            actions_f = actions

            if not isinstance(rewards, torch.Tensor):
                rewards_f = torch.tensor(
                    data=rewards, dtype=states_f.dtype, device=states_f.device, requires_grad=False)
            else:
                rewards_f = rewards

            if self.is_without_reward_batch_axis:
                if self.is_without_reward_time_axis:
                    rewards_f = cp_unsqueeze(data=rewards_f, dims=self.sorted_reward_bt_axes, sort=False)
                else:
                    rewards_f = torch.unsqueeze(input=rewards_f, dim=self.reward_batch_axis)
            else:
                if self.is_without_reward_time_axis:
                    rewards_f = torch.unsqueeze(input=rewards_f, dim=self.reward_time_axis)

            if self.add_timepoints_as == 's':
                self.tmp_states.append(states_f)
                self.tmp_actions.append(actions_f)
                self.tmp_rewards.append(rewards_f)
                self.tmp_next_states.append(next_states_f)
            else:
                self.tmp_states[index].append(states_f)
                self.tmp_actions[index].append(actions_f)
                self.tmp_rewards[index].append(rewards_f)
                self.tmp_next_states[index].append(next_states_f)

        return None

    def add_list(self, states, actions, rewards, next_states):

        for a in range(0, self.n_agents, 1):
            if states is not None:
                self.add_element(
                    states=states[a], actions=actions[a], rewards=rewards[a], next_states=next_states[a], index=a)
            #     self.tmp_states[a].append(states[a])
            #     self.tmp_actions[a].append(actions[a])
            #     self.tmp_rewards[a].append(rewards[a])
            #     self.tmp_next_states[a].append(next_states[a])
        return None

    def add_episodes(self):

        if self.add_timepoints_as == 's':
            # concatenate
            new_states = torch.cat(self.tmp_states, dim=self.state_time_axis)
            new_actions = torch.cat(self.tmp_actions, dim=self.action_time_axis)
            new_rewards = torch.cat(self.tmp_rewards, dim=self.reward_time_axis)
            new_next_states = torch.cat(self.tmp_next_states, dim=self.state_time_axis)

            # add
            self.states.append(new_states)
            self.actions.append(new_actions)
            self.rewards.append(new_rewards)
            self.next_states.append(new_next_states)
        else:
            # concatenate
            new_states = [
                torch.cat(self.tmp_states[a], dim=self.state_time_axis) for a in range(0, self.n_agents, 1)]
            new_actions = [
                torch.cat(self.tmp_actions[a], dim=self.action_time_axis) for a in range(0, self.n_agents, 1)]
            new_rewards = [
                torch.cat(self.tmp_rewards[a], dim=self.reward_time_axis) for a in range(0, self.n_agents, 1)]
            new_next_states = [
                torch.cat(self.tmp_next_states[a], dim=self.state_time_axis) for a in range(0, self.n_agents, 1)]

            # add
            self.states += new_states
            self.actions += new_actions
            self.rewards += new_rewards
            self.next_states += new_next_states

        self.tmp_states = None
        self.tmp_actions = None
        self.tmp_rewards = None
        self.tmp_next_states = None

        self.current_len = len(self)
        self.remove_extras()

    def remove_extras(self):

        self.current_len = len(self)
        n_extras = self.current_len - self.capacity

        if n_extras > 0:

            tot_episodes = self.get_tot_episodes()
            tot_episodes_minus_one = tot_episodes - 1

            cum_time_points = 0
            i = 0
            while (n_extras > cum_time_points) and ((tot_episodes_minus_one - i) > self.batch_size):
                cum_time_points += self.states[i].shape[self.state_time_axis]
                i += 1

            if cum_time_points > n_extras:
                i -= 1

            if i > 0:
                self.states = self.states[slice(i, tot_episodes, 1)]
                self.actions = self.actions[slice(i, tot_episodes, 1)]
                self.rewards = self.rewards[slice(i, tot_episodes, 1)]
                self.next_states = self.next_states[slice(i, tot_episodes, 1)]

                self.current_len = len(self)
            #     n_extras = self.current_len - self.capacity
            #
            # if n_extras > 0:
            #     state_indexes_0 = tuple([
            #         slice(n_extras, self.states[0].shape[d], 1) if d == self.state_time_axis else
            #         slice(0, self.states[0].shape[d], 1) for d in range(0, self.states[0].ndim, 1)])
            #
            #     action_indexes_0 = tuple([
            #         slice(n_extras, self.actions[0].shape[d], 1) if d == self.action_time_axis else
            #         slice(0, self.actions[0].shape[d], 1) for d in range(0, self.actions[0].ndim, 1)])
            #
            #     reward_indexes_0 = tuple([
            #         slice(n_extras, self.rewards[0].shape[d], 1) if d == self.reward_time_axis else
            #         slice(0, self.rewards[0].shape[d], 1) for d in range(0, self.rewards[0].ndim, 1)])
            #
            #     self.states[0] = self.states[0][state_indexes_0]
            #     self.actions[0] = self.actions[0][action_indexes_0]
            #     self.rewards[0] = self.rewards[0][reward_indexes_0]
            #     self.next_states[0] = self.next_states[0][state_indexes_0]
            #
            #     self.current_len = len(self)

        return None

    def sample(self):

        tot_episodes = self.get_tot_episodes()

        if self.batch_size > tot_episodes:
            raise ValueError('self.batch_size > self.get_tot_episodes()')

        # ep_indexes = np.random.permutation(x=tot_episodes).tolist()
        # ep_indexes = np.random.randint(low=0, high=tot_episodes, size=tuple([self.batch_size]), dtype='i').tolist()
        # ep_indexes = sorted(self.rng.choice(
        #     a=tot_episodes, size=tuple([self.batch_size]), replace=False, p=None, axis=0, shuffle=True).tolist())
        ep_indexes = self.rng.choice(
            a=tot_episodes, size=tuple([self.batch_size]), replace=False, p=None, axis=0, shuffle=True)

        min_time_lengths_b = min(
            [self.states[ep_indexes[i]].shape[self.state_time_axis] for i in range(0, self.batch_size, 1)])
        time_size_b = min(min_time_lengths_b, self.time_size)

        states = []
        actions = []
        rewards = []
        next_states = []
        for i in range(0, self.batch_size, 1):

            time_length_bi = self.states[ep_indexes[i]].shape[self.state_time_axis]

            if time_length_bi == time_size_b:
                states.append(self.states[ep_indexes[i]])
                actions.append(self.actions[ep_indexes[i]])
                rewards.append(self.rewards[ep_indexes[i]])
                next_states.append(self.next_states[ep_indexes[i]])

            elif time_length_bi > time_size_b:

                if self.is_prob_last_greater_than_0 and (random.random() < self.prob_last):
                    end_time_idx_i = time_length_bi
                    start_time_idx_i = end_time_idx_i - time_size_b
                else:
                    start_time_idx_i = np.random.randint(
                        low=0, high=time_length_bi - time_size_b + 1, size=None, dtype='i').item()
                    end_time_idx_i = start_time_idx_i + time_size_b

                state_indexes_i = tuple([
                    slice(start_time_idx_i, end_time_idx_i, 1) if d == self.state_time_axis else
                    slice(0, self.states[ep_indexes[i]].shape[d], 1) for d in range(0, self.states[ep_indexes[i]].ndim, 1)])

                action_indexes_i = tuple([
                    slice(start_time_idx_i, end_time_idx_i, 1) if d == self.action_time_axis else
                    slice(0, self.actions[ep_indexes[i]].shape[d], 1)
                    for d in range(0, self.actions[ep_indexes[i]].ndim, 1)])

                reward_indexes_i = tuple([
                    slice(start_time_idx_i, end_time_idx_i, 1) if d == self.reward_time_axis else
                    slice(0, self.rewards[ep_indexes[i]].shape[d], 1)
                    for d in range(0, self.rewards[ep_indexes[i]].ndim, 1)])

                states.append(self.states[ep_indexes[i]][state_indexes_i])
                actions.append(self.actions[ep_indexes[i]][action_indexes_i])
                rewards.append(self.rewards[ep_indexes[i]][reward_indexes_i])
                next_states.append(self.next_states[ep_indexes[i]][state_indexes_i])
            else:
                raise ValueError('time_length_bi < time_size_b')

            # states.append(self.states.pop(ep_indexes[i]))
            # actions.append(self.actions.pop(ep_indexes[i]))
            # rewards.append(self.rewards.pop(ep_indexes[i]))
            # next_states.append(self.next_states.pop(ep_indexes[i]))
            # self.current_len = len(self)

        states = torch.cat(states, dim=self.state_batch_axis)
        next_states = torch.cat(next_states, dim=self.state_batch_axis)
        actions = torch.cat(actions, dim=self.action_batch_axis)
        rewards = torch.cat(rewards, dim=self.reward_batch_axis)

        return dict(states=states, actions=actions, rewards=rewards, next_states=next_states)


class TimedDQNMethods(DQNMethods, TimedOutputMethods):

    def __init__(
            self,
            model, axis_time_outs, axis_batch_outs, axis_features_outs, axis_models_losses,
            possible_actions, action_selection_type='active', same_indexes_actions=None,
            gamma=0.999, reward_bias=0.0, loss_scales_actors=None):

        """

        :type axis_batch_outs: int
        :type axis_features_outs: int
        :type axis_models_losses: int
        :type possible_actions: list[list[int | float] | tuple[int | float]] |
                                tuple[list[int | float] | tuple[int | float]]
        :type action_selection_type: str
        :type same_indexes_actions: int | list | tuple | np.ndarray | torch.Tensor | None
        :type gamma: int | float
        :type reward_bias: int | float
        :type loss_scales_actors: list[int | float] | tuple[int | float] |
                                  np.ndarray[int | float] | torch.Tensor[int | float] | float | int | None
        """

        superclass = TimedDQNMethods
        try:
            # noinspection PyUnresolvedReferences
            self.superclasses_initiated
        except AttributeError:
            self.superclasses_initiated = []
        except NameError:
            self.superclasses_initiated = []

        if DQNMethods not in self.superclasses_initiated:
            DQNMethods.__init__(
                self=self, model=model, axis_features_outs=axis_features_outs, axis_models_losses=axis_models_losses,
                possible_actions=possible_actions, action_selection_type=action_selection_type,
                same_indexes_actions=same_indexes_actions,
                gamma=gamma, reward_bias=reward_bias, loss_scales_actors=loss_scales_actors)
            if DQNMethods not in self.superclasses_initiated:
                self.superclasses_initiated.append(DQNMethods)

        if TimedOutputMethods not in self.superclasses_initiated:
            TimedOutputMethods.__init__(
                self=self, axis_time_outs=axis_time_outs, axis_batch_outs=axis_batch_outs,
                axis_features_outs=axis_features_outs, axis_models_losses=axis_models_losses,
                M=self.A, loss_scales=self.loss_scales_actors)
            if TimedOutputMethods not in self.superclasses_initiated:
                self.superclasses_initiated.append(TimedOutputMethods)

        if superclass not in self.superclasses_initiated:
            self.superclasses_initiated.append(superclass)

    def remove_last_values_actions(self, values_actions: list):

        if self.axis_time_outs is None:
            raise ValueError('self.axis_time_outs')
        else:
            A = len(values_actions)
            values_actions_out = [None for a in range(0, A, 1)]

            for a in range(A):
                tuple_indexes_a = tuple(
                    [slice(0, values_actions[a].shape[d], 1)
                     if d != self.axis_time_outs
                     else slice(0, values_actions[a].shape[d] - 1, 1)
                     for d in range(0, values_actions[a].ndim, 1)])

                values_actions_out[a] = values_actions[a][tuple_indexes_a]

        return values_actions_out
