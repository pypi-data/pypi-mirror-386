#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.


import os
from logging import DEBUG, WARN
from unittest.mock import MagicMock, mock_open, patch

import torch
from botorch.acquisition.objective import ScalarizedPosteriorTransform
from botorch.exceptions.errors import UnsupportedError
from botorch.models.transforms.input import Normalize
from botorch.utils.testing import BotorchTestCase
from botorch_community.models.prior_fitted_network import (
    BoundedRiemannPosterior,
    MultivariatePFNModel,
    PFNModel,
)
from botorch_community.models.utils.prior_fitted_network import (
    download_model,
    ModelPaths,
)
from botorch_community.posteriors.riemann import MultivariateRiemannPosterior
from pfns.model.transformer_config import CrossEntropyConfig, TransformerConfig
from pfns.train import MainConfig, OptimizerConfig
from torch import nn, Tensor


class DummyPFN(nn.Module):
    def __init__(self, n_buckets: int = 1000):
        """A dummy PFN model for testing purposes.

        This class implements a mocked PFN model that returns
        constant values for testing. It mimics the interface of actual PFN models
        but with simplified behavior.

        Args:
            n_buckets: Number of buckets for the output distribution. Default is 1000.
        """

        super().__init__()
        self.n_buckets = n_buckets
        self.criterion = MagicMock()
        self.criterion.borders = torch.linspace(0, 1, n_buckets + 1)

    def forward(self, train_X: Tensor, train_Y: Tensor, test_X: Tensor) -> Tensor:
        return torch.zeros(*test_X.shape[:-1], self.n_buckets, device=test_X.device)


