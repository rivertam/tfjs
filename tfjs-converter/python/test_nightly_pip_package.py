# Copyright 2018 Google LLC
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
"""Test the Python API and shell binary of the tensorflowjs pip package."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.python.eager import def_function
from tensorflow.python.framework import constant_op
from tensorflow.python.framework import dtypes
from tensorflow.python.framework import tensor_spec
from tensorflow.python.ops import variables
from tensorflow.python.tools import freeze_graph
from tensorflow.python.training.tracking import tracking
from tensorflow.python.saved_model.save import save
import tensorflow_hub as hub

import tensorflowjs as tfjs

class APIAndShellTest(tf.test.TestCase):
  """Nightly tests for the Python API of the pip package."""

  @classmethod
  def setUpClass(cls):
    cls.class_tmp_dir = tempfile.mkdtemp()
    cls.tf_saved_model_dir = os.path.join(cls.class_tmp_dir, 'tf_saved_model')

  @classmethod
  def tearDownClass(cls):
    shutil.rmtree(cls.class_tmp_dir)

  def setUp(self):
    # Make sure this file is not being run from the source directory, to
    # avoid picking up source files.
    # if os.path.isdir(
    #     os.path.join(os.path.dirname(__file__), 'tensorflowjs')):
    #   self.fail('Do not run this test from the Python source directory. '
    #             'This file is intended to be run on pip install.')

    self._tmp_dir = tempfile.mkdtemp()
    super(APIAndShellTest, self).setUp()

  def tearDown(self):
    if os.path.isdir(self._tmp_dir):
      shutil.rmtree(self._tmp_dir)
    super(APIAndShellTest, self).tearDown()

  def testConvertTfHubModelToTfjsGraphModel(self):
    # 1. Convert tfhub mobilenet v2 module.
    tfhub_url = (
        'https://tfhub.dev/google/imagenet/mobilenet_v2_100_224'
        '/feature_vector/3'
    )
    graph_model_output_dir = os.path.join(self._tmp_dir, 'tfjs_graph')
    process = subprocess.Popen([
        'tensorflowjs_converter', '--input_format', 'tf_hub',
        tfhub_url, graph_model_output_dir
    ])
    process.communicate()
    self.assertEqual(0, process.returncode)

    # 2. Check the files that belong to the conversion result.
    files = glob.glob(os.path.join(graph_model_output_dir, '*'))
    self.assertIn(os.path.join(graph_model_output_dir, 'model.json'), files)
    weight_files = sorted(
        glob.glob(os.path.join(graph_model_output_dir, 'group*.bin')))
    self.assertEqual(len(weight_files), 3)

  def testConvertKerasSavedModelToTfjsGraphModel(self):
    """create the keras mobilenet v2 model."""
    # 1. Create a saved model from keras mobilenet v2.
    model = tf.keras.applications.MobileNetV2()

    save_dir = os.path.join(self._tmp_dir, 'mobilenetv2')
    save(model, save_dir)

    # 2. Convert to graph model.
    graph_model_output_dir = os.path.join(self._tmp_dir, 'tfjs_graph')
    process = subprocess.Popen([
        'tensorflowjs_converter', '--input_format', 'tf_saved_model',
        save_dir, graph_model_output_dir
    ])
    process.communicate()
    self.assertEqual(0, process.returncode)

    # 3. Check the files that belong to the conversion result.
    files = glob.glob(os.path.join(graph_model_output_dir, '*'))
    self.assertIn(os.path.join(graph_model_output_dir, 'model.json'), files)
    weight_files = sorted(
        glob.glob(os.path.join(graph_model_output_dir, 'group*.bin')))
    self.assertEqual(len(weight_files), 4)

  def testConvertKerasHdf5ModelToTfjsGraphModel(self):
    # 1. Create a model for testing.
    model = tf.keras.applications.MobileNetV2()

    h5_path = os.path.join(self._tmp_dir, 'model.h5')
    model.save(h5_path)

    # 2. Convert the keras hdf5 model to tfjs_layers_model format.
    graph_model_output_dir = os.path.join(self._tmp_dir, 'tfjs_graph')
    # Implicit value of --output_format: tfjs_layers_model
    process = subprocess.Popen([
        'tensorflowjs_converter', '--input_format', 'keras',
        '--output_format', 'tfjs_graph_model',
        h5_path, graph_model_output_dir
    ])
    process.communicate()
    self.assertEqual(0, process.returncode)

    # 3. Check the files that belong to the conversion result.
    files = glob.glob(os.path.join(graph_model_output_dir, '*'))
    self.assertIn(os.path.join(graph_model_output_dir, 'model.json'), files)
    weight_files = sorted(
        glob.glob(os.path.join(graph_model_output_dir, 'group*.bin')))
    self.assertEqual(len(weight_files), 4)

if __name__ == '__main__':
  tf.test.main()
