# MIT License
#
# Copyright (c) 2022 Playtika Ltd.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Comprehensive Offline Policy Evaluation (OPE) estimators.

This module provides a complete set of estimators for OPE.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar, Dict, Optional, Tuple, Type

import numpy as np
from scipy.stats import bootstrap

from pybandits.base import Float01, PyBanditsBaseModel
from pybandits.pydantic_version_compatibility import (
    NonNegativeFloat,
    PositiveFloat,
    PositiveInt,
    PrivateAttr,
    validate_call,
)


class BaseOfflinePolicyEstimator(PyBanditsBaseModel, ABC):
    """Base class for all OPE estimators.

    This class defines the interface for all OPE estimators and provides a common method for estimating the policy value.

    Parameters
    ----------
    alpha : Float01, default=0.05
        Significance level for confidence interval estimation.
    n_bootstrap_samples : int, default=10000
        Number of bootstrap samples for confidence interval estimation.
    random_state : int, default=None
        Random seed for bootstrap sampling.
    """

    alpha: Float01 = 0.05
    n_bootstrap_samples: int = 10000
    random_state: Optional[int] = None
    name: ClassVar

    @classmethod
    def _check_array(
        cls,
        name: str,
        data: Dict[str, np.ndarray],
        ndim: PositiveInt,
        dtype: type,
        n_samples: PositiveInt,
        n_actions: Optional[PositiveInt] = None,
    ):
        if name in data:
            array = data[name]
            if array.ndim != ndim:
                raise ValueError(f"{name} must be a {ndim}D array.")
            if array.shape[0] != n_samples:
                raise ValueError(f"action and {name} must have the same length.")
            if array.dtype != dtype:
                raise ValueError(f"{name} must be a {dtype} array")
            if ndim > 1:
                if array.shape[1] != n_actions:
                    raise ValueError(f"{name} must have the same number of actions as the action array.")

    @classmethod
    def _check_sum(cls, name: str, data: Dict[str, np.ndarray]):
        if name in data:
            array = data[name]
            if not array.sum(axis=-1).all():
                raise ValueError(f"{name} must have at least one non-zero element on each column.")

    @classmethod
    def _check_inputs(cls, action: np.ndarray, **kwargs):
        """
        Check the inputs for the estimator.

        Parameters
        ----------
        action : np.ndarray
            Array of actions taken.
        """
        if action.ndim != 1:
            raise ValueError("action must be a 1D array.")
        if action.dtype != int:
            raise ValueError("action must be an integer array.")
        n_samples = action.shape[0]
        n_actions = np.unique(action).shape[0]

        for name, dtype in zip(["reward", "propensity_score", "expected_importance_weight"], [int, float, float]):
            cls._check_array(name, kwargs, 1, dtype, n_samples)

        for name in ["estimated_policy", "expected_reward"]:
            cls._check_array(name, kwargs, 2, float, n_samples, n_actions)

        for name in ["propensity_score", "estimated_policy", "expected_importance_weight"]:
            cls._check_sum(name, kwargs)

    @validate_call(config=dict(arbitrary_types_allowed=True))
    def estimate_policy_value_with_confidence_interval(self, **kwargs) -> Tuple[float, float, float, float]:
        """
        Estimate the policy value with a confidence interval.

        Parameters
        ----------
        action : np.ndarray
            Array of actions taken.

        Returns
        -------
        Tuple[float, float, float, float]
            Estimated policy value, mean, lower bound, and upper bound of the confidence interval.
        """
        self._check_inputs(**kwargs)
        sample_reward = self.estimate_sample_rewards(**kwargs)
        estimated_policy_value = sample_reward.mean()
        bootstrap_result = bootstrap(
            data=(sample_reward,),
            statistic=np.mean,
            confidence_level=1 - self.alpha,
            n_resamples=self.n_bootstrap_samples,
            random_state=self.random_state,
        )
        low, high = bootstrap_result.confidence_interval
        std = bootstrap_result.standard_error
        return estimated_policy_value, low, high, std

    @abstractmethod
    def estimate_sample_rewards(self, **kwargs) -> np.ndarray:
        """
        Estimate sample rewards.

        Returns
        -------
        np.ndarray
            Estimated sample rewards.
        """


