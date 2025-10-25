# Copyright 2024 The AI Edge Quantizer Authors.
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
# ==============================================================================

"""Hadamard rotation decomposed pattern transformation."""

from flatbuffers import flexbuffers
import numpy as np
from ai_edge_quantizer import qtyping
from ai_edge_quantizer.transformations import transformation_utils
from ai_edge_litert import schema_py_generated  # pylint: disable=g-direct-tensorflow-import


def _to_flexbuffer(
    hadamard_size: int,
    random_binary_vector: list[np.int8],
) -> bytes:
  """Converts hadamard_size to flexbuffer."""
  fbb = flexbuffers.Builder()
  with fbb.Map():
    fbb.Int('hadamard_size', hadamard_size)
    fbb.VectorFromElements('random_binary_vector', random_binary_vector)
  return fbb.Finish()


def _update_embedding_lookup_consumers(
    transformation: transformation_utils.TransformationInput,
    new_tensor_id: int,
) -> bool:
  """Updates the consumers of the embedding lookup op to use the new tensor.

  Args:
    transformation: The transformation input to update the consumers of.
    new_tensor_id: The new tensor id to use as the input to the embedding lookup
      consumers.
  """
  for consumer in transformation.consumers:
    # If the consumer is a graph output and not an op, we can ignore it here
    # since the graph output will be updated later.
    if consumer == -1:
      continue
    consumer_op = transformation.subgraph.operators[consumer]
    # Find the input that was attached to the insertion point, and replace it
    # with the new tensor.
    for i in range(len(consumer_op.inputs)):
      if consumer_op.inputs[i] == transformation.tensor_id:
        consumer_op.inputs[i] = new_tensor_id


def _update_fully_connected_consumers(
    transformation: transformation_utils.TransformationInput,
    new_tensor_id: int,
) -> bool:
  """Updates the fully connected op(s) to use the new tensor.

  Since the new tensor is inserted to the fully_connected's input, we need to
  scan each consumer (in case of multiple fully_connected ops), and update
  the input tensor to the new tensor.

  Args:
    transformation: The transformation input to update the consumers of.
    new_tensor_id: The new tensor id to use as the input to the fully connected
      consumers.

  Returns:
    True if the fully connected op(s) were updated to use the new tensor.
  """
  updated = False
  for consumer in transformation.consumers:
    if (
        transformation_utils.get_schema_op_id(transformation, consumer)
        == schema_py_generated.BuiltinOperator.FULLY_CONNECTED
    ):
      transformation.subgraph.operators[consumer].inputs[0] = new_tensor_id
      updated = True
  return updated


def _make_hadamard_matrix(size: int):
  """Generates a Hadamard matrix of the given size.

  Args:
    size: The size of the Hadamard matrix. Must be a power of 2. This represents
      a single dimension. E.g. if size is 4, then the Hadamard matrix is a 4x4
      matrix.

  Returns:
    The Hadamard matrix.

  Raises:
    ValueError: If the size is not a power of 2.
  """
  if size <= 0 or (size & (size - 1)) != 0:
    raise ValueError('Hadamard matrix size must be a power of 2. ')
  h = h2 = np.array([[1, 1], [1, -1]])
  current_size = 2
  while current_size < size:
    h = np.kron(h, h2)
    current_size *= 2
  return h / np.sqrt(size)