class TestPriorFittedNetwork(BotorchTestCase):
    def test_raises(self):
        for dtype in (torch.float, torch.double):
            tkwargs = {"device": self.device, "dtype": dtype}
            train_X = torch.rand(10, 3, **tkwargs)
            train_Y = torch.rand(10, 1, **tkwargs)
            train_Yvar = torch.rand(10, 1, **tkwargs)
            test_X = torch.rand(5, 3, **tkwargs)

            with self.assertLogs(logger="botorch", level=DEBUG) as log:
                PFNModel(train_X, train_Y, DummyPFN(), train_Yvar=train_Yvar)
                self.assertIn(
                    "train_Yvar provided but ignored for PFNModel.",
                    log.output[0],
                )

            train_Y_4d = torch.rand(10, 2, 2, 1, **tkwargs)
            with self.assertRaises(UnsupportedError):
                PFNModel(train_X, train_Y_4d, DummyPFN())

            train_Y_2d = torch.rand(10, 2, **tkwargs)
            with self.assertRaises(UnsupportedError):
                PFNModel(train_X, train_Y_2d, DummyPFN())

            with self.assertRaises(UnsupportedError):
                PFNModel(torch.rand(10, 3, 3, 2, **tkwargs), train_Y, DummyPFN())

            with self.assertRaises(UnsupportedError):
                PFNModel(train_X, torch.rand(11, **tkwargs), DummyPFN())

            pfn = PFNModel(train_X, train_Y, DummyPFN())

            with self.assertRaises(UnsupportedError):
                pfn.posterior(test_X, output_indices=[0, 1])
            with self.assertLogs(logger="botorch", level=WARN) as log:
                pfn.posterior(test_X, observation_noise=True)
                self.assertIn(
                    "observation_noise is not supported for PFNModel",
                    log.output[0],
                )
            with self.assertRaises(UnsupportedError):
                pfn.posterior(
                    test_X,
                    posterior_transform=ScalarizedPosteriorTransform(
                        weights=torch.ones(1)
                    ),
                )

            # (b', b, d) prediction works as expected
            test_X = torch.rand(5, 4, 2, **tkwargs)
            post = pfn.posterior(test_X)
            self.assertEqual(post.mean.shape, torch.Size([5, 4, 1]))

            # X dims should be 1 to 4
            test_X = torch.rand(5, 4, 2, 1, 2, **tkwargs)
            with self.assertRaises(UnsupportedError):
                pfn.posterior(test_X)

    def test_shapes(self):
        tkwargs = {"device": self.device, "dtype": torch.float}

        # no q dimension
        train_X = torch.rand(10, 3, **tkwargs)
        train_Y = torch.rand(10, 1, **tkwargs)
        test_X = torch.rand(5, 3, **tkwargs)

        pfn = PFNModel(train_X, train_Y, DummyPFN(n_buckets=100))

        for batch_first in [True, False]:
            with self.subTest(batch_first=batch_first):
                pfn.batch_first = batch_first
                posterior = pfn.posterior(test_X)

                self.assertEqual(posterior.probabilities.shape, torch.Size([5, 100]))
                self.assertEqual(posterior.mean.shape, torch.Size([5, 1]))

        # q=1
        test_X = torch.rand(5, 1, 3, **tkwargs)
        posterior = pfn.posterior(test_X)

        self.assertEqual(posterior.probabilities.shape, torch.Size([5, 1, 100]))
        self.assertEqual(posterior.mean.shape, torch.Size([5, 1, 1]))

        # no shape basically
        test_X = torch.rand(3, **tkwargs)
        posterior = pfn.posterior(test_X)

        self.assertEqual(posterior.probabilities.shape, torch.Size([100]))
        self.assertEqual(posterior.mean.shape, torch.Size([1]))

        # prepare_data
        X = torch.rand(5, 3, **tkwargs)
        X, train_X, train_Y, orig_X_shape = pfn._prepare_data(X)
        self.assertEqual(X.shape, torch.Size([1, 5, 3]))
        self.assertEqual(train_X.shape, torch.Size([1, 10, 3]))
        self.assertEqual(train_Y.shape, torch.Size([1, 10, 1]))
        self.assertEqual(orig_X_shape, torch.Size([5, 3]))

    def test_input_transform(self):
        model = PFNModel(
            train_X=torch.rand(10, 3),
            train_Y=torch.rand(10, 1),
            input_transform=Normalize(d=3),
            model=DummyPFN(),
        )
        self.assertIsInstance(model.input_transform, Normalize)
        self.assertEqual(model.input_transform.bounds.shape, torch.Size([2, 3]))

    def test_unpack_checkpoint(self):
        config = MainConfig(
            priors=[],
            optimizer=OptimizerConfig(
                optimizer="adam",
                lr=0.001,
            ),
            model=TransformerConfig(
                criterion=CrossEntropyConfig(num_classes=3),
            ),
            batch_shape_sampler=None,
        )

        model = config.model.create_model()

        state_dict = model.state_dict()
        checkpoint = {
            "config": config.to_dict(),
            "model_state_dict": state_dict,
        }

        loaded_model = PFNModel(
            train_X=torch.rand(10, 3),
            train_Y=torch.rand(10, 1),
            input_transform=Normalize(d=3),
            model=checkpoint,
            load_training_checkpoint=True,
        )

        loaded_state_dict = loaded_model.pfn.state_dict()
        self.assertEqual(
            sorted(loaded_state_dict.keys()),
            sorted(state_dict.keys()),
        )
        for k in loaded_state_dict.keys():
            self.assertTrue(torch.equal(loaded_state_dict[k], state_dict[k]))


