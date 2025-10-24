#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from itertools import product

import torch
from botorch.utils.test_helpers import get_fully_bayesian_model
from botorch.utils.testing import BotorchTestCase
from botorch_community.acquisition.bayesian_active_learning import (
    qBayesianQueryByComittee,
    qBayesianVarianceReduction,
    qStatisticalDistanceActiveLearning,
)


class TestQStatisticalDistanceActiveLearning(BotorchTestCase):
    def test_q_statistical_distance_active_learning(self):
        torch.manual_seed(1)
        tkwargs = {"device": self.device}
        distance_metrics = ("hellinger", "kl_divergence")
        num_objectives = 1
        num_models = 3
        for (
            dtype,
            distance_metric,
            standardize_model,
            infer_noise,
        ) in product(
            (torch.float, torch.double),
            distance_metrics,
            (False, True),  # standardize_model
            (True,),  # infer_noise - only one option avail in PyroModels
        ):
            tkwargs["dtype"] = dtype
            input_dim = 2
            train_X = torch.rand(4, input_dim, **tkwargs)
            train_Y = torch.rand(4, num_objectives, **tkwargs)

            model = get_fully_bayesian_model(
                train_X=train_X,
                train_Y=train_Y,
                num_models=num_models,
                standardize_model=standardize_model,
                infer_noise=infer_noise,
                **tkwargs,
            )

            # test acquisition
            X_pending_list = [None, torch.rand(2, input_dim, **tkwargs)]
            for i in range(len(X_pending_list)):
                X_pending = X_pending_list[i]

                acq = qStatisticalDistanceActiveLearning(
                    model=model,
                    X_pending=X_pending,
                    distance_metric=distance_metric,
                )

                test_Xs = [
                    torch.rand(4, 1, input_dim, **tkwargs),
                    torch.rand(4, 3, input_dim, **tkwargs),
                    torch.rand(4, 5, 1, input_dim, **tkwargs),
                    torch.rand(4, 5, 3, input_dim, **tkwargs),
                ]

                for j in range(len(test_Xs)):
                    acq_X = acq.forward(test_Xs[j])
                    acq_X = acq(test_Xs[j])
                    # assess shape
                    self.assertTrue(acq_X.shape == test_Xs[j].shape[:-2])

        with self.assertRaises(ValueError):
            acq = qStatisticalDistanceActiveLearning(
                model=model,
                distance_metric="NOT_A_DISTANCE",
                X_pending=X_pending,
            )


class TestQBayesianQueryByComittee(BotorchTestCase):
    def test_q_bayesian_query_by_comittee(self):
        torch.manual_seed(1)
        tkwargs = {"device": self.device}
        num_objectives = 1
        num_models = 3
        for (
            dtype,
            standardize_model,
            infer_noise,
        ) in product(
            (torch.float, torch.double),
            (False, True),  # standardize_model
            (True,),  # infer_noise - only one option avail in PyroModels
        ):
            tkwargs["dtype"] = dtype
            input_dim = 2
            train_X = torch.rand(4, input_dim, **tkwargs)
            train_Y = torch.rand(4, num_objectives, **tkwargs)

            model = get_fully_bayesian_model(
                train_X=train_X,
                train_Y=train_Y,
                num_models=num_models,
                standardize_model=standardize_model,
                infer_noise=infer_noise,
                **tkwargs,
            )

            # test acquisition
            X_pending_list = [None, torch.rand(2, input_dim, **tkwargs)]
            for i in range(len(X_pending_list)):
                X_pending = X_pending_list[i]

                acq = qBayesianQueryByComittee(
                    model=model,
                    X_pending=X_pending,
                )

                test_Xs = [
                    torch.rand(4, 1, input_dim, **tkwargs),
                    torch.rand(4, 3, input_dim, **tkwargs),
                    torch.rand(4, 5, 1, input_dim, **tkwargs),
                    torch.rand(4, 5, 3, input_dim, **tkwargs),
                ]

                for j in range(len(test_Xs)):
                    acq_X = acq.forward(test_Xs[j])
                    acq_X = acq(test_Xs[j])
                    # assess shape
                    self.assertTrue(acq_X.shape == test_Xs[j].shape[:-2])


class TestQBayesianVarianceReduction(BotorchTestCase):
    def test_q_bayesian_variance_reduction(self):
        torch.manual_seed(1)
        tkwargs = {"device": self.device}
        num_objectives = 1
        num_models = 3
        for (
            dtype,
            standardize_model,
            infer_noise,
        ) in product(
            (torch.float, torch.double),
            (False, True),  # standardize_model
            (True,),  # infer_noise - only one option avail in PyroModels
        ):
            tkwargs["dtype"] = dtype
            input_dim = 2
            train_X = torch.rand(4, input_dim, **tkwargs)
            train_Y = torch.rand(4, num_objectives, **tkwargs)

            model = get_fully_bayesian_model(
                train_X=train_X,
                train_Y=train_Y,
                num_models=num_models,
                standardize_model=standardize_model,
                infer_noise=infer_noise,
                **tkwargs,
            )

            # test acquisition
            X_pending_list = [None, torch.rand(2, input_dim, **tkwargs)]
            for i in range(len(X_pending_list)):
                X_pending = X_pending_list[i]

                acq = qBayesianVarianceReduction(
                    model=model,
                    X_pending=X_pending,
                )

                test_Xs = [
                    torch.rand(4, 1, input_dim, **tkwargs),
                    torch.rand(4, 3, input_dim, **tkwargs),
                    torch.rand(4, 5, 1, input_dim, **tkwargs),
                    torch.rand(4, 5, 3, input_dim, **tkwargs),
                ]

                for j in range(len(test_Xs)):
                    acq_X = acq.forward(test_Xs[j])
                    acq_X = acq(test_Xs[j])
                    # assess shape
                    self.assertTrue(acq_X.shape == test_Xs[j].shape[:-2])
