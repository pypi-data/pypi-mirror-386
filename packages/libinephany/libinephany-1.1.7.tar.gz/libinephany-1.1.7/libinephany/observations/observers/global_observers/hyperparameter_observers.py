# ======================================================================================================================
#
# IMPORTS
#
# ======================================================================================================================

import random
from typing import Any

from torch.optim import SGD, Adam, AdamW

from libinephany.observations import observation_utils
from libinephany.observations.observation_utils import StatisticStorageTypes
from libinephany.observations.observers.base_observers import GlobalObserver
from libinephany.observations.observers.global_observers.constants import LHOPT_CONSTANTS
from libinephany.pydantic_models.schemas.observation_models import ObservationInputs
from libinephany.pydantic_models.schemas.tensor_statistics import TensorStatistics
from libinephany.pydantic_models.states.hyperparameter_states import HyperparameterStates
from libinephany.utils.enums import ModelFamilies

# ======================================================================================================================
#
# CLASSES
#
# ======================================================================================================================


class InitialHyperparameters(GlobalObserver):

    def __init__(self, pad_with: float = 0.0, **kwargs) -> None:
        """
        :param kwargs: Miscellaneous keyword arguments.
        """

        super().__init__(**kwargs)

        self.pad_with = pad_with

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """

        if self.include_hparams is None:
            raise ValueError(f"{self.__class__.__name__} must be provided with include_hparams.")

        available_hparams = HyperparameterStates.get_all_hyperparameters()

        return len([hparam for hparam in available_hparams if hparam in self.include_hparams])

    @property
    def can_standardize(self) -> bool:
        """
        :return: Whether the observation can be standardized.
        """

        return False

    @property
    def can_inform(self) -> bool:
        """
        :return: Whether observations from the observer can be used in the agent info dictionary.
        """

        return False

    @property
    def requires_include_hparams(self) -> bool:
        """
        :return: Whether the observation requires include_hparams to be provided.
        """

        return True

    def _get_observation_format(self) -> StatisticStorageTypes:
        """
        :return: Format the observation returns data in. Must be one of the enum attributes in the StatisticStorageTypes
        enumeration class.
        """

        return StatisticStorageTypes.VECTOR

    def _observe(
        self,
        observation_inputs: ObservationInputs,
        hyperparameter_states: HyperparameterStates,
        tracked_statistics: dict[str, dict[str, float | TensorStatistics]],
        action_taken: float | int | None,
    ) -> float | int | list[int | float] | TensorStatistics:
        """
        :param observation_inputs: Observation input metrics not calculated with statistic trackers.
        :param hyperparameter_states: HyperparameterStates that manages the hyperparameters.
        :param tracked_statistics: Dictionary mapping statistic tracker class names to dictionaries mapping module
        names to floats or TensorStatistic models.
        :param action_taken: Action taken by the agent this class instance is assigned to.
        :return: Single float/int, list of floats/ints or TensorStatistics model to add to the observation vector.
        """

        assert self.include_hparams is not None

        initial_internal_values = hyperparameter_states.get_initial_internal_values(self.include_hparams)
        self._cached_observation = initial_internal_values
        initial_internal_values_list = [
            self.pad_with if initial_internal_value is None else initial_internal_value
            for hparam_name, initial_internal_value in initial_internal_values.items()
            if hparam_name in self.include_hparams
        ]
        return initial_internal_values_list

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {}


class OptimizerTypeOneHot(GlobalObserver):

    OPTIMS = [Adam.__name__, AdamW.__name__, SGD.__name__]

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """

        return len(self.OPTIMS)

    @property
    def can_inform(self) -> bool:
        """
        :return: Whether observations from the observer can be used in the agent info dictionary.
        """

        return False

    def _get_observation_format(self) -> StatisticStorageTypes:
        """
        :return: Format the observation returns data in. Must be one of the enum attributes in the StatisticStorageTypes
        enumeration class.
        """

        return StatisticStorageTypes.VECTOR

    def _observe(
        self,
        observation_inputs: ObservationInputs,
        hyperparameter_states: HyperparameterStates,
        tracked_statistics: dict[str, dict[str, float | TensorStatistics]],
        action_taken: float | int | None,
    ) -> float | int | list[int | float] | TensorStatistics:
        """
        :param observation_inputs: Observation input metrics not calculated with statistic trackers.
        :param hyperparameter_states: HyperparameterStates that manages the hyperparameters.
        :param tracked_statistics: Dictionary mapping statistic tracker class names to dictionaries mapping module
        names to floats or TensorStatistic models.
        :param action_taken: Action taken by the agent this class instance is assigned to.
        :return: Single float/int, list of floats/ints or TensorStatistics model to add to the observation vector.
        """

        optimizer_type = self.observer_config.optimizer_name

        if optimizer_type not in self.OPTIMS:
            index = None

        else:
            index = self.OPTIMS.index(optimizer_type)

        return observation_utils.create_one_hot_observation(vector_length=self.vector_length, one_hot_index=index)

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {}