def insert_decomposed_hadamard_rotation(
    transformation_input: transformation_utils.TransformationInput,
) -> qtyping.TransformationInfo:
  """Inserts a decomposed pattern of Hadamard rotation on this tensor.

  This function works for float32 tensors only. Instead of inserting a single
  custom op (aeq.hadamard_rotation), this inserts the mathematical equivalent
  expressed in built-in TFLite ops. The mathematical equivalent is:
    x' = reshape(x, (-1, hadamard_size))
    x' = x' @ H(hadamard_size)
    x' = reshape(x, x.shape)
  where H(n) is a Hadamard matrix of size n.

  Args:
    transformation_input: The transformation input to insert the ops on.

  Returns:
    The transformation info of the inserted ops.

  Raises:
    ValueError: If the transformation input is not a uniform quantization
    transformation.
    ValueError: If the Hadamard quantization params are not set.
    ValueError: If the tensor is not a float32 tensor.
    ValueError: If no supported ops were found as the tensor's producer or
    consumers.
  """
  if not isinstance(
      transformation_input.quant_params, qtyping.UniformQuantParams
  ):
    raise ValueError('Hadamard rotation supports uniform quantization only')

  if transformation_input.quant_params.hadamard is None:
    raise ValueError(
        'Hadamard rotation quantization params are not set but op insertion is'
        ' requested.'
    )

  tensor = transformation_input.subgraph.tensors[transformation_input.tensor_id]
  if tensor.type != schema_py_generated.TensorType.FLOAT32:
    raise ValueError(
        'The Hadamard rotation op supports float32 tensors only. Got'
        f' {tensor.type} tensor.'
    )

  # Insert x' = tfl.reshape to reshape x to (-1, hadamard_size)
  hadamard_size = transformation_input.quant_params.hadamard.hadamard_size
  tensor_size = np.prod(tensor.shape)
  num_hadamard_blocks = tensor_size // hadamard_size
  prerotate_shape = [num_hadamard_blocks, hadamard_size]
  prerotate_shape_tensor_id = transformation_utils.add_new_constant_tensor(
      tensor.name + b'_prerotate_shape',
      np.array(prerotate_shape, dtype=np.int32),
      schema_py_generated.TensorType.INT32,
      transformation_input.subgraph,
      transformation_input.buffers,
  )
  prerotate_reshape_output_tensor_id = (
      transformation_utils.add_new_activation_tensor(
          tensor.name + b'_prerotate_reshaped',
          prerotate_shape,
          schema_py_generated.TensorType.FLOAT32,
          transformation_input.subgraph,
      )
  )

  prerotate_reshape_op_code_idx = transformation_utils.add_op_code(
      schema_py_generated.BuiltinOperator.RESHAPE,
      transformation_input.op_codes,
      'RESHAPE',
  )
  prerorate_reshape_op = schema_py_generated.OperatorT()
  prerorate_reshape_op.opcodeIndex = prerotate_reshape_op_code_idx
  prerorate_reshape_op.inputs = [
      transformation_input.tensor_id,
      prerotate_shape_tensor_id,
  ]
  prerorate_reshape_op.outputs = [prerotate_reshape_output_tensor_id]

  # Generate hadamard_matrix(hadamard_size).
  # We could quantize this to INT4 for better memory efficiency, but for large
  # models the memory overhead is not significant, and floating point
  # computation does seem to result in better accuracy.
  hadamard_matrix = _make_hadamard_matrix(hadamard_size)
  hadamard_matrix_tensor_id = transformation_utils.add_new_constant_tensor(
      tensor.name + b'_hadamard_matrix',
      hadamard_matrix.astype(np.float32),
      schema_py_generated.TensorType.FLOAT32,
      transformation_input.subgraph,
      transformation_input.buffers,
  )

  # Insert x' = tfl.fully_connected(x', hadamard_matrix)
  fc_output_tensor_id = transformation_utils.add_new_activation_tensor(
      tensor.name + b'_rotated',
      prerotate_shape,
      schema_py_generated.TensorType.FLOAT32,
      transformation_input.subgraph,
  )

  fc_op_code_idx = transformation_utils.add_op_code(
      schema_py_generated.BuiltinOperator.FULLY_CONNECTED,
      transformation_input.op_codes,
      'FULLY_CONNECTED',
  )
  fc_op = schema_py_generated.OperatorT()
  fc_op.opcodeIndex = fc_op_code_idx
  fc_op.inputs = [prerotate_reshape_output_tensor_id, hadamard_matrix_tensor_id]
  fc_op.outputs = [fc_output_tensor_id]
  fc_options = schema_py_generated.FullyConnectedOptionsT()
  fc_options.fusedActivationFunction = (
      schema_py_generated.ActivationFunctionType.NONE
  )
  fc_op.builtinOptionsType = (
      schema_py_generated.BuiltinOptions.FullyConnectedOptions
  )
  fc_op.builtinOptions = fc_options

  # Insert x' = tfl.reshape(x', x.shape)
  post_reshape_op_code_idx = transformation_utils.add_op_code(
      schema_py_generated.BuiltinOperator.RESHAPE,
      transformation_input.op_codes,
      'RESHAPE',
  )
  post_reshape_op = schema_py_generated.OperatorT()
  post_reshape_op.opcodeIndex = post_reshape_op_code_idx
  post_reshape_shape_tensor_id = transformation_utils.add_new_constant_tensor(
      tensor.name + b'_postrotate_shape',
      np.array(tensor.shape, dtype=np.int32),
      schema_py_generated.TensorType.INT32,
      transformation_input.subgraph,
      transformation_input.buffers,
  )

  post_reshape_output_tensor_id = (
      transformation_utils.add_new_activation_tensor(
          tensor.name + b'_postrotate_reshaped',
          tensor.shape,
          schema_py_generated.TensorType.FLOAT32,
          transformation_input.subgraph,
      )
  )
  post_reshape_op.inputs = [
      fc_output_tensor_id,
      post_reshape_shape_tensor_id,
  ]
  post_reshape_op.outputs = [post_reshape_output_tensor_id]

  # Update the users of this tensor to use the new tensor.
  if (
      transformation_utils.get_producer_schema_op_id(transformation_input)
      == schema_py_generated.BuiltinOperator.EMBEDDING_LOOKUP
  ):
    _update_embedding_lookup_consumers(
        transformation_input, post_reshape_output_tensor_id
    )
  elif not _update_fully_connected_consumers(
      transformation_input, post_reshape_output_tensor_id
  ):
    raise ValueError(
        'The Hadamard rotation op supports embedding lookup and fully connected'
        ' ops only, but no such ops were found.'
    )

  # If the tensor is a graph output, we need to replace the tensor with the
  # new tensor.
  for i, output in enumerate(transformation_input.subgraph.outputs):
    if output == transformation_input.tensor_id:
      transformation_input.subgraph.outputs[i] = post_reshape_output_tensor_id

  # Find the actual insertion point. The insertion point should be after the
  # producer op and before the first consumer op. The max() operation ensures
  # that we're not using -1 as the insertion point.
  first_consumer_id = min(transformation_input.consumers)
  op_id = max(transformation_input.producer + 1, first_consumer_id)

  # Insert the new ops in the correct order.
  transformation_input.subgraph.operators.insert(op_id, prerorate_reshape_op)
  transformation_input.subgraph.operators.insert(op_id + 1, fc_op)
  transformation_input.subgraph.operators.insert(op_id + 2, post_reshape_op)

  return qtyping.TransformationInfo(
      op_id=op_id,
      num_ops_added=3,
      output_tensor_id=post_reshape_output_tensor_id,
  )
