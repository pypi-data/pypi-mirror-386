"""
TODO:


  - Solve the issue for set-contention in the chain storage when two nodes try to set the same key at the same time
    - (better) implement a lock mechanism for the chain storage when setting a key value that 
      will allow multiple nodes to compete for the set-operation and thus load-balance it
      OR
    - implement set-value moving TOKEN via the network
  

  - peer-to-peer managed:
    - node 1 registers a app_id X via a list of peers that includes node 1, node 2 and node 3
    - node 2 sets value by:
      - key
      - value 
      - app_id X
    - node 2 broadcasts the set opration to all app_id X peers (not all peers)
    - node 2 waits for confirmations from at least half of the app_id peers
    - if node 4 tries to set key in app_id X, it will be rejected
    
  


"""


from naeural_core.business.base.network_processor import NetworkProcessorPlugin

_CONFIG = {
  **NetworkProcessorPlugin.CONFIG,

  'PROCESS_DELAY' : 0,

  'MAX_INPUTS_QUEUE_SIZE' : 100,

  'ALLOW_EMPTY_INPUTS' : True,
  "ACCEPT_SELF" : False,
  
  "FULL_DEBUG_PAYLOADS" : False,
  "CHAIN_STORE_DEBUG" : False, # main debug flag
  
  
  "MIN_CONFIRMATIONS" : 1,
  
  "CHAIN_PEERS_REFRESH_INTERVAL" : 60,

  'VALIDATION_RULES' : { 
    **NetworkProcessorPlugin.CONFIG['VALIDATION_RULES'],
  },  
}

__VER__ = '0.8.1'