class ModelFamilyOneHot(GlobalObserver):

    UNIT_EPISODE = "episode"
    UNIT_TIMESTEP = "timestep"

    def __init__(
        self,
        *,
        zero_vector_chance: float = 0.2,
        zero_vector_frequency_unit: str = "episode",
        **kwargs,
    ) -> None:
        """
        :param zero_vector_chance: Chance of the output vector being masked with zeros.
        :param zero_vector_frequency_unit: Unit of time to sample the zero vector.
        :param kwargs: Miscellaneous keyword arguments.
        """
        super().__init__(**kwargs)
        self.should_zero = False

        assert 0.0 <= zero_vector_chance < 1.0
        self.zero_vector_chance = zero_vector_chance
        self._sample_zero_vector()

        if zero_vector_frequency_unit not in [self.UNIT_EPISODE, self.UNIT_TIMESTEP]:
            raise ValueError(f"Unknown zero_vector_frequency_unit: {zero_vector_frequency_unit}")

        self.zero_vector_frequency_unit = zero_vector_frequency_unit
        self.family_vector = self._create_family_vector()

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """

        return len(ModelFamilies)

    @property
    def can_inform(self) -> bool:
        """
        :return: Whether observations from the observer can be used in the agent info dictionary.
        """

        return False

    def _get_observation_format(self) -> StatisticStorageTypes:
        """
        :return: Format the observation returns data in. Must be one of the enum attributes in the StatisticStorageTypes
        enumeration class.
        """

        return StatisticStorageTypes.VECTOR

    def _create_family_vector(self) -> list[float]:
        """
        :return: Creates and returns the model family one-hot vector.
        """

        family_name = self.observer_config.nn_family_name
        known_name = family_name in (family.value for family in ModelFamilies)

        if known_name:
            family_idx = ModelFamilies.get_index(family_name)

        else:
            family_idx = None

        return observation_utils.create_one_hot_observation(vector_length=self.vector_length, one_hot_index=family_idx)

    def _observe(
        self,
        observation_inputs: ObservationInputs,
        hyperparameter_states: HyperparameterStates,
        tracked_statistics: dict[str, dict[str, float | TensorStatistics]],
        action_taken: float | int | None,
    ) -> float | int | list[int | float] | TensorStatistics:
        """
        :param observation_inputs: Observation input metrics not calculated with statistic trackers.
        :param hyperparameter_states: HyperparameterStates that manages the hyperparameters.
        :param tracked_statistics: Dictionary mapping statistic tracker class names to dictionaries mapping module
        names to floats or TensorStatistic models.
        :param action_taken: Action taken by the agent this class instance is assigned to.
        :return: Single float/int, list of floats/ints or TensorStatistics model to add to the observation vector.
        """

        if not self.in_training_mode:
            return self.family_vector

        if self.zero_vector_frequency_unit == self.UNIT_TIMESTEP:
            self._sample_zero_vector()

        if self.should_zero:
            return [0.0 for _ in range(self.vector_length)]

        else:
            return self.family_vector

    def _sample_zero_vector(self) -> None:
        """
        Determines whether the output vector of this observer should be masked with zeros.
        """
        self.should_zero = random.choices([True, False], [self.zero_vector_chance, (1 - self.zero_vector_chance)])[0]

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {}

    def reset(self) -> None:
        """
        Resets the observer.
        """

        self._sample_zero_vector()


class LHOPTHyperparameterRatio(GlobalObserver):
    """
    LHOPT-specific hyperparameter ratio observer that returns the ratio of current value to initial value
    for all hyperparameter actions.

    This observer computes: current_value / initial_value for each hyperparameter,
    providing insights into how much hyperparameters have changed from their starting values.
    """

    def __init__(self, pad_with: float = 0.0, **kwargs) -> None:
        """
        :param include_hparams: Names of the hyperparameters to include in the initial values vector returned by
        this observation.
        :param kwargs: Miscellaneous keyword arguments.
        """

        super().__init__(**kwargs)

        self.pad_with = pad_with

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """

        if self.include_hparams is None:
            raise ValueError(f"{self.__class__.__name__} must be provided with include_hparams.")

        available_hparams = HyperparameterStates.get_all_hyperparameters()

        return len([hparam for hparam in available_hparams if hparam in self.include_hparams])

    @property
    def can_standardize(self) -> bool:
        """
        :return: Whether the observation can be standardized.
        """

        return False

    @property
    def can_inform(self) -> bool:
        """
        :return: Whether observations from the observer can be used in the agent info dictionary.
        """

        return False

    @property
    def requires_include_hparams(self) -> bool:
        """
        :return: Whether the observation requires include_hparams to be provided.
        """

        return True

    def _get_observation_format(self) -> StatisticStorageTypes:
        """
        :return: Format the observation returns data in. Must be one of the enum attributes in the StatisticStorageTypes
        enumeration class.
        """

        return StatisticStorageTypes.VECTOR

    def _observe(
        self,
        observation_inputs: ObservationInputs,
        hyperparameter_states: HyperparameterStates,
        tracked_statistics: dict[str, dict[str, float | TensorStatistics]],
        action_taken: float | int | None,
    ) -> float | int | list[int | float] | TensorStatistics:
        """
        :param observation_inputs: Observation input metrics not calculated with statistic trackers.
        :param hyperparameter_states: HyperparameterStates that manages the hyperparameters.
        :param tracked_statistics: Dictionary mapping statistic tracker class names to dictionaries mapping module
        names to floats or TensorStatistic models.
        :param action_taken: Action taken by the agent this class instance is assigned to.
        :return: Single float/int, list of floats/ints or TensorStatistics model to add to the observation vector.
        """

        assert self.include_hparams is not None

        # Get initial and current hyperparameter values
        initial_values = hyperparameter_states.get_initial_internal_values(self.include_hparams)
        initial_values = {
            hparam_name: self.pad_with if initial_value is None else initial_value
            for hparam_name, initial_value in initial_values.items()
            if hparam_name in self.include_hparams
        }
        current_values = hyperparameter_states.get_current_internal_values(self.include_hparams)
        current_values = {
            hparam_name: self.pad_with if current_value is None else current_value
            for hparam_name, current_value in current_values.items()
            if hparam_name in self.include_hparams
        }

        ratios = []

        for hparam_name in initial_values.keys():
            initial_value = initial_values[hparam_name]
            current_value = current_values[hparam_name]

            if initial_value is None or current_value is None:
                ratios.append(0.0)
                continue

            if abs(initial_value) < LHOPT_CONSTANTS["ZERO_DIVISION_TOLERANCE"]:
                ratios.append(0.0)
            else:
                ratios.append(current_value / initial_value)

        return ratios

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {}
