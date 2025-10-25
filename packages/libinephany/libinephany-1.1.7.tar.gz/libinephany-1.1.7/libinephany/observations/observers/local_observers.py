# ======================================================================================================================
#
# IMPORTS
#
# ======================================================================================================================

import math
from typing import Any

from libinephany.observations import observation_utils, statistic_trackers
from libinephany.observations.observation_utils import StatisticStorageTypes, compute_cdf_feature
from libinephany.observations.observers.base_observers import LocalObserver
from libinephany.observations.observers.global_observers.constants import LHOPT_CONSTANTS
from libinephany.pydantic_models.schemas.observation_models import ObservationInputs
from libinephany.pydantic_models.schemas.tensor_statistics import TensorStatistics
from libinephany.pydantic_models.states.hyperparameter_states import HyperparameterStates
from libinephany.utils import exceptions
from libinephany.utils.enums import ModuleTypes
from libinephany.utils.transforms import HyperparameterTransformType

# ======================================================================================================================
#
# CLASSES
#
# ======================================================================================================================


class FirstOrderGradients(LocalObserver):

    @property
    def requires_include_statistics(self) -> bool:
        """
        :return: Whether the observation requires include_statistics to be provided.
        """

        return True

    def _get_observation_format(self) -> StatisticStorageTypes:
        """
        :return: Format the observation returns data in. Must be one of the enum attributes in the StatisticStorageTypes
        enumeration class.
        """

        return StatisticStorageTypes.TENSOR_STATISTICS

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

        assert self.parameter_group_name is not None

        statistics = tracked_statistics[statistic_trackers.FirstOrderGradients.__name__]

        if self.parameter_group_name not in statistics:
            return TensorStatistics()

        agent_stats = statistics[self.parameter_group_name]

        return agent_stats

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {statistic_trackers.FirstOrderGradients.__name__: dict(include_statistics=self.include_statistics)}


class SecondOrderGradients(LocalObserver):

    def __init__(
        self,
        *,
        compute_hessian_diagonal: bool = False,
        **kwargs,
    ) -> None:
        """
        :param compute_hessian_diagonal: Whether to compute the Hessian diagonal to determine second order gradients
        or use the squared first order gradients as approximations in the same way Adam does.
        :param kwargs: Miscellaneous keyword arguments.
        """

        super().__init__(**kwargs)

        self.compute_hessian_diagonal = compute_hessian_diagonal

    @property
    def requires_include_statistics(self) -> bool:
        """
        :return: Whether the observation requires include_statistics to be provided.
        """

        return True

    def _get_observation_format(self) -> StatisticStorageTypes:
        """
        :return: Format the observation returns data in. Must be one of the enum attributes in the StatisticStorageTypes
        enumeration class.
        """

        return StatisticStorageTypes.TENSOR_STATISTICS

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

        assert self.parameter_group_name is not None

        statistics = tracked_statistics[statistic_trackers.SecondOrderGradients.__name__]

        if self.parameter_group_name not in statistics:
            return TensorStatistics()

        agent_stats = statistics[self.parameter_group_name]

        return agent_stats

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {
            statistic_trackers.SecondOrderGradients.__name__: dict(
                include_statistics=self.include_statistics, compute_hessian_diagonal=self.compute_hessian_diagonal
            )
        }


class Activations(LocalObserver):

    @property
    def requires_include_statistics(self) -> bool:
        """
        :return: Whether the observation requires include_statistics to be provided.
        """

        return True

    def _get_observation_format(self) -> StatisticStorageTypes:
        """
        :return: Format the observation returns data in. Must be one of the enum attributes in the StatisticStorageTypes
        enumeration class.
        """

        return StatisticStorageTypes.TENSOR_STATISTICS

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

        assert self.parameter_group_name is not None

        statistics = tracked_statistics[statistic_trackers.ActivationStatistics.__name__]

        if self.parameter_group_name not in statistics:
            return TensorStatistics()

        agent_stats = statistics[self.parameter_group_name]

        return agent_stats

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {statistic_trackers.ActivationStatistics.__name__: dict(include_statistics=self.include_statistics)}


