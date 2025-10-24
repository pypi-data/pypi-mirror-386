# MIT License
#
# Copyright (c) 2025 IRT Antoine de Saint Exupéry et Université Paul Sabatier Toulouse III - All
# rights reserved. DEEL and FOR are research programs operated by IVADO, IRT Saint Exupéry,
# CRIAQ and ANITI - https://www.deel.ai/.
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
SmoothGrad method
"""

from __future__ import annotations

from collections.abc import Callable

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer

from interpreto.attributions.aggregations import MeanAggregator
from interpreto.attributions.base import AttributionExplainer, MultitaskExplainerMixin
from interpreto.attributions.perturbations import GaussianNoisePerturbator
from interpreto.commons.granularity import Granularity, GranularityAggregationStrategy
from interpreto.model_wrapping.inference_wrapper import InferenceModes


class SmoothGrad(MultitaskExplainerMixin, AttributionExplainer):
    """
    SmoothGrad is an enhanced version of gradient-based interpretability methods, such as saliency maps.
    It reduces the noise and visual instability often seen in raw gradient attributions by averaging gradients
    over multiple noisy versions of the input. The result is a smoothed importance score for each token.

    Procedure:

    - Generate multiple perturbed versions of the input by adding noise (Gaussian) to the input embeddings.
    - For each noisy input, compute the gradient of the output with respect to the embeddings.
    - Average the gradients across all samples.
    - Aggregate the result per token (e.g., by norm with the input) to get the final attribution scores.

    **Reference:**
    Smilkov et al. (2017). *SmoothGrad: removing noise by adding noise.*
    [Paper](https://arxiv.org/abs/1706.03825)

    Examples:
        >>> from interpreto import Smoothgrad
        >>> method = Smoothgrad(model, tokenizer, batch_size=4,
        >>>                     n_perturbations=50, noise_std=0.01)
        >>> explanations = method.explain(text)
    """

    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        batch_size: int = 4,
        granularity: Granularity = Granularity.WORD,
        granularity_aggregation_strategy: GranularityAggregationStrategy = GranularityAggregationStrategy.MEAN,
        device: torch.device | None = None,
        inference_mode: Callable[[torch.Tensor], torch.Tensor] = InferenceModes.LOGITS,
        input_x_gradient: bool = True,
        n_perturbations: int = 10,  # TODO: find better name
        noise_std: float = 0.1,
    ):
        """
        Initialize the attribution method.

        Args:
            model (PreTrainedModel): model to explain
            tokenizer (PreTrainedTokenizer): Hugging Face tokenizer associated with the model
            batch_size (int): batch size for the attribution method
            granularity (Granularity, optional): The level of granularity for the explanation.
                Options are: `ALL_TOKENS`, `TOKEN`, `WORD`, or `SENTENCE`.
                Defaults to Granularity.WORD.
                To obtain it, `from interpreto import Granularity` then `Granularity.WORD`.
            granularity_aggregation_strategy (GranularityAggregationStrategy): how to aggregate token-level attributions into granularity scores.
                Options are: MEAN, MAX, MIN, SUM, and SIGNED_MAX.
                Ignored for `granularity` set to `ALL_TOKENS` or `TOKEN`.
            device (torch.device): device on which the attribution method will be run
            inference_mode (Callable[[torch.Tensor], torch.Tensor], optional): The mode used for inference.
                It can be either one of LOGITS, SOFTMAX, or LOG_SOFTMAX. Use InferenceModes to choose the appropriate mode.
            input_x_gradient (bool, optional): If True, multiplies the input embeddings with
                their gradients before aggregation. Defaults to ``True``.
            n_perturbations (int): the number of interpolations to generate
            noise_std (float): standard deviation of the Gaussian noise to add to the inputs
        """
        perturbator = GaussianNoisePerturbator(
            inputs_embedder=model.get_input_embeddings(), n_perturbations=n_perturbations, std=noise_std
        )

        super().__init__(
            model=model,
            tokenizer=tokenizer,
            batch_size=batch_size,
            device=device,
            perturbator=perturbator,
            aggregator=MeanAggregator(),
            granularity=granularity,
            granularity_aggregation_strategy=granularity_aggregation_strategy,
            inference_mode=inference_mode,
            use_gradient=True,
            input_x_gradient=input_x_gradient,
        )
