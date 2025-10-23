from naeural_core.data.base import DataCaptureThread
from naeural_core.data.mixins_libs import _DataSensorMixin

_CONFIG = {
  **DataCaptureThread.CONFIG,
  'VALIDATION_RULES' : {
    **DataCaptureThread.CONFIG['VALIDATION_RULES'],
  },
}

class StructuredLiveDataCapture(DataCaptureThread,
                                _DataSensorMixin,
                                ):

  CONFIG = _CONFIG


  
  def startup(self):
    # NON-threaded code in startup
    super().startup()
    self._start_sensor()
    self._metadata = self._sensor_metadata
    return
  
  
  def connect(self):
    return self.sensor.maybe_reconnect()
  
    
  def _run_data_aquisition_step(self):
    _obs, _train, _count = self._get_sensor_data()
    
    self._metadata.dataframe_current = _count + 1

    self._add_inputs(
      [
        self._new_input(img=None, struct_data=_obs, metadata=self._metadata.__dict__.copy(), init_data=_train),
      ]
    )
    return 
    
  def _release(self):
    self.sensor.release()
    return  
  
  