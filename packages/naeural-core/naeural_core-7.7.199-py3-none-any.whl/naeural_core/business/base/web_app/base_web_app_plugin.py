import os
import shutil
import subprocess
import tempfile
import psutil

from jinja2 import Environment, FileSystemLoader

from naeural_core.business.base import BasePluginExecutor
from naeural_core.business.base.web_app.base_tunnel_engine_plugin import BaseTunnelEnginePlugin

__VER__ = '0.0.0.0'

# This may be used for running ready-made builds
WEB_APP_DEFAULT_ENV_VARS = {
  "HOSTNAME": "0.0.0.0"
}
WEB_APP_DEFAULT_GIT_TRACK_MODE = 'commit'

_CONFIG = {
  **BasePluginExecutor.CONFIG,
  'ALLOW_EMPTY_INPUTS': True,
  'RUN_WITHOUT_IMAGE': True,
  'PROCESS_DELAY': 5,
  
  'GIT_REQUEST_DELAY': 60 * 10,  # 10 minutes

  # NGROK Section
  # TODO: this will be removed after migration to the new tunnel engine
  'NGROK_USE_API': True,
  'NGROK_ENABLED': False,
  'NGROK_DOMAIN': None,
  'NGROK_EDGE_LABEL': None,
  'NGROK_URL_PING_INTERVAL': 30,
  'NGROK_AUTH_TOKEN': None,

  # Generic tunnel engine Section
  "TUNNEL_ENGINE": "ngrok",  # or "cloudflare"

  "TUNNEL_ENGINE_ENABLED": True,
  "TUNNEL_ENGINE_PING_INTERVAL": 30,  # seconds
  "TUNNEL_ENGINE_PARAMETERS": {
  },

  'SUPRESS_LOGS_AFTER_INTERVAL' : 120,  # 2 minutes until logs suppression

  'ASSETS': None,

  'SETUP_COMMANDS': [],
  'START_COMMANDS': [],
  'ENV_VARS': {},
  'AUTO_START': True,
  'FORCED_RELOAD_INTERVAL': None,

  'PORT': None,
  "DEBUG_WEB_APP": False,

  'VALIDATION_RULES': {
    **BasePluginExecutor.CONFIG['VALIDATION_RULES']
  },
}