class ChainStoreBasePlugin(NetworkProcessorPlugin):
  CONFIG = _CONFIG
  
  CS_STORE = "SSTORE"
  CS_CONFIRM = "SCONFIRM"
  CS_DATA = "CHAIN_STORE_DATA"
  CS_PEERS = "PEERS"

  CS_CONFIRM_BY = "confirm_by"
  CS_CONFIRM_BY_ADDR = "confirm_by_addr"
  CS_CONFIRMATIONS = "confirms"
  CS_MIN_CONFIRMATIONS = "min_confirms"
  CS_OP = "op"
  CS_KEY = "key"
  CS_VALUE = "value"
  CS_OWNER = "owner"
  CS_READONLY = "readonly"
  CS_TOKEN = "token"
  CS_STORAGE_MEM = "__chain_storage" # shared memory key
  CS_GETTER = "__chain_storage_get"
  CS_SETTER = "__chain_storage_set"
  
  
  
  
  def on_init(self):
    super().on_init() # not mandatory anymore?
    
    self.P(" === ChainStoreBasicPlugin INIT")
    
    self.__chainstore_identity = "CS_MSG_{}".format(self.uuid(7))
    
    self.__ops = self.deque()
    
    try:
      self.__chain_storage = self.cacheapi_load_pickle(default={}, verbose=True)
    except Exception as e:
      self.P(f" === Chain storage could not be loaded: {e}")
      self.__chain_storage = {}
      
    memory = self.plugins_shmem
      

    ## DEBUG ONLY:
    if self.CS_STORAGE_MEM in memory:
      self.P(" === Chain storage already exists", color="r")
      self.__chain_storage = memory[self.CS_STORAGE_MEM]
    ## END DEBUG ONLY
    
    memory[self.CS_STORAGE_MEM] = self.__chain_storage
    memory[self.CS_GETTER] = self._get_value
    memory[self.CS_SETTER] = self._set_value
    
    self.__last_chain_peers_refresh = 0
    self.__chain_peers = []
    self.__maybe_refresh_chain_peers()
    return
  
  
  def __debug_dump_chain_storage(self):
    if self.cfg_chain_store_debug:
      self.P(" === Chain storage dump:\n{}".format(self.json_dumps(self.__chain_storage, indent=2)))
    return
   
  
  
  
  def __maybe_refresh_chain_peers(self):
    """
    This method refreshes the chain peers list from the network using the whitelist generated
    by the blockchain engine. This means it will allow broadcasting the local keys to all the
    oracle nodes in the network as well as the manually added nodes. This pretty much covers 
    the "private" part of the ChainStore.
    
    However the chain storage should be also accessible to all the nodes in the network so that 
    they can ALL the values stored in the chain storage publicly
        
    """
    if (self.time() - self.__last_chain_peers_refresh) > self.cfg_chain_peers_refresh_interval:
      _chain_peers = self.bc.get_whitelist(with_prefix=True)
      # now check and preserve only online peers
      self.__chain_peers = [
        peer for peer in _chain_peers if self.netmon.network_node_is_online(peer)
      ]
      self.__last_chain_peers_refresh = self.time()
    return
  
  
  def __send_data_to_chain_peers(self, data, peers=None):
    # check if list or str
    send_to = self.deepcopy(self.__chain_peers)
    if isinstance(peers, (str, list)) and len(peers) > 0:
      if isinstance(peers, str):
        peers = [peers]
      # end if not a list
      peers = [peer for peer in peers if peer not in self.__chain_peers]
      send_to.extend(peers)
    # end if peers
      
    self.send_encrypted_payload(node_addr=send_to, **data)
    return
  
  
  def __get_min_peer_confirmations(self):
    if self.cfg_min_confirmations is not None and self.cfg_min_confirmations > 0:
      return self.cfg_min_confirmations    
    return len(self.__chain_peers) // 2 + 1
  
  
  def __save_chain_storage(self):
    self.cacheapi_save_pickle(self.__chain_storage, verbose=True)
    self.__last_chain_storage_save = self.time()
    return
  
  ## START setter-getter methods

  def __get_key_value(self, key):
    return self.__chain_storage.get(key, {}).get(self.CS_VALUE, None)


  def __get_key_owner(self, key):
    return self.__chain_storage.get(key, {}).get(self.CS_OWNER, None)
  
  
  def __get_key_readonly(self, key):
    return self.__chain_storage.get(key, {}).get(self.CS_READONLY, False)


  def __get_key_token(self, key):
    return self.__chain_storage.get(key, {}).get(self.CS_TOKEN, None)


  def __get_key_confirmations(self, key):
    return self.__chain_storage.get(key, {}).get(self.CS_CONFIRMATIONS, 0)

  
  def __get_key_min_confirmations(self, key):
    return self.__chain_storage.get(key, {}).get(self.CS_MIN_CONFIRMATIONS, 0)


  def __reset_confirmations(self, key):
    self.__chain_storage[key][self.CS_CONFIRMATIONS] = 0
    self.__chain_storage[key][self.CS_MIN_CONFIRMATIONS] = self.__get_min_peer_confirmations()
    return


  def __increment_confirmations(self, key):
    self.__chain_storage[key][self.CS_CONFIRMATIONS] += 1
    return
  
  def __set_confirmations(self, key, confirmations):
    self.__chain_storage[key][self.CS_CONFIRMATIONS] = confirmations
    return


  def __set_key_value(self, key, value, owner,  readonly=False, token=None, local_sync_storage_op=False):
    """
    This method is called to set a key-value pair in the chain storage.
    
    Parameters:
    ----------
    
    key : str
      The key to set the value for
    
    value : any
      The value to set
      
    owner : str
      The owner of the key-value pair
      
    readonly : bool
      If True the key-value pair will be readonly and cannot be overwritten by other owners
      
    token: any
      A token to be used for the set operation. If the token is not None, any read/write operations
      will have to have the same token.
      
    local_sync_storage_op : bool
      If `True` will only set the local kv pair without broadcasting to the network. 
      This operation is used for remote sync when a node receives a set operation from 
      the network and needs to set the value in the local chain storage replica.
      
    """
    # key should be composed of the chainstore app identity and the actual key
    # so if two chainstore apps are running on the same node, they will not overwrite each other
    # also this way we can implement chaistore app allow-listing
    chain_key = key
    self.__chain_storage[chain_key] = {
      self.CS_KEY       : key,
      self.CS_VALUE     : value,
      self.CS_OWNER     : owner,
      self.CS_READONLY  : readonly,
      self.CS_TOKEN     : token,
    }    
    self.__reset_confirmations(key)
    if local_sync_storage_op:
      # set the confirmations to -1 to indicate that the key is remote synced on this node
      self.__set_confirmations(key, -1) # set to -1 to indicate that the key is remote synced on this node
    self.__save_chain_storage()
    return


  def _set_value(
    self, 
    key, 
    value, 
    owner=None, 
    readonly=False,
    token=None,
    local_sync_storage_op=False, 
    peers=None,
    debug=False, 
  ):
    """ 
    This method is called to set a value in the chain storage.
    If called locally will push a broadcast request to the network, 
    while if called from the network will set the value in the chain storage.
    
    Parameters:
    ----------
    
    key : str
      The key to set the value for
      
    value : any
      The value to set
      
    owner : str 
      The owner of the key-value pair
      
    readonly : bool
      If True the key-value pair will be readonly and cannot be overwritten by other owners
      
    token: any
      A token to be used for the set operation. If the token is not None, any read/write operations 
      will have to have the same token.
            
    local_sync_storage_op : bool
      If True will only set the local kv pair without broadcasting to the network
      
    peers : list
      A list of peers to send the data to. If None, will use only the chain peers list.

    debug : bool
      If True will print debug messages
      
      
    Returns:
    --------
    
    
    
    """
    where = "FROM_LOCAL: " if not local_sync_storage_op else "FROM_REMOTE: "
    debug = debug or self.cfg_chain_store_debug
    debug_val = str(value)[:20] + "..." if len(str(value)) > 20 else str(value)
    if owner is None:
      owner = self.get_instance_path()
    need_store = True
    existing_owner = None
    existing_value = None
    if key in self.__chain_storage:
      existing_value = self.__get_key_value(key)
      existing_owner = self.__get_key_owner(key)
      is_readonly = self.__get_key_readonly(key)
      existing_token = self.__get_key_token(key)
      if token != existing_token:
        if debug:
          self.P(f" === Key {key} has a different token {existing_token} from {existing_owner} than the one provided {token} from {owner}", color='r')
        need_store = False
      elif existing_value == value:
        if debug:
          self.P(f" === Key {key} stored by {existing_owner} has the same value")
        need_store = False
      elif is_readonly and existing_owner != owner:
        if debug:
          self.P(f" === Key {key} readonly by {existing_owner} (requester: {owner})", color='r')
        need_store = False
    # end if key in chain storage
    if need_store:
      if debug:
        set_or_overwrite = "overwriting" if existing_owner not in [None, owner] else "setting"        
        self.P(f" === {where}{set_or_overwrite} <{key}> = <{debug_val}> by {owner} (orig: {existing_owner}), is_remote={local_sync_storage_op}")
      self.__set_key_value(
        key=key, value=value, owner=owner, 
        local_sync_storage_op=local_sync_storage_op, 
        readonly=readonly, token=token,
      )
      if not local_sync_storage_op:      
        # now send set-value (including confirmation request) to all
        op = {      
            self.CS_OP        : self.CS_STORE,
            self.CS_KEY       : key,        
            self.CS_VALUE     : value,   
            self.CS_OWNER     : owner,
            self.CS_TOKEN     : token,
            self.CS_READONLY  : readonly, # if the key is readonly, it will not be overwritten by other owners
            self.CS_PEERS     : peers,
        }
        self.__ops.append(op)
        if debug:
          self.P(f" === {where} key {key} locally stored for {owner}. Now waiting for confirmations...")
        # at this point we can wait until we have enough confirmations
        _timeout = self.time() + 10
        _done = False
        _prev_confirm = 0
        _max_retries = 2
        _retries = 0
        while not _done: # this LOCKS the calling thread set_value
          recv_confirm = self.__get_key_confirmations(key)
          if recv_confirm > _prev_confirm:
            _prev_confirm = recv_confirm
            if debug:
              self.P(f" === {where}Key received '{key}' has {recv_confirm} confirmations")
          if recv_confirm >= self.__get_key_min_confirmations(key):
            if debug:
              self.P(f" === {where}KEY CONFIRMED '{key}': has enough ({recv_confirm}) confirmations")
            _done = True
            need_store = True
            continue
          elif self.time() > _timeout:
            if debug:
              self.P(f" === {where}Key '{key}' has not enough confirmations after timeout", color='r')
            _retries += 1
            if _retries > _max_retries:
              if debug:
                self.P(f" === {where}Key '{key}' has not enough confirmations after {_max_retries} retries", color='r')
              _done = True
              need_store = False
            else:
              if debug:
                self.P(f" === {where}Retrying key '{key}' with timeout...", color='r')
              self.__ops.append(op)
              _timeout = self.time() + 10
            # end if retries
          # end if timeout
          self.sleep(0.100)  # sleep for 100ms to give protocol sync time
        # end while not done
      else:
        if debug:
          self.P(f" === {where}{key} locally sync-stored for remote {owner}")
      # end if not sync_storage
    # end if need_store
    return need_store


  def _get_value(self, key, token=None, get_owner=False, debug=False):
    """ This method is called to get a value from the chain storage """
    debug = debug or self.cfg_chain_store_debug
    if debug:
      self.P(f" === Getting value for key {key}")

    existing_token = self.__get_key_token(key)
    result_value, result_owner = None, None
    if token != existing_token:
      if debug:
        self.P(f" === Key {key} has a different token {existing_token} than the one provided {token}", color='r')
    else:
      result_value = self.__get_key_value(key)
      if get_owner:
        result_owner = self.__get_key_owner(key)
    # end if token
    if result_value is not None:
      result_value = self.deepcopy(result_value)  # make sure we return a copy of the value, in case it is mutable
    if get_owner:
      return result_value, result_owner
    return result_value
  
  ### END setter-getter methods


  def __maybe_broadcast(self):
    """ 
    This method is called to broadcast the chain store operations to the network.
    For each operation in the queue, a broadcast is sent to the network    
    """
    if self.cfg_chain_store_debug and len(self.__ops) > 0:
      self.P(f" === Broadcasting {len(self.__ops)} chain store {self.CS_STORE} ops to {self.__chain_peers}")
    while len(self.__ops) > 0:
      data = self.__ops.popleft()
      peers = data.get(self.CS_PEERS, None)
      payload_data = {
        self.CS_DATA : data
      }
      self.__send_data_to_chain_peers(payload_data, peers=peers)
    return


  def __exec_store(self, data, peers=None):
    """ 
    This method is called when a store operation is received from the network. The method will:
      - set the value in the chain storage
      - send a ecrypted confirmation of the storage operation to the network
    """
    key = data.get(self.CS_KEY, None)
    value = data.get(self.CS_VALUE , None)
    owner = data.get(self.CS_OWNER, None)
    readonly = data.get(self.CS_READONLY, False) # if the key is readonly local node consumers cannot overwrite it
    token = data.get(self.CS_TOKEN, None)
    if self.cfg_chain_store_debug:
      self.P(f" === REMOTE: Exec remote-to-local-sync store for {key}={value} by {owner}")
    result = self._set_value(
      key, value, owner=owner, 
      token=token, readonly=readonly,
      local_sync_storage_op=True,
    )
    if result:
      # now send confirmation of the storage execution
      if self.cfg_chain_store_debug:
        self.P(f" === REMOTE: {self.CS_CONFIRM} for {key} of {owner} to {self.__chain_peers}")
      data = {
        self.CS_DATA : {
          self.CS_OP : self.CS_CONFIRM,
          self.CS_KEY: key,
          self.CS_VALUE : value,
          self.CS_OWNER : owner,
          self.CS_CONFIRM_BY : self.get_instance_path(),
          self.CS_CONFIRM_BY_ADDR : self.ee_addr,
        }
      }
      self.__send_data_to_chain_peers(data, peers=peers)
    else:
      if self.cfg_chain_store_debug:
        self.P(f" === REMOTE: Store for {key}={value} of {owner} failed", color='r')
    return


  def __exec_received_confirm(self, data):
    """ This method is called when a confirmation of a broadcasted store operation is received from the network """
    key = data.get(self.CS_KEY, None)
    value = data.get(self.CS_VALUE, None)
    owner = data.get(self.CS_OWNER, None)
    confirm_by = data.get(self.CS_CONFIRM_BY, None)
    op = data.get(self.CS_OP, None)
    
    local_owner = self.__get_key_owner(key)
    local_value = self.__get_key_value(key)
    if self.cfg_chain_store_debug:
      self.P(f" === LOCAL: Received {op} from {confirm_by} for  {key}={value}, owner{owner}")
    if owner == local_owner and value == local_value:
      self.__increment_confirmations(key)
      if self.cfg_chain_store_debug:
        self.P(f" === LOCAL: Key {key} confirmed by {confirm_by}")
    return

  @NetworkProcessorPlugin.payload_handler()
  def default_handler(self, payload):
    sender = payload.get(self.const.PAYLOAD_DATA.EE_SENDER, None)
    alias = payload.get(self.const.PAYLOAD_DATA.EE_ID, None)
    destination = payload.get(self.const.PAYLOAD_DATA.EE_DESTINATION, None)
    is_encrypted = payload.get(self.const.PAYLOAD_DATA.EE_IS_ENCRYPTED, False)
    destination = destination if isinstance(destination, list) else [destination]
    decrypted_data = self.receive_and_decrypt_payload(data=payload)    
    # DEBUG AREA
    if self.cfg_chain_store_debug:
      from_myself = sender == self.ee_addr
      str_sender = sender if not from_myself else f"{sender} (myself)"
      self.P(f" === PAYLOAD_CSTORE: from {str_sender} (enc={is_encrypted})")
      if self.ee_addr in destination:
        self.P(f" === PAYLOAD_CSTORE: received for me")
      else:
        if not from_myself:
          self.P(f" === PAYLOAD_CSTORE: to {destination} (not for me {self.ee_addr})", color='r')
        return
    # try to decrypt the payload
    if self.cfg_chain_store_debug:
      if decrypted_data is None or len(decrypted_data) == 0:
        self.P(f" === PAYLOAD_CSTORE: FAILED decrypting payload", color='r')
      else:
        self.P(f" === PAYLOAD_CSTORE: decrypted payload OK")
    # END DEBUG AREA    
    # get the data and call the appropriate operation method
    data = decrypted_data.get(self.CS_DATA, {})
    operation = data.get(self.CS_OP, None)
    owner = data.get(self.CS_OWNER, None)
    if self.cfg_chain_store_debug:
      if operation is None:
        self.P(f" === PAYLOAD_CSTORE: NO OPERATION from data: {data}", color='r')
      else:
        self.P(f" === PAYLOAD_CSTORE: {operation=} from {alias=} {owner=}")
    if operation == self.CS_STORE:
      self.__exec_store(data, peers=sender) # make sure you send also to the sender
    elif operation == self.CS_CONFIRM:
      self.__exec_received_confirm(data)
    return
  

  
  def process(self):
    self.__maybe_refresh_chain_peers()
    self.__maybe_broadcast()
    return 
