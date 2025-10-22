############
#
# Copyright (c) 2024 Maxim Yudayev and KU Leuven eMedia Lab
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
#
# Created 2024-2025 for the KU Leuven AidWear, AidFOG, and RevalExo projects
# by Maxim Yudayev [https://yudayev.com].
#
# ############

from collections import OrderedDict

from hermes.base.stream import Stream

from hermes.dots.movella.handler import MOVELLA_PAYLOAD_MODE
from hermes.dots.movella.constants import MOVELLA_STATUS_MASK


class DotsStream(Stream):
  """A structure to store DOTs stream's data.
  """
  def __init__(self, 
               device_mapping: dict[str,str],
               num_joints: int = 5,
               sampling_rate_hz: int = 60,
               payload_mode: str = 'RateQuantitieswMag',
               timesteps_before_solidified: int = 0,
               update_interval_ms: int = 100,
               transmission_delay_period_s: int | None = None,
               **_) -> None:
    super().__init__()
    self._num_joints = num_joints
    self._sampling_rate_hz = sampling_rate_hz
    self._data_getters = MOVELLA_PAYLOAD_MODE[payload_mode]['methods']
    self._transmission_delay_period_s = transmission_delay_period_s
    self._timesteps_before_solidified = timesteps_before_solidified
    self._update_interval_ms = update_interval_ms

    # Invert device mapping to map device_id -> joint_name
    (joint_names, device_ids) = tuple(zip(*(device_mapping.items())))
    self._device_mapping: OrderedDict[str, str] = OrderedDict(zip(device_ids, joint_names))

    self._define_data_notes()

    for data_name, data_getter in self._data_getters.items():
      self.add_stream(device_name='dots-imu',
                      stream_name=data_name,
                      data_type=data_getter['type_str'],
                      sample_size=(self._num_joints, *data_getter['n_dim']),
                      sampling_rate_hz=self._sampling_rate_hz,
                      data_notes=self._data_notes['dots-imu'][data_name],
                      timesteps_before_solidified=self._timesteps_before_solidified)

    self.add_stream(device_name='dots-imu',
                    stream_name='timestamp',
                    data_type='uint32',
                    sample_size=(self._num_joints,),
                    sampling_rate_hz=self._sampling_rate_hz,
                    data_notes=self._data_notes['dots-imu']['timestamp'])
    self.add_stream(device_name='dots-imu',
                    stream_name='toa_s',
                    data_type='float64',
                    sample_size=(self._num_joints,),
                    sampling_rate_hz=self._sampling_rate_hz,
                    data_notes=self._data_notes['dots-imu']['toa_s'])
    self.add_stream(device_name='dots-imu',
                    stream_name='counter',
                    data_type='uint32',
                    sample_size=(self._num_joints,),
                    sampling_rate_hz=self._sampling_rate_hz,
                    is_measure_rate_hz=True,
                    data_notes=self._data_notes['dots-imu']['counter'])

    if self._transmission_delay_period_s:
      self.add_stream(device_name='dots-connection',
                      stream_name='transmission_delay',
                      data_type='float32',
                      sample_size=(1,),
                      sampling_rate_hz=1.0/self._transmission_delay_period_s,
                      data_notes=self._data_notes['dots-connection']['transmission_delay'])


  def get_fps(self) -> dict[str, float | None]:
    return {'dots-imu': super()._get_fps('dots-imu', 'timestamp')}


  def _define_data_notes(self) -> None:
    self._data_notes = {}
    self._data_notes.setdefault('dots-imu', {})
    self._data_notes.setdefault('dots-connection', {})

    self._data_notes['dots-imu']['acceleration'] = OrderedDict([
      ('Description', 'Linear acceleration in the [X,Y,Z] direction w.r.t. sensor local coordinate system'),
      ('Units', 'meter/second^2'),
      (Stream.metadata_data_headings_key, list(self._device_mapping.values())),
    ])
    self._data_notes['dots-imu']['gyroscope'] = OrderedDict([
      ('Description', 'Angular velocity in the [X,Y,Z] direction w.r.t. sensor local coordinate system'),
      ('Units', 'degree/second'),
      (Stream.metadata_data_headings_key, list(self._device_mapping.values())),
    ])
    self._data_notes['dots-imu']['magnetometer'] = OrderedDict([
      ('Description', 'Magnetometer reading in the [X,Y,Z] direction'),
      ('Units', 'arbitrary unit normalized to earth field strength during factory calibration (~40uT), '
                'w.r.t. sensor local coordinate system'),
      (Stream.metadata_data_headings_key, list(self._device_mapping.values())),
    ])
    self._data_notes['dots-imu']['quaternion'] = OrderedDict([
      ('Description', 'Quaternion rotation vector [W,X,Y,Z]'),
      (Stream.metadata_data_headings_key, list(self._device_mapping.values())),
    ])
    self._data_notes['dots-imu']['euler'] = OrderedDict([
      ('Description', 'Euler rotation vector [X,Y,Z], for roll, pitch, and yaw'),
      (Stream.metadata_data_headings_key, list(self._device_mapping.values())),
    ])
    self._data_notes['dots-imu']['free_acceleration'] = OrderedDict([
      ('Description', 'Free linear acceleration in the [X,Y,Z] direction, with the Earth gravity component deducted, '
                      'w.r.t. sensor local coordinate system'),
      ('Units', 'meter/second^2'),
      (Stream.metadata_data_headings_key, list(self._device_mapping.values())),
    ])
    self._data_notes['dots-imu']['dq'] = OrderedDict([
      ('Description', 'Quaternion rotation increment vector [W,X,Y,Z] in the time window of sampling rate'),
      (Stream.metadata_data_headings_key, list(self._device_mapping.values())),
    ])
    self._data_notes['dots-imu']['dv'] = OrderedDict([
      ('Description', 'Angular velocity increment in the [X,Y,Z] direction in the time window of sampling rate,'
                      'w.r.t. sensor local coordinate system'),
      ('Units', 'degree'),
      (Stream.metadata_data_headings_key, list(self._device_mapping.values())),
    ])
    self._data_notes['dots-imu']['timestamp'] = OrderedDict([
      ('Description', 'Time of sampling of the packet w.r.t. sensor on-board 1MHz clock, '
                      'clearing on startup and overflowing every ~1.2 hours'),
      ('Units', 'microsecond in range [0, (2^32)-1]'),
      (Stream.metadata_data_headings_key, list(self._device_mapping.values())),
    ])
    self._data_notes['dots-imu']['toa_s'] = OrderedDict([
      ('Description', 'Time of arrival of the packet w.r.t. system clock.'),
      ('Units', 'seconds'),
      (Stream.metadata_data_headings_key, list(self._device_mapping.values())),
    ])
    self._data_notes['dots-imu']['status'] = OrderedDict([
      ('Description', 'One-hot-encoded bit mask specifying out-of-range status of a measurement in the 9-DOF inertial data.'),
      ('Options', MOVELLA_STATUS_MASK),
      (Stream.metadata_data_headings_key, list(self._device_mapping.values())),
    ])
    self._data_notes['dots-imu']['counter'] = OrderedDict([
      ('Description', 'Index of the sampled packet per device, w.r.t. the start of the recording, starting from 0. '
                      'At sample rate of 60Hz, corresponds to ~19884 hours of recording, longer than the battery life of the sensors.'),
      ('Range', '[0, (2^32)-1]'),
      (Stream.metadata_data_headings_key, list(self._device_mapping.values())),
    ])
    self._data_notes['dots-connection']['transmission_delay'] = OrderedDict([
      ('Description', 'Periodic transmission delay estimate of the connection link to the sensor, '
                      'inter-tracker synchronization characterized by Movella under 10 microseconds'),
      ('Units', 'seconds'),
      ('Sample period', self._transmission_delay_period_s),
    ])
