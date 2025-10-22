"""
TODO: change from ee_id-based to ee_addr-based

"""
import json
import os
import numpy as np

from time import time, sleep
from copy import deepcopy
from collections import deque, OrderedDict
from datetime import datetime as dt
from naeural_core import DecentrAIObject
from naeural_core import constants as ct
from naeural_core.bc import DefaultBlockEngine, BCct

from .epochs_manager import EpochsManager

UNUSEFULL_HB_KEYS = [
  ct.HB.DEVICE_LOG,
  ct.HB.ERROR_LOG,
  ct.HB.TIMERS,
]

class NetMonCt:
  PIPELINES = 'pipelines'
  PLUGINS_STATUSES = 'plugins_statuses'
  TIMESTAMP = 'timestamp'
  PLUGINS = 'plugins'
  INITIATOR = 'initiator'
  OWNER = 'owner'
  LAST_CONFIG = 'last_config'
  PLUGIN_INSTANCE = 'instance'
  PLUGIN_START = 'start'
  PLUGIN_LAST_ERROR = 'last_error'
  PLUGIN_LAST_ALIVE = 'last_alive'
  IS_DEEPLOYED = 'is_deeployed'
  DEEPLOY_SPECS = 'deeploy_specs'
  INSTANCE_CONF = 'instance_conf'


def exponential_score(left, right, val, right_is_better=False, normed=False):
  num = 50
  interval = np.linspace(left, right, num=num)
  scores = np.linspace(100, 1, num=num) # TODO try with np.geomspace
  if right_is_better:
    rng = range(len(interval)-1, -1, -1)
    sgn = '>='
  else:
    rng = range(len(interval))
    sgn = '<='

  for s,i in enumerate(rng):
    str_eval = '{}{}{}'.format(val, sgn, interval[i])
    res = eval(str_eval)
    if res:
      if normed:
        return scores[s] / 100.1
      else:
        return scores[s]

  return 0
#enddef


NETMON_MUTEX = 'NETMON_MUTEX'

NETMON_DB = 'db.pkl'
NETMON_DB_SUBFOLDER = 'network_monitor'

ERROR_ADDRESS = '0xai_unknownunknownunknown'
MISSING_ID = 'missing_id'

