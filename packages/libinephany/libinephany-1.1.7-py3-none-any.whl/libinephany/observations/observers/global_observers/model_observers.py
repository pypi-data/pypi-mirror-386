# ======================================================================================================================
#
# IMPORTS
#
# ======================================================================================================================

import math
from typing import Any

from libinephany.observations import observation_utils, statistic_trackers
from libinephany.observations.observation_utils import StatisticStorageTypes
from libinephany.observations.observers.base_observers import GlobalObserver
from libinephany.observations.observers.global_observers.base_classes import LHOPTBaseObserver
from libinephany.observations.observers.global_observers.constants import LHOPT_CONSTANTS
from libinephany.pydantic_models.schemas.observation_models import ObservationInputs
from libinephany.pydantic_models.schemas.tensor_statistics import TensorStatistics
from libinephany.pydantic_models.states.hyperparameter_states import HyperparameterStates

# ======================================================================================================================
#
# CLASSES
#
# ======================================================================================================================


class GlobalActivations(GlobalObserver):

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

        statistics = tracked_statistics[statistic_trackers.ActivationStatistics.__name__]

        return observation_utils.average_tensor_statistics(tensor_statistics=list(statistics.values()))  # type: ignore

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {statistic_trackers.ActivationStatistics.__name__: dict(include_statistics=self.include_statistics)}


class GlobalParameterUpdates(GlobalObserver):

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

        statistics = tracked_statistics[statistic_trackers.ParameterUpdateStatistics.__name__]

        return observation_utils.average_tensor_statistics(tensor_statistics=list(statistics.values()))  # type: ignore

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {statistic_trackers.ParameterUpdateStatistics.__name__: dict(include_statistics=self.include_statistics)}


class GlobalParameters(GlobalObserver):

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

        statistics = tracked_statistics[statistic_trackers.ParameterStatistics.__name__]

        return observation_utils.average_tensor_statistics(tensor_statistics=list(statistics.values()))  # type: ignore

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {statistic_trackers.ParameterStatistics.__name__: dict(include_statistics=self.include_statistics)}


class GlobalLAMBTrustRatio(GlobalObserver):

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

        statistics = tracked_statistics[statistic_trackers.LAMBTrustRatioStatistics.__name__]

        return sum(statistics.values()) / len(statistics)  # type: ignore

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {statistic_trackers.LAMBTrustRatioStatistics.__name__: dict(use_log_transform=self.use_log_transform)}


class NumberOfParameters(GlobalObserver):

    def __init__(
        self,
        *,
        use_log_transform: bool = True,
        **kwargs,
    ) -> None:
        """
        :param use_log_transform: Whether to transform the return of the Observer by ln(1 + N).
        :param kwargs: Miscellaneous keyword arguments.
        """

        super().__init__(**kwargs)

        self.use_log_transform = use_log_transform

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

        count = list(tracked_statistics[statistic_trackers.NumberOfParameters.__name__].values())[0]

        if self.use_log_transform:
            return math.log(1 + count)  # type: ignore

        else:
            return count

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {statistic_trackers.NumberOfParameters.__name__: None}


class NumberOfLayers(GlobalObserver):

    def __init__(
        self,
        *,
        use_log_transform: bool = True,
        trainable_only: bool = False,
        **kwargs,
    ) -> None:
        """
        :param use_log_transform: Whether to transform the return of the Observer by ln(1 + N).
        :param trainable_only: Whether to only count trainable layers.
        :param kwargs: Miscellaneous keyword arguments.
        """

        super().__init__(**kwargs)

        self.use_log_transform = use_log_transform
        self.trainable_only = trainable_only

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

        count = list(tracked_statistics[statistic_trackers.NumberOfLayers.__name__].values())[0]

        if self.use_log_transform:
            return math.log(1 + count)  # type: ignore

        else:
            return count

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {statistic_trackers.NumberOfLayers.__name__: dict(trainable_only=self.trainable_only)}