class TestPriorFittedNetworkUtils(BotorchTestCase):
    @patch("botorch_community.models.utils.prior_fitted_network.requests.get")
    @patch("botorch_community.models.utils.prior_fitted_network.gzip.GzipFile")
    @patch("botorch_community.models.utils.prior_fitted_network.torch.load")
    @patch("botorch_community.models.utils.prior_fitted_network.torch.save")
    @patch("botorch_community.models.utils.prior_fitted_network.os.path.exists")
    @patch("botorch_community.models.utils.prior_fitted_network.os.makedirs")
    def test_download_model_cache_miss(
        self,
        _mock_makedirs,
        mock_exists,
        mock_torch_save,
        mock_torch_load,
        mock_gzip,
        mock_requests_get,
    ):
        # Simulate cache miss
        mock_exists.return_value = False

        # Mock the requests.get to simulate a network call
        mock_requests_get.return_value = MagicMock(
            status_code=200, content=b"fake content"
        )

        # Mock the gzip.GzipFile to simulate decompression
        mock_gzip.return_value.__enter__.return_value = mock_open(
            read_data=b"fake model data"
        ).return_value

        # Mock torch.load to simulate loading a model
        fake_model = MagicMock(spec=torch.nn.Module)
        mock_torch_load.return_value = fake_model

        # Call the function
        model = download_model(
            ModelPaths.pfns4bo_hebo,
            cache_dir=os.environ.get("RUNNER_TEMP", "/tmp") + "/test_cache",
            # $RUNNER_TEMP is set by GitHub Actions as tmp, /tmp does not work there
        )

        # Assertions for cache miss
        mock_requests_get.assert_called_once()
        mock_gzip.assert_called_once()
        mock_torch_load.assert_called_once()
        mock_torch_save.assert_called_once()
        self.assertEqual(model, fake_model)

        # Test loading in model init
        model = PFNModel(
            train_X=torch.rand(10, 3),
            train_Y=torch.rand(10, 1),
        )
        self.assertEqual(model.pfn, fake_model.to("cpu"))

    @patch("botorch_community.models.utils.prior_fitted_network.torch.load")
    @patch("botorch_community.models.utils.prior_fitted_network.os.path.exists")
    def test_download_model_cache_hit(self, mock_exists, mock_torch_load):
        # Simulate cache hit
        mock_exists.return_value = True

        # Mock torch.load to simulate loading a model
        fake_model = MagicMock(spec=torch.nn.Module)
        mock_torch_load.return_value = fake_model

        # Call the function
        model = download_model(
            ModelPaths.pfns4bo_hebo,
            cache_dir=os.environ.get("RUNNER_TEMP", "/tmp") + "/test_cache",
            # $RUNNER_TEMP is set by GitHub Actions as tmp, /tmp does not work there
        )

        # Assertions for cache hit
        # mock_exists is called once here and once through os.makedirs
        # which checks if directory exists
        self.assertEqual(mock_exists.call_count, 2)
        mock_torch_load.assert_called_once()
        self.assertEqual(model, fake_model)


