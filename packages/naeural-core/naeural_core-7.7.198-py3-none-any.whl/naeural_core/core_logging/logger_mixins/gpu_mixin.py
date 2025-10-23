import gc
import traceback
import platform

class _GPUMixin(object):
  """
  Mixin for GPU functionalities that are attached to `libraries.logger.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `libraries.logger.Logger`

  In this mixin we can use any attribute/method of the Logger.

  * Obs: This mixin uses also attributes/methods of `_MachineInfoMixin`:
    - self.get_machine_memory
    - self.get_avail_memory
  """

  def __init__(self):
    super(_GPUMixin, self).__init__()

    try:
      from ratio1.logging.logger_mixins.machine_mixin import _MachineMixin
    except ModuleNotFoundError:
      raise ModuleNotFoundError("Cannot use _GPUMixin without having _MachineMixin")

    self._done_first_smi_error = False
    return

  @staticmethod
  def clear_gpu_memory():
    try:
      import tensorflow as tf
      import gc
      gc.collect()
      tf.keras.backend.clear_session()
    except:
      pass
    try:
      import torch as th
      import gc
      gc.collect()
      th.cuda.empty_cache()
      th.cuda.clear_memory_allocated()
    except:
      pass

  @staticmethod
  def get_gpu_memory_map():
    import subprocess
    """Get the current gpu usage.

    Returns
    -------
    usage: dict
        Keys are device ids as integers.
        Values are memory usage as integers in MB.
    """
    result = subprocess.check_output(
      [
        'nvidia-smi', '--query-gpu=memory.used',
        '--format=csv,nounits,noheader'
      ])
    result = result.decode('utf-8')
    # Convert lines into a dictionary
    gpu_memory = [int(x) for x in result.strip().split('\n')]
    gpu_memory_map = dict(zip(range(len(gpu_memory)), gpu_memory))
    return gpu_memory_map

  def skip_gpu_info_check(self):
    return vars(self).get('_GPUMixin__no_gpu_avail', False)

  def gpu_info(self, show=False, mb=False, current_pid=False):
    """
    Collects GPU info. Must have torch installed & non-mandatory nvidia-smi

    Parameters
    ----------
    show : bool, optional
      show data as gathered. The default is False.
    mb : bool, optional
      collect memory in MB otherwise in GB. The default is False.
    current_pid: bool, optional
      return data only for GPUs used by current process or all if current process does
    not use GPU
    

    Returns
    -------
    lst_inf : list of dicts
      all GPUs info from CUDA:0 to CUDA:n.

    """

    def _main_func():
      if self.skip_gpu_info_check():
        return []

      try:
        # first get name
        import torch as th
        import os
      except:
        self.P("ERROR: `gpu_info` call failed - PyTorch probably is not installed:\n{}".format(
          traceback.format_exc())
        )
        self.__no_gpu_avail = True
        return None

      nvsmires, device_props, dct_proc_info = None, None, None
      try:
        from pynvml_utils import nvidia_smi
        import pynvml
        nvsmi = nvidia_smi.getInstance()
        nvsmires = nvsmi.DeviceQuery('memory.free, memory.total, memory.used, utilization.gpu, temperature.gpu, fan.speed')
        pynvml_avail = True
      except:
        pynvml_avail = False

      if not pynvml_avail or len(nvsmires) == 0:
        self.__no_gpu_avail = True

      lst_inf = []
      # now we iterate all devices
      n_gpus = th.cuda.device_count()
      if n_gpus > 0:
        gc.collect()
        th.cuda.empty_cache()
      current_pid_has_usage = False
      current_pid_gpus = []

      try:
        for device_id in range(n_gpus):
          dct_device = {}
          device_props = th.cuda.get_device_properties(device_id)
          dct_device['NAME'] = device_props.name
          dct_device['TOTAL_MEM'] = round(
            device_props.total_memory / 1024 ** (2 if mb else 3),
            2
          )
          mem_total = None
          mem_allocated = None
          gpu_used = None
          gpu_temp = None
          gpu_temp_max = None
          fan_speed, fan_speed_unit = -1, "N/A"
          if pynvml_avail and nvsmires is not None and 'gpu' in nvsmires:
            dct_gpu = nvsmires['gpu'][device_id]
            mem_total = round(
              dct_gpu['fb_memory_usage']['total'] / (1 if mb else 1024),
              2
            )  # already from th
            mem_allocated = round(
              dct_gpu['fb_memory_usage']['used'] / (1 if mb else 1024),
              2
            )
            gpu_used = dct_gpu['utilization']['gpu_util']
            if isinstance(gpu_used, str):
              gpu_used = -1
            gpu_temp = dct_gpu['temperature']['gpu_temp']
            gpu_temp_max = dct_gpu['temperature']['gpu_temp_max_threshold']

            fan_speed = dct_gpu.get('fan_speed', -1)
            fan_speed = -1 if fan_speed == 'N/A' else fan_speed
            fan_speed_unit = dct_gpu.get('fan_speed_unit', "N/A")

            handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
            processes = []
            for proc in pynvml.nvmlDeviceGetComputeRunningProcesses(handle):
              dct_proc_info = {k.upper(): v for k,v in proc.__dict__.items()}
              used_mem = dct_proc_info.pop('USEDGPUMEMORY', None)
              dct_proc_info['ALLOCATED_MEM'] = round(
                used_mem / 1024 ** (2 if mb else 3) if used_mem is not None else 0.0,
                2
              )
              processes.append(dct_proc_info)
              if dct_proc_info['PID'] == os.getpid():
                current_pid_has_usage = True
                current_pid_gpus.append(device_id)
            #endfor
            dct_device['PROCESSES'] = processes
            dct_device['USED_BY_PROCESS'] = device_id in current_pid_gpus
          else:
            str_os = platform.platform()
            ## check if platform is Tegra and record
            if 'tegra' in str_os.lower():
              # we just record the overall fre memory
              mem_total = self.get_machine_memory(gb=not mb)
              mem_allocated = mem_total  - self.get_avail_memory(gb=not mb)
              gpu_used = 1
              gpu_temp = 1
              gpu_temp_max = 100
              if not self._done_first_smi_error and nvsmires is not None:
                self.P("Running `gpu_info` on Tegra platform: {}".format(nvsmires), color='r')
                self._done_first_smi_error = True
            elif not self._done_first_smi_error:
              str_log = "ERROR: Please make sure you have both pytorch and pynvml in order to monitor the GPU"
              str_log += "\nError info: pynvml_avail={}, nvsmires={}".format(pynvml_avail, nvsmires)
              self.P(str_log)
              self._done_first_smi_error = True
          #endif
          dct_device['ALLOCATED_MEM'] = mem_allocated
          dct_device['FREE_MEM'] = -1
          if all(x is not None for x in [mem_total, mem_allocated]):
            dct_device['FREE_MEM'] = round(mem_total - mem_allocated, 2)
          dct_device['MEM_UNIT'] = 'MB' if mb else 'GB'
          dct_device['GPU_USED'] = gpu_used
          dct_device['GPU_TEMP'] = gpu_temp
          dct_device['GPU_TEMP_MAX'] = gpu_temp_max
          dct_device['GPU_FAN_SPEED'] = fan_speed
          dct_device['GPU_FAN_SPEED_UNIT'] = fan_speed_unit

          lst_inf.append(dct_device)
        #end for all devices
      except Exception as e:
        self.P("gpu_info exception for device_id {}: {}\n devicepros: {}\n nvsmires: {}\n dct_proc_info: {}".format(
          device_id, e,
          device_props, nvsmires, dct_proc_info), color='r'
        )

      if show:
        self.P("GPU information for {} device(s):".format(len(lst_inf)), color='y')
        for dct_gpu in lst_inf:
          for k, v in dct_gpu.items():
            self.P("  {:<14} {}".format(k + ':', v), color='y')

      if current_pid and current_pid_has_usage:
        return [lst_inf[x] for x in current_pid_gpus]
      else:
        return lst_inf
    #enddef

    # if multiple threads call at the same time the method `log.gpu_info`, then `pynvml_avail` will be False
    #   (most probably due to the queries that are performed using nvidia_smi)
    with self.managed_lock_resource('gpu_info'):
      res = _main_func()
    # endwith lock
    return res
  
  
  def get_gpu_info(self, device_id=0, mb=False):
    """
    Returns GPU info for a specific device
    """
    res = {}
    if not self.skip_gpu_info_check():
      gpu_info = self.gpu_info()
      if gpu_info is not None and len(gpu_info) > 0 and device_id < len(gpu_info):
        res = gpu_info[device_id]
    return res
  
  
  def get_gpu_total_mem(self, device_id=0, mb=False):
    """
    Returns total memory of a specific GPU device
    """
    res = 0
    if not self.skip_gpu_info_check():
      device_info = self.get_gpu_info(device_id=device_id, mb=mb)
      if device_info is not None and len(device_info) > 0:
        res = device_info['TOTAL_MEM']
    return res
  
  
  def get_gpu_free_mem(self, device_id=0, mb=False):
    """
    Returns free memory of a specific GPU device
    """
    res = 0
    if not self.skip_gpu_info_check():
      device_info = self.get_gpu_info(device_id=device_id, mb=mb)
      if device_info is not None and len(device_info) > 0:
        res = device_info['FREE_MEM']
    return res
  
  
  def get_gpu_name(self, device_id=0):
    """
    Returns name of a specific GPU device
    """
    res = 'N/A'
    if not self.skip_gpu_info_check():
      device_info = self.get_gpu_info(device_id=device_id)
      if device_info is not None and len(device_info) > 0:
        res = device_info['NAME']
    return res
  
  
  def get_gpu_fan_speed(self, device_id=0):
    """
    Returns fan speed of a specific GPU device
    """
    res = 'N/A'
    if not self.skip_gpu_info_check():
      device_info = self.get_gpu_info(device_id=device_id)
      if device_info is not None and len(device_info) > 0:
        res = device_info.get('GPU_FAN_SPEED')
    return res
    


if __name__ == '__main__':
  print(_GPUMixin.get_gpu_memory_map())