class ParameterUpdates(LocalObserver):

    @property
    def requires_include_statistics(self) -> bool:
        """
        :return: Whether the observation requires include_statistics to be provided.
        """

        return True

    def _get_observation_format(self) -> StatisticStorageTypes:
        """
        :return: Format the observation returns data in. Must be one of the enum attributes in the StatisticStorageTypes
        enumeration class.
        """

        return StatisticStorageTypes.TENSOR_STATISTICS

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

        assert self.parameter_group_name is not None

        statistics = tracked_statistics[statistic_trackers.ParameterUpdateStatistics.__name__]

        if self.parameter_group_name not in statistics:
            return TensorStatistics()

        agent_stats = statistics[self.parameter_group_name]

        return agent_stats

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {statistic_trackers.ParameterUpdateStatistics.__name__: dict(include_statistics=self.include_statistics)}


class Parameters(LocalObserver):

    @property
    def requires_include_statistics(self) -> bool:
        """
        :return: Whether the observation requires include_statistics to be provided.
        """

        return True

    def _get_observation_format(self) -> StatisticStorageTypes:
        """
        :return: Format the observation returns data in. Must be one of the enum attributes in the StatisticStorageTypes
        enumeration class.
        """

        return StatisticStorageTypes.TENSOR_STATISTICS

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

        assert self.parameter_group_name is not None

        statistics = tracked_statistics[statistic_trackers.ParameterStatistics.__name__]

        if self.parameter_group_name not in statistics:
            return TensorStatistics()

        agent_stats = statistics[self.parameter_group_name]

        return agent_stats

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {statistic_trackers.ParameterStatistics.__name__: dict(include_statistics=self.include_statistics)}


class LAMBTrustRatio(LocalObserver):

    def __init__(
        self,
        *,
        use_log_transform: bool = False,
        **kwargs,
    ) -> None:
        """
        :param use_log_transform: Whether to transform the LAMB trust ratio by taking ln(1 + R).
        :param kwargs: Other observation keyword arguments.
        """

        super().__init__(**kwargs)

        self.use_log_transform = use_log_transform

    def _get_observation_format(self) -> StatisticStorageTypes:
        """
        :return: Format the observation returns data in. Must be one of the enum attributes in the StatisticStorageTypes
        enumeration class.
        """

        return StatisticStorageTypes.FLOAT

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

        assert self.parameter_group_name is not None

        statistics = tracked_statistics[statistic_trackers.LAMBTrustRatioStatistics.__name__]

        if self.parameter_group_name not in statistics:
            return 0.0

        agent_stats = statistics[self.parameter_group_name]

        return agent_stats

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {statistic_trackers.LAMBTrustRatioStatistics.__name__: dict(use_log_transform=self.use_log_transform)}


class ActionOneHot(LocalObserver):

    DISCRETE_INDEX = 0

    @property
    def is_discrete(self) -> bool:
        """
        :return: Whether the agent is using discrete actions.
        """

        valid_actions = self.number_of_discrete_actions is not None and self.number_of_discrete_actions > 0
        return self.action_scheme_index == self.DISCRETE_INDEX and valid_actions

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """

        if self.is_discrete:
            return self.number_of_discrete_actions

        return 0

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

        if not self.is_discrete:
            return []

        return observation_utils.create_one_hot_observation(
            vector_length=self.vector_length, one_hot_index=action_taken if action_taken is None else int(action_taken)
        )

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {}


class ActionSchemeOneHot(LocalObserver):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        exceptions.warn_once(
            f"{str(self.__class__.__name__)} is deprecated and will be removed in an upcoming release."
        )

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """

        return self.number_of_action_schemes

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
        assert self.parameter_group_name is not None

        return observation_utils.create_one_hot_observation(
            vector_length=self.vector_length, one_hot_index=self.action_scheme_index
        )

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {}


class PreviousActionRepresentation(LocalObserver):
    """
    Observer that returns the representation of the previous action taken by the agent.

    This observer tracks the previous action and returns it in an appropriate format:
    - For discrete actions: returns one-hot encoding of the previous action
    - For continuous actions: returns the previous action value directly
    """

    DISCRETE_INDEX = 0

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._previous_action: float | int | None = None

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """
        return self.number_of_discrete_actions if self.is_discrete else 1

    @property
    def is_discrete(self) -> bool:
        """
        :return: Whether the agent is using discrete actions.
        """

        valid_actions = self.number_of_discrete_actions is not None and self.number_of_discrete_actions > 0
        return self.action_scheme_index == self.DISCRETE_INDEX and valid_actions

    @property
    def can_inform(self) -> bool:
        """
        :return: Whether observations from the observer can be used in the agent info dictionary.
        """
        return False

    def _get_observation_format(self) -> StatisticStorageTypes:
        """
        :return: Format the observation returns data in.
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
        Returns the representation of the previous action.

        :param observation_inputs: Observation input metrics not calculated with statistic trackers.
        :param hyperparameter_states: HyperparameterStates that manages the hyperparameters.
        :param tracked_statistics: Dictionary mapping statistic tracker class names to dictionaries mapping module
        names to floats or TensorStatistic models.
        :param action_taken: Action taken by the agent this class instance is assigned to.
        :return: Previous action representation (one-hot vector for discrete, float for continuous).
        """

        if self._previous_action is None:
            result = [0.0] * self.vector_length
        else:
            if self.is_discrete:
                result = observation_utils.create_one_hot_observation(
                    vector_length=self.vector_length, one_hot_index=int(self._previous_action)
                )
            else:
                result = [float(self._previous_action)]

        self._previous_action = action_taken

        return result

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """
        return {}

    def reset(self) -> None:
        """Resets the observer by clearing the previous action."""
        self._previous_action = None