class NetworkMonitor(DecentrAIObject):
  
  HB_HISTORY = 2 * 60 * 60 // 10  # 2 hours of history with 10 seconds intervals
  


  def __init__(self, log, node_name, node_addr, epoch_manager=None, blockchain_manager=None, **kwargs):
    self.node_name = node_name
    self.node_addr = node_addr
    self.__network_heartbeats = {}
    self.network_hashinfo = {}
    # simple pipeline caching mechanism for live node monitoring
    self.__nodes_pipelines = {} 
    self.__registered_hb_pipelines = 0
    self.state_already_loaded = False
    self.__registered_direct_pipelines = 0
    # end simple pipeline caching mechanism
    self.__epoch_manager = epoch_manager
    self.__blockchain_manager = blockchain_manager
    super(NetworkMonitor, self).__init__(log=log, prefix_log='[NMON]', **kwargs)    
    return


  @property
  def all_heartbeats(self):
    result = self.__network_heartbeats
    return result


  @property
  def all_nodes(self):
    """
    Returns the list of all remote nodes that are available or not.
    Returns
    -------
    list[str]
        The list of all remote nodes that are available or not.
    """
    return self.__network_nodes_list()


  @property
  def available_nodes(self):
    """
    Returns the list of remote nodes that are available.
    Returns
    -------
    list[str]
        The list of remote nodes that are available.
    """
    return [x for x in self.all_nodes if self.network_node_is_available(x)]
  
  @property
  def available_nodes_prefixed(self):
    """
    Returns the list of remote nodes that are available with the prefix.
    Returns
    -------
    list[str]
        The list of remote nodes that are available.
    """
    return [self._add_address_prefix(x) for x in self.all_nodes if self.network_node_is_available(x)]

  @property
  def accessible_nodes(self):
    """
    Returns the list of remote nodes that allow the current node to connect to them.

    Returns
    -------
    list[str]
        The list of remote nodes that allow the current node to connect to them.
    """
    return [x for x in self.available_nodes if self.network_node_is_accessible(x)]

  @property
  def epoch_manager(self):
    return self.__epoch_manager


  def startup(self):
    if self.__blockchain_manager is None:
      self.P("Blockchain manager not available", color='r')
      self.__blockchain_manager = DefaultBlockEngine(
        log=self.log,
        name=self.node_name,
        config={}, # use default blockchain config
      )

    self.network_load_status()    

    self.P(f"Initializing Network Monitor on {self.node_addr}", boxed=True)
    if self.__epoch_manager is None:
      self.__epoch_manager = EpochsManager(log=self.log, owner=self)

    return

  
  def _set_network_heartbeats(self, network_heartbeats):
    with self.log.managed_lock_resource(NETMON_MUTEX):

      new_network_heartbeats = {}
      need_sorting = []

      if isinstance(network_heartbeats, dict):
        for addr in network_heartbeats:
          __addr_no_prefix = self.__remove_address_prefix(addr) 

          if __addr_no_prefix not in new_network_heartbeats:
            new_network_heartbeats[__addr_no_prefix] = []
          else:
            # this can be triggered only if the same edge node has been using multiple prefixes
            # for the same public key address
            self.P("Found multiple entries for address with no prefix: {}. This entry will require sorting".format(__addr_no_prefix), color='r')
            need_sorting.append(__addr_no_prefix)
          new_network_heartbeats[__addr_no_prefix].extend(network_heartbeats[addr])
        # endfor loop through network heartbeats entries

        for addr_no_prefix in need_sorting:
          # sort the heartbeats by sent time
          new_network_heartbeats[addr_no_prefix] = sorted(
            new_network_heartbeats[addr_no_prefix], 
            key=lambda x: x[ct.HB.CURRENT_TIME],
          )
        # end for sort required entries

        for addr_no_prefix in new_network_heartbeats:
          for hb in new_network_heartbeats[addr_no_prefix][:-1]:
            self.__pop_repeating_info_from_heartbeat(hb)
          # endfor pop repeating info
          for key_to_delete in UNUSEFULL_HB_KEYS:
            new_network_heartbeats[addr_no_prefix][-1].pop(key_to_delete, None)
            
          new_network_heartbeats[addr_no_prefix] = deque(new_network_heartbeats[addr_no_prefix], maxlen=self.HB_HISTORY)
        # endfor pop repeating info

        self.__network_heartbeats = new_network_heartbeats
      else:
        self.P("Error setting network heartbeats. Invalid type: {}".format(type(network_heartbeats)), color='r')
    # endwith lock
    return 


  def __remove_address_prefix(self, addr):
    """Remove the address prefix if it exists"""
    return self.__blockchain_manager.maybe_remove_prefix(addr)
  
  
  def _add_address_prefix(self, addr):
    """Add the address prefix if it doesn't exist"""
    return self.__blockchain_manager._add_prefix(addr)
  
  
  def node_address_to_eth_address(self, addr):
    return self.__blockchain_manager.node_address_to_eth_address(addr)


  def __pop_repeating_info_from_heartbeat(self, hb):
    """This method will remove the extra info from the heartbeat that is not required for time series analysis"""
    hb.pop(ct.HB.ACTIVE_PLUGINS, None)
    hb.pop(ct.HB.CONFIG_STREAMS, None)
    hb.pop(ct.HB.DCT_STATS, None)
    hb.pop(ct.HB.COMM_STATS, None)
    
    hb.pop(ct.HB.R1FS_ID, None)
    hb.pop(ct.HB.R1FS_ONLINE, None)

    hb.pop(ct.HB.EE_WHITELIST, None)
    hb.pop(ct.PAYLOAD_DATA.EE_PAYLOAD_PATH, None)

    hb.pop(ct.HB.TIMERS, None)
    hb.pop(ct.HB.DEVICE_LOG, None)
    hb.pop(ct.HB.ERROR_LOG, None)

    hb.pop(ct.PAYLOAD_DATA.EE_VERSION, None)
    hb.pop(ct.HB.LOGGER_VERSION, None)
    hb.pop(ct.HB.VERSION, None)
    hb.pop(ct.HB.PY_VER, None)
    hb.pop(ct.HB.HEARTBEAT_VERSION, None)

    hb.pop(ct.HB.GIT_BRANCH, None)
    hb.pop(ct.HB.CONDA_ENV, None)
    hb.pop(ct.HB.CPU, None)
    hb.pop(ct.HB.CPU_NR_CORES, None)
    hb.pop(ct.HB.DEFAULT_CUDA, None)
    hb.pop(ct.HB.GPU_INFO, None)
    hb.pop(ct.HB.MACHINE_IP, None)
    hb.pop(ct.HB.SECURED, None)
    hb.pop(ct.HB.EE_IS_SUPER, None)
    hb.pop(ct.HB.DID, None)
    hb.pop(ct.HB.COMM_RELAY, None)

    hb.pop(ct.PAYLOAD_DATA.EE_ID, None)
    hb.pop(ct.PAYLOAD_DATA.INITIATOR_ID, None)
    hb.pop(ct.PAYLOAD_DATA.EE_IS_ENCRYPTED, None)
    hb.pop(ct.PAYLOAD_DATA.EE_EVENT_TYPE, None)
    hb.pop(ct.PAYLOAD_DATA.EE_FORMATTER, None)

    # Pop all tags starting with EE_NT
    for key in list(hb.keys()):
      if key and key.startswith(ct.HB.PREFIX_EE_NODETAG):
        hb.pop(key, None)
    return

  def __pop_repeating_info_from_previous_heartbeat(self, addr):
    __addr_no_prefix = self.__remove_address_prefix(addr)
    hb_deque = self.__network_heartbeats[__addr_no_prefix]
    if len(hb_deque) < 2:
      return
    self.__pop_repeating_info_from_heartbeat(hb_deque[-2])
    return
  
  
  def __register_node_pipelines(self, addr, pipelines, plugins_statuses=None, verbose=False):
    if isinstance(pipelines, list) and len(pipelines) > 0:      
      __addr_no_prefix = self.__remove_address_prefix(addr)
      if __addr_no_prefix not in self.__nodes_pipelines:
        self.__nodes_pipelines[__addr_no_prefix] = {
        }
      self.__nodes_pipelines[__addr_no_prefix][NetMonCt.PIPELINES] = pipelines
      self.__nodes_pipelines[__addr_no_prefix][NetMonCt.PLUGINS_STATUSES] = plugins_statuses
      self.__nodes_pipelines[__addr_no_prefix][NetMonCt.TIMESTAMP] = time()
      if verbose:
        self.P(f"Registered {len(pipelines)} pipelines for node {addr}")
    else:
      if verbose:
        self.P(f"No pipelines available for node {addr}: {pipelines}", color='r')
    return
  
  
  def __maybe_register_hb_pipelines(self, addr, hb):
    """Register the pipelines if available - will be used for pipeline monitoring"""
    __addr_no_prefix = self.__remove_address_prefix(addr)
    pipelines = hb.pop(ct.HB.PIPELINES, None)
    if isinstance(pipelines, list) and len(pipelines) > 0:
      plugins_statuses = hb.pop(ct.HB.ACTIVE_PLUGINS, [])
      self.__register_node_pipelines(addr, pipelines, plugins_statuses=plugins_statuses)
      self.__registered_hb_pipelines += 1
    return
  

  def __register_heartbeat(self, addr, data):
    # first check if data is encoded (as it always should be)
    if ct.HB.ENCODED_DATA in data:
      str_data = data.pop(ct.HB.ENCODED_DATA)
      dct_hb = json.loads(self.log.decompress_text(str_data))
      data = {
        **data,
        **dct_hb,
      }
    #endif encoded data

    __eeid = data.get(ct.EE_ID, MISSING_ID)
    __addr_no_prefix = self.__remove_address_prefix(addr) 
    
    # we remove any extra bloaded info from the HB inside the network monitor
    for key_to_delete in UNUSEFULL_HB_KEYS:
      data.pop(key_to_delete, None)
    # end remove

    with self.log.managed_lock_resource(NETMON_MUTEX):
      if __addr_no_prefix not in self.__network_heartbeats:
        self.P("Box alive: {}:{}.".format(addr, __eeid), color='y')
        self.__network_heartbeats[__addr_no_prefix] = deque(maxlen=self.HB_HISTORY)
      #endif
      self.__network_heartbeats[__addr_no_prefix].append(data)
      # now register pipelines if avail
      self.__maybe_register_hb_pipelines(addr, data)
      # now remove the extra info from the previous heartbeat
      # this is done to avoid having the same info in multiple sequential heartbeats
      self.__pop_repeating_info_from_previous_heartbeat(addr)
    # endwith lock
    return


  def get_box_heartbeats(self, addr):
    __addr_no_prefix = self.__remove_address_prefix(addr) 
    box_heartbeats = deque(self.all_heartbeats[__addr_no_prefix], maxlen=self.HB_HISTORY)
    return box_heartbeats

  def start_timer(self, tmr_id):
    return self.log.start_timer(tmr_id, section="NetworkMonitor")
  
  def end_timer(self, tmr_id):
    return self.log.end_timer(tmr_id, section="NetworkMonitor")

  # Helper protected methods section
  if True:
    def __network_nodes_list(self, from_hb=False):
      if self.all_heartbeats is None:
        return []

      nodes_addrs = list(self.all_heartbeats.keys())
      if from_hb:          
        nodes_addrs = []
        for key in self.all_heartbeats:
          hb = self.all_heartbeats[key][-1]
          addr = hb.get(ct.HB.EE_ADDR, None)
          if addr is not None:
            nodes_addrs.append(addr)
        # end for
      # endif from_hb

      return nodes_addrs

    def __network_node_past_hearbeats_by_number(self, addr, nr=1, reverse_order=True):
      addr = self.__remove_address_prefix(addr)
      if addr not in self.__network_nodes_list():
        self.P("`_network_node_past_hearbeats_by_number`: ADDR '{}' not available".format(addr))
        return
      
      box_heartbeats = self.get_box_heartbeats(addr)
      if reverse_order:
        lst_heartbeats = list(reversed(box_heartbeats))[:nr]
      else:
        lst_heartbeats = box_heartbeats[-nr:]
      return lst_heartbeats

    def __network_node_past_heartbeats_by_interval(
      self, addr, minutes=60, dt_now=None, reverse_order=True,
      debug_unavailable=False
    ):
      addr = self.__remove_address_prefix(addr)
      if addr not in self.__network_nodes_list():
        if debug_unavailable:
          self.P("`_network_node_past_heartbeats_by_interval`: ADDR '{}' not available".format(addr), color='r')
        return []
      
      if dt_now is None:
        dt_now = dt.now()
        
      lst_heartbeats = []
      box_heartbeats = self.get_box_heartbeats(addr)
      for heartbeat in reversed(box_heartbeats):
        ts = heartbeat.get(ct.HB.RECEIVED_TIME)
        if ts is None:
          remote_time = heartbeat[ct.HB.CURRENT_TIME]
          remote_tz = heartbeat.get(ct.PAYLOAD_DATA.EE_TIMEZONE)
          ts = self.log.utc_to_local(remote_time, remote_utc=remote_tz, fmt=ct.HB.TIMESTAMP_FORMAT)
        else:
          ts = dt.strptime(ts, ct.HB.TIMESTAMP_FORMAT)
        passed_minutes = (dt_now - ts).total_seconds() / 60.0
        if passed_minutes < 0 or passed_minutes > minutes:
          break
        lst_heartbeats.append(heartbeat)
      #endfor
      if not reverse_order:
        lst_heartbeats = list(reversed(lst_heartbeats))
      return lst_heartbeats

    def __network_node_last_heartbeat(self, addr, return_empty_dict=False, debug_unavailable=False):
      __addr_no_prefix = self.__remove_address_prefix(addr) 
      if __addr_no_prefix not in self.__network_nodes_list():
        msg = "`_network_node_last_heartbeat`: ADDR '{}' not available".format(addr)
        if not return_empty_dict:
          raise ValueError(msg)
        else:
          if debug_unavailable:
            self.P(msg, color='r')
          return {}
        #endif raise or return
      return self.all_heartbeats[__addr_no_prefix][-1]

    def __network_node_last_valid_heartbeat(self, addr, minutes=3):
      past_heartbeats = self.__network_node_past_heartbeats_by_interval(addr=addr, minutes=minutes, )
      if len(past_heartbeats) == 0:
        return

      return past_heartbeats[0]

    def __convert_node_id_address(self, network_heartbeats):
      """
      Method to convert the database from the old format to the new format
      The old format was using the node_id as the key, and the new format uses the address as the key
      
      Parameters
      ----------
      network_heartbeats : dict
          The dictionary with the network heartbeats

      Returns
      -------
      dict
          The dictionary with the network heartbeats with the address as the key
      """
      new_network_heartbeats = {}
      needs_sorting = []

      for node_id, data in network_heartbeats.items():
        addr = data[-1].get(ct.HB.EE_ADDR)
        if addr is None:
          self.P(f"Node ID {node_id} has no address. Skipping...", color='r')
          continue
        if addr not in new_network_heartbeats:
          new_network_heartbeats[addr] = []
        else:
          self.P("WARNING: Found multiple node ids with the same address {}.".format(addr), color='r')
          needs_sorting.append(addr)
        new_network_heartbeats[addr].extend(data)
      # end for convert entries from node id to address

      for addr in needs_sorting:
        new_network_heartbeats[addr] = sorted(
          new_network_heartbeats[addr], 
          key=lambda x: x[ct.HB.CURRENT_TIME],
        )
      # end for sort required entries (one address, multiple node ids)
      return new_network_heartbeats

    def __looks_like_an_address(self, string):
      if not isinstance(string, str):
        return False
      if len(string) == 44:
        return True
      if len(string) != 49:
        return False
      if string[:5] == '0xai_':
        return True
      if string[:5] == 'aixp_':
        return True

      return False

    def __maybe_convert_node_id_address(self, network_heartbeats):
      """
      Method to convert the database from the old format to the new format
      The old format was using the node_id as the key, and the new format uses the address as the key
      
      As we cannot say for sure what is an address, we will use the heuristic that if the key doesn't 
      look like an address, we will convert it

      We cannot have a state where we save both the node_id and the address, so we will convert all the keys,
      as this conversion will happen one time only

      Parameters
      ----------
      network_heartbeats : dict
          The dictionary with the network heartbeats

      Returns
      -------
      dict
          The dictionary with the network heartbeats with the address as the key
      """
      if network_heartbeats is None:
        return {}
      if any([not self.__looks_like_an_address(key) for key in network_heartbeats.keys()]):
        self.P("WARNING: Found old format net_mon database. Converting to new format", color='r')
        self.log.save_pickle_to_data(network_heartbeats, 'network_heartbeats_old.pkl', subfolder_path=NETMON_DB_SUBFOLDER)
        return self.__convert_node_id_address(network_heartbeats)
      
      return network_heartbeats

  # "MACHINE_MEMORY" section (protected methods)
  if True:
    def __network_node_machine_memory(self, addr):
      hearbeat = self.__network_node_last_heartbeat(addr=addr)
      return hearbeat.get(ct.HB.MACHINE_MEMORY)
  #endif


  # "AVAILABLE_MEMORY" section (protected methods)
  if True:
    def __network_node_past_available_memory_by_number(self, addr, nr=1, norm=True):
      machine_mem = self.__network_node_machine_memory(addr=addr)
      lst_heartbeats = self.__network_node_past_hearbeats_by_number(addr=addr, nr=nr)
      lst = [h[ct.HB.AVAILABLE_MEMORY] / machine_mem if norm else h[ct.HB.AVAILABLE_MEMORY] for h in lst_heartbeats]
      return lst

    def __network_node_past_available_memory_by_interval(self, addr, minutes=60, norm=True, reverse_order=True):
      machine_mem = self.__network_node_machine_memory(addr=addr)
      lst_heartbeats = self.__network_node_past_heartbeats_by_interval(addr=addr, minutes=minutes, reverse_order=reverse_order)
      lst = [h[ct.HB.AVAILABLE_MEMORY] / machine_mem if norm else h[ct.HB.AVAILABLE_MEMORY] for h in lst_heartbeats]
      return lst

    def __network_node_last_available_memory(self, addr, norm=True):
      machine_mem = self.__network_node_machine_memory(addr=addr)
      hearbeat = self.__network_node_last_heartbeat(addr=addr)
      return hearbeat[ct.HB.AVAILABLE_MEMORY] / machine_mem if norm else hearbeat[ct.HB.AVAILABLE_MEMORY]
  #endif

  # "PROCESS_MEMORY" section (protected methods)
  if True:
    def __network_node_past_process_memory_by_number(self, addr, nr=1, norm=True):
      machine_mem = self.__network_node_machine_memory(addr=addr)
      lst_heartbeats = self.__network_node_past_hearbeats_by_number(addr=addr, nr=nr)
      lst = [h[ct.HB.PROCESS_MEMORY] / machine_mem if norm else h[ct.HB.PROCESS_MEMORY] for h in lst_heartbeats]
      return lst

    def __network_node_past_process_memory_by_interval(self, addr, minutes=60, norm=True):
      machine_mem = self.__network_node_machine_memory(addr=addr)
      lst_heartbeats = self.__network_node_past_heartbeats_by_interval(addr=addr, minutes=minutes)
      lst = [100*h[ct.HB.PROCESS_MEMORY] / machine_mem if norm else h[ct.HB.PROCESS_MEMORY] for h in lst_heartbeats]
      return lst

    def __network_node_last_process_memory(self, addr, norm=True):
      machine_mem = self.__network_node_machine_memory(addr=addr)
      hearbeat = self.__network_node_last_heartbeat(addr=addr)
      return hearbeat[ct.HB.PROCESS_MEMORY] / machine_mem if norm else hearbeat[ct.HB.PROCESS_MEMORY]
  #endif

  # "CPU_USED" section (protected methods)
  if True:
    def __network_node_past_cpu_used_by_number(self, addr, nr=1):
      lst_heartbeats = self.__network_node_past_hearbeats_by_number(addr=addr, nr=nr)
      lst = [h[ct.HB.CPU_USED] for h in lst_heartbeats]
      return lst
    
    def __get_timestamps(self, lst_heartbeats):
      timestamps = [h[ct.HB.CURRENT_TIME].split('.')[0] for h in lst_heartbeats]
      return timestamps

    def __network_node_past_cpu_used_by_interval(
      self, addr, minutes=60, dt_now=None, 
      return_timestamps=False, reverse_order=True
    ):
      lst_heartbeats = self.__network_node_past_heartbeats_by_interval(
        addr=addr, minutes=minutes, dt_now=dt_now, reverse_order=reverse_order
      )
      lst = [h[ct.HB.CPU_USED] for h in lst_heartbeats]
      if return_timestamps:
        timestamps = self.__get_timestamps(lst_heartbeats)
        return lst, timestamps
      else:
        return lst

    def __network_node_last_cpu_used(self, addr):
      hearbeat = self.__network_node_last_heartbeat(addr=addr)
      return hearbeat[ct.HB.CPU_USED]
          
  #endif

  # "GPUS" section (protected methods)
  if True:
    def __network_node_past_gpus_by_number(self, addr, nr=1):
      lst_heartbeats = self.__network_node_past_hearbeats_by_number(addr=addr, nr=nr)
      lst = [h[ct.HB.GPUS] for h in lst_heartbeats]
      for i in range(len(lst)):
        if isinstance(lst[i], str):
          lst[i] = {}
      return lst

    def __network_node_past_gpus_by_interval(
      self, addr, minutes=60, dt_now=None, 
      return_timestamps=False, reverse_order=True
    ):
      lst_heartbeats = self.__network_node_past_heartbeats_by_interval(
        addr=addr, minutes=minutes, dt_now=dt_now, reverse_order=reverse_order,
      )
      lst = [h[ct.HB.GPUS] for h in lst_heartbeats]
      for i in range(len(lst)):
        if isinstance(lst[i], str):
          lst[i] = {}
      if return_timestamps:
        timestamps = self.__get_timestamps(lst_heartbeats)
        return lst, timestamps
      else:
        return lst

    def __network_node_last_gpus(self, addr):
      hearbeat = self.__network_node_last_heartbeat(addr=addr)
      gpus = hearbeat.get(ct.HB.GPUS, "N/A")
      if isinstance(gpus, str):
        gpus = []
      return gpus
  #endif

  # "UPTIME" section (protected methods)
  if True:
    def __network_node_uptime(self, addr, as_minutes=True):
      hearbeat = self.__network_node_last_heartbeat(addr=addr)
      result = hearbeat[ct.HB.UPTIME]
      if as_minutes:
        result = result / 60
      return result
  #endif

  # "DEVICE_STATUS" section (protected methods)
  if True:
    def __network_node_past_device_status_by_number(self, addr, nr=1):
      lst_heartbeats = self.__network_node_past_hearbeats_by_number(addr=addr, nr=nr)
      lst = [h[ct.HB.DEVICE_STATUS] for h in lst_heartbeats]
      return lst

    def __network_node_past_device_status_by_interval(self, addr, minutes=60):
      lst_heartbeats = self.__network_node_past_heartbeats_by_interval(addr=addr, minutes=minutes)
      lst = [h[ct.HB.DEVICE_STATUS] for h in lst_heartbeats]
      return lst

    def __network_node_last_device_status(self, addr):
      hearbeat = self.__network_node_last_heartbeat(addr=addr, return_empty_dict=True)      
      return hearbeat.get(ct.HB.DEVICE_STATUS, "UNKNOWN")
  #endif

  # "ACTIVE_PLUGINS" section (protected methods)
  if True:
    def __network_node_past_active_plugins_by_number(self, addr, nr=1):
      lst_heartbeats = self.__network_node_past_hearbeats_by_number(addr=addr, nr=nr)
      lst = [h[ct.HB.ACTIVE_PLUGINS] for h in lst_heartbeats]
      return lst

    def __network_node_past_active_plugins_by_interval(self, addr, minutes=60):
      lst_heartbeats = self.__network_node_past_heartbeats_by_interval(addr=addr, minutes=minutes)
      lst = [h[ct.HB.ACTIVE_PLUGINS] for h in lst_heartbeats]
      return lst

    def __network_node_last_active_plugins(self, addr):
      hearbeat = self.__network_node_last_heartbeat(addr=addr)
      return hearbeat[ct.HB.ACTIVE_PLUGINS]
  #endif

  # "TOTAL_DISK" section (protected methods)
  if True:
    def __network_node_total_disk(self, addr):
      hearbeat = self.__network_node_last_heartbeat(addr=addr)
      return hearbeat.get(ct.HB.TOTAL_DISK, -1)
  #endif

  # "AVAILABLE_DISK" section (protected methods)
  if True:
    def __network_node_past_available_disk_by_number(self, addr, nr=1, norm=True):
      total_disk = self.__network_node_total_disk(addr=addr)
      lst_heartbeats = self.__network_node_past_hearbeats_by_number(addr=addr, nr=nr)
      lst = [h[ct.HB.AVAILABLE_DISK] / total_disk if norm else h[ct.HB.AVAILABLE_DISK] for h in lst_heartbeats]
      return lst

    def __network_node_past_available_disk_by_interval(self, addr, minutes=60, norm=True):
      total_disk = self.__network_node_total_disk(addr=addr)
      lst_heartbeats = self.__network_node_past_heartbeats_by_interval(addr=addr, minutes=minutes)
      lst = [h[ct.HB.AVAILABLE_DISK] / total_disk if norm else h[ct.HB.AVAILABLE_DISK] for h in lst_heartbeats]
      return lst

    def __network_node_last_available_disk(self, addr, norm=True):
      total_disk = self.__network_node_total_disk(addr=addr)
      hearbeat = self.__network_node_last_heartbeat(addr=addr)
      avail_size = hearbeat.get(ct.HB.AVAILABLE_DISK, 0)
      return avail_size / total_disk if norm else avail_size
  #endif

  # "SERVING_PIDS" section (protected methods)
  if True:
    def __network_node_past_serving_pids_by_number(self, addr, nr=1):
      lst_heartbeats = self.__network_node_past_hearbeats_by_number(addr=addr, nr=nr)
      lst = [h[ct.HB.SERVING_PIDS] for h in lst_heartbeats]
      return lst

    def __network_node_past_serving_pids_by_interval(self, addr, minutes=60):
      lst_heartbeats = self.__network_node_past_heartbeats_by_interval(addr=addr, minutes=minutes)
      lst = [h[ct.HB.SERVING_PIDS] for h in lst_heartbeats]
      return lst

    def __network_node_last_serving_pids(self, addr):
      hearbeat = self.__network_node_last_heartbeat(addr=addr)
      return hearbeat[ct.HB.SERVING_PIDS]
  #endif

  # "LOOPS_TIMINGS" section (protected methods)
  if True:
    def __network_node_past_loops_timings_by_number(self, addr, nr=1):
      lst_heartbeats = self.__network_node_past_hearbeats_by_number(addr=addr, nr=nr)
      lst = [h[ct.HB.LOOPS_TIMINGS] for h in lst_heartbeats]
      return lst

    def __network_node_past_loops_timings_by_interval(self, addr, minutes=60):
      lst_heartbeats = self.__network_node_past_heartbeats_by_interval(addr=addr, minutes=minutes)
      lst = [h[ct.HB.LOOPS_TIMINGS] for h in lst_heartbeats]
      return lst

    def __network_node_last_loops_timings(self, addr):
      hearbeat = self.__network_node_last_heartbeat(addr=addr)
      return hearbeat[ct.HB.LOOPS_TIMINGS]
  #endif

  # "DEFAULT_CUDA" section (protected methods)
  if True:
    def __network_node_default_cuda(self, addr, as_int=True):
      hearbeat = self.__network_node_last_heartbeat(addr=addr)
      if ct.HB.DEFAULT_CUDA not in hearbeat:        
        alias = self.network_node_eeid(addr)
        fn = self.log.save_output_json(
          data_json=hearbeat, 
          fname=f"{self.log.time_to_str()}_{alias}_{self.__remove_address_prefix(addr)}_heartbeat.json", 
        )
        self.P(f"Node {addr} does not have a default CUDA device set in hb. Hb saved in {fn}", color='error')
        return None
      default_cuda = hearbeat[ct.HB.DEFAULT_CUDA]
      if as_int:
        if ':' not in default_cuda:
          return
        default_cuda = int(default_cuda.split(':')[1])

      return default_cuda
  #endif
  
    

  # PUBLIC METHODS SECTION
  if True:    
    
    
    
    def network_node_total_cpu_cores(self, addr):
      """
      Returns the number of CPU cores of the node.
      """
      hearbeat = self.__network_node_last_heartbeat(addr=addr)
      return hearbeat.get(ct.HB.CPU_NR_CORES)
    
    
    def network_node_avail_cpu_cores(self, addr):
      """
      Returns the number of available CPU cores of the node.
      The available cores are computed as the total cores weighted by the CPU usage
      in the last heartbeat.
      """
      hearbeat = self.__network_node_last_heartbeat(addr=addr)
      cpu_used = hearbeat.get(ct.HB.CPU_USED, 0)
      known_cores = self.network_node_total_cpu_cores(addr=addr)
      avail_cores = (1 - cpu_used / 100) * known_cores
      return avail_cores


    def network_node_get_cpu_avail_cores(
      self, addr, minutes=60, dt_now=None, 
      reverse_order=True
    ):
      """
      Returns the available cores for a node.
      The available cores are computed as the total cores weighted by the CPU usage
      in the last period.
      """
      lst_cpu_interval = self.__network_node_past_cpu_used_by_interval(
        addr=addr, minutes=minutes, dt_now=dt_now, reverse_order=reverse_order
      )
      avail_cores = 0
      if lst_cpu_interval:
        cpu_mean = round(np.mean(lst_cpu_interval), 2) / 100
        hearbeat = self.__network_node_last_heartbeat(addr=addr)
        known_cores = hearbeat.get(ct.HB.CPU_NR_CORES, 1)
        avail_cores = (1 - cpu_mean) * known_cores
      return avail_cores
    
    
    def network_node_average_avail_cpu_cores(self, addr):
      """
      Returns the average available CPU cores for a node in the last hour.
      The available cores are computed as the total cores weighted by the CPU usage
      """
      return self.network_node_get_cpu_avail_cores(
        addr=addr, minutes=60, dt_now=None, reverse_order=True
      )

    
    def network_node_last_comm_info(self, addr):
      """
        "COMMS" : {
          "IN_KB": value /-1 if not available
          "OUT_KB" : value /-1 if not available
          "HB" : {
              "ERR" : "Never" / "2020-01-01 00:00:00"
              "MSG" : "OK" / "Connection timeout ..."
              "IN_KB" : value /-1 if not available
              "OUT_KB" : value /-1 if not available
              "FAILS" : value - 0 is best :)
            }
          "PAYL" ...
          "CMD"  ...
          "NTIF" ...
        }
      """
      dct_comms = {}    
      hb = self.__network_node_last_heartbeat(addr=addr, return_empty_dict=True)
      dct_comms[ct.HB.COMM_INFO.IN_KB] = round(hb.get(ct.HB.COMM_INFO.IN_KB, -1), 3)
      dct_comms[ct.HB.COMM_INFO.OUT_KB] = round(hb.get(ct.HB.COMM_INFO.OUT_KB, -1), 3)
      dct_stats = hb.get(ct.HB.COMM_STATS, {})
      mapping = {
        ct.COMMS.COMMUNICATION_HEARTBEATS : "HB",
        ct.COMMS.COMMUNICATION_DEFAULT : "PAYL",
        ct.COMMS.COMMUNICATION_COMMAND_AND_CONTROL : "CMD",
        ct.COMMS.COMMUNICATION_NOTIFICATIONS : "NTIF",
      }
      for k,v in dct_stats.items():
        if k not in mapping:
          # we ignore the local communicator stats
          continue
        report = mapping[k]
        remote_error_time = v.get("ERRTM", None)
        local_error_time = remote_error_time
        if isinstance(remote_error_time, str):
          remote_tz = hb.get(ct.PAYLOAD_DATA.EE_TIMEZONE)
          local_error_time = self.log.utc_to_local(
            remote_error_time, 
            remote_utc=remote_tz, 
            fmt=ct.HB.TIMESTAMP_FORMAT_SHORT,
            as_string=True,
          )
        dct_comms[report] = {
          "ERR"     : local_error_time or "Never",
          "MSG"     : str(v.get("ERROR", None) or "OK"),
          "FAILS"   : v.get("FAILS", 0),
          ct.HB.COMM_INFO.IN_KB : v.get(ct.HB.COMM_INFO.IN_KB, -1),
          ct.HB.COMM_INFO.OUT_KB : v.get(ct.HB.COMM_INFO.OUT_KB, -1),
        }
      return dct_comms
      
    
    def network_node_info_available(self, addr):
      _addr_no_prefix = self.__remove_address_prefix(addr)
      return _addr_no_prefix in self.__network_nodes_list()
    
    
    def network_node_last_heartbeat(self, addr):
      return self.__network_node_last_heartbeat(addr=addr, return_empty_dict=True)    
    
    
    def register_node_pipelines(self, addr, pipelines, plugins_statuses=None, verbose=False):
      self.__register_node_pipelines(addr, pipelines, plugins_statuses=plugins_statuses, verbose=verbose)
      self.__registered_direct_pipelines += 1
      return
    
    def get_hb_vs_direct_pipeline_sources(self):
      return self.__registered_hb_pipelines, self.__registered_direct_pipelines


    def register_heartbeat(self, addr, data):
      # save the timestamp when received the heartbeat,
      # helpful to know when computing the availability score
      # this data is saved using the local time and could "appear" different
      # from the timestamp in the heartbeat due to zone differences
      # when reconstructing RECEIVED_TIME we will use local timezone
      data[ct.HB.RECEIVED_TIME] = dt.now().strftime(ct.HB.TIMESTAMP_FORMAT)
      self.__register_heartbeat(addr, data)
      self.epoch_manager.register_data(addr, data) # TODO: change this?
      return
        
    def network_nodes_status(self):
      """
      Return a dict with the status of all the nodes. Each key is the address without the prefix
      """
      dct_results = {}
      nodes = self.__network_nodes_list()
      for addr in nodes:
        dct_res = self.network_node_status(addr=addr)
        dct_results[addr] = dct_res
      return dct_results

    def network_known_nodes(self):
      """
      Return a dict with the known nodes and their last timestamp and pipeline config
      The addresses are without the prefix
      """
      return self.__nodes_pipelines

    def network_known_configs(self):
      return {x: self.__nodes_pipelines[x]['pipelines'] for x in self.__nodes_pipelines}
    
    
    def network_node_main_loop(self, addr):
      try:
        dct_timings = self.__network_node_last_loops_timings(addr=addr)
      except:
        return 1e10
      return round(dct_timings['main_loop_avg_time'],4)
      
          
    def network_node_is_ok_loops_timings(self, addr, max_main_loop_timing=1):
      return self.network_node_main_loop(addr) <= max_main_loop_timing


    def network_node_is_ok_uptime(self, addr, min_uptime=60):
      uptime = self.__network_node_uptime(addr=addr)
      return uptime >= min_uptime


    def network_node_uptime(self, addr, as_str=True):
      uptime_sec = self.__network_node_uptime(addr=addr, as_minutes=False)
      if as_str:
        result = self.log.elapsed_to_str(uptime_sec)
      else:
        result = uptime_sec
      return result

    def network_node_total_disk(self, addr):
      """
      Returns the total disk of the node.
      """
      total_disk = self.__network_node_total_disk(addr=addr)
      return total_disk

    def network_node_available_disk(self, addr, norm=False):
      available_disk = self.__network_node_last_available_disk(addr=addr, norm=norm)
      return available_disk
    
    
    def network_node_avail_disk(self, addr, norm=False):
      """
      Returns the available disk of the node.
      If norm is True, returns the percentage of available disk.
      """
      return self.network_node_available_disk(addr=addr, norm=norm)
    


    def network_node_available_disk_prc(self, addr):
      prc_available_disk = self.__network_node_last_available_disk(addr=addr, norm=True)
      return prc_available_disk


    def network_node_is_ok_available_disk_prc(self, addr, min_prc_available=0.15):
      # can create other heuristics based on what happened on the last x minutes interval (using _network_node_past_available_disk_by_interval)
      prc_available_disk = self.network_node_available_disk_prc(addr=addr)
      return prc_available_disk >= min_prc_available


    def network_node_is_ok_available_disk_size(self, addr, min_gb_available=50):
      # can create other heuristics based on what happened on the last x minutes interval (using _network_node_past_available_disk_by_interval)
      available_disk = self.network_node_available_disk(addr=addr)
      return available_disk >= min_gb_available


    def network_node_available_memory(self, addr, norm=False):
      available_mem = self.__network_node_last_available_memory(addr=addr, norm=norm)
      return available_mem


    def network_node_available_memory_prc(self, addr):
      prc_available_mem = self.__network_node_last_available_memory(addr=addr, norm=True)
      return prc_available_mem

    
    def network_node_total_mem(self, addr):
      """
      Returns the total memory of the node.
      """
      return self.__network_node_machine_memory(addr=addr)
    
    
    def network_node_avail_mem(self, addr, norm=False):
      """
      Returns the available memory of the node.
      If norm is True, returns the percentage of available memory.
      """
      return self.network_node_available_memory(addr=addr, norm=norm)
    

    def network_node_is_ok_available_memory_prc(self, addr, min_prc_available=0.20):
      # can create other heuristics based on what happened on the last x minutes interval (using _network_node_past_available_memory_by_interval)
      prc_available_mem = self.network_node_available_memory_prc(addr=addr)
      return prc_available_mem >= min_prc_available

    def network_node_is_ok_available_memory_size(self, addr, min_gb_available=2):
      # can create other heuristics based on what happened on the last x minutes interval (using _network_node_past_available_memory_by_interval)
      available_mem = self.network_node_available_memory(addr=addr)
      return available_mem >= min_gb_available


    def network_node_is_ok_device_status(self, addr, dt_now=None):
      if self.__network_node_last_device_status(addr=addr) != ct.DEVICE_STATUS_ONLINE:
        return False

      if ct.DEVICE_STATUS_EXCEPTION in self.__network_node_past_device_status_by_interval(addr=addr, minutes=60):
        return False
      
      if self.network_node_last_seen(addr=addr, as_sec=True, dt_now=dt_now) > 60:
        return False

      return True

    def network_node_simple_status(self, addr, dt_now=None):
      if ct.DEVICE_STATUS_EXCEPTION in self.__network_node_past_device_status_by_interval(addr=addr, minutes=60):
        return "PAST-EXCEPTION"
      
      if self.network_node_last_seen(addr=addr, as_sec=True, dt_now=dt_now) > 60:
        return "LOST STATUS"

      last_status = self.__network_node_last_device_status(addr=addr)
      return last_status
    
    
    def network_node_is_online(self, addr, dt_now=None):
      return self.network_node_simple_status(addr=addr, dt_now=dt_now) == ct.DEVICE_STATUS_ONLINE            
    
    
    def network_node_py_ver(self, addr):
      result = None
      hb = self.__network_node_last_heartbeat(addr)
      if isinstance(hb, dict):
        result = hb.get(ct.HB.PY_VER)
      return result    
    
    
    def network_node_r1fs_id(self, addr):
      result = None
      hb = self.__network_node_last_heartbeat(addr)
      if isinstance(hb, dict):
        result = hb.get(ct.HB.R1FS_ID)
      return result
    
    
    def network_node_r1fs_online(self, addr):
      result = None
      hb = self.__network_node_last_heartbeat(addr)
      if isinstance(hb, dict):
        result = hb.get(ct.HB.R1FS_ONLINE)
      return result
    
    
    def network_node_r1fs_relay(self, addr):
      result = None
      hb = self.__network_node_last_heartbeat(addr)
      if isinstance(hb, dict):
        result = hb.get(ct.HB.R1FS_RELAY)
      return result
    
    
    def network_node_version(self, addr):
      result = None
      hb = self.__network_node_last_heartbeat(addr)
      if isinstance(hb, dict):
        result = hb.get(ct.HB.VERSION)
      return result

    
    def network_node_is_recent(self, addr, dt_now=None, max_recent_minutes=15):
      elapsed_seconds = self.network_node_last_seen(addr=addr, as_sec=True, dt_now=dt_now)
      mins = elapsed_seconds / 60
      recent = mins <= max_recent_minutes
      return recent


    def network_node_is_ok_cpu_used(self, addr, max_cpu_used=50):
      # can create other heuristics based on what happened on the last x minutes interval (using _network_node_past_cpu_used_by_interval)
      return self.__network_node_last_cpu_used(addr=addr) <= max_cpu_used


    def network_node_is_available(self, addr):
      ok_loops_timings = self.network_node_is_ok_loops_timings(addr=addr, max_main_loop_timing=5)
      ok_avail_disk = self.network_node_is_ok_available_disk_size(addr=addr, min_gb_available=5)
      ok_avail_mem = self.network_node_is_ok_available_memory_size(addr=addr)
      ok_cpu_used = self.network_node_is_ok_cpu_used(addr=addr, max_cpu_used=50)
      ok_device_status = self.network_node_is_ok_device_status(addr=addr)
      ok_uptime = self.network_node_is_ok_uptime(addr=addr, min_uptime=60)

      # TODO: add uptime back
      ok_node = ok_loops_timings and ok_avail_disk and ok_avail_mem and ok_cpu_used and ok_device_status # and ok_uptime
      return ok_node

    def network_node_is_accessible(self, addr):
      """
      Method to check if the remote node is accessible to the local node.
      Parameters
      ----------
      addr : str
          The address of the remote node

      Returns
      -------
      bool
          True if the remote node is accessible, False otherwise
      """
      is_local = addr == self.node_addr
      is_allowed = self.__remove_address_prefix(self.node_addr) in self.network_node_whitelist(addr=addr)
      is_unsecured = not self.network_node_is_secured(addr=addr)
      return is_allowed or is_local or is_unsecured

    def network_node_gpu_capability(
        self, addr, device_id, min_gpu_used=20, max_gpu_used=90,
        min_prc_allocated_mem=20, max_prc_allocated_mem=90,
        min_gpu_mem_gb=4, max_gpu_mem_gb=30,
        show_warnings=False
    ):

      gpus = self.__network_node_last_gpus(addr=addr)
      dct_ret = {
        'WEIGHTED_CAPABILITY'       : 0, 
        'INDIVIDUAL_CAPABILITIES'   : {}, 
        'DEVICE_ID'                 : device_id,
        'NAME'                      : None,
      }

      if not isinstance(device_id, int):
        if show_warnings:
          self.P("Requested device_id '{}' in `network_node_gpu_capability` is not integer for e2:{}".format(device_id, addr), color='r')
        return dct_ret

      if device_id >= len(gpus):
        if show_warnings:
          self.P("Requested device_id '{}' in `network_node_gpu_capability` not available e2:{}".format(device_id, addr), color='r')
        return dct_ret

      dct_g = gpus[device_id]
      dct_ret['NAME'] = dct_g.get('NAME')

      # these default values for `get`s are meant to generate a 0 score for each monitorized parameter if they are not returned in the dictionary
      allocated_mem = dct_g.get('ALLOCATED_MEM', 1) or 1
      total_mem = dct_g.get('TOTAL_MEM', 1) or 1
      gpu_used = dct_g.get('GPU_USED', 100) or 100
      prc_allocated_mem = 100 * allocated_mem / total_mem

      capabilities = {
        'GPU_USED'      : {'SCORE': None, 'WEIGHT': 0.4, 'STR_VAL' : "{:.2f}%".format(gpu_used)},
        'GPU_MEM'       : {'SCORE': None, 'WEIGHT': 0.2, 'STR_VAL' : "{:.2f}GB".format(total_mem)},
        'ALLOCATED_MEM' : {'SCORE': None, 'WEIGHT': 0.4, 'STR_VAL' : "{:.2f}%".format(prc_allocated_mem)},
      }

      capabilities['ALLOCATED_MEM']['SCORE'] = round(exponential_score(
        left=min_prc_allocated_mem, right=max_prc_allocated_mem,
        val=prc_allocated_mem, right_is_better=False
      ), 2)
      capabilities['GPU_USED']['SCORE'] = round(exponential_score(
        left=min_gpu_used, right=max_gpu_used,
        val=gpu_used, right_is_better=False
      ), 2)
      capabilities['GPU_MEM']['SCORE'] = round(exponential_score(
        left=min_gpu_mem_gb, right=max_gpu_mem_gb,
        val=total_mem, right_is_better=True
      ), 2)
      dct_ret['INDIVIDUAL_CAPABILITIES'] = capabilities

      weighted_capability = 0
      for sw in capabilities.values():
        score = sw['SCORE']
        weight = sw['WEIGHT']

        if score == 0:
          # if any parameter has score 0, then it means something is wrong with the gpu, thus it can't be used
          return dct_ret

        weighted_capability += score * weight
      #endfor

      dct_ret['WEIGHTED_CAPABILITY'] = round(weighted_capability, 2)
      return dct_ret

    def network_node_default_gpu_capability(
        self, addr, min_gpu_used=20, max_gpu_used=90,
        min_prc_allocated_mem=20, max_prc_allocated_mem=90,
        min_gpu_mem_gb=4, max_gpu_mem_gb=30,
        show_warnings=False
    ):
      default_cuda = self.__network_node_default_cuda(addr=addr, as_int=True)
      dct_gpu_capability = self.network_node_gpu_capability(
        addr=addr, device_id=default_cuda,
        min_gpu_used=min_gpu_used,
        max_gpu_used=max_gpu_used,
        min_prc_allocated_mem=min_prc_allocated_mem,
        max_prc_allocated_mem=max_prc_allocated_mem,
        min_gpu_mem_gb=min_gpu_mem_gb,
        max_gpu_mem_gb=max_gpu_mem_gb,
        show_warnings=show_warnings
      )

      return dct_gpu_capability
    

    def network_node_gpus_capabilities(
        self, addr, min_gpu_used=20, max_gpu_used=90,
        min_prc_allocated_mem=20, max_prc_allocated_mem=90,
        min_gpu_mem_gb=8, max_gpu_mem_gb=30,
        show_warnings=False
    ):
      capabilities = []
      for device_id in range(len(self.__network_node_last_gpus(addr=addr))):
        dct_gpu_capability = self.network_node_gpu_capability(
          addr=addr, device_id=device_id,
          min_gpu_used=min_gpu_used,
          max_gpu_used=max_gpu_used,
          min_prc_allocated_mem=min_prc_allocated_mem,
          max_prc_allocated_mem=max_prc_allocated_mem,
          min_gpu_mem_gb=min_gpu_mem_gb,
          max_gpu_mem_gb=max_gpu_mem_gb,
          show_warnings=show_warnings
        )

        capabilities.append(dct_gpu_capability)
      # endfor

      return capabilities


    def network_top_n_avail_nodes(self, n, min_gpu_capability=10, verbose=1, permit_less=False):
      """
      This method will return the top n available nodes in the network based on their GPU capabilities.

      Parameters
      ----------
      n : int
          The number of nodes to return
          
      min_gpu_capability : int, optional
          The minimum GPU capability, by default 10
          
      verbose : int, optional
          show info, by default 1
          
      permit_less : bool, optional
          If True will return even below minimal capability, by default False

      Returns
      -------
      """
      ### TODO continous process (1 iter/s), `network_top_n_aval_nodes` just have to return the map, not to compute it every time.
      ### TODO nmon_reader (shared object) that reads and returns the map. Effective nmon will be thread (continous process)

      def log_nodes_details():
        self.P("Top {} available nodes search finished. There are {}/{} available nodes in the network.".format(
          n, len(lst_available_nodes), len(lst_nodes)
        ))

        if len(lst_tuples) > 0:
          str_log = "There are {}/{} nodes with GPU capabilities: (GPU_USED: {}->{} / ALLOCATED_MEM: {}->{} / GPU_MEM: {}->{})".format(
            len(lst_tuples), len(lst_available_nodes),
            min_gpu_used, max_gpu_used,
            min_prc_allocated_mem, max_prc_allocated_mem,
            min_gpu_mem_gb, max_gpu_mem_gb,
          )
          for name, score in lst_tuples:
            individual_capabilities = dct_individual_capabilities[name]
            details = " | ".join(["{}: {}".format(_k,_v) for _k,_v in individual_capabilities.items()])
            str_log += "\n * {}: {} (device_id: {}) (details: {})".format(name, score, dct_device_id[name], details)
          #endfor
          self.P(str_log)
        else:
          self.P("No available node with GPU capabilities.", color='y')
        return
      #enddef

      lst_nodes = self.__network_nodes_list()
      lst_available_nodes = list(filter(
        lambda _addr: self.network_node_is_available(addr=_addr),
        lst_nodes
      ))

      # filter the nodes that are not in the whitelist (working with no-prefix addresses only)
      lst_allowed_nodes = list(filter(
        lambda _addr:  self.__remove_address_prefix(self.node_addr) in self.network_node_whitelist(addr=_addr) or _addr == self.node_addr or not self.network_node_is_secured(addr=_addr),
        lst_available_nodes
      ))

      lst_capabilities = []
      dct_individual_capabilities = {}
      dct_device_id = {}
      min_gpu_used, max_gpu_used = 20, 90
      min_prc_allocated_mem, max_prc_allocated_mem = 20, 90
      min_gpu_mem_gb, max_gpu_mem_gb = 4, 40
      for _addr in lst_allowed_nodes:
        dct_gpu_capability = self.network_node_default_gpu_capability(
          addr=_addr,
          min_gpu_used=min_gpu_used, max_gpu_used=max_gpu_used,
          min_prc_allocated_mem=min_prc_allocated_mem, max_prc_allocated_mem=max_prc_allocated_mem,
          min_gpu_mem_gb=min_gpu_mem_gb, max_gpu_mem_gb=max_gpu_mem_gb,
        )

        lst_capabilities.append(dct_gpu_capability['WEIGHTED_CAPABILITY'])
        dct_individual_capabilities[_addr] = dct_gpu_capability['INDIVIDUAL_CAPABILITIES']
        dct_device_id[_addr] = dct_gpu_capability['DEVICE_ID']
      #endfor

      np_capabilities_ranking = np.argsort(lst_capabilities)[::-1]

      np_nodes_sorted = np.array(lst_allowed_nodes)[np_capabilities_ranking]
      np_capabilities_sorted = np.array(lst_capabilities)[np_capabilities_ranking]

      good_indexes = np.where(np_capabilities_sorted >= min_gpu_capability)[0]

      good_nodes_sorted = list(map(lambda elem: str(elem), np_nodes_sorted[good_indexes][:n]))
      good_capabilities_sorted = list(map(lambda elem: float(elem), np_capabilities_sorted[good_indexes][:n]))
      lst_tuples = list(zip(good_nodes_sorted, good_capabilities_sorted))
      nr_found_workers = len(lst_tuples)

      if verbose >= 1:
        log_nodes_details()

      if nr_found_workers == n:
        final_log = "Successfully found {} workers: {}".format(nr_found_workers, good_nodes_sorted)
        color = 'g'
        ret = good_nodes_sorted
      else:
        final_log = "Unsuccessful search - only {}/{} workers qualify: {}".format(nr_found_workers, n, good_nodes_sorted)
        color = 'y'
        ret = [] if not permit_less else good_nodes_sorted
      #endif

      if verbose >= 1:
        self.P(final_log, color=color)

      return ret
    
    
    def network_save_status(self):
      self.P("Saving network map status...")
      with self.log.managed_lock_resource(NETMON_MUTEX):

        self.start_timer("network_save_status")
        self.log.save_pickle_to_data(
          data=self.__network_heartbeats, 
          fn=NETMON_DB,
          subfolder_path='network_monitor'
        )
        # now we add epoch manager save
        self.epoch_manager.save_status()
        elapsed = self.end_timer("network_save_status")
        self.P("Network map status saved in {:.2f} seconds".format(elapsed))
      # endwith lock
      return
    
    
    def network_load_status(self, external_db=None):
      """
      Load network map status from previous session.
      """
      result = False
      
      if external_db is None:
        _fn = os.path.join(NETMON_DB_SUBFOLDER, NETMON_DB)
        db_file = self.log.get_data_file(_fn)
      else:
        db_file = external_db if os.path.isfile(external_db) else None
      #endif external_db is not None

      if db_file is not None:
        self.P("Previous nodes states found. Loading network map status...")
        __network_heartbeats = self.log.load_pickle(db_file)
        __network_heartbeats = self.__maybe_convert_node_id_address(__network_heartbeats)
        if __network_heartbeats is not None:
          # update the current network info with the loaded info
          # this means that all heartbeats received until this point
          # will be appended after the loaded ones 
          current_heartbeats = self.__network_heartbeats # save current heartbeats maybe already received
          self._set_network_heartbeats(__network_heartbeats) # load the history
          nr_loaded = len(self.__network_heartbeats)
          nr_received = len(current_heartbeats)
          previous_keys = set(self.__network_heartbeats.keys())
          current_keys = set(current_heartbeats.keys())
          not_present_keys = previous_keys - current_keys
          
          # keys are without prefix, so we add it
          not_present_addrs = [self.__network_heartbeats[x][-1].get(ct.HB.EE_ADDR, None) for x in not_present_keys]
          not_present_addrs = [x for x in not_present_addrs if x is not None]
          not_present_eeids = [self.__network_node_last_heartbeat(x).get(ct.EE_ID) for x in not_present_addrs]
          not_present_nodes = [f"{node_id}: {node_addr}" for node_id, node_addr in zip(not_present_eeids, not_present_addrs)]
          self.P("Current network of {} nodes inited with {} previous nodes".format(
            nr_received, nr_loaded), boxed=True
          )
          self.P("Nodes not present in current network: {}".format(not_present_nodes), color='r')
          # lock the NETMON_MUTEX
          # now put back the newest heartbeats we received before loading the history
          for addr in current_heartbeats:
            for data in current_heartbeats[addr]:
              # TODO: replace register_heartbeat with something simpler
              self.__register_heartbeat(addr, data)
          # unlock the NETMON_MUTEX
          # end for
          result = True
        else:
          msg = "Error loading network map status"
          msg += "\n  File: {}".format(db_file)
          msg += "\n  Size: {}".format(os.path.getsize(db_file))
          self.P(msg, color='r')
        #endif __network_heartbeats loaded ok
      else:
        self.P("No previous network map status found.", color='r')
      #endif db_file is not None
      self.state_already_loaded = True # register even the try failed
      return result
    
      
    def network_node_last_seen(self, addr, as_sec=True, dt_now=None):
      """
      Returns the `datetime` in local time when a particular remote node has last been seen
      according to its heart-beats.

      Parameters
      ----------
      addr : str
        the node address.
        
      as_sec: bool (optional)
        will returns seconds delta instead of actual date
        
      dt_now: datetime (optional)
        replace now datetime with given one. default uses current datetime

      Returns
      -------
      dt_remote_to_local : datetime
        the local datetime when node was last seen.
      
        OR
      
      elapsed: float
        number of seconds last seen
      

      """
      hb = self.__network_node_last_heartbeat(addr=addr, return_empty_dict=True)
      if len(hb) == 0:
        return 9999999999 if as_sec else None

      ts = hb.get(ct.HB.RECEIVED_TIME)
      tz = self.log.timezone

      if ts is None:
        # if heartbeat is too old, we can't know when it was received
        # so we use the timestamp of the heartbeat
        ts = hb[ct.PAYLOAD_DATA.EE_TIMESTAMP]
        tz = hb.get(ct.PAYLOAD_DATA.EE_TIMEZONE)

      dt_remote_to_local = self.log.utc_to_local(ts, tz, fmt=ct.HB.TIMESTAMP_FORMAT)
      if dt_now is None:
        dt_now = dt.now()

      elapsed = dt_now.timestamp() - dt_remote_to_local.timestamp()

      if as_sec:
        return elapsed
      else:
        return dt_remote_to_local
    
    def network_node_past_temperatures_history(
      self, addr, minutes=60, dt_now=None, 
      reverse_order=True, return_timestamps=False
    ):
      """
      Returns the temperature history of a remote node in the last `minutes` minutes.

      Parameters
      ----------
      
      addr : str
          address of the node
      minutes : int, optional
          minutes to look back, by default 60
      dt_now : datetime, optional
          override the now-time, by default None
      reverse_order : bool, optional  
          return the list in reverse order, by default True
              
      """
      result = None

      lst_heartbeats = self.__network_node_past_heartbeats_by_interval(
        addr=addr, minutes=minutes, dt_now=dt_now, reverse_order=reverse_order,
      )
      temperatures = [x[ct.HB.TEMPERATURE_INFO] for x in lst_heartbeats if x is not None]
      max_temps = [x['max_temp'] for x in temperatures if x is not None]
      temps = [x['temperatures'] for x in temperatures if x is not None]
      max_temp_sensor = [x['max_temp_sensor'] for x in temperatures if x is not None]

      result = {
        'all_sensors' : temperatures,
        'max_temp'   : max_temps,
        'max_temp_sensor' :  max_temp_sensor[-1] if len(max_temp_sensor) > 0 else None,
      }
      return result
    
    
    def network_node_default_cuda(self, addr, as_int=True):
      """
      Returns the default CUDA device ID of a remote node.
      If no GPU is available, returns None.
      
      Parameters
      ----------
      addr : str
          The address of the remote node.
      as_int : bool, optional
          If True, returns the device ID as an integer, by default False (returns as string).
      
      Returns
      -------
      int or str or None
          The default CUDA device ID or None if no GPU is available.
      """
      return self.__network_node_default_cuda(addr=addr, as_int=as_int)
    
    
    def network_node_default_gpu_data(self, addr):
      result = {}
      gpus = self.__network_node_last_gpus(addr=addr)
      if len(gpus) > 0:
        device_id = self.__network_node_default_cuda(addr=addr)
        if not isinstance(device_id, int):
          device_id = 0
        result = gpus[device_id]
      return result
    

    def network_node_default_gpu_name(self, addr):
      """
      Returns the name of the default GPU of a remote node.
      If no GPU is available, returns None.
      """
      default_gpu = self.network_node_default_gpu_data(addr=addr)     
      return default_gpu.get('NAME', None)
    
    
    def network_node_default_gpu_total_mem(self, addr):
      """
      Returns the memory of the default GPU of a remote node.
      If no GPU is available, returns None.
      """
      default_gpu = self.network_node_default_gpu_data(addr=addr)     
      return default_gpu.get('TOTAL_MEM', None)
    
    
    def network_node_default_gpu_avail_mem(self, addr):
      """
      Returns the available memory of the default GPU of a remote node.
      If no GPU is available, returns None.
      """
      default_gpu = self.network_node_default_gpu_data(addr=addr)     
      return default_gpu.get('FREE_MEM', None)
    
    
    def network_node_default_gpu_load(self, addr):
      """
      Returns the load of the default GPU of a remote node.
      If no GPU is available, returns None.
      """
      default_gpu = self.network_node_default_gpu_data(addr=addr)     
      return default_gpu.get('GPU_USED', None)
    
    
    def network_node_default_gpu_usage(self, addr):
      """
      Returns the usage of the default GPU of a remote node.
      If no GPU is available, returns None.
      """
      return self.network_node_default_gpu_load(addr=addr)
    
    def network_node_last_gpu_status(self, addr):
      """
      Returns the last GPU status of a remote node.
      If no GPU is available, returns None.
      """
      gpus = self.__network_node_last_gpus(addr=addr)
      return gpus
    
    
    def network_node_gpu_summary(self, addr):
      """
      Returns a summary of the GPU status of a remote node.
      If no GPU is available, returns None.
      """
      hb = self.__network_node_last_heartbeat(addr=addr, return_empty_dict=True)
      gpu_info = hb.get(ct.HB.GPU_INFO, None)
      return gpu_info

    
      
    def network_node_default_gpu_history(
      self, addr, minutes=60, dt_now=None, 
      reverse_order=True, return_timestamps=False
    ):
      device_id = self.__network_node_default_cuda(addr=addr)
      lst_statuses, timestamps = [], []
      if device_id is not None:
        result = self.__network_node_past_gpus_by_interval(
          addr=addr, minutes=minutes, dt_now=dt_now, 
          reverse_order=reverse_order, return_timestamps=return_timestamps,
        )
        if return_timestamps:
          lst_all_statuses, timestamps = result
        else:
          lst_all_statuses = result
          
        try:
          # TODO: fix this bug !
          lst_statuses = [x[device_id] for x in lst_all_statuses]
        except:
          pass
      
      if return_timestamps:
        return lst_statuses, timestamps
      return lst_statuses
      
    
    def network_node_default_gpu_average_avail_mem(self, addr, minutes=60, dt_now=None):
      result = None
      lst_statuses = self.network_node_default_gpu_history(addr=addr, minutes=minutes, dt_now=dt_now)
      mem = [x['FREE_MEM'] for x in lst_statuses]
      try:
        val = np.mean(mem)
        result = round(val, 1) if not np.isnan(val) else None
      except:
        pass
      return result
    
    
    def network_node_default_gpu_average_load(self, addr, minutes=60, dt_now=None):
      result = None
      lst_statuses = self.network_node_default_gpu_history(addr=addr, minutes=minutes, dt_now=dt_now)      
      try:
        gpuload = [x['GPU_USED'] for x in lst_statuses]
        val = np.mean(gpuload)
        result = round(val, 1) if not np.isnan(val) else None
      except:
        pass
      return result
    
    
    def network_node_remote_time(self, addr):
      hb = self.__network_node_last_heartbeat(addr=addr, return_empty_dict=True)
      return hb.get(ct.HB.CURRENT_TIME)
    
    
    def network_node_deploy_type(self, addr):
      hb = self.__network_node_last_heartbeat(addr=addr, return_empty_dict=True)
      return hb.get(ct.HB.GIT_BRANCH)      
    

    def network_node_is_supervisor(self, addr):
      hb = self.__network_node_last_heartbeat(addr=addr, return_empty_dict=True)
      res = hb.get(ct.HB.EE_IS_SUPER, False)
      if res is None:
        res = False
      if isinstance(res, str):
        res = res.lower() == 'true'
      return res


    def network_node_addr(self, eeid, include_prefix=False):
      addr = None
      candidates = []
      for addr in self.all_nodes:
        hb = self.__network_node_last_heartbeat(addr=addr, return_empty_dict=True)
        if hb.get(ct.EE_ID) == eeid:
          candidates.append(addr)
      if len(candidates) == 0:
        addr = None
      elif len(candidates) == 1:
        addr = candidates[0]
      else:
        # if there are multiple candidates, we will return the one with the most recent heartbeat
        lst_last_seen = [(addr, self.network_node_last_seen(addr=addr, as_sec=True)) for addr in candidates]
        addr = min(lst_last_seen, key=lambda x: x[1])[0]
      
      if include_prefix and addr is not None:
        addr = self._add_address_prefix(addr)
        
      return addr


    def network_node_eeid(self, addr):
      hb = self.__network_node_last_heartbeat(addr=addr, return_empty_dict=True)
      return hb.get(ct.EE_ID, MISSING_ID)

    def network_node_has_did(self, addr: str):
      """ Returns True if the node has DID (Docker In Docker) enabled in the heartbeat."""
      hb = self.__network_node_last_heartbeat(addr=addr, return_empty_dict=True)
      return hb.get(ct.HB.DID, False)

    def network_node_comm_relay(self, addr: str):
      """Returns the communication relay of a remote node as indicated in the first heartbeat."""
      hb = self.__network_node_last_heartbeat(addr=addr, return_empty_dict=True)
      return hb.get(ct.HB.COMM_RELAY, '')

    def network_node_whitelist(self, addr):
      """Returns the whitelist of a remote node exactly as it was received in the heartbeat - naturally without any prefix."""
      hb = self.__network_node_last_heartbeat(addr=addr, return_empty_dict=True)
      return hb.get(ct.HB.EE_WHITELIST, ['<abnormal list>'])
    
    def network_node_local_tz(self, addr, as_zone=True):
      hb = self.__network_node_last_heartbeat(addr=addr, return_empty_dict=True)
      if as_zone:
        return hb.get(ct.PAYLOAD_DATA.EE_TZ)
      else:
        return hb.get(ct.PAYLOAD_DATA.EE_TIMEZONE)
      
    def network_node_today_heartbeats(self, addr, dt_now=None):
      """
      Returns the today (overridable via dt_now) heartbeats of a particular remote node.

      Parameters
      ----------
      addr : str
          address of the node
      dt_now : datetime, optional
          override the now-time, by default None
      """
      if dt_now is None:
        dt_now = dt.now()
      dt_now = dt_now.replace(hour=0, minute=0, second=0, microsecond=0)
      hbs = self.__network_heartbeats[addr]
      for hb in hbs:
        ts = hb[ct.PAYLOAD_DATA.EE_TIMESTAMP]
        dt_ts = self.log.utc_to_local(ts, fmt=ct.HB.TIMESTAMP_FORMAT)
        if dt_ts >= dt_now:
          yield hb
      
            
    def network_node_is_secured(self, addr):
      hb = self.__network_node_last_heartbeat(addr=addr, return_empty_dict=True)
      return hb.get(ct.HB.SECURED, False) 
    
    
    def network_node_pipelines(self, addr):
      """ 
      This function returns the pipelines of a remote node based on the cached information.
      Formerly, it was based on the heartbeat information as shown below, but now it is based on the cached information.
      
        hb = self.__network_node_last_heartbeat(addr=addr, return_empty_dict=True)
        return hb.get(ct.HB.CONFIG_STREAMS)
      
      """
      __addr_no_prefix = self.__remove_address_prefix(addr)
      node_info = self.__nodes_pipelines.get(__addr_no_prefix, {})
      return node_info.get(NetMonCt.PIPELINES, [])
    
    
    def network_node_pipeline_info(self, addr, pipeline):
      """
      This function returns the pipeline info of a remote node based on the cached information.
      Formerly, it was based on the heartbeat information as shown below, but now it is based on the cached information.
      
        hb = self.__network_node_last_heartbeat(addr=addr, return_empty_dict=True)
        return hb.get(ct.HB.CONFIG_STREAMS)
      
      """
      __addr_no_prefix = self.__remove_address_prefix(addr)
      pipelines = self.network_node_pipelines(addr=__addr_no_prefix)
      for pipeline_info in pipelines:
        if pipeline_info.get('NAME') == pipeline:
          return pipeline_info
      return {}
    
    
    def network_node_apps(self, addr):
      """
      This function returns the apps of a remote node based on the cached information.
      Formerly, it was based on the heartbeat information as shown below, but now it is based 
      on the cached information.
      """
      __addr_no_prefix = self.__remove_address_prefix(addr)
      node_info = self.__nodes_pipelines.get(__addr_no_prefix, {})
      plugins_statuses = node_info.get(NetMonCt.PLUGINS_STATUSES, [])
      pipelines = node_info.get(NetMonCt.PIPELINES, [])
      apps = {}
      
      if isinstance(pipelines, list) and len(pipelines) > 0:
        for pipeline_info in pipelines:
          pipeline = pipeline_info.get(ct.NAME)
          apps[pipeline] = {
            NetMonCt.INITIATOR : pipeline_info.get(ct.CONFIG_STREAM.K_INITIATOR_ADDR),
            NetMonCt.OWNER : pipeline_info.get(ct.CONFIG_STREAM.K_OWNER, None),
            NetMonCt.LAST_CONFIG : pipeline_info.get(ct.CONFIG_STREAM.LAST_UPDATE_TIME),
            NetMonCt.IS_DEEPLOYED : pipeline_info.get(ct.CONFIG_STREAM.IS_DEEPLOYED, False) == True,
            NetMonCt.DEEPLOY_SPECS : pipeline_info.get(ct.CONFIG_STREAM.DEEPLOY_SPECS, {}),
            NetMonCt.PLUGINS : {}
          }

          plugins = pipeline_info.get(ct.PLUGINS, [])
          for plugin_conf in plugins:
            signature = plugin_conf.get(ct.SIGNATURE)
            if signature is None:
              continue
            if signature not in apps[pipeline][NetMonCt.PLUGINS]:
              apps[pipeline][NetMonCt.PLUGINS][signature] = []
              instances = plugin_conf[ct.INSTANCES]
              for instance_conf in instances:
                instance_id = instance_conf.get(ct.INSTANCE_ID)
                instance_info = {
                  NetMonCt.PLUGIN_INSTANCE : instance_id,
                  NetMonCt.PLUGIN_START : instance_conf.get(ct.HB.ACTIVE_PLUGINS_INFO.INIT_TIMESTAMP),
                  NetMonCt.PLUGIN_LAST_ALIVE : instance_conf.get(ct.HB.ACTIVE_PLUGINS_INFO.EXEC_TIMESTAMP),
                  NetMonCt.PLUGIN_LAST_ERROR : instance_conf.get(ct.HB.ACTIVE_PLUGINS_INFO.LAST_ERROR_TIME),
                  NetMonCt.INSTANCE_CONF: instance_conf
                }
                for status_info in plugins_statuses:
                  # now we check for instance_id, pipeline, signature
                  if (
                    status_info.get(ct.HB.ACTIVE_PLUGINS_INFO.INSTANCE_ID) == instance_id and
                    status_info.get(ct.HB.ACTIVE_PLUGINS_INFO.STREAM_ID) == pipeline and
                    status_info.get(ct.HB.ACTIVE_PLUGINS_INFO.SIGNATURE) == signature
                  ):
                    instance_info[NetMonCt.PLUGIN_START] = status_info.get(ct.HB.ACTIVE_PLUGINS_INFO.INIT_TIMESTAMP)
                    instance_info[NetMonCt.PLUGIN_LAST_ALIVE] = status_info.get(ct.HB.ACTIVE_PLUGINS_INFO.EXEC_TIMESTAMP)
                    instance_info[NetMonCt.PLUGIN_LAST_ERROR] = status_info.get(ct.HB.ACTIVE_PLUGINS_INFO.LAST_ERROR_TIME)
                    break
                  #end found the plugin status
                #end search for status
                apps[pipeline][NetMonCt.PLUGINS][signature].append(instance_info)
              # end for each instance of the current signature
            # endif signature is new
          # end for each plugin
        # end for each pipeline
        
      # if isinstance(plugins_statuses, list) and len(plugins_statuses) > 0:
      #   for status in plugins_statuses:
      #     pipeline = status.get(ct.HB.ACTIVE_PLUGINS_INFO.STREAM_ID)
      #     signature = status.get(ct.HB.ACTIVE_PLUGINS_INFO.SIGNATURE)
      #     if pipeline not in apps:
      #       pipeline_info = self.network_node_pipeline_info(addr=__addr_no_prefix, pipeline=pipeline)

      #     if signature not in apps[pipeline][NetMonCt.PLUGINS]:
      #       apps[pipeline][NetMonCt.PLUGINS][signature] = []
      #     apps[pipeline][NetMonCt.PLUGINS][signature].append({
      #       NetMonCt.PLUGIN_INSTANCE      : status.get(ct.HB.ACTIVE_PLUGINS_INFO.INSTANCE_ID),
      #       NetMonCt.PLUGIN_START         : status.get(ct.HB.ACTIVE_PLUGINS_INFO.INIT_TIMESTAMP),
      #       NetMonCt.PLUGIN_LAST_ALIVE    : status.get(ct.HB.ACTIVE_PLUGINS_INFO.EXEC_TIMESTAMP),
      #       NetMonCt.PLUGIN_LAST_ERROR    : status.get(ct.HB.ACTIVE_PLUGINS_INFO.LAST_ERROR_TIME),
      #     })
      # else:
      #   pass # maybe some other logic to be added here
      return apps
    
    
    def network_known_apps(self, target_nodes=None):
      """
      This function returns the apps of all remote ONLINE nodes based on the cached information.
      """
      apps = {}
      fails = {}
      if target_nodes is None:
        target_nodes = list(self.__nodes_pipelines.keys())
      for addr in target_nodes:
        if self.network_node_is_online(addr=addr):
          node_apps = self.network_node_apps(addr=addr)
          if len(node_apps) == 0:
            fails[addr] = self.network_node_pipelines(addr=addr)
          full_addr = self._add_address_prefix(addr)
          apps[full_addr] = node_apps
      if len(fails) > 0:
        self.P("Failed to get plugin infor for following nodes(pipelines):\n{}".format(
            json.dumps(fails, indent=2)
          ), color='r'
        )
      return apps

    def network_known_pipelines(self, target_nodes=None):
      """
      This function returns the pipelines of all remote ONLINE nodes based on the cached information.
      """
      apps = {}
      fails = {}
      if target_nodes is None:
        target_nodes = list(self.__nodes_pipelines.keys())
      for addr in target_nodes:
        if self.network_node_is_online(addr=addr):
          node_apps = self.network_node_pipelines(addr=addr)
          # Filter out admin_pipeline entries
          filtered_apps = []
          for pipeline in node_apps:
            pipeline_name = pipeline.get(ct.CONFIG_STREAM.K_NAME)
            if pipeline_name != "admin_pipeline":
              filtered_apps.append(pipeline)
          full_addr = self._add_address_prefix(addr)
          apps[full_addr] = filtered_apps
      if len(fails) > 0:
        self.P("Failed to get plugin infor for following nodes(pipelines):\n{}".format(
          json.dumps(fails, indent=2)
        ), color='r'
        )
      return apps
        
    
    def network_node_hb_interval(self, addr):
      hb = self.__network_node_last_heartbeat(addr=addr, return_empty_dict=True)
      return hb.get(ct.HB.EE_HB_TIME)
  
    
    def network_node_status(self, addr, min_uptime=60, dt_now=None):
      try:
        eeid = self.network_node_eeid(addr)
        avail_disk = self.__network_node_last_available_disk(addr=addr, norm=False)
        avail_disk_prc = round(self.__network_node_last_available_disk(addr=addr, norm=True),3)

        avail_mem = self.__network_node_last_available_memory(addr=addr, norm=False)
        avail_mem_prc = round(self.__network_node_last_available_memory(addr=addr, norm=True), 3)

        is_alert_disk = avail_disk_prc < 0.15
        is_alert_ram = avail_mem_prc < 0.15

        #comms
        dct_comms = self.network_node_last_comm_info(addr=addr)
        #end comms

        dct_gpu_capability = self.network_node_default_gpu_capability(addr=addr)
        gpu_name = dct_gpu_capability['NAME']
        
        score=dct_gpu_capability['WEIGHTED_CAPABILITY']
        
        uptime_sec = round(self.__network_node_uptime(addr=addr, as_minutes=False),2)      
        uptime_min = uptime_sec / 60
        ok_uptime = uptime_sec >= (min_uptime * 60)
        
        working_status = self.network_node_simple_status(addr=addr, dt_now=dt_now)
        is_online = working_status == ct.DEVICE_STATUS_ONLINE
        
        recent = self.network_node_is_recent(addr=addr, dt_now=dt_now)

        trusted = recent and is_online and ok_uptime
        trust_val = exponential_score(left=0, right=min_uptime * 4, val=uptime_min, normed=True, right_is_better=True)
        trust = 0 if not is_online else round(trust_val,3)
        trust = trusted * trust
        
        score = round(score * trust_val,2)
        if trusted and score == 0:
          score = 10
          
        cpu_past1h = round(np.mean(self.__network_node_past_cpu_used_by_interval(addr=addr, minutes=60, dt_now=dt_now)),2)
        cpu_past1h = cpu_past1h if not np.isnan(cpu_past1h) else None
        main_loop_time = self.network_node_main_loop(addr) 
        main_loop_freq = 0 if main_loop_time == 0 else 1 / (main_loop_time + 1e-14)
        
        trust_info = 'NORMAL_EVAL'

        # Cpu temperature history analysis
        temp_hist = self.network_node_past_temperatures_history(
          addr=addr, minutes=60, dt_now=dt_now,
          reverse_order=True,
        )

        max_temperature = temp_hist['max_temp'] # get pre-processed max temperatures

        cpu_temp = max_temperature[-1] if len(max_temperature) > 0 else -1
        cpu_temp_past1h = np.mean(max_temperature) if len(max_temperature) > 0 else -1
        
        # Gpu temperature history analysis
        gpu_hist = self.network_node_default_gpu_history(
          addr=addr, minutes=60, dt_now=dt_now, reverse_order=True)

        gpu_temp_hist = [x['GPU_TEMP'] for x in gpu_hist]
        gpu_temp = gpu_temp_hist[-1] if len(gpu_temp_hist) > 0 else None
        gpu_temp_past1h = np.mean(gpu_temp_hist) if len(gpu_temp_hist) > 0 else None
        
        gpu_fan_hist = [x.get('GPU_FAN_SPEED', None) for x in gpu_hist]
        if None in gpu_fan_hist:
          gpu_fan = None
          gpu_fan_past1h = None
        elif len(gpu_fan_hist) == 0:
          gpu_fan = None
          gpu_fan_past1h = None
        elif any(isinstance(x, str) for x in gpu_fan_hist):
          # Handle the case when the fan speed is a string
          # Meaning errors most of the time ()
          gpu_fan = None
          gpu_fan_past1h = None
        else:
          gpu_fan = gpu_fan_hist[-1]
          gpu_fan_past1h = np.mean(gpu_fan_hist)

        is_secured = self.network_node_is_secured(addr)
        trusted = is_secured and trusted

        dct_result = dict(
          address=self._add_address_prefix(addr),
          eth_address=self.node_address_to_eth_address(addr),
          trusted=trusted,
          trust=trust,
          secured=is_secured,
          whitelist=self.network_node_whitelist(addr),
          trust_info=trust_info,
          is_supervisor=self.network_node_is_supervisor(addr),
          working=working_status,
          recent=recent,
          deployment=self.network_node_deploy_type(addr) or "Unknown",
          version=self.network_node_version(addr),
          py_ver=self.network_node_py_ver(addr),
          last_remote_time=self.network_node_remote_time(addr),
          node_tz=self.network_node_local_tz(addr),
          node_utc=self.network_node_local_tz(addr, as_zone=False),
          
          r1fs_id=self.network_node_r1fs_id(addr),
          r1fs_online=self.network_node_r1fs_online(addr),
          r1fs_relay=self.network_node_r1fs_relay(addr),
          
          main_loop_avg_time=main_loop_time,
          main_loop_freq=round(main_loop_freq, 2),
          
          pipelines_count=len(self.network_node_pipelines(addr)) - 1,
          
          # main_loop_cap
          uptime=self.log.elapsed_to_str(uptime_sec),
          last_seen_sec=round(self.network_node_last_seen(addr, as_sec=True, dt_now=dt_now),2),
          
          avail_disk=avail_disk,
          avail_disk_prc=avail_disk_prc,
          is_alert_disk=is_alert_disk,

          avail_mem=avail_mem,  
          avail_mem_prc=avail_mem_prc,  
          is_alert_ram=is_alert_ram,    
          
          cpu_past1h=cpu_past1h,        
          cpu_temp=cpu_temp,
          cpu_temp_past1h=cpu_temp_past1h,

          gpu_load_past1h=self.network_node_default_gpu_average_load(addr=addr, minutes=60, dt_now=dt_now),
          gpu_mem_past1h=self.network_node_default_gpu_average_avail_mem(addr=addr, minutes=60, dt_now=dt_now),

          gpu_temp=gpu_temp,
          gpu_temp_past1h=gpu_temp_past1h,

          gpu_fan=gpu_fan,
          gpu_fan_past1h=gpu_fan_past1h,

          gpu_name=gpu_name,
          SCORE=score,        
          
          eeid=eeid,
          #comms:
          comms=dct_comms,
          #end comms
          tags=self.get_network_node_tags(addr),
        )
      except Exception as e:
        self.P(f"Error in network_node_status for '{eeid}' <{addr}>: {e}", color='r')
        raise
      return dct_result    
    
    
    def network_node_history(self, addr, minutes=8*60, dt_now=None, reverse_order=True, hb_step=4):
      # TODO: set HIST_DEBUG to False
      HIST_DEBUG = True
      lst_heartbeats = self.__network_node_past_heartbeats_by_interval(
        addr=addr, minutes=minutes, dt_now=dt_now,
        reverse_order=True,
      )
      last_hb = lst_heartbeats[0]
        
      timestamps = self.__get_timestamps(lst_heartbeats)
      hb = self.__network_node_last_heartbeat(addr)
      
      cpu_hist = self.__network_node_past_cpu_used_by_interval(
        addr=addr, minutes=minutes,  dt_now=dt_now, return_timestamps=HIST_DEBUG,
        reverse_order=True,
      )
            
      mem_avail_hist = self.__network_node_past_available_memory_by_interval(
        addr=addr, minutes=minutes, 
        reverse_order=True, norm=False,
        # dt_now=dt_now, # must implement
      )

      gpu_hist = self.network_node_default_gpu_history(
        addr=addr, minutes=minutes, dt_now=dt_now, return_timestamps=HIST_DEBUG,        
        reverse_order=True, 
      )
      
      current_disk = self.__network_node_last_available_disk(
        addr=addr, norm=False
      )

      # Temperature history analysis
      temp_hist = self.network_node_past_temperatures_history(
        addr=addr, minutes=minutes, dt_now=dt_now,
        reverse_order=True,
      )
      temperatures = temp_hist['all_sensors'] # this is unused for the moment and show ALL sensors
      max_temperature = temp_hist['max_temp'] # get pre-processed max temperatures
      max_temp_sensor = temp_hist['max_temp_sensor'] # get last max-temp sensor
      
      if HIST_DEBUG: # debug / sanity-checks
        cpu_hist, cpu_timestamps = cpu_hist
        gpu_hist, gpu_timestamps = gpu_hist
        assert hb == last_hb
        assert timestamps == cpu_timestamps      
        assert timestamps == gpu_timestamps
      # endif debug

      gpu_load_hist = [x['GPU_USED'] for x in gpu_hist]
      gpu_mem_avail_hist = [x['FREE_MEM'] for x in gpu_hist]
      
      gpu_temp_hist = [x['GPU_TEMP'] for x in gpu_hist]
      gpu_temp_max_allowed = gpu_hist[-1]['GPU_TEMP_MAX'] if len(gpu_hist) > 0 else None
      
      total_disk=hb[ct.HB.TOTAL_DISK]
      total_mem=hb[ct.HB.MACHINE_MEMORY]
      gpu_mem_total = gpu_hist[0]['TOTAL_MEM'] if len(gpu_hist) > 0 else None
      
      # we assume data is from oldest to last newest (reversed order)
      timestamps = timestamps[::hb_step]
      cpu_hist = cpu_hist[::hb_step]
      mem_avail_hist = mem_avail_hist[::hb_step]
      gpu_load_hist = gpu_load_hist[::hb_step]
      gpu_mem_avail_hist = gpu_mem_avail_hist[::hb_step]
      temperatures = temperatures[::hb_step]
      max_temperature = max_temperature[::hb_step]
      gpu_temp_hist = gpu_temp_hist[::hb_step]
      
      
      if not reverse_order:
        timestamps = list(reversed(timestamps))
        cpu_hist = list(reversed(cpu_hist))
        mem_avail_hist = list(reversed(mem_avail_hist))
        gpu_load_hist = list(reversed(gpu_load_hist))
        gpu_mem_avail_hist = list(reversed(gpu_mem_avail_hist))
        temperatures = list(reversed(temperatures))
        max_temperature = list(reversed(max_temperature))
        gpu_temp_hist = list(reversed(gpu_temp_hist))
      
      dct_result = OrderedDict(dict(
        total_disk=total_disk,
        current_disk=current_disk,
        total_mem=total_mem,
        mem_avail_hist=mem_avail_hist,
        cpu_hist=cpu_hist,
        gpu_mem_total=gpu_mem_total,
        gpu_load_hist=gpu_load_hist,
        gpu_mem_avail_hist=gpu_mem_avail_hist,
        gpu_temp_hist=gpu_temp_hist,
        gpu_temp_max_allowed=gpu_temp_max_allowed,
        temperatures=temperatures, # should we add this ?
        max_temperature=max_temperature,
        max_temp_sensor=max_temp_sensor,
        timestamps=timestamps,
      ))
      
      return dct_result

    def __get_tag_from_heartbeat(self, hb, tag_suffix, only_value=False):
      """
      Private method to get a specific tag value from heartbeat data.
      
      Args:
        hb: The heartbeat data dictionary
        tag_suffix: The suffix to look for in the heartbeat data (e.g., 'DC', 'REG', 'CT')
        only_value: If True, return only the value part; if False, return the full tag
        
      Returns:
        The tag value if found, None otherwise
      """
      if isinstance(hb, dict):
        # Construct the full key and get directly from heartbeat
        full_key = f"{ct.HB.PREFIX_EE_NODETAG}{tag_suffix}"
        v = hb.get(full_key)
        
        if v is not None:
          if not v:
            return None
          if isinstance(v, str):
            v = v.strip()
            if v == '' or v.lower() in ['none', 'null']:
              return None
          
          if isinstance(v, bool):
            return v if only_value else (tag_suffix if v else None)
          else:
            return v if only_value else f"{tag_suffix}:{v}"
      return None

    def get_network_node_tags(self, node_address):
      """
      Gets all tags for a network node.
      
      Parameters:
      -----------
      node_address : str
          The address of the node

      Returns:
      --------
      list: A list of tags associated with the node
        Example: ["KYB","DC:HOSTINGER", "CT:FR", "REG:EU"]
      """

      result = []
      hb = self.__network_node_last_heartbeat(node_address)
      # get tags from HB.
      if isinstance(hb, dict):
        tags = {k: v for k, v in hb.items() if k.startswith(ct.HB.PREFIX_EE_NODETAG)}
        for tag_key in tags.keys():
          tag_key_clean = tag_key.replace(ct.HB.PREFIX_EE_NODETAG, '')
          tag = self.__get_tag_from_heartbeat(hb, tag_key_clean, only_value=False)
          if tag:
            result.append(tag)

      # get remaining tags that are not in HB (from DB or other source).
      other_tags = []

      for method_name in dir(self):
        if method_name.startswith(f"network_node_get_tag_"):
          tag_name = method_name.replace("network_node_get_tag_", "").upper()
          _method = getattr(self, method_name)
          if callable(_method):
            try:
              tag = _method(addr=node_address, only_value=False)
              if tag:
                other_tags.append(tag)
            except Exception as e:
              self.P(f"Error getting tag by calling _method {method_name}: {e}", color='r')
      result = result + other_tags
      result = list(set(result))

      return result

    def network_node_get_tag_is_kyb(self, addr, only_value=True):
      hb = self.__network_node_last_heartbeat(addr)
      return self.__get_tag_from_heartbeat(hb, ct.HB.TAG_IS_KYB, only_value=only_value)

    def network_node_get_tag_dc(self, addr, only_value=True):
      hb = self.__network_node_last_heartbeat(addr)
      return self.__get_tag_from_heartbeat(hb, ct.HB.TAG_DC, only_value=only_value)

    def network_node_get_tag_reg(self, addr, only_value=True):
      hb = self.__network_node_last_heartbeat(addr)
      return self.__get_tag_from_heartbeat(hb, ct.HB.TAG_REG, only_value=only_value)

    def network_node_get_tag_ct(self, addr, only_value=True):
      hb = self.__network_node_last_heartbeat(addr)
      return self.__get_tag_from_heartbeat(hb, ct.HB.TAG_CT, only_value=only_value)

    # End node tags.
  #endif


if __name__ == '__main__':
  from naeural_core import Logger
  l = Logger(lib_name='tstn', base_folder='.', app_folder='_local_cache')
  network_heartbeats = l.load_pickle_from_output('test_network_heartbeats.pkl')
  
  str_dt = '2023-05-25 18:13:00'
  dt_now = None # l.str_to_date(str_dt)
  addrs = list(network_heartbeats.keys())
  # TODO: change address here to the address of gts-test2
  addr = addrs[0]
  
  nmon = NetworkMonitor(log=l)
  nmon._set_network_heartbeats(network_heartbeats)
  res = {}
  for addr in addrs:
    if addr == addrs[0]:
      print()
    res[addr] = nmon.network_node_status(addr=addr, min_uptime=120, dt_now=dt_now)
  l.P("Results:\n{}".format(
    json.dumps(res, indent=4), 
  ))
  l.P(nmon.network_node_history(addr))
  