class ReplayMethod(BaseOfflinePolicyEstimator):
    """
    Replay Method estimator.

    This estimator is a simple baseline that estimates the policy value by averaging the rewards of the matched samples.

    References
    ----------
    Unbiased Offline Evaluation of Contextual-bandit-based News Article Recommendation Algorithms (Li, Chu, Langford, and Wang, 2011)
    https://arxiv.org/pdf/1003.5956

    Parameters
    ----------
    alpha : Float01, default=0.05
        Significance level for confidence interval estimation.
    n_bootstrap_samples : int, default=10000
        Number of bootstrap samples for confidence interval estimation.
    random_state : int, default=None
        Random seed for bootstrap sampling.

    """

    name = "rep"

    def estimate_sample_rewards(
        self, action: np.ndarray, reward: np.ndarray, estimated_policy: np.ndarray, **kwargs
    ) -> np.ndarray:
        """
        Estimate the sample rewards.

        Parameters
        ----------
        action : np.ndarray
            Array of actions taken.
        reward : np.ndarray
            Array of rewards corresponding to each action.
        estimated_policy : np.ndarray
            Array of action distributions.

        Returns
        -------
        sample_reward : np.ndarray
            Estimated sample rewards.
        """
        n_samples = action.shape[0]
        matched_evaluation_policy = estimated_policy[np.arange(n_samples), action]
        matched_action = matched_evaluation_policy == 1
        sample_reward = (
            reward * matched_action / matched_action.mean() if matched_action.any() else np.zeros_like(matched_action)
        )
        return sample_reward


class GeneralizedInverseProbabilityWeighting(BaseOfflinePolicyEstimator, ABC):
    """
    Abstract generalization of the Inverse Probability Weighting (IPW) estimator.

    References
    ----------
    Learning from Logged Implicit Exploration Data (Strehl, Langford, Li, and Kakade, 2010)
    https://arxiv.org/pdf/1003.0120

    Parameters
    ----------
    alpha : Float01, default=0.05
        Significance level for confidence interval estimation.
    n_bootstrap_samples : int, default=10000
        Number of bootstrap samples for confidence interval estimation.
    random_state : int, default=None
        Random seed for bootstrap sampling.
    """

    @abstractmethod
    def _get_importance_weights(self, **kwargs) -> np.ndarray:
        """
        Get the importance weights.

        Returns
        -------
        np.ndarray
            Array of importance weights.
        """

    def estimate_sample_rewards(self, reward: np.ndarray, shrinkage_method: Optional[Callable], **kwargs) -> np.ndarray:
        """
        Estimate the sample rewards.

        Parameters
        ----------
        reward : np.ndarray
            Array of rewards corresponding to each action.
        shrinkage_method : Optional[Callable]
            Shrinkage method for the importance weights.

        Returns
        -------
        sample_reward : np.ndarray
            Estimated sample rewards.
        """
        importance_weight = self._get_importance_weights(**kwargs)
        importance_weight = shrinkage_method(importance_weight) if shrinkage_method is not None else importance_weight
        sample_reward = reward * importance_weight
        return sample_reward


