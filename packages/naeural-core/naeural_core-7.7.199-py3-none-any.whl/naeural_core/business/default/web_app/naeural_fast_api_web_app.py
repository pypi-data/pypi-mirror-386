from naeural_core.business.default.web_app.fast_api_web_app import FastApiWebAppPlugin as BasePlugin
from ratio1 import Session

__VER__ = '0.1.0.0'

_CONFIG = {
  **BasePlugin.CONFIG,

  'SAVE_PERIOD': 60,
  "ALLOW_EMPTY_INPUTS": True,
  
  'VALIDATION_RULES': {
    **BasePlugin.CONFIG['VALIDATION_RULES'],
  },
}


class NaeuralFastApiWebApp(BasePlugin):
  CONFIG = _CONFIG

  def __init__(self, **kwargs):
    self.requests_responses = {}
    self.requests_meta = {}
    self.unsolved_requests = set()
    self.session = None
    self.last_save_time = None
    self.force_persistence = False
    super(NaeuralFastApiWebApp, self).__init__(**kwargs)
    return

  def debug_on_payload(self, sess, node_addr, pipeline, signature, instance, payload):
    if self.cfg_debug_mode and not self.__ignore_signature(signature):
      self.P(f'[Session]Payload received from {node_addr} on signature {signature}: {payload}')
    return

  def on_init(self):
    # !!!This approach, although works, will not be allowed in the future because it's not safe
    # TODO: maybe refactor after the new requests system is done
    self.session = Session(
      name=f'{self.str_unique_identification}',
      config=self.global_shmem['config_communication']['PARAMS'],
      log=self.log,
      bc_engine=self.global_shmem[self.ct.BLOCKCHAIN_MANAGER],
      on_payload=self.debug_on_payload,
    )
    super(NaeuralFastApiWebApp, self).on_init()
    self.__maybe_load_persistence_data()
    return

  def relevant_plugin_signatures(self):
    """
    Returns a list of the relevant plugin signatures for the requests sent by this plugin.

    Returns
    -------
    res : list[str]
        The list of relevant plugin signatures.
        If empty, all the requests will be considered relevant.
    """
    return []

  def __ignore_signature(self, signature):
    if not isinstance(self.relevant_plugin_signatures(), list):
      return False
    if signature is None:
      return True
    if len(self.relevant_plugin_signatures()) > 0:
      relevants_lower = [s.lower() for s in self.relevant_plugin_signatures()]
      return signature.lower() not in relevants_lower
    return False

  def process_response_payload(self, payload_data):
    """
    Processes the payload data received from the network.
    Parameters
    ----------
    payload_data : dict
        The payload data.

    Returns
    -------
    res : dict
        The processed response data.
    """
    return payload_data

  def __process_payload_response(self, payload_data: dict):
    """
    Processes the payload data received from the network and updates the requests_responses dictionary.

    Parameters
    ----------

    payload_data : dict
        The payload data.
    """
    signature = payload_data.get('signature', None)
    # Check if the signature is relevant for this plugin.
    if self.__ignore_signature(signature):
      return
    # Check if the payload is a response to a request sent by this plugin.
    request_id = payload_data.get('request_id', None)
    if request_id is not None and request_id in self.unsolved_requests:
      self.requests_responses[request_id] = self.process_response_payload(self.deepcopy(payload_data))
      self.unsolved_requests.remove(request_id)
    return

  def __preprocess_payload_data(self, payload):
    """
    Preprocesses the payload data received from the network.
    First, it checks if the payload data is encrypted and tries to decrypt it.
    Then, it normalizes the keys to lowercase for easier processing.

    Parameters
    ----------

    payload : dict
        The payload data.

    Returns
    -------

    res : dict
        The preprocessed payload data.
    """
    # In case of encrypted data, try to decrypt it.
    payload_data = self.check_payload_data(payload)
    if payload_data is None:
      return
    # Normalize keys to lowercase for easier processing.
    return {k.lower(): v for k, v in payload_data.items()}

  def handle_received_payload(self, payload_data):
    """
    Handles the received payload data.
    This method should be overridden by the user to define the logic for processing the payload data.

    Parameters
    ----------

    payload_data : dict
        The payload data.
    """
    return

  def __maybe_handle_payloads(self):
    payloads = self.dataapi_struct_datas(as_list=True)
    if self.cfg_debug_mode and len(payloads) > 0:
      self.P(f'Received {len(payloads)} payloads.')
    for payload in payloads:
      preprocessed_payload = self.__preprocess_payload_data(payload)
      if preprocessed_payload is None:
        continue
      self.__process_payload_response(preprocessed_payload)
      self.handle_received_payload(preprocessed_payload)
    # endfor payloads
    return

  def get_request_meta(self, **kwargs):
    return kwargs

  def send_network_request(self, **kwargs):
    return NotImplementedError

  def __register_network_request(self, **kwargs):
    """
    Registers a request and sends it to the network through the send_request method.
    Parameters
    ----------
    kwargs : dict
        The keyword arguments to be passed to the send_request method.

    Returns
    -------
    res : bool
        True if the request was successfully registered, False otherwise.
    msg : str
        The error message in case of failure.
    """
    try:
      if 'request_id' not in kwargs:
        request_id = self.uuid()
        kwargs['request_id'] = request_id
      else:
        request_id = kwargs['request_id']
      request_timeout = kwargs.get('timeout', None)
      self.requests_meta[request_id] = self.get_request_meta(**kwargs)
      self.requests_meta[request_id]['start_time'] = self.time()
      if request_timeout is not None:
        self.requests_meta[request_id]['timeout'] = request_timeout
      self.unsolved_requests.add(request_id)
      self.send_network_request(**kwargs)
      return True, None
    except Exception as e:
      msg = f'Error registering request: {e}'
      self.P(msg, color='r')
      return False, msg

  def register_network_request(self, **kwargs):
    return self.__register_network_request(**kwargs)

  def __maybe_get_network_response(self, request_id):
    """
    Returns the network response for specified request if available.
    Parameters
    ----------
    request_id : str
        The request id.

    Returns
    -------
    res : dict
      The network response
    """
    try:
      if request_id in self.requests_responses:
        return self.requests_responses[request_id]
      # endif request_id in requests_responses
      if request_id in self.unsolved_requests:
        req_meta = self.requests_meta.get(request_id) or {}
        timeout = req_meta.get('timeout', None)
        start_time = req_meta.get('start_time', None)
        if timeout is not None and start_time is not None and self.time() - start_time > timeout:
          self.unsolved_requests.remove(request_id)
          return {'error': f'Request {request_id} timed out! Took longer than {timeout} seconds.'}
        # endif timeout reached
      # endif request_id in unsolved_requests
    except Exception as e:
      self.P(f'Error getting network response: {e}', color='r')
    return None

  def maybe_get_network_response(self, request_id):
    return self.__maybe_get_network_response(request_id)

  """BEGIN PERSISTENCE"""
  if True:
    def webapp_get_persistence_data_object(self):
      """
      Here the user can define a dictionary with the data that needs to be saved in the plugin's cache.
      For example, the user can save the plugin's state as follows:
      return {'state': self.state}
      Returns
      -------
      res : dict - the data object to be saved
      """
      return {}

    def __webapp_persistence_save(self):
      data_obj = self.webapp_get_persistence_data_object()
      if len(data_obj.keys()) > 0:
        self.persistence_serialization_save(obj=data_obj)
      # endif data object not empty
      return

    def maybe_persistence_save(self):
      is_save_time = self.last_save_time is None or (self.time() - self.last_save_time > self.cfg_save_period)
      if self.force_persistence or is_save_time:
        self.last_save_time = self.time()
        self.__webapp_persistence_save()
        self.force_persistence = False
      # endif save time
      return

    def webapp_load_persistence_data_object(self, data):
      """
      Here the user can define the logic to load the data object saved in the plugin's cache.
      For example, the user can update the plugin's state based on the loaded data as follows:
      self.state = data['state']
      Parameters
      ----------
      data : dict - the data object to be loaded
      """
      return

    def __maybe_load_persistence_data(self):
      saved_data = self.persistence_serialization_load()
      if saved_data is not None:
        self.webapp_load_persistence_data_object(saved_data)
      # endif saved data available
      return
  """END PERSISTENCE"""

  def process(self):
    super(NaeuralFastApiWebApp, self).process()
    self.maybe_persistence_save()
    self.__maybe_handle_payloads()
    return