class LogRatioOfPreviousAndCurrentParamNormEnvStepObserver(LHOPTBaseObserver):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._previous_param_norm = None

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """
        return 2  # [tanh_feature, cdf_feature]

    @property
    def requires_include_statistics(self) -> bool:
        """
        :return: Whether the observation requires include_statistics to be provided.
        """

        return True

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

        statistics = tracked_statistics[statistic_trackers.ParameterStatistics.__name__]

        current_param_norm = observation_utils.average_tensor_statistics(
            tensor_statistics=[stats for stats in statistics.values() if isinstance(stats, TensorStatistics)]
        ).norm_

        if self._previous_param_norm is None:
            self._previous_param_norm = current_param_norm
            self._compute_cdf_feature(0.0)  # default value since we can't compute log ratio yet
            self._update_time()
            return [0.0, 0.0]

        log_ratio = self._compute_log_ratio(current_param_norm, self._previous_param_norm)
        tanh_feature = math.tanh(max(-LHOPT_CONSTANTS["TANH_BOUND"], min(LHOPT_CONSTANTS["TANH_BOUND"], log_ratio)))
        cdf_feature = self._compute_cdf_feature(log_ratio)
        self._update_time()
        self._previous_param_norm = current_param_norm

        return [tanh_feature, cdf_feature]

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {
            statistic_trackers.ParameterStatistics.__name__: dict(include_statistics=self.include_statistics),
        }

    def reset(self) -> None:
        """
        Reset the observer by clearing the previous parameter norm and time series.
        """

        super().reset()
        self._previous_param_norm = None


class LogRatioOfUpdateAndPreviousParamNormEnvStepObserver(LHOPTBaseObserver):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._previous_param_norm = None

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """
        return 2  # [tanh_feature, cdf_feature]

    @property
    def requires_include_statistics(self) -> bool:
        """
        :return: Whether the observation requires include_statistics to be provided.
        """

        return True

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
        names to floats or TensorStatistics models.
        :param action_taken: Action taken by the agent this class instance is assigned to.
        :return: List containing [raw_log_ratio, cdf_feature].
        """

        update_statistics = tracked_statistics[statistic_trackers.ParameterUpdateStatistics.__name__]
        param_statistics = tracked_statistics[statistic_trackers.ParameterStatistics.__name__]
        update_norm = observation_utils.average_tensor_statistics(
            tensor_statistics=[stats for stats in update_statistics.values() if isinstance(stats, TensorStatistics)]
        ).norm_

        current_param_norm = observation_utils.average_tensor_statistics(
            tensor_statistics=[stats for stats in param_statistics.values() if isinstance(stats, TensorStatistics)]
        ).norm_

        if self._previous_param_norm is None:
            self._previous_param_norm = current_param_norm
            self._compute_cdf_feature(0.0)  # default value since we can't compute log ratio yet
            self._update_time()
            return [0.0, 0.0]

        log_ratio = self._compute_log_ratio(update_norm, self._previous_param_norm)
        tanh_feature = math.tanh(max(-LHOPT_CONSTANTS["TANH_BOUND"], min(LHOPT_CONSTANTS["TANH_BOUND"], log_ratio)))
        cdf_feature = self._compute_cdf_feature(log_ratio)

        self._update_time()
        self._previous_param_norm = current_param_norm

        return [tanh_feature, cdf_feature]

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {
            statistic_trackers.ParameterUpdateStatistics.__name__: dict(include_statistics=self.include_statistics),
            statistic_trackers.ParameterStatistics.__name__: dict(include_statistics=self.include_statistics),
        }

    def reset(self) -> None:
        """
        Reset the observer by clearing the previous parameter norm and time series.
        """

        super().reset()
        self._previous_param_norm = None


class LHOPTAverageParameterUpdateMagnitudeObserver(LHOPTBaseObserver):

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """
        return 2  # [raw_feature, cdf_feature]

    @property
    def requires_include_statistics(self) -> bool:
        """
        :return: Whether the observation requires include_statistics to be provided.
        """

        return True

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

        statistics = tracked_statistics[statistic_trackers.AverageParameterUpdateMagnitudeStatistics.__name__]

        raw_feature = list(statistics.values())[0]  # type: ignore[list-item]

        cdf_feature = self._compute_cdf_feature(raw_feature)  # type: ignore[arg-type]
        self._update_time()

        return [raw_feature, cdf_feature]  # type: ignore[list-item]

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {
            statistic_trackers.AverageParameterUpdateMagnitudeStatistics.__name__: dict(
                include_statistics=self.include_statistics, sample_frequency=LHOPT_CONSTANTS["DEFAULT_SAMPLE_FREQUENCY"]
            )
        }