class InverseProbabilityWeighting(GeneralizedInverseProbabilityWeighting):
    """
    Inverse Probability Weighing (IPW) estimator.

    References
    ----------
    Learning from Logged Implicit Exploration Data (Strehl, Langford, Li, and Kakade, 2010)
    https://arxiv.org/pdf/1003.0120

    Parameters
    ----------
    alpha : Float01, default=0.05
        Significance level for confidence interval estimation.
    n_bootstrap_samples : int, default=10000
        Number of bootstrap samples for confidence interval estimation.
    random_state : int, default=None
        Random seed for bootstrap sampling.
    """

    name = "ipw"

    def estimate_sample_rewards(
        self,
        action: np.ndarray,
        reward: np.ndarray,
        propensity_score: np.ndarray,
        estimated_policy: np.ndarray,
        shrinkage_method: Optional[Callable] = None,
        **kwargs,
    ) -> np.ndarray:
        """
        Estimate the sample rewards.

        Parameters
        ----------
        action : np.ndarray
            Array of actions taken.
        reward : np.ndarray
            Array of rewards corresponding to each action.
        propensity_score : np.ndarray
            Array of propensity scores.
        estimated_policy : np.ndarray
            Array of action distributions.

        Returns
        -------
        sample_reward : np.ndarray
            Estimated sample rewards.
        """
        return super().estimate_sample_rewards(
            reward=reward,
            action=action,
            propensity_score=propensity_score,
            estimated_policy=estimated_policy,
            shrinkage_method=shrinkage_method,
        )

    def _get_importance_weights(
        self,
        action: np.ndarray,
        propensity_score: np.ndarray,
        estimated_policy: np.ndarray,
        **kwargs,
    ) -> np.ndarray:
        """
        Get the importance weights.

        Parameters
        ----------
        action : np.ndarray
            Array of actions taken
        propensity_score : np.ndarray
            Array of propensity scores.
        estimated_policy : np.ndarray
            Array of action distributions.

        Returns
        -------
        importance_weight : np.ndarray
            Array of importance weights.
        """
        n_samples = action.shape[0]
        importance_weight = estimated_policy[np.arange(n_samples), action] / propensity_score
        return importance_weight


class SelfNormalizedInverseProbabilityWeighting(InverseProbabilityWeighting):
    """
    Self-Normalized Inverse Propensity Score (SNIPS) estimator.

    References
    ----------
    The Self-normalized Estimator for Counterfactual Learning (Swaminathan and Joachims, 2015)
    https://papers.nips.cc/paper_files/paper/2015/file/39027dfad5138c9ca0c474d71db915c3-Paper.pdf

    Parameters
    ----------
    alpha : Float01, default=0.05
        Significance level for confidence interval estimation.
    n_bootstrap_samples : int, default=10000
        Number of bootstrap samples for confidence interval estimation.
    random_state : int, default=None
        Random seed for bootstrap sampling.
    """

    name = "snips"

    def estimate_sample_rewards(
        self,
        action: np.ndarray,
        reward: np.ndarray,
        propensity_score: np.ndarray,
        estimated_policy: np.ndarray,
        shrinkage_method: Optional[Callable] = None,
        **kwargs,
    ) -> np.ndarray:
        """
        Estimate the sample rewards.

        Parameters
        ----------
        action : np.ndarray
            Array of actions taken.
        reward : np.ndarray
            Array of rewards corresponding to each action.
        propensity_score : np.ndarray
            Array of propensity scores.
        estimated_policy : np.ndarray
            Array of action distributions.
        shrinkage_method : Optional[Callable]
            Shrinkage method for the importance weights.

        Returns
        -------
        sample_reward : np.ndarray
            Estimated sample rewards.
        """

        def self_normalized_shrink_weights(importance_weight: np.ndarray) -> np.ndarray:
            importance_weight = (
                shrinkage_method(importance_weight) if shrinkage_method is not None else importance_weight
            )
            return importance_weight / importance_weight.mean()

        sample_reward = super().estimate_sample_rewards(
            action=action,
            reward=reward,
            propensity_score=propensity_score,
            estimated_policy=estimated_policy,
            shrinkage_method=self_normalized_shrink_weights,
        )
        return sample_reward


class DirectMethod(BaseOfflinePolicyEstimator):
    """
    Direct Method (DM) estimator.

    This estimator uses the evaluation policy to Estimate the sample rewards.

    References
    ----------
    The Offset Tree for Learning with Partial Labels (Beygelzimer and Langford, 2009)
    https://arxiv.org/pdf/0812.4044


    Parameters
    ----------
    alpha : Float01, default=0.05
        Significance level for confidence interval estimation.
    n_bootstrap_samples : int, default=10000
        Number of bootstrap samples for confidence interval estimation.
    random_state : int, default=None
        Random seed for bootstrap sampling.
    """

    name = "dm"

    def estimate_sample_rewards(
        self,
        estimated_policy: np.ndarray,
        expected_reward: np.ndarray,
        **kwargs,
    ) -> np.ndarray:
        """
        Estimate the sample rewards.

        Parameters
        ----------
        estimated_policy : np.ndarray
            Array of action distributions.
        expected_reward : np.ndarray
            Array of expected rewards.

        Returns
        -------
        sample_reward : np.ndarray
            Estimated sample rewards.
        """
        n_samples = expected_reward.shape[0]
        base_expected_reward = expected_reward[np.arange(n_samples), :]
        evaluation_policy = estimated_policy[np.arange(n_samples), :]
        expected_reward = np.average(
            base_expected_reward,
            weights=evaluation_policy,
            axis=1,
        )
        return expected_reward