class TestMultivariatePFN(BotorchTestCase):
    def setUp(self):
        train_X = torch.rand(10, 3)
        train_Y = torch.rand(10, 1)
        self.pfn = MultivariatePFNModel(train_X, train_Y, DummyPFN())

    def test_posterior(self):
        X = torch.rand(1, 3)
        post = self.pfn.posterior(X)
        self.assertNotIsInstance(post, MultivariateRiemannPosterior)
        X = torch.rand(4, 3)
        R = torch.rand(1, 4, 4)
        with patch(
            "botorch_community.models.prior_fitted_network.MultivariatePFNModel"
            ".estimate_correlations",
            return_value=R,
        ):
            post = self.pfn.posterior(X)
        self.assertIsInstance(post, MultivariateRiemannPosterior)
        self.assertTrue(torch.equal(post.correlation_matrix, R.squeeze(0)))

    def test_estimate_covariances(self):
        b = 3
        q = 4
        cond_val = torch.rand(b, q)
        cond_mean = torch.rand(b, q, q)
        var = torch.ones(b, q)
        mean = torch.rand(b, q)
        # Fill in particular values for the [1, 1, 2] entries
        mean[1, 1] = 2.0
        mean[1, 2] = 3.0
        cond_mean[1, 2, 1] = 3.0
        cond_mean[1, 1, 2] = 4.0
        cond_mean[1, 1, 1] = 2.1
        cond_mean[1, 2, 2] = 3.1
        cond_val[1, 1] = 3.0
        cond_val[1, 2] = 4.0
        with patch(
            "botorch_community.models.prior_fitted_network.MultivariatePFNModel."
            "_map_psd"
        ) as mock_map_psd:
            self.pfn._estimate_covariances(
                cond_mean=cond_mean, cond_val=cond_val, mean=mean, var=var
            )
        cov = mock_map_psd.call_args[0][0]
        # Compare to analytical value of 10
        self.assertEqual(torch.round(cov[1, 1, 2], decimals=2).item(), 10.0)
        self.assertEqual(torch.round(cov[1, 2, 1], decimals=2).item(), 10.0)

    def test_compute_conditional_means(self):
        probabilities = torch.zeros(3, 2, 1000)
        probabilities[0, 0, 9] = 1.0
        probabilities[0, 1, 19] = 1.0
        probabilities[1, 0, 29] = 1.0
        probabilities[1, 1, 39] = 1.0
        probabilities[2, 0, 49] = 1.0
        probabilities[2, 1, 59] = 1.0
        marginals = BoundedRiemannPosterior(
            borders=self.pfn.borders,
            probabilities=probabilities,
        )
        return_value = torch.zeros(3 * 2, 2, 1000)
        return_value[..., 100] = 1.0
        X = torch.ones(3, 2, 5)
        X[:, 1, :] = 2.0
        with patch(
            "botorch_community.models.prior_fitted_network.MultivariatePFNModel."
            "pfn_predict",
            return_value=return_value,
        ) as mock_pfn_predict:
            self.pfn._compute_conditional_means(
                X=X,
                train_X=torch.zeros(3, 4, 5),
                train_Y=torch.zeros(3, 4, 1),
                marginals=marginals,
            )
        res = mock_pfn_predict.call_args[1]
        self.assertTrue(torch.equal(res["X"], torch.cat([X, X])))
        X1 = torch.zeros(1, 5, 5)
        X1[:, -1, :] = 1.0
        X2 = torch.zeros(1, 5, 5)
        X2[:, -1, :] = 2.0
        self.assertTrue(
            torch.equal(res["train_X"], torch.cat([X1, X2, X1, X2, X1, X2], dim=0))
        )
        a = []
        for i in range(6):
            Y = torch.zeros(1, 5, 1)
            Y[0, -1, 0] = (i + 1) * 0.01
            a.append(Y)
        self.assertTrue(
            torch.equal(torch.round(res["train_Y"], decimals=2), torch.cat(a, dim=0))
        )

    def test_estimate_correlations(self):
        probabilities = torch.ones(2, 3, 1000)
        probabilities = probabilities / probabilities.sum(dim=-1, keepdim=True)
        marginals = BoundedRiemannPosterior(
            borders=self.pfn.borders,
            probabilities=probabilities,
        )
        cond_mean = 0.5 * (1 + torch.rand(2, 3, 3))
        with patch(
            "botorch_community.models.prior_fitted_network.MultivariatePFNModel."
            "_compute_conditional_means",
            return_value=(cond_mean, 0.9 * torch.ones(2, 3)),
        ):
            R = self.pfn.estimate_correlations(
                X=torch.ones(2, 3, 5),
                train_X=torch.zeros(2, 4, 5),
                train_Y=torch.zeros(2, 4, 1),
                marginals=marginals,
            )
        self.assertAllClose(torch.diagonal(R, dim1=-2, dim2=-1), torch.ones(2, 3))
        # Test with no batch dimension
        marginals = BoundedRiemannPosterior(
            borders=self.pfn.borders,
            probabilities=probabilities[0, ...],
        )
        cond_mean = cond_mean[:1, ...]
        with patch(
            "botorch_community.models.prior_fitted_network.MultivariatePFNModel."
            "_compute_conditional_means",
            return_value=(cond_mean, 0.9 * torch.ones(1, 3)),
        ):
            R = self.pfn.estimate_correlations(
                X=torch.ones(1, 3, 5),
                train_X=torch.zeros(1, 4, 5),
                train_Y=torch.zeros(1, 4, 1),
                marginals=marginals,
            )
        self.assertEqual(R.shape, torch.Size([1, 3, 3]))
        self.assertAllClose(torch.diagonal(R, dim1=-2, dim2=-1), torch.ones(1, 3))
