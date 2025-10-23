# Copyright 2025 DeepMind Technologies Limited.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for UKAEA's TGLFNN surrogate."""

from absl.testing import absltest
from absl.testing import parameterized
from fusion_surrogates.tglfnn_ukaea import tglfnn_ukaea_model
import jax.numpy as jnp


class TGLFNNukaeaModelTest(parameterized.TestCase):

  @parameterized.named_parameters(
      dict(
          testcase_name="batched_inputs",
          input_shape=(5, 10, 13),
          expected_output_shape=(5, 10, 2),
      ),
      dict(
          testcase_name="non_batched_inputs",
          input_shape=(10, 13),
          expected_output_shape=(10, 2),
      ),
      dict(
          testcase_name="single_batch_dimension",
          input_shape=(1, 3, 13),
          expected_output_shape=(1, 3, 2),
      ),
      dict(
          testcase_name="single_data_dimension",
          input_shape=(3, 1, 13),
          expected_output_shape=(3, 1, 2),
      ),
  )
  def test_predict_shape(self, input_shape, expected_output_shape):
    """Test that the predict function returns the correct shape."""
    model = tglfnn_ukaea_model.TGLFNNukaeaModel(machine="multimachine")
    inputs = jnp.ones(input_shape)
    predictions = model.predict(inputs)

    for label in model.output_labels:
      self.assertEqual(predictions[label].shape, expected_output_shape)


if __name__ == "__main__":
  absltest.main()