class GeneralizedDoublyRobust(BaseOfflinePolicyEstimator, ABC):
    """
    Abstract generalization of the Doubly Robust (DR) estimator.

    References
    ----------
    Doubly Robust Policy Evaluation and Optimization (Dudík, Erhan, Langford, and Li, 2014)
    https://arxiv.org/pdf/1503.02834

    More Robust Doubly Robust Off-policy Evaluation (Farajtabar, Chow, and Ghavamzadeh, 2018)
    https://arxiv.org/pdf/1802.03493


    Parameters
    ----------
    alpha : Float01, default=0.05
        Significance level for confidence interval estimation.
    n_bootstrap_samples : int, default=10000
        Number of bootstrap samples for confidence interval estimation.
    random_state : int, default=None
        Random seed for bootstrap sampling.
    """

    _alternative_method_cls: Type[InverseProbabilityWeighting]
    _dm: DirectMethod = PrivateAttr()
    _other_method: BaseOfflinePolicyEstimator = PrivateAttr()

    def model_post_init(self, __context: Any) -> None:
        self._dm = DirectMethod(
            alpha=self.alpha, n_bootstrap_samples=self.n_bootstrap_samples, random_state=self.random_state
        )
        self._other_method = self._alternative_method_cls(
            alpha=self.alpha, n_bootstrap_samples=self.n_bootstrap_samples, random_state=self.random_state
        )

    def estimate_sample_rewards(
        self,
        action: np.ndarray,
        reward: np.ndarray,
        propensity_score: np.ndarray,
        estimated_policy: np.ndarray,
        expected_reward: np.ndarray,
        **kwargs,
    ) -> np.ndarray:
        """
        Estimate the sample rewards.

        Parameters
        ----------
        action : np.ndarray
            Array of actions taken.
        reward : np.ndarray
            Array of rewards corresponding to each action.
        propensity_score : np.ndarray
            Array of propensity scores.
        estimated_policy : np.ndarray
            Array of action distributions.
        expected_reward : np.ndarray
            Array of expected rewards.

        Returns
        -------
        sample_reward : np.ndarray
            Estimated rewards.
        """
        dm_sample_reward = self._dm.estimate_sample_rewards(
            action=action, estimated_policy=estimated_policy, expected_reward=expected_reward
        )
        other_sample_reward = self._other_method.estimate_sample_rewards(
            action=action,
            reward=reward - dm_sample_reward,
            propensity_score=propensity_score,
            estimated_policy=estimated_policy,
            shrinkage_method=self._shrink_weights,
        )
        sample_reward = dm_sample_reward + other_sample_reward
        return sample_reward

    def _shrink_weights(self, importance_weight: np.ndarray) -> np.ndarray:
        return importance_weight


class DoublyRobust(GeneralizedDoublyRobust):
    """
     Doubly Robust (DR) estimator.

     References
     ----------
     Doubly Robust Policy Evaluation and Optimization (Dudík, Erhan, Langford, and Li, 2014)
     https://arxiv.org/pdf/1503.02834

    More Robust Doubly Robust Off-policy Evaluation (Farajtabar, Chow, and Ghavamzadeh, 2018)
    https://arxiv.org/pdf/1802.03493


     Parameters
     ----------
     alpha : Float01, default=0.05
         Significance level for confidence interval estimation.
     n_bootstrap_samples : int, default=10000
         Number of bootstrap samples for confidence interval estimation.
     random_state : int, default=None
         Random seed for bootstrap sampling.
    """

    name = "dr"
    _alternative_method_cls = InverseProbabilityWeighting