class DepthOneHot(LocalObserver):

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """

        return 3

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

        assert self.parameter_group_name is not None

        return observation_utils.create_one_hot_depth_encoding(
            agent_controlled_modules=list(self.observer_config.agent_modules.keys()),
            parameter_group_name=self.parameter_group_name,
        )

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {}


class ModuleTypeOneHot(LocalObserver):

    MODULE_TYPE_TO_IDX = {
        "convolutional": 0,
        "attention": 1,
        "linear": 2,
        "embedding": 3,
        "lstm": 4,
    }

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """

        return len(ModuleTypes)

    @property
    def can_inform(self) -> bool:
        """
        :return: Whether observations from the observer can be used in the agent info dictionary.
        """

        return False

    @property
    def can_standardize(self) -> bool:
        """
        :return: Whether the observation can be standardized.
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

        assert self.parameter_group_name is not None

        agent_modules = self.observer_config.agent_modules
        module_type = agent_modules[self.parameter_group_name]

        if module_type in {field.value for field in ModuleTypes}:
            one_hot_index = ModuleTypes.get_index(module_type)

        else:
            one_hot_index = None

        return observation_utils.create_one_hot_observation(
            vector_length=self.vector_length, one_hot_index=one_hot_index
        )

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {}


class CurrentHyperparameters(LocalObserver):

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
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """

        if self.include_hparams is None:
            raise ValueError(f"{self.__class__.__name__} must be provided with include_hparams.")

        available_hparams = HyperparameterStates.get_layerwise_hyperparameters()

        return len([hparam for hparam in available_hparams if hparam in self.include_hparams])

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

        assert self.parameter_group_name is not None

        current_internal_values = hyperparameter_states[self.parameter_group_name].get_current_internal_values(
            include_hparams=self.include_hparams
        )

        self._cached_observation = current_internal_values

        return list(current_internal_values.values())

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {}


class CurrentHyperparameterDeltas(LocalObserver):

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
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """

        if self.include_hparams is None:
            raise ValueError(f"{self.__class__.__name__} must be provided with include_hparams.")

        available_hparams = HyperparameterStates.get_layerwise_hyperparameters()

        return len([hparam for hparam in available_hparams if hparam in self.include_hparams])

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

        assert self.parameter_group_name is not None
        assert self.include_hparams is not None

        current_deltas = hyperparameter_states[self.parameter_group_name].get_current_deltas(
            include_hparams=self.include_hparams
        )

        self._cached_observation = current_deltas

        return list(current_deltas.values())

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {}


class HyperparameterTransformTypes(LocalObserver):

    TRANSFORM_TYPE_TO_IDX = dict(((s, i) for i, s in enumerate(HyperparameterTransformType)))

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
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """

        if self.include_hparams is None:
            raise ValueError(f"{self.__class__.__name__} must be provided with include_hparams.")

        available_hparams = HyperparameterStates.get_layerwise_hyperparameters()

        return len(HyperparameterTransformType) * len(
            [hparam for hparam in available_hparams if hparam in self.include_hparams]
        )

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

        assert self.parameter_group_name is not None
        assert self.include_hparams is not None

        parameter_group_hparams = hyperparameter_states[self.parameter_group_name]
        hyperparameter_transform_types = parameter_group_hparams.get_hyperparameter_transform_types(
            include_hparams=self.include_hparams
        )
        hyperparameter_transform_types_onehot_list = [
            observation_utils.create_one_hot_observation(
                vector_length=len(HyperparameterTransformType), one_hot_index=self.TRANSFORM_TYPE_TO_IDX[transform_type]
            )
            for transform_type in hyperparameter_transform_types.values()
        ]
        hyperparameter_transform_types_onehot_concat = observation_utils.concatenate_lists(
            hyperparameter_transform_types_onehot_list
        )

        return hyperparameter_transform_types_onehot_concat

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {}