class LogRatioOfUpdateAndPreviousParamNormInnerStepObserver(LHOPTBaseObserver):
    def __init__(self, **kwargs):
        """
        This observer is used to compute the log ratio of the update and previous parameter norm for the inner step.
        The sample frequency of the statistics needs to be set to 4 (according to the OpenAI paper).
        """
        super().__init__(**kwargs)
        self._previous_param_norm = None

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """
        return 2  # [tanh_feature, cdf_feature]

    @property
    def requires_include_statistics(self) -> bool:
        """
        :return: Whether the observation requires include_statistics to be provided.
        """

        return True

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
        names to floats or TensorStatistics models.
        :param action_taken: Action taken by the agent this class instance is assigned to.
        :return: List containing [raw_log_ratio, cdf_feature].
        """

        update_statistics = tracked_statistics[statistic_trackers.LHOPTParameterUpdateStatistics.__name__]
        param_statistics = tracked_statistics[statistic_trackers.LHOPTParameterStatistics.__name__]
        update_norm = observation_utils.average_tensor_statistics(
            tensor_statistics=[stats for stats in update_statistics.values() if isinstance(stats, TensorStatistics)]
        ).norm_

        current_param_norm = observation_utils.average_tensor_statistics(
            tensor_statistics=[stats for stats in param_statistics.values() if isinstance(stats, TensorStatistics)]
        ).norm_

        if self._previous_param_norm is None:
            self._previous_param_norm = current_param_norm
            self._compute_cdf_feature(0.0)  # default value since we can't compute log ratio yet
            self._update_time()
            return [0.0, 0.0]
        log_ratio = self._compute_log_ratio(update_norm, self._previous_param_norm)
        tanh_feature = math.tanh(max(-LHOPT_CONSTANTS["TANH_BOUND"], min(LHOPT_CONSTANTS["TANH_BOUND"], log_ratio)))
        cdf_feature = self._compute_cdf_feature(log_ratio)
        self._update_time()
        self._previous_param_norm = current_param_norm

        return [tanh_feature, cdf_feature]

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {
            statistic_trackers.LHOPTParameterUpdateStatistics.__name__: dict(
                include_statistics=self.include_statistics, sample_frequency=LHOPT_CONSTANTS["DEFAULT_SAMPLE_FREQUENCY"]
            ),
            statistic_trackers.LHOPTParameterStatistics.__name__: dict(
                include_statistics=self.include_statistics, sample_frequency=LHOPT_CONSTANTS["DEFAULT_SAMPLE_FREQUENCY"]
            ),
        }

    def reset(self) -> None:
        """
        Reset the observer by clearing the previous parameter norm and time series.
        """

        super().reset()
        self._previous_param_norm = None


class LHOPTGlobalLAMBTrustRatio(LHOPTBaseObserver):

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

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """
        return 2  # [raw_value, cdf_feature]

    @property
    def requires_include_statistics(self) -> bool:
        """
        :return: Whether the observation requires include_statistics to be provided.
        """

        return True

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

        statistics = tracked_statistics[statistic_trackers.LHOPTLAMBTrustRatioStatistics.__name__]

        raw_value = sum(statistics.values()) / len(statistics)  # type: ignore[arg-type]
        cdf_feature = self._compute_cdf_feature(raw_value)  # type: ignore[arg-type]
        self._update_time()
        return [raw_value, cdf_feature]  # type: ignore[list-item]

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {
            statistic_trackers.LHOPTLAMBTrustRatioStatistics.__name__: dict(
                include_statistics=self.include_statistics,
                use_log_transform=self.use_log_transform,
                sample_frequency=LHOPT_CONSTANTS["DEFAULT_SAMPLE_FREQUENCY"],
            )
        }