class SelfNormalizedDoublyRobust(GeneralizedDoublyRobust):
    """
    Self-Normalized Doubly Robust (SNDR) estimator.

    This estimator uses the self-normalized importance weights to combine the DR and IPS estimators.

    References
    ----------
    Intrinsically Efficient, Stable, and Bounded Off-Policy Evaluation for Reinforcement Learning (Kallus and Uehara, 2019)
    https://arxiv.org/pdf/1906.03735

    Parameters
    ----------
    alpha : Float01, default=0.05
        Significance level for confidence interval estimation.
    n_bootstrap_samples : int, default=10000
        Number of bootstrap samples for confidence interval estimation.
    random_state : int, default=None
        Random seed for bootstrap sampling.
    """

    name = "sndr"
    _alternative_method_cls = SelfNormalizedInverseProbabilityWeighting


class SwitchDoublyRobust(DoublyRobust):
    """
    Switch Doubly Robust (Switch-DR) estimator.

    This estimator uses a switching rule based on the propensity score to combine the DR and IPS estimators.

    References
    ----------
    Optimal and Adaptive Off-policy Evaluation in Contextual Bandits (Wang, Agarwal, and Dudik, 2017)
    https://arxiv.org/pdf/1507.02646

    Parameters
    ----------
    alpha : Float01, default=0.05
        Significance level for confidence interval estimation.
    n_bootstrap_samples : int, default=10000
        Number of bootstrap samples for confidence interval estimation.
    random_state : Optional[int], default=None
        Random seed for bootstrap sampling.
    switch_threshold : float, default=inf
        Threshold for the importance weight to switch between the DR and IPS estimators.
    """

    name = "switch-dr"
    switch_threshold: float = float("inf")

    def _shrink_weights(self, importance_weight: np.ndarray) -> np.ndarray:
        switch_indicator = importance_weight >= self.switch_threshold
        return switch_indicator * importance_weight


class DoublyRobustWithOptimisticShrinkage(DoublyRobust):
    """
    Optimistic version of DRos estimator.

    This estimator uses a shrinkage factor to shrink the importance weight in the native DR.

    References
    ----------
    Doubly Robust Off-Policy Evaluation with Shrinkage (Su, Dimakopoulou, Krishnamurthy, and Dudik, 2020)
    https://arxiv.org/pdf/1907.09623

    Parameters
    ----------
    alpha : Float01, default=0.05
        Significance level for confidence interval estimation.
    n_bootstrap_samples : int, default=10000
        Number of bootstrap samples for confidence interval estimation.
    random_state : int, default=None
        Random seed for bootstrap sampling.
    shrinkage_factor : float, default=0.0
        Shrinkage factor for the importance weights.
        If set to 0 or infinity, the estimator is equivalent to the native DM or DR estimators, respectively.
    """

    shrinkage_factor: NonNegativeFloat = 0.0
    name = "dros-opt"

    def _shrink_weights(self, importance_weight: np.ndarray) -> np.ndarray:
        if self.shrinkage_factor == 0:
            return np.zeros_like(importance_weight)
        elif self.shrinkage_factor == float("inf"):
            return importance_weight
        return self.shrinkage_factor * importance_weight / (importance_weight**2 + self.shrinkage_factor)


class DoublyRobustWithPessimisticShrinkage(DoublyRobust):
    """
    Pessimistic version of DRos estimator.

    This estimator uses a shrinkage factor to shrink the importance weight in the native DR.

    References
    ----------
    Doubly Robust Off-Policy Evaluation with Shrinkage (Su, Dimakopoulou, Krishnamurthy, and Dudik, 2020)
    https://arxiv.org/pdf/1907.09623

    Parameters
    ----------
    alpha : Float01, default=0.05
        Significance level for confidence interval estimation.
    n_bootstrap_samples : int, default=10000
        Number of bootstrap samples for confidence interval estimation.
    random_state : int, default=None
        Random seed for bootstrap sampling.
    shrinkage_factor : float, default=0.0
        Shrinkage factor for the importance weights.
    """

    name = "dros-pess"
    shrinkage_factor: PositiveFloat = float("inf")

    def _shrink_weights(self, importance_weight: np.ndarray) -> np.ndarray:
        importance_weight = np.minimum(self.shrinkage_factor, importance_weight)
        return importance_weight