class SinusoidalDepth(LocalObserver):

    def __init__(self, dimensionality: int = 16, **kwargs) -> None:
        """
        :param dimensionality:
        :param kwargs: Miscellaneous keyword arguments.
        """

        super().__init__(**kwargs)

        assert dimensionality % 2 == 0, "Dimensionality of a sinusoidal depth encoding must be even."

        self.dimensionality = dimensionality

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """

        return self.dimensionality

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

        assert self.parameter_group_name is not None

        return observation_utils.create_sinusoidal_depth_encoding(
            agent_controlled_modules=list(self.observer_config.agent_modules.keys()),
            parameter_group_name=self.parameter_group_name,
            dimensionality=self.dimensionality,
        )

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {}


class PercentageDepth(LocalObserver):

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

        return StatisticStorageTypes.FLOAT

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

        assert self.parameter_group_name is not None

        modules = list(self.observer_config.agent_modules.keys())
        depth = modules.index(self.parameter_group_name)

        return depth / len(modules)

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {}


class LogOfNoiseScaleObserver(LocalObserver):

    def __init__(
        self,
        *,
        decay_factor: float = LHOPT_CONSTANTS["DEFAULT_DECAY_FACTOR"],
        time_window: int = LHOPT_CONSTANTS["DEFAULT_TIME_WINDOW"],
        **kwargs,
    ) -> None:
        """
        :param decay_factor: Decay factor for CDF calculation in [1, 2.5, 5, 10, 20]
        :param time_window: Number of time steps to consider for CDF calculation
        :param include_statistics: List of statistics to include.
        or use the squared first order gradients as approximations in the same way Adam does.
        :param kwargs: Miscellaneous keyword arguments.
        """

        super().__init__(**kwargs)

        self.decay_factor = max(0.0, decay_factor)
        self.time_window = max(1, time_window)

        # Store time series data for CDF calculation
        self._time_series: list[tuple[float, float]] = []  # (time, value) pairs
        self._current_time: float = 0.0

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
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """
        return 2  # [log_noise_scale, cdf_feature]

    @property
    def requires_include_statistics(self) -> bool:
        """
        :return: Whether the observation requires include_statistics to be provided.
        """

        return True

    def _get_observation_format(self) -> StatisticStorageTypes:
        """
        :return: Format the observation returns data in. Must be one of the enum attributes in the StatisticStorageTypes
        enumeration class.
        """

        return StatisticStorageTypes.VECTOR

    def _update_time(self) -> None:
        """Update the current time counter."""
        self._current_time += 1.0

    def _compute_cdf_feature(self, value: float) -> float:
        """
        Compute CDF feature for the given value.
        training loss will be added to the time series after this call.
        :param value: The value to compute CDF feature for
        :return: CDF feature value
        """
        return compute_cdf_feature(value, self._time_series, self.decay_factor, self._current_time, self.time_window)

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

        statistics = tracked_statistics[statistic_trackers.LogOfNoiseScaleStatistics.__name__]
        raw_value = list(statistics.values())[0]  # type: ignore[list-item]

        assert isinstance(raw_value, float), f"Expected float, got {type(raw_value)}"  # to avoid type errors with mypy

        batch_size = hyperparameter_states.global_hparams.batch_size.external_value
        learning_rate = hyperparameter_states.parameter_group_hparams[
            self.parameter_group_name
        ].learning_rate.external_value

        log_b_over_epsilon = math.log(batch_size / learning_rate)
        log_noise_scale = raw_value + log_b_over_epsilon

        cdf_feature = self._compute_cdf_feature(log_noise_scale)  # type: ignore[arg-type]
        self._update_time()

        return [log_noise_scale, cdf_feature]  # type: ignore[list-item]

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {
            statistic_trackers.LogOfNoiseScaleStatistics.__name__: dict(
                include_statistics=self.include_statistics, sample_frequency=LHOPT_CONSTANTS["DEFAULT_SAMPLE_FREQUENCY"]
            )
        }

    def reset(self) -> None:
        """Reset the observer by clearing the time series."""
        self._time_series = []
        self._current_time = 0.0