class BaseWebAppPlugin(
  # _NgrokMixinPlugin,
  # _CloudflareMixinPlugin,
  # BasePluginExecutor
  BaseTunnelEnginePlugin
):
  """
  A base plugin which will handle the lifecycle of a web application.
  Through this plugin, you can expose your business logic as a web application,
  using some implementation of a web server.

  You can also deploy your web application to the internet using ngrok.
  To do this, set the `TUNNEL_ENGINE_ENABLED` flag to True in config and set the necessary
  environment variables.

  TODO: add ngrok necessary data in the config (after securing the configs)
  """

  CONFIG = _CONFIG


  def _on_init(self):

    self.__git_commit_hash = None
    self.__last_release_tag = None
    self.__last_asset_id = None
    self.__last_asset_updated_at = None
    self.__git_request_time = 0
    self.__first_log_displayed = None
    
    self.reset_tunnel_engine()
    self.__last_tunnel_engine = self.cfg_tunnel_engine

    self.__wait_count = 0

    # TODO: move this to process
    self._allocate_port()

    self.prepared_env = None
    self.base_env = None

    self.__init_temp_dir()
        
    self.assets_initialized = False
    self.failed = False
    self.__commands_ready = False

    self.can_run_start_commands = self.cfg_auto_start
    self.setup_commands_started = []
    self.setup_commands_finished = []
    self.setup_commands_processes = []
    self.setup_commands_start_time = []

    self.start_commands_started = []
    self.start_commands_finished = []
    self.start_commands_processes = []
    self.start_commands_start_time = []
    self.webapp_reload_last_timestamp = 0

    self.dct_logs_reader = {}
    self.dct_err_logs_reader = {}

    super(BaseWebAppPlugin, self)._on_init()
    return


  def __init_temp_dir(self):
    if getattr(self, "script_temp_dir", None) is not None:
      self.P(f"Deleting {self.script_temp_dir} ...")
      shutil.rmtree(self.script_temp_dir)
    self.script_temp_dir = tempfile.mkdtemp()
    self.P(f"Created {self.script_temp_dir}")
    return
  
  
  def __can_request_git(self):
    if self.time() - self.__git_request_time > self.cfg_git_request_delay:
      self.__git_request_time = self.time()
      return True
    return False


  # Port allocation
  def __check_port_valid(self):
    # Check the config as we're going to use it to start processes.
    port = self.get_port()
    if not isinstance(port, int):
      raise ValueError("Port not an int")
    if port < 0 or port > 65535:
      raise ValueError("Invalid port value {}".format(port))
    return

  def __get_all_used_ports(self):
    res = set()
    for conn in psutil.net_connections(kind='all'):
      # Local address is not always a tuple.
      if not isinstance(conn.laddr, str):
        res.add(conn.laddr.port)  # Local port
    # endfor
    return sorted(res)

  def _allocate_port(self):
    """
    TODO: (Bleo) this should be migrated to the new correct version 
    
    
    In case the port is not provided, a random unused one will be allocated.
    In case the port is provided, it will be checked for availability.
    If the provided port is not available, the allocation will be retried
    until a port is found.
    """
    cnt_tries = 0
    done = False
    while not done:
      with self.managed_lock_resource('USED_PORTS'):
        if 'USED_PORTS' not in self.plugins_shmem:
          self.plugins_shmem['USED_PORTS'] = {}
        dct_shmem_ports = self.plugins_shmem['USED_PORTS']
        used_ports = self.__get_all_used_ports()
        configured_port = self.get_port()
        if configured_port is not None:
          self.__check_port_valid()

          if configured_port not in used_ports:
            dct_shmem_ports[self.str_unique_identification] = configured_port
            done = True
          else:
            cnt_tries += 1
        else:
          port = self.np.random.randint(30000, 32500)
          total_tries = 1000
          tries = 0
          while port in used_ports and tries < total_tries:
            tries += 1
            port = self.np.random.randint(30000, 32500)
          # endwhile
          if tries >= total_tries:
            raise Exception(f"Could not find an available port after {total_tries} tries.")
          # endif tries
          dct_shmem_ports[self.str_unique_identification] = port
          done = True
        # endif port
      # endwith lock
      if not done:
        sleep_seconds = 5
        self.P(
          f"Preconfigured port {configured_port} is already in use at try {cnt_tries}. Retrying in {sleep_seconds}...",
          color='r'
        )
        self.sleep(sleep_seconds)
    return

  def __deallocate_port(self):
    # TODO: both this and __allocate_port don t actually allocate/deallocate ports
    #  They just mark them as so.
    port = self.port

    with self.managed_lock_resource('USED_PORTS'):
      if 'USED_PORTS' in self.plugins_shmem:
        self.plugins_shmem['USED_PORTS'].pop(self.str_unique_identification, None)
    # endwith lock

    self.P(f"Released port {port}")
    return

  def get_additional_env_vars(self):
    return {
      "EE_NODE_ALIAS": self.eeid,
      "EE_NODE_ADDRESS": self.bc.address,
      "EE_NODE_ETH_ADDRESS": self.bc.eth_address,
      "EE_NODE_NETWORK": self.evm_network,
      "EE_NODE_VER": self.ee_ver
    }

  def __prepare_env(self, assets_path):
    # pop all `EE_` keys
    prepared_env = dict(self.os_environ)
    to_pop_keys = []
    for key in prepared_env:
      if key.startswith('EE_'):
        to_pop_keys.append(key)
    # endfor all keys

    for key in to_pop_keys:
      prepared_env.pop(key)

    # add mandatory keys
    prepared_env["PWD"] = self.script_temp_dir
    prepared_env["PORT"] = str(self.port)

    self.base_env = prepared_env.copy()

    # add default keys
    prepared_env = {
      **prepared_env,
      **WEB_APP_DEFAULT_ENV_VARS,
    }

    # add optional keys, found in `.env` file from assets folder if provided.
    if assets_path is not None:
      env_file_path = self.os_path.join(assets_path, '.env')
      if self.os_path.exists(env_file_path):
        with open(env_file_path, 'r') as f:
          for line in f:
            if line.startswith('#') or len(line.strip()) == 0:
              continue
            key, value = line.strip().split('=', 1)
            prepared_env[key] = value
        # endwith

        # TODO: should we remove the .env file?
      # endif env file
    # endif assets path provided

    # add optional keys, found in config
    if self.cfg_env_vars is not None and isinstance(self.cfg_env_vars, dict):
      processed_env = {k: str(v) for k, v in self.cfg_env_vars.items()}
      prepared_env.update(processed_env)

    additional_env_vars = self.get_additional_env_vars() or {}
    prepared_env.update(additional_env_vars)

    self.prepared_env = prepared_env

    return prepared_env

  # process handling methods
  def __run_command(self, command, env=None, read_stdout=True, read_stderr=True):
    if isinstance(command, list):
      command_args = command
    elif isinstance(command, str):
      command_args = command.split(' ')
    else:
      raise ValueError("Command must be a string or a list of strings")

    process = subprocess.Popen(
      command_args,
      env=env,
      cwd=self.script_temp_dir,
      stdout=subprocess.PIPE if read_stdout else None,
      stderr=subprocess.PIPE if read_stderr else None,
      bufsize=0, # this is important for real-time output
    )
    # daemon is set to None in order to allow the process to close gracefully
    logs_reader = self.LogReader(process.stdout, size=100, daemon=None) if read_stdout else None
    err_logs_reader = self.LogReader(process.stderr, size=100, daemon=None) if read_stderr else None
    return process, logs_reader, err_logs_reader

  def __wait_for_command(self, process, timeout):
    process_finished = False
    failed = False
    try:
      process.wait(timeout)
      failed = process.returncode != 0
      process_finished = True
    except subprocess.TimeoutExpired:
      pass

    return process_finished, failed

  def kill_process_and_children(self, proc: subprocess.Popen, timeout=3):
    try:
      parent = psutil.Process(proc.pid)
    except psutil.NoSuchProcess:
      return

    # Get child processes (recursive=True → grandchildren, etc.)
    children = parent.children(recursive=True)

    # Send SIGKILL to children first
    for child in children:
      try:
        child.kill()
      except psutil.NoSuchProcess:
        pass

    # Kill the parent
    try:
      parent.kill()
    except psutil.NoSuchProcess:
      pass

    # Wait for them to terminate
    gone, alive = psutil.wait_procs([parent, *children], timeout=timeout)
    if alive:
      # Some processes are still alive
      for p in alive:
        p.terminate()  # or p.kill() again
    return

  def __maybe_kill_process(self, process, key, max_tries=5):
    if process is None:
      return
    tries = 0
    success = False
    while tries < max_tries and not success:
      tries += 1
      try:
        self.P(f"Forcefully killing process {key}(try {tries}/{max_tries})")
        self.kill_process_and_children(process, timeout=3)
        # Check if it's done
        if process.poll() is not None:
          self.P(f"Process {key} is fully terminated.")
          success = True
        else:
          self.P(f"Process {key} still alive. Retrying.")
        self.__maybe_print_key_logs(key)
        if success:
          self.P(f"Killed process {key} from {tries} tries.")
      except Exception as exc:
        self.P(f'Could not kill process {key} (try {tries}/{max_tries}). Reason: {exc}')
    # endwhile
    return

  # logs handling methods
  def __maybe_print_all_logs(self, indent=35):
    for key, logs_reader in self.dct_logs_reader.items():
      if logs_reader is not None:
        logs = logs_reader.get_next_characters()
        if len(logs) > 0:
          self.on_log_handler(logs, key)
          if isinstance(self.cfg_supress_logs_after_interval, int) and self.cfg_supress_logs_after_interval > 0:
            time_since_first_log = 0 if self.__first_log_displayed is None else (self.time() - self.__first_log_displayed)
            if time_since_first_log > self.cfg_supress_logs_after_interval and len(logs) > 0:
              # only print logs if the first log was displayed less than `supress_logs_after_interval` seconds ago
              indented_logs = self.indent_strings(logs, indent=indent)
              self.P(f"Showing stdout logs [{key}]:\n{indented_logs}")
              self.logs.append(f"[{key}]: {logs}")
              if self.__first_log_displayed is None:
                self.__first_log_displayed = self.time()
            #end if time_since_first_log
          #end if supress_logs_after_interval
        # endif logs
      #end if logs_reader
    #endfor all logs readers

    for key, err_logs_reader in self.dct_err_logs_reader.items():
      if err_logs_reader is not None:
        err_logs = err_logs_reader.get_next_characters()
        if len(err_logs) > 0:
          self.on_log_handler(err_logs, key)
          indented_err_logs = self.indent_strings(err_logs, indent=indent)
          self.P(f"Showing error logs [{key}]:\n{indented_err_logs}")
          self.err_logs.append(f"[{key}]: {err_logs}")
    return


  def __maybe_print_key_logs(self, key):
    logs_reader = self.dct_logs_reader.get(key)
    if logs_reader is not None:
      logs = logs_reader.get_next_characters()
      if len(logs) > 0:
        self.P(f"[stdout][{key}]: {logs}")
        self.logs.append(f"[{key}]: {logs}")

    err_logs_reader = self.dct_err_logs_reader.get(key)
    if err_logs_reader is not None:
      err_logs = err_logs_reader.get_next_characters()
      if len(err_logs) > 0:
        self.P(f"[stderr][{key}]: {err_logs}")
        self.err_logs.append(f"[{key}]: {err_logs}")
    return


  def __get_delta_logs(self):
    logs = list(self.logs)
    logs = "".join(logs)
    self.logs.clear()

    err_logs = list(self.err_logs)
    err_logs = "".join(err_logs)
    self.err_logs.clear()

    return logs, err_logs

  def __maybe_read_and_stop_key_log_readers(self, key):
    if self.cfg_debug_web_app:
      self.P(f"Reading and stopping log readers for key {key}...")
    # endif debug web app
    logs_reader = self.dct_logs_reader.get(key)
    if logs_reader is not None:
      if self.cfg_debug_web_app:
        self.P(f"Stopping log reader for key {key}...")
      logs_reader.stop()

    err_logs_reader = self.dct_err_logs_reader.get(key)
    if err_logs_reader is not None:
      if self.cfg_debug_web_app:
        self.P(f"Stopping error log reader for key {key}...")
      err_logs_reader.stop()

    self.__maybe_print_key_logs(key)

    self.dct_logs_reader.pop(key, None)
    self.dct_err_logs_reader.pop(key, None)
    return

  def _maybe_read_and_stop_all_log_readers(self):
    self.P("Reading and stopping all log readers...")
    log_keys = set(list(self.dct_logs_reader.keys()) + list(self.dct_err_logs_reader.keys()))
    self.P(f"Log keys: {log_keys}")
    for key in log_keys:
      self.__maybe_read_and_stop_key_log_readers(key)
    return

  # setup commands methods
  def __maybe_run_all_setup_commands(self):
    if self.failed:
      return

    has_finished_setup_commands = self.__has_finished_setup_commands()
    if has_finished_setup_commands:
      return
    
    self.P("Running setup commands (`has_finished_setup_commands: {}`)".format(has_finished_setup_commands))

    for idx in range(len(self.get_setup_commands())):
      self.__maybe_run_nth_setup_command(idx)
    return


  def _maybe_close_setup_commands(self):
    if not any(self.setup_commands_started):
      self.P("No setup commands were started. Skipping teardown.")
      return

    if all(self.setup_commands_finished):
      self.P("All setup commands have finished. Skipping teardown.")
      return

    idx_process_list = [(idx, process) for idx, process in enumerate(self.setup_commands_processes)]
    # reverse the list to kill the last started processes first
    reversed_idx_process_list = idx_process_list[::-1]
    for idx, process in reversed_idx_process_list:
      if self.setup_commands_started[idx] and not self.setup_commands_finished[idx]:
        self.P(f"Setup command nr {idx} has not finished. Killing it.")
        self.__maybe_kill_process(process, f"setup_{idx}")
    # endfor all setup commands
    return


  def __maybe_run_nth_setup_command(self, idx, timeout=None):
    if self.failed:
      return

    if idx > 0 and not self.setup_commands_finished[idx - 1]:
      # Previous setup command has not finished yet. Skip this one.
      return

    if not self.setup_commands_started[idx]:
      self.P(f"Running setup command nr {idx}: {self.get_setup_commands()[idx]}")
      proc, logs_reader, err_logs_reader = self.__run_command(self.get_setup_commands()[idx], self.base_env)
      self.setup_commands_processes[idx] = proc
      self.dct_logs_reader[f"setup_{idx}"] = logs_reader
      self.dct_err_logs_reader[f"setup_{idx}"] = err_logs_reader

      self.setup_commands_started[idx] = True
      self.setup_commands_start_time[idx] = self.time()
    # endif setup command started

    if not self.setup_commands_finished[idx]:
      finished, failed = self.__wait_for_command(
        process=self.setup_commands_processes[idx],
        timeout=0.1,
      )

      self.setup_commands_finished[idx] = finished

      if finished and not failed:
        self.__maybe_read_and_stop_key_log_readers(f"setup_{idx}")
        self.add_payload_by_fields(
          command_type="setup",
          command_idx=idx,
          command_str=self.get_setup_commands()[idx],
          command_status="success"
        )
        self.P(f"Setup command nr {idx} finished successfully")
      elif finished and failed:
        self.__maybe_read_and_stop_key_log_readers(f"setup_{idx}")
        self.add_payload_by_fields(
          command_type="setup",
          command_idx=idx,
          command_str=self.get_setup_commands()[idx],
          command_status="failed"
        )
        self.P(f"ERROR: Setup command nr {idx} finished with exit code {self.setup_commands_processes[idx].returncode}")
        self.failed = True
      elif not finished and timeout is not None and timeout > 0:
        if self.time() - self.setup_commands_start_time[idx] > timeout:
          self.setup_commands_processes[idx].kill()
          self.__maybe_read_and_stop_key_log_readers(f"setup_{idx}")
          self.P(f"ERROR: Setup command nr {idx} timed out")
          self.add_payload_by_fields(
            command_type="setup",
            command_idx=idx,
            command_str=self.get_setup_commands()[idx],
            command_status="timeout"
          )
          self.failed = True
    # endif setup command finished
    return


  def __has_finished_setup_commands(self):
    return all(self.setup_commands_finished)


  # start commands methods
  def __maybe_run_all_start_commands(self):
    if self.failed:
      return

    if self.__has_finished_start_commands():
      return

    if not self.__has_finished_setup_commands():
      return

    if not self.can_run_start_commands:
      return
    
    if not self.__all_start_running():
      self.P("Running START commands...")
    else:
      self.__wait_count += 1
      self.P(f"Waiting for START commands (pass #{self.__wait_count})...")
      self.sleep(1)

    for idx in range(len(self.get_start_commands())):
      self.__maybe_run_nth_start_command(idx)
    return


  def __all_start_running(self):
    result = True
    cmds = self.get_start_commands()
    for idx in range(len(cmds)):
      if not self.start_commands_started[idx]:
        result = False
        break
    return result


  def _maybe_close_start_commands(self):
    if not any(self.start_commands_started):
      self.P("Server was never started. Skipping teardown.")
      return

    idx_process_list = [(idx, process) for idx, process in enumerate(self.start_commands_processes)]
    # reverse the list to kill the last started processes first
    reversed_start_commands = idx_process_list[::-1]
    for idx, process in reversed_start_commands:
      self.__maybe_kill_process(process, f"start_{idx}")
    # endfor all start commands

  def __maybe_run_nth_start_command(self, idx, timeout=5):
    if self.failed:
      return

    if idx > 0 and not self.start_commands_finished[idx - 1]:
      # Previous start command has not finished yet. Skip this one.
      return

    if not self.start_commands_started[idx]:
      cmd = self.get_start_commands()[idx]
      self.P(f"Running start command nr {idx}: {cmd}")
      proc, logs_reader, err_logs_reader = self.__run_command(cmd, self.prepared_env)
      self.start_commands_processes[idx] = proc
      self.dct_logs_reader[f"start_{idx}"] = logs_reader
      self.dct_err_logs_reader[f"start_{idx}"] = err_logs_reader

      self.start_commands_started[idx] = True
      self.start_commands_start_time[idx] = self.time()
    # endif start command started

    if not self.start_commands_finished[idx]:
      finished, _ = self.__wait_for_command(
        process=self.start_commands_processes[idx],
        timeout=0.1,
      )

      self.start_commands_finished[idx] = finished

      if finished:
        self.__maybe_read_and_stop_key_log_readers(f"start_{idx}")
        self.add_payload_by_fields(
          command_type="start",
          command_idx=idx,
          command_str=self.get_start_commands()[idx],
          command_status="failed"
        )
        self.P(f"Start command nr {idx} finished unexpectedly. Please check the logs.")
        self.failed = True

      elif self.time() - self.start_commands_start_time[idx] > timeout:
        self.start_commands_finished[idx] = True
        cmd = self.get_start_commands()[idx]
        self.add_payload_by_fields(
          command_type="start",
          command_idx=idx,
          command_str=cmd,
          command_status="success"
        )
        self.P(f"Start cmd {idx} '{cmd}' is running after {timeout}s.")
    # endif setup command finished
    return

  def __has_finished_start_commands(self):
    return all(self.start_commands_finished)
  
  
  def _reload_server(self):
    self.P("Initiating server reload...")
    
    self._maybe_close_setup_commands()
    self._maybe_close_start_commands()
    self._maybe_read_and_stop_all_log_readers()

    self.maybe_stop_tunnel_engine()

    self.assets_initialized = False
    self.failed = False

    self.setup_commands_started = [False] * len(self.get_setup_commands())
    self.setup_commands_finished = [False] * len(self.get_setup_commands())
    self.setup_commands_processes = [None] * len(self.get_setup_commands())
    self.setup_commands_start_time = [None] * len(self.get_setup_commands())

    self.start_commands_started = [False] * len(self.get_start_commands())
    self.start_commands_finished = [False] * len(self.get_start_commands())
    self.start_commands_processes = [None] * len(self.get_start_commands())
    self.start_commands_start_time = [None] * len(self.get_start_commands())

    self.__init_temp_dir()
    self.__deallocate_port()
    self.P('Attempting to init assets due to reload...')
    self._allocate_port()
    # In case a new port is allocated instead of the one previously used.
    # The commands will be relogged in case something changed because of the
    # port reallocation.
    self.__commands_ready = False
    self.__maybe_setup_commands()
    self.__maybe_init_assets()
    self.maybe_start_tunnel_engine()
    return  
  
  
  
  def __check_new_repo_version(self):
    result = False  # return false by default including if no git url is provided
    if not isinstance(self.cfg_assets, dict):
      return result
    # endif valid assets dict
    operation = self.cfg_assets.get('operation')
    # first check not to run this operation too many times
    if operation == 'clone':
      url = self.cfg_assets.get('url')
      if url is None:
        self.P(f"Operation {operation}, but no URL provided. Check assets!", color="r")
        return result
      if not isinstance(url, str):
        self.P(f"Operation {operation}, but URL is not a string. Check assets!", color="r")
        return result
      # endif valid url provided
      username = self.cfg_assets.get('username')
      token = self.cfg_assets.get('token')
      track_mode = self.cfg_assets.get('track', WEB_APP_DEFAULT_GIT_TRACK_MODE)

      # If we haven't cloned anything yet, treat it like a new version:
      if self.__git_commit_hash is None and track_mode == 'commit':
        self.P("No previous local git commit info. Assuming new commit and initializing...")
        return True
      if self.__last_release_tag is None and track_mode == 'tag':
        self.P("No previous local release tag info. Assuming new release and initializing...")
        return True

      # 1. Check for a new commit.
      if track_mode == 'commit':
        if self.__can_request_git():
          remote_commit = self.git_get_last_commit_hash(repo_url=url, user=username, token=token)
          if remote_commit is None:
            self.P("Could not get the commit hash. Assuming no new version.")
            result = False
          elif remote_commit != self.__git_commit_hash:
            self.P(
              f"New git commit found: local={self.__git_commit_hash} vs remote={remote_commit}."
              f"Server reloading procedure will be initiated..."
            )
            result = True
        # endif can request git
      # 2. Check for a new release.
      elif track_mode == 'tag':
        if self.__can_request_git():
          last_release = self.git_get_last_release_tag(repo_url=url, user=username, token=token)
          if last_release is None:
            self.P("Could not get the last release tag. Assuming no new version.")
            result = False
          elif last_release != self.__last_release_tag:
            self.P(
              f"New release tag found: local={self.__last_release_tag} vs remote={last_release}."
              f"Server reloading procedure will be initiated..."
            )
            result = True
      # endif track_mode
    elif operation == 'release_asset':
      url = self.cfg_assets.get('url')
      if not isinstance(url, str):
        self.P(f"Operation release_asset, but URL is not valid. Check assets!", color="r")
        return result

      token = self.cfg_assets.get('token')
      release_tag_substring = self.cfg_assets.get('release_tag')
      asset_filter = self.cfg_assets.get('asset_filter')

      # If we have never downloaded anything, assume "new version"
      if self.__last_asset_id is None:
        self.P("[release_asset] No cached asset ID. Assuming new asset.")
        return True

      # Try to check for an updated asset
      if self.__can_request_git():  # or rename to __can_make_gh_api_request()
        new_info = self.git_get_latest_release_asset_info(
          repo_url=url,
          token=token,
          release_tag_substring=release_tag_substring,
          asset_filter=asset_filter
        )
        if not new_info:
          self.P("[release_asset] Could not get asset info. Assuming no new version.")
          return False

        # Compare new_info with our cached values
        new_asset_id = new_info["asset_id"]
        new_asset_updated = new_info["asset_updated_at"]
        old_asset_id = self.__last_asset_id
        old_asset_updated = self.__last_asset_updated_at

        if new_asset_id != old_asset_id or new_asset_updated != old_asset_updated:
          self.P(
            f"[release_asset] New asset found!\n"
            f"Old asset_id={old_asset_id}, updated_at={old_asset_updated}\n"
            f"New asset_id={new_asset_id}, updated_at={new_asset_updated}\n"
            "Server reloading procedure will be initiated..."
          )
          result = True
        # endif new asset version
      # endif can request git
    # endif operation handling
    return result

  def check_assets_path(self, assets_path, raise_exception=True):
    """
    Utility method for checking if the assets path is safe.
    That means it is either a URL or a safe relative path.
    Parameters
    ----------
    assets_path : str
        The path to the assets.
    raise_exception : bool
        If True, an exception will be raised if the path is not safe.
        Otherwise, an error will be added to the plugin.

    """
    # TODO: maybe allow some local assets in case of private networks?
    # If the assets path is a local path, it must be a safe path.
    if os.path.exists(assets_path) and not self.is_path_safe(assets_path, base_path='.'):
      msg = ("Local assets in not safe paths are off-limits!"
             "Please provide a URL or a safe relative path(without any symlink or \"../\").")
      if raise_exception:
        raise ValueError(msg)
      else:
        self.add_error(msg)
      return
    return

  def validate_assets(self):
    """
    Validate the configuration of `ASSETS`.
    This will check if someone is trying to retrieve local files or other sensitive data.

    Returns
    -------

    """
    # If no assets are provided, no validation is needed.
    if self.cfg_assets is None:
      return

    if not isinstance(self.cfg_assets, (dict, str)):
      self.add_error("`ASSETS`, if specified, must be a dictionary or a string.")
      return
    # endif valid assets type

    # If no assets path can be obtained, no validation is needed.
    assets_path = self.cfg_assets if isinstance(self.cfg_assets, str) else self.cfg_assets.get('url')
    if assets_path is None:
      return

    # The assets path must be a string.
    if not isinstance(assets_path, str):
      self.add_error("`ASSETS.url` must be a string.")
      return

    # If the assets path is a local path, it must be a safe path.
    self.check_assets_path(assets_path=assets_path, raise_exception=False)

    return

  # assets handling methods
  def __maybe_download_assets(self):
    """
      self.cfg_assets = {
        "url": "https://example.com/assets.zip",
        "operation": "download",
      }
      self.cfg_assets = {
        "url": "https://github.com/user/repo",
        "username": "username",
        "token": "token",
        "operation": "clone",
      }
      self.cfg_assets = {
        "url": "https://github.com/user/repo",
        "username": null,
        "token": null,
        "operation": "clone",
        "track": "commit"  # Default value
      }
      self.cfg_assets = {
        "url": "https://github.com/user/repo",
        "username": null,
        "token": null,
        "operation": "clone",
        "track": "tag"
      }
      self.cfg_assets = {
        "url": "https://github.com/user/repo",
        "username": null,
        "token": null,
        "operation": "clone",
        "track": "tag",
        "release_tag": "latest"
      }
      self.cfg_assets = {
        "url": "https://github.com/user/repo",
        "username": null,
        "token": null,
        "operation": "release_asset",
        "asset_filter": "your-web-app-build.zip"
        "release_tag": "latest"
      }
      self.cfg_assets = {
        "url": "/path/to/local/dir",
        "operation": "download",
      }
      self.cfg_assets = {
        "url"=[["base64_encoded_file", "encoded_file_name"], ...],
        "operation": "decode",
      }
    """
    # handle assets url: download, extract, then copy, then delete
    relative_assets_path = self.os_path.join('downloaded_assets', self.plugin_id, 'assets')

    # 1) Parse the assets configuration
    operation = None
    assets_path = None

    # check if assets is a dict or a string
    # and extract the url and operation
    if isinstance(self.cfg_assets, dict):
      dct_data = self.cfg_assets
      operation = dct_data.get("operation", "download")
      assets_path = dct_data.get("url", None)

    elif isinstance(self.cfg_assets, str):
      assets_path = self.cfg_assets
      operation = "download"

    if assets_path is None:
      return None
      # raise ValueError("No assets provided")

    self.check_assets_path(assets_path=assets_path, raise_exception=True)

    # 2) Handle each operation
    if operation == "release_asset":
      username = dct_data.get("username")
      token = dct_data.get("token")
      release_tag_substring = dct_data.get("release_tag")
      asset_filter = dct_data.get("asset_filter")

      download_dir = self.os_path.join(self.get_output_folder(), relative_assets_path)
      local_file = self.git_download_release_asset(
        repo_url=assets_path,
        user=username,
        token=token,
        release_tag_substring=release_tag_substring,
        asset_filter=asset_filter,
        download_dir=download_dir
      )
      if not local_file:
        err_msg = "[ERROR] Could not download the prebuilt artifact."
        self.P(err_msg, color='r')
        raise Exception(err_msg)
        return None

      # ------------------------------------
      # (A) Cache release metadata for checks
      # ------------------------------------
      # We can re-call git_get_latest_release_asset_info to get exactly what we used
      latest_info = self.git_get_latest_release_asset_info(
        assets_path, token=token,
        release_tag_substring=release_tag_substring,
        asset_filter=asset_filter
      )
      if latest_info:
        self.__last_release_tag = latest_info["release_tag"]
        self.__last_asset_id = latest_info["asset_id"]
        self.__last_asset_updated_at = latest_info["asset_updated_at"]
        self.P(f"Cached release tag: {self.__last_release_tag}")
        self.P(f"Cached asset ID: {self.__last_asset_id}")
        self.P(f"Cached asset updated_at: {self.__last_asset_updated_at}")
      # endif latest_info

      # Auto-extract if needed
      final_extract_dir = download_dir
      if local_file.endswith(".zip"):
        new_dir = self.os_path.join('downloaded_assets', self.plugin_id, 'unzipped_asset')
        self.maybe_download(
          url=local_file,
          fn=new_dir,
          target='output',
          unzip=True
        )
        os.remove(local_file)
        final_extract_dir = self.os_path.join(self.get_output_folder(), new_dir)
      else:
        self.P(f"Prebuilt artifact is not .zip. Leaving as is: {local_file}")

      self.P(f"Prebuilt artifact is ready at {final_extract_dir}")
      return final_extract_dir
    elif operation == "clone":
      username = dct_data.get("username", None)
      token = dct_data.get("token", None)
      track_mode = dct_data.get("track", "commit")  # default = commit
      release_tag_substring = dct_data.get("release_tag", None)

      # Clone the repo into relative_assets_path
      self.git_clone(
        repo_url=assets_path,
        repo_dir=relative_assets_path,
        target='output',
        user=username,
        token=token,
        pull_if_exists=True, # no need to pull if each time we delete the folder
      )

      # If the user wants to track "tag" instead of "commit"
      if track_mode == "tag":
        # 2A) Find the newest release tag (optionally filtered)
        last_release_tag = self.git_get_last_release_tag(
          repo_url=assets_path,
          user=username,
          token=token,
          tag_name=release_tag_substring,  # e.g. "latest" or "mainnet"
        )
        if last_release_tag:
          # 2B) Checkout that release tag in the *already cloned* repo
          full_repo_dir = self.os_path.join(self.get_output_folder(), relative_assets_path)
          self.git_checkout_tag(repo_dir=full_repo_dir, tag=last_release_tag)

          # 2C) Cache the release tag
          self.__last_release_tag = last_release_tag
          self.P(f"Checked out release tag: {last_release_tag}")
        else:
          self.P("No matching release tag found; staying on default HEAD.", color='y')
      # endif release mode

      # 2D) Regardless of commit or release, store the commit hash for debugging
      full_repo_dir = self.os_path.join(self.get_output_folder(), relative_assets_path)
      commit_hash = self.git_get_local_commit_hash(repo_dir=full_repo_dir)
      self.__git_commit_hash = commit_hash
      self.P(f"Finished cloning git repository. Current commit hash: {commit_hash}")
    elif operation == "download":
      self.maybe_download(
        url=assets_path,
        fn=relative_assets_path,
        target='output'
      )
    elif operation == "decode":
      target_dir = self.os_path.join(self.get_output_folder(), relative_assets_path)
      for base64_encoded_file, encoded_file_name in assets_path:
        file_path = self.os_path.join(target_dir, encoded_file_name)
        os.makedirs(self.os_path.dirname(file_path), exist_ok=True)

        encoded_file = self.base64_to_str(base64_encoded_file, decompress=True)
        with open(file_path, 'w') as f:
          f.write(encoded_file)
        # endwith
      # endfor
    else:
      raise ValueError(f"Invalid operation {operation}")

    # now check if it is a zip file
    assets_path = self.os_path.join(self.get_output_folder(), relative_assets_path)
    if self.os_path.isfile(assets_path):
      if not assets_path.endswith('.zip'):
        os.rename(assets_path, assets_path + '.zip')
        assets_path += '.zip'

      relative_assets_path = self.os_path.join('downloaded_assets', self.plugin_id, 'unzipped')
      self.maybe_download(
        url=assets_path,
        fn=relative_assets_path,
        target='output',
        unzip=True
      )
      # remove zip file
      os.remove(assets_path)

    assets_path = self.os_path.join(self.get_output_folder(), relative_assets_path)
    return assets_path

  def __maybe_forced_reload(self):
    reload_interval = self.cfg_forced_reload_interval or 0
    if reload_interval > 0 and self.time() - self.webapp_reload_last_timestamp > reload_interval:
      self.P(f"Forced restart initiated due to `FORCED_RELOAD_INTERVAL` ({reload_interval} seconds)")
      self._reload_server()
    return

  def __maybe_init_assets(self):
    if self.assets_initialized:
      self.__maybe_forced_reload()
      # check if new git assets are available
      new_repo_version = self.__check_new_repo_version()
      if new_repo_version:
        self.P("New git assets available. Reloading server...")        
        self._reload_server()
      return
    
    self.P("Initializing assets (`assets_initialized: {}`)".format(self.assets_initialized))

    # download/clone/create/unzip assets
    assets_path = self.__maybe_download_assets()

    # prepare environment variables
    self.__prepare_env(assets_path=assets_path)

    # initialize assets -- copy them to the temp directory
    self.initialize_assets(
      src_dir=assets_path,
      dst_dir=self.script_temp_dir,
      jinja_args=self.jinja_args
    )

    self.webapp_reload_last_timestamp = self.time()
    self.assets_initialized = True
    return

  
  
  # other plugin default methods
  
  def __setup_commands(self):
    setup_commands = self.get_setup_commands()
    self.setup_commands_started = [False] * len(setup_commands)
    self.setup_commands_finished = [False] * len(setup_commands)
    self.setup_commands_processes = [None] * len(setup_commands)
    self.setup_commands_start_time = [None] * len(setup_commands)

    start_commands = self.get_start_commands()
    self.start_commands_started = [False] * len(start_commands)
    self.start_commands_finished = [False] * len(start_commands)
    self.start_commands_processes = [None] * len(start_commands)
    self.start_commands_start_time = [None] * len(start_commands)

    self.logs = self.deque(maxlen=1000)
    self.dct_logs_reader = {}

    self.err_logs = self.deque(maxlen=1000)
    self.dct_err_logs_reader = {}

    self.P(f"Port: {self.port}")
    self.P(f"Setup commands: {setup_commands}")
    self.P(f"Start commands: {start_commands}")
    return


  def _on_close(self):
    self._maybe_close_setup_commands()
    self._maybe_close_start_commands()

    # close all log readers that are still running
    # this should not have any effect, as the logs should have been
    # closed during the teardown of the setup and start processes
    self._maybe_read_and_stop_all_log_readers()

    # cleanup the temp directory
    shutil.rmtree(self.script_temp_dir)

    self.__deallocate_port()

    super(BaseWebAppPlugin, self)._on_close()
    return


  def on_close(self):
    # This method is called by super(BaseWebAppPlugin, self)._on_close()
    super(BaseWebAppPlugin, self).on_close()
    self.maybe_stop_tunnel_engine()
    return

  def on_config(self):
    self.P(f"Reconfigured plugin. Current tunnel engine: {self.cfg_tunnel_engine} | Last tunnel engine: {self.__last_tunnel_engine}")
    if self.cfg_tunnel_engine != self.__last_tunnel_engine:
      self.P(f"Tunnel engine changed from {self.__last_tunnel_engine} to {self.cfg_tunnel_engine}")
      if self.__last_tunnel_engine == 'ngrok':
        self.maybe_stop_tunnel_engine_ngrok()
      self._reload_server()
      self.__last_tunnel_engine = self.cfg_tunnel_engine
    # endif tunnel engine changed
    return

  def _on_command(self, data, delta_logs=None, full_logs=None, start=None, reload=None, **kwargs):
    super(BaseWebAppPlugin, self)._on_command(data, **kwargs)

    if (isinstance(data, str) and data.upper() == 'DELTA_LOGS') or delta_logs:
      logs, err_logs = self.__get_delta_logs()
      self.add_payload_by_fields(
        command_params=data,
        logs=logs,
        err_logs=err_logs,
      )
    if (isinstance(data, str) and data.upper() == 'FULL_LOGS') or full_logs:
      # TODO: Implement full logs
      self.add_payload_by_fields(
        command_params=data,
        logs=[]
      )

    if (isinstance(data, str) and data.upper() == 'START') or start:
      self.can_run_start_commands = True
      self.P("Starting server")

    if (isinstance(data, str) and data.upper() == 'RELOAD') or reload:
      self._reload_server()

    return

  def get_port(self):
    # Override of the auto-generated cfg_port property to handle
    # ports from environment variables.
    configured_port = self.cfg_port
    if isinstance(configured_port, str):
      configured_port = configured_port.strip()
      if configured_port.isdigit():
        configured_port = int(configured_port)
    # endif configured_port is str
    return configured_port

  # Exposed methods
  @property
  def port(self):
    if 'USED_PORTS' not in self.plugins_shmem:
      return None
    if self.str_unique_identification not in self.plugins_shmem['USED_PORTS']:
      return None
    port = self.plugins_shmem['USED_PORTS'][self.str_unique_identification]
    return port

  @property
  def jinja_args(self):
    return {}

  def get_setup_commands(self):
    setup_commands = self.cfg_setup_commands
    try:
      setup_commands = super(BaseWebAppPlugin, self).get_setup_commands() + setup_commands
    except Exception as e:
      pass
    return setup_commands

  def get_start_commands(self):
    start_commands = self.cfg_start_commands
    try:
      start_commands = start_commands + super(BaseWebAppPlugin, self).get_start_commands()
    except Exception as e:
      pass
    return start_commands

  def initialize_assets(self, src_dir, dst_dir, jinja_args):
    """
    Initialize and copy assets, expanding any jinja templates.
    All files from the source directory are copied to the
    destination directory with the following exceptions:
      - are symbolic links are ignored
      - files named ending with .jinja are expanded as jinja templates,
        .jinja is removed from the filename and the result copied to
        the destination folder.
    This maintains the directory structure of the source folder.
    In case src_dir is None, only the .env files are written in the destination folder.

    Parameters
    ----------
    src_dir: str or None, path to the source directory
    dst_dir: str, path to the destination directory
    jinja_args: dict, jinja keys to use while expanding the templates

    Returns
    -------
    None
    """

    # now copy the assets to the destination
    self.P(f'Copying assets from {src_dir} to {dst_dir} with keys {jinja_args}')

    if src_dir is not None:
      env = Environment(loader=FileSystemLoader('.'))
      # Walk through the source directory.
      for root, _, files in os.walk(src_dir):
        for file in files:
          src_file_path = self.os_path.join(root, file)
          dst_file_path = self.os_path.join(
            dst_dir,
            self.os_path.relpath(src_file_path, src_dir)
          )

          # If we have a symlink don't do anything.
          if self.os_path.islink(src_file_path):
            continue

          # Make sure the destination directory exists.
          os.makedirs(self.os_path.dirname(dst_file_path), exist_ok=True)

          is_jinja_template = False
          if src_file_path.endswith(('.jinja')):
            dst_file_path = dst_file_path[:-len('.jinja')]
            is_jinja_template = True
          if src_file_path.endswith(('.j2')):
            dst_file_path = dst_file_path[:-len('.j2')]
            is_jinja_template = True

          # If this file is a jinja template render it to a file with the .jinja suffix removed.
          # Otherwise just copy the file to the destination directory.
          if is_jinja_template:
            template = env.get_template(src_file_path)
            rendered_content = template.render(jinja_args)
            with open(dst_file_path, 'w') as f:
              f.write(rendered_content)
          else:
            shutil.copy2(src_file_path, dst_file_path)
          # endif is jinja template
        # endfor all files
      # endfor os.walk
    # endif src_dir is not None

    # write .env file in the target directory
    # environment variables are passed in subprocess.Popen, so this is not needed
    # but it's useful for debugging
    with open(self.os_path.join(self.script_temp_dir, '.env'), 'w') as f:
      for key, value in self.prepared_env.items():
        f.write(f"{key}={value}\n")

    with open(self.os_path.join(self.script_temp_dir, '.start_env_used'), 'w') as f:
      for key, value in self.prepared_env.items():
        f.write(f"{key}={value}\n")

    with open(self.os_path.join(self.script_temp_dir, '.setup_env_used'), 'w') as f:
      for key, value in self.base_env.items():
        f.write(f"{key}={value}\n")

    # now cleanup the download folder if it exists
    downloaded_assets_path = self.os_path.join(self.get_output_folder(), 'downloaded_assets', self.plugin_id)
    if self.os_path.exists(downloaded_assets_path):
      shutil.rmtree(downloaded_assets_path)

    self.P("Assets copied successfully")

    return

  def __maybe_setup_commands(self):
    if self.__commands_ready:
      return
    self.__setup_commands()
    self.__commands_ready = True
    return

  def _process(self):  # Check: _process as opposed to process
    self.__maybe_setup_commands()

    self.__maybe_init_assets()  # Check: auto-updates point here?

    self.maybe_init_tunnel_engine()

    self.__maybe_run_all_setup_commands()

    self.maybe_start_tunnel_engine()

    self.__maybe_run_all_start_commands()

    self.__maybe_print_all_logs() # Check: must review

    super(BaseWebAppPlugin, self)._process() # Check: why is this required
    self.maybe_tunnel_engine_ping()
    return