class SubGaussianInverseProbabilityWeighting(InverseProbabilityWeighting):
    """
    SubGaussian Inverse Probability Weighing estimator.

    References
    ----------
    Subgaussian and Differentiable Importance Sampling for Off-Policy Evaluation and Learning (Metelli, Russo, and Restelli, 2021)
    https://proceedings.neurips.cc/paper_files/paper/2021/file/4476b929e30dd0c4e8bdbcc82c6ba23a-Paper.pdf

    Parameters
    ----------
    alpha : Float01, defaults to 0.05
        Significance level for confidence interval estimation.
    n_bootstrap_samples : int, defaults to 10000
        Number of bootstrap samples for confidence interval estimation.
    random_state : int, defaults to None
        Random seed for bootstrap sampling.
    shrinkage_factor : Float01, defaults to 0.0
        Shrinkage factor for the importance weights.

    """

    name = "sg-ipw"
    shrinkage_factor: Float01 = 0.0

    def _shrink_weights(self, importance_weight: np.ndarray) -> np.ndarray:
        return importance_weight / (1 - self.shrinkage_factor + self.shrinkage_factor * importance_weight)


class SubGaussianDoublyRobust(GeneralizedDoublyRobust):
    """
    SubGaussian Doubly Robust estimator.

    References
    ----------
    Subgaussian and Differentiable Importance Sampling for Off-Policy Evaluation and Learning (Metelli, Russo, and Restelli, 2021)
    https://proceedings.neurips.cc/paper_files/paper/2021/file/4476b929e30dd0c4e8bdbcc82c6ba23a-Paper.pdf

    Parameters
    ----------
    alpha : Float01, defaults to 0.05
        Significance level for confidence interval estimation.
    n_bootstrap_samples : int, defaults to 10000
        Number of bootstrap samples for confidence interval estimation.
    random_state : int, defaults to None
        Random seed for bootstrap sampling.
    """

    name = "sg-dr"
    _alternative_method_cls = SubGaussianInverseProbabilityWeighting


class BalancedInverseProbabilityWeighting(GeneralizedInverseProbabilityWeighting):
    """
    Balanced Inverse Probability Weighing estimator.

    References
    ----------
    Balanced Off-Policy Evaluation in General Action Spaces (Sondhi, Arbour, and Dimmery, 2020)
    https://arxiv.org/pdf/1906.03694


    Parameters
    ----------
    alpha : Float01, defaults to 0.05
        Significance level for confidence interval estimation.
    n_bootstrap_samples : int, defaults to 10000
        Number of bootstrap samples for confidence interval estimation.
    random_state : int, defaults to None
        Random seed for bootstrap sampling.

    ----------
    Arjun Sondhi, David Arbour, and Drew Dimmery
    "Balanced Off-Policy Evaluation in General Action Spaces.", 2020.
    """

    name = "b-ipw"

    def _get_importance_weights(self, expected_importance_weight: np.ndarray, **kwargs) -> np.ndarray:
        """
        Get the importance weights.

        Parameters
        ----------
        expected_importance_weight : np.ndarray
            Array of expected importance weights.

        Returns
        -------
        expected_importance_weight : np.ndarray
            Array of expected importance weights.
        """
        return expected_importance_weight

    def estimate_sample_rewards(
        self,
        reward: np.ndarray,
        expected_importance_weight: np.ndarray,
        **kwargs,
    ) -> np.ndarray:
        """
        Estimate the sample rewards.

        Parameters
        ----------
        reward : np.ndarray
            Array of rewards corresponding to each action.
        expected_importance_weight : np.ndarray
            Array of expected importance weights.

        Returns
        -------
        sample_reward : np.ndarray
            Estimated rewards.
        """
        return super().estimate_sample_rewards(
            reward=reward, expected_importance_weight=expected_importance_weight, shrinkage_method=None
        )
