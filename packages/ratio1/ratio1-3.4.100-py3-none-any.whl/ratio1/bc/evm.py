import json
import os

from collections import namedtuple
from copy import deepcopy

from datetime import timezone, datetime

from eth_account import Account
from eth_utils import keccak, to_checksum_address
from eth_account.messages import encode_defunct

from ..const.base import EE_VPN_IMPL_ENV_KEY, dAuth, BCctbase, ETHVarTypes, EVM_ABI_DATA
from ..const.evm_net import EVM_NET_DATA, EvmNetData

EE_VPN_IMPL = str(os.environ.get(EE_VPN_IMPL_ENV_KEY, False)).lower() in [
  'true', '1', 'yes', 'y', 't', 'on'
]

Web3Vars = namedtuple(
  "Web3Vars", [  
    "w3", 
    "rpc_url", 
    "network", 
    "genesis_date",
    "epoch_length_seconds",
    "nd_contract_address", 
    "r1_contract_address", 
    "proxy_contract_address",  
    "controller_contract_address",
    "poai_manager_address",
    "get_oracles_abi",
  ]
)


if not EE_VPN_IMPL:
  from web3 import Web3
else:
  class Web3:
    """
    VPS enabled. Web3 is not available.
    """



class _EVMMixin:
  
  # EVM address methods
  if True:
    @staticmethod
    def is_valid_evm_address(address: str) -> bool:
      """
      Check if the input string is a valid Ethereum (EVM) address using basic heuristics.

      Parameters
      ----------
      address : str
          The address string to verify.

      Returns
      -------
      bool
          True if `address` meets the basic criteria for an EVM address, False otherwise.
      """
      # Basic checks:
      # A) Must start with '0x'
      # B) Must be exactly 42 characters in total
      # C) All remaining characters must be valid hexadecimal digits
      if not isinstance(address, str):
        return False
      if not address.startswith("0x"):
        return False
      if len(address) != 42:
        return False
      
      hex_part = address[2:]
      # Ensure all characters in the hex part are valid hex digits
      return all(c in "0123456789abcdefABCDEF" for c in hex_part)
    
    @property
    def eth_types(self) -> ETHVarTypes:
      return ETHVarTypes
    
    @staticmethod
    def is_valid_eth_address(address: str) -> bool:
      """
      Check if the input string is a valid Ethereum (EVM) address using basic heuristics.

      Parameters
      ----------
      address : str
          The address string to verify.

      Returns
      -------
      bool
          True if `address` meets the basic criteria for an EVM address, False otherwise.
      """
      return _EVMMixin.is_valid_evm_address(address)


    def _get_eth_address(self, pk=None):
      if pk is None:
        pk = self.public_key
      raw_public_key = pk.public_numbers()

      # Compute Ethereum-compatible address
      x = raw_public_key.x.to_bytes(32, 'big')
      y = raw_public_key.y.to_bytes(32, 'big')
      uncompressed_key = b'\x04' + x + y
      keccak_hash = keccak(uncompressed_key[1:])  # Remove 0x04 prefix
      eth_address = "0x" + keccak_hash[-20:].hex()
      eth_address = to_checksum_address(eth_address)
      return eth_address    


    def _get_eth_account(self):
      private_key_bytes = self.private_key.private_numbers().private_value.to_bytes(32, 'big')
      return Account.from_key(private_key_bytes)
    
    
    def node_address_to_eth_address(self, address):
      """
      Converts a node address to an Ethereum address.

      Parameters
      ----------
      address : str
          The node address convert.

      Returns
      -------
      str
          The Ethereum address.
      """
      public_key = self._address_to_pk(address)
      return self._get_eth_address(pk=public_key)


    def is_node_address_in_eth_addresses(self, node_address: str, lst_eth_addrs) -> bool:
      """
      Check if the node address is in the list of Ethereum addresses

      Parameters
      ----------
      node_address : str
        the node address.
        
      lst_eth_addrs : list
        list of Ethereum addresses.

      Returns
      -------
      bool
        True if the node address is in the list of Ethereum addresses.

      """
      eth_addr = self.node_address_to_eth_address(node_address)
      return eth_addr in lst_eth_addrs    
  
  
  # EVM networks
  if True:
    def reset_network(self, network: str):
      assert network.lower() in dAuth.EVM_NET_DATA, f"Invalid network: {network}"
      os.environ[dAuth.DAUTH_NET_ENV_KEY] = network      
      return self.get_evm_network()
    
    def get_evm_network(self) -> str:
      """
      Get the current network

      Returns
      -------
      str
        the network name.

      """
      if EE_VPN_IMPL:
        return "VPN"        
      network = os.environ.get(dAuth.DAUTH_NET_ENV_KEY, dAuth.DAUTH_SDK_NET_DEFAULT)
      
      if not self._first_checks_done[dAuth.DAUTH_NET_ENV_KEY]:
        if dAuth.DAUTH_NET_ENV_KEY not in os.environ:
          self.P(f"Using default {network=}...", verbosity=2)
        else:
          self.P(f"Using {network=} from `{dAuth.DAUTH_NET_ENV_KEY}` env key...", verbosity=2)
        self._first_checks_done[dAuth.DAUTH_NET_ENV_KEY] = True
      # done first checks
      
      if not hasattr(self, "current_evm_network") or self.current_evm_network != network:
        self.current_evm_network = network
        network_data = self.get_network_data(network)
        rpc_url = network_data[dAuth.EvmNetData.DAUTH_RPC_KEY]
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.P(f"Resetting Web3 for {network=} via {rpc_url=}...")
      return network
    
    @property
    def evm_network(self):
      if EE_VPN_IMPL:
        return "VPN"
      return self.get_evm_network()

    
    def get_network_data(self, network: str) -> dict:
      assert isinstance(network, str) and network.lower() in dAuth.EVM_NET_DATA, f"Invalid network: {network}"
      return dAuth.EVM_NET_DATA[network.lower()]
    

    @property
    def network_rpc(self):
      return self.get_network_data(self.evm_network)[dAuth.EvmNetData.DAUTH_RPC_KEY]


    @property
    def nd_contract_address(self):
      return self.get_network_data(self.evm_network)[dAuth.EvmNetData.DAUTH_ND_ADDR_KEY]
    
    @property
    def r1_contract_address(self):
      return self.get_network_data(self.evm_network)[dAuth.EvmNetData.DAUTH_R1_ADDR_KEY]


    def _get_web3_vars(self, network=None) -> Web3Vars:
      if network is None:
        network = self.evm_network
        w3 = self.web3
      else:
        w3 = None
        
      network_data = self.get_network_data(network)
      nd_contract_address = network_data[dAuth.EvmNetData.DAUTH_ND_ADDR_KEY]
      rpc_url = network_data[dAuth.EvmNetData.DAUTH_RPC_KEY]
      r1_contract_address = network_data[dAuth.EvmNetData.DAUTH_R1_ADDR_KEY]
      proxy_contract_address = network_data[dAuth.EvmNetData.DAUTH_PROXYAPI_ADDR_KEY]
      str_genesis_date = network_data[dAuth.EvmNetData.EE_GENESIS_EPOCH_DATE_KEY]
      controller_contract_address = network_data[dAuth.EvmNetData.DAUTH_CONTROLLER_ADDR_KEY]
      poai_manager_address = network_data[dAuth.EvmNetData.DAUTH_POAI_MANAGER_ADDR_KEY]
      get_oracles_abi = network_data[dAuth.EvmNetData.DAUTH_GET_ORACLES_ABI]
      genesis_date = self.log.str_to_date(str_genesis_date).replace(tzinfo=timezone.utc)
      ep_sec = (
        network_data[dAuth.EvmNetData.EE_EPOCH_INTERVAL_SECONDS_KEY] * 
        network_data[dAuth.EvmNetData.EE_EPOCH_INTERVALS_KEY]
      )

      if w3 is None:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.P(f"Created temporary Web3 for {network=} via {rpc_url=}...", verbosity=2)
      #end if
      
      result = Web3Vars(
        w3=w3, 
        rpc_url=rpc_url, 
        network=network,
        genesis_date=genesis_date,
        epoch_length_seconds=ep_sec,
        nd_contract_address=nd_contract_address, 
        r1_contract_address=r1_contract_address, 
        proxy_contract_address=proxy_contract_address, 
        controller_contract_address=controller_contract_address,
        poai_manager_address=poai_manager_address,
        get_oracles_abi=get_oracles_abi,
      )
      return result

  # Epoch handling
  if True:    
    def get_epoch_id(self, date : any, network: str = None):
      """
      Given a date as string or datetime, returns the epoch id - ie the number of days since 
      the genesis epoch.

      Parameters
      ----------
      date : str or date
        The date as string that will be converted to epoch id.
      """
      w3vars = self._get_web3_vars(network)
      if isinstance(date, str):
        # remove milliseconds from string
        date = date.split('.')[0]
        date = self.log.str_to_date(date)
        # again this is correct to replace in order to have a timezone aware date
        # and not consider the local timezone. the `date` string naive should be UTC offsetted
        date = date.replace(tzinfo=timezone.utc) 
      # compute difference between date and self.__genesis_date in seconds
      elapsed_seconds = (date - w3vars.genesis_date).total_seconds()
      
      # the epoch id starts from 0 - the genesis epoch
      # the epoch id is the number of days since the genesis epoch
      # # TODO: change this if we move to start-from-one offset by adding +1
      # OBS: epoch always ends at AB:CD:59 no matter what 
      epoch_id = int(elapsed_seconds / w3vars.epoch_length_seconds) 
      return epoch_id


    def get_current_date(self):
      # we convert local time to UTC time
      return datetime.now(timezone.utc)


    def get_time_epoch(self):
      """
      Returns the current epoch id.
      """
      return self.get_epoch_id(self.get_current_date())

    
    def get_current_epoch(self):
      """
      Returns the current epoch id using `get_time_epoch`.
      """
      return self.get_time_epoch()    
    
  ## End Epoch handling
      

  # EVM signing methods (internal)
  if True:
    def eth_hash_message(self, types, values, as_hex=False):
      """
      Hashes a message using the keccak256 algorithm.

      Parameters
      ----------
      types : list
          The types of the values.
          
      values : list of any
          The values to hash.

      Returns
      -------
      bytes
          The hash of the message in hexadecimal format.
      """
      message = Web3.solidity_keccak(types, values)
      if as_hex:
        return message.hex()
      return message
    
    
    def eth_sign_message(
      self, 
      types : list, values : list, 
      payload: dict = None,
      verbose: bool = False,
      no_hash: bool = False,
    ):
      """
      Signs a message using the private key.

      Parameters
      ----------
      types : list
          The types of the values.
          
      values : list of any
          The values to sign.
          
      payload: dict, optional
          If provided, the payload will be completed with the signature based on
          the `values` and `types` provided. The default is None.
          
      no_hash : bool, optional
          This is used to skip the hashing of the message. The default is False.

      Returns
      -------
      str
          The signature of the message.
          
      Notes
      -----
      
      This function is using the `eth_account` property generated from the private key via
      the `_get_eth_account` method at the time of the object creation.
      """
      if verbose:
        msg_size = len(values)
        self.P(f"Signing {msg_size=} with {types=}")
      if no_hash:
        assert len(values) == 1 and isinstance(values[0], str), "Only one str value is allowed for no hashing."
        message_hash = values[0].encode('utf-8')
      else:
        message_hash = self.eth_hash_message(types, values, as_hex=False)
      signable_message = encode_defunct(primitive=message_hash)
      signed_message = Account.sign_message(signable_message, private_key=self.eth_account.key)
      if hasattr(signed_message, "message_hash"): # backward compatibility
        signed_message_hash = signed_message.message_hash
      else:
        signed_message_hash = signed_message.messageHash
      signature = signed_message.signature.hex()
      signature = "0x" + signature if not signature.startswith("0x") else signature
      if payload is not None:
        payload[BCctbase.ETH_SIGN] = signature
        payload[BCctbase.ETH_SENDER] = self.eth_address      
      return {
          "message_hash": message_hash.hex(),
          "r": hex(signed_message.r),
          "s": hex(signed_message.s),
          "v": signed_message.v,
          "signature": signature,
          "signed_message": signed_message_hash.hex(),
          "sender" : self.eth_address,
          "eth_signed_data" : types,
      }
      

    def eth_verify_message_signature(
      self, 
      values: list, 
      types: list, 
      signature: str, 
      raise_if_error=False,
      no_hash=False,
    ):
      """
      Verifies an EVM-compatible signature by:
        1) Recomputing the message hash from the provided types/values.
        2) Recovering the signer's address from the signature.
        3) Returning the recovered address or None if verification fails.

      Parameters
      ----------
      values : list
        The original values that were signed.
        
      types : list
        The type definitions (e.g., ["address", "uint256[]", "uint256[]"]).
        Must match exactly what was used to produce the signature.
        
      signature : str
        The signature in hex form (e.g. "0x1234abcd...").

      Returns
      -------
      str or None
        The recovered address as a string (in checksum format), or None if verification fails.
      """
      result = None
      try:
        # 1) Recompute the message hash used at signing time
        if no_hash:
          message_hash = values[0].encode('utf-8')
        else:
          message_hash = self.eth_hash_message(types, values, as_hex=False)
        signable_message = encode_defunct(primitive=message_hash)
        
        # 2) Convert the hex signature string into bytes
        signature_bytes = bytes.fromhex(signature.removeprefix("0x"))
        
        # 3) Recover the address from the signature
        recovered_address = Account.recover_message(signable_message, signature=signature_bytes)
        
        result = recovered_address

      except Exception as exc:
        if raise_if_error:
          raise exc
        else:
          self.P("Signature verification failed: {}".format(exc), color='r')
        # Any error (e.g., malformed signature, mismatch) leads to failure
        result = None
      return result   
         


    def eth_sign_text(
      self, 
      message, 
      signature_only=True,
      no_hash: bool = False,
    ):
      """
      Signs a text message using the private key.

      Parameters
      ----------
      message : str
          The message to sign.
          
      signature_only : bool, optional
          Whether to return only the signature. The default is True

      Returns
      -------
      str
          The signature of the message.
      """
      types = ["string"]
      values = [message]
      result = self.eth_sign_message(
        types, values,
        no_hash=no_hash,
      )
      if signature_only:
        return result["signature"]
      return result   


    def eth_verify_text_signature(
      self, 
      text: str, 
      signature: str, 
      no_hash=False,
      message_prefix: str = "",
      raise_if_error=False,
    ):
      """
      Verifies the signature of a message by checking if the recovered address matches the expected sender.

      Parameters
      ----------
      message : str
          The message that was signed.
          
      signature : str
          The signature in hex form (e.g. "0x1234abcd...").                
          
      no_hash : bool, optional
          If True, the message is not hashed before verification. The default is False.
          This is useful for raw text messages that are not hashed such as the ones signed by
          wallets.
          
      message_prefix : str, optional
          A prefix to be added to the message before hashing (or signing). The default is "".

      Returns
      -------
      bool or None
          True if the signature is valid, False otherwise.
      """
      types = ["string"]
      values = [message_prefix + text]
      result = self.eth_verify_message_signature(
        values=values, types=types, signature=signature, no_hash=no_hash,
        raise_if_error=raise_if_error
      )
      return result
      
    
    
    def eth_sign_payload(
      self, 
      payload: dict, 
      add_data=True,
      indent=0,
      no_hash=False,
      message_prefix: str = "",
    ):
      """
      Signs a payload using the private key.
      
      Parameters
      ----------
      
      payload : dict
          The payload to sign. Must be a dictionary.
          
      add_data : bool, optional
          Whether to add the signature and sender address to the payload. The default is True.
          
      indent : int, optional
          The indentation level for the JSON string. The default is 0.
          
      no_hash : bool, optional
          If True, the message is not hashed before signing. The default is False.
          This is useful for raw text messages that are not hashed such as the ones signed by
          wallets.
          
          
      Returns
      -------
      
      str: 
          The signature of the payload.
          
      """
      assert isinstance(payload, dict), "Data must be a dictionary" 
      str_data = self.safe_dict_to_json(payload, indent=indent)
      str_message = message_prefix + str_data
      signature = self.eth_sign_text(
        str_message, signature_only=True, no_hash=no_hash
      )
      if add_data:
        payload[BCctbase.ETH_SIGN] = signature
        payload[BCctbase.ETH_SENDER] = self.eth_address
      return signature
    

    def eth_verify_payload_signature(
      self, 
      payload: dict, 
      no_hash=False, 
      message_prefix: str = "",
      indent=0,
      raise_if_error=False
    ):
      """
      Verifies the signature of a payload by checking if the recovered address matches 
      the expected sender.
      
      Parameters
      ----------
      
      payload : dict
          The payload that was signed. Must contain the keys ETH_SENDER and ETH_SIGN.
          
      no_hash : bool, optional
          If True, the message is not hashed before verification. The default is False.
          This is useful for raw text messages that are not hashed such as the ones signed by
          wallets.
          
      message_prefix : str, optional
          A prefix to be added to the message before hashing (or signing). The default is "".
          
      
      indent : int, optional
          The indentation level for the JSON string. The default is 0.
                  
        
      """
      result = None
      _payload = deepcopy(payload)
      sender = _payload.pop(BCctbase.ETH_SENDER, None)
      signature = _payload.pop(BCctbase.ETH_SIGN, None)
      error_msg = ""
      if sender is None or signature is None:
        error_msg += "Payload must contain both ETH_SENDER and ETH_SIGN fields. "
      if not self.is_valid_eth_address(sender):
        error_msg += "Invalid Ethereum address in ETH_SENDER field. "
      
      if error_msg:
        if raise_if_error:
          raise Exception(error_msg)
        else:
          self.P(error_msg, color='r')
          result = None
      else:
        str_data = self.safe_dict_to_json(_payload, indent=indent)
        result = self.eth_verify_text_signature(
          text=str_data, signature=signature, message_prefix=message_prefix,
          no_hash=no_hash, raise_if_error=raise_if_error
        )
        if result is None:
          if raise_if_error:
            raise Exception("Signature verification failed.")
          else:
            self.P("Signature verification failed.", color='r')
          result = None
      # end if
      return result
      
      
    def eth_sign_node_epochs(
      self, 
      node, 
      epochs, 
      epochs_vals, 
      signature_only=True, 
      use_evm_node_addr=True
    ):
      """
      Signs the node availability

      Parameters
      ----------
      node : str
          The node address to sign. Either the node address or the Ethereum address based on `use_evm_node_addr`.
          
      epochs : list of int
          The epochs to sign.
          
      epochs_vals : list of int
          The values for each epoch.
          
      signature_only : bool, optional
          Whether to return only the signature. The default is True.
          
      use_evm_node_addr : bool, optional
          Whether to use the Ethereum address of the node. The default is True.

      Returns
      -------
      str
          The signature of the message.
      """
      if use_evm_node_addr:
        types = [ETHVarTypes.ETH_ADDR, ETHVarTypes.ETH_ARRAY_INT, ETHVarTypes.ETH_ARRAY_INT]  
      else:
        types = [ETHVarTypes.ETH_STR, ETHVarTypes.ETH_ARRAY_INT, ETHVarTypes.ETH_ARRAY_INT]
      values = [node, epochs, epochs_vals]
      result = self.eth_sign_message(types, values)
      if signature_only:
        return result["signature"]
      return result
    
        
      
    
    
  ### Web3 functions
  if True:     
    def web3_hash_message(self, types, values, as_hex=False):
      """
      Hashes a message using the keccak256 algorithm.

      Parameters
      ----------
      types : list
          The types of the values.
          
      values : list of any
          The values to hash.

      Returns
      -------
      bytes
          The hash of the message in hexadecimal format.
      """
      return self.eth_hash_message(types, values, as_hex=as_hex)
    
    def web3_sign_message(self, types, values):
      """
      Signs a message using the private key.

      Parameters
      ----------
      types : list
          The types of the values.
          
      values : list of any
          The values to sign.

      Returns
      -------
      str
          The signature of the message.
          
      Notes
      -----

      """
      return self.eth_sign_message(types, values)
    
    def web3_to_checksum_address(self, address: str) -> str:
      """
      Converts an Ethereum address to its checksum format.

      Parameters
      ----------
      address : str
          The Ethereum address to convert.

      Returns
      -------
      str
          The checksum address.
      """
      return to_checksum_address(address)
          
    def web3_is_node_licensed(self, address : str, network=None, debug=False) -> bool:
      """
      Check if the address is allowed to send commands to the node

      Parameters
      ----------
      address : str
        the address to check.
      """
      if EE_VPN_IMPL:
        self.P("VPN implementation. Skipping Ethereum check.", color='r')
        return False
      
      w3vars = self._get_web3_vars(network)
      
      assert self.is_valid_eth_address(address), "Invalid Ethereum address"
      
      if debug:
        self.P(f"Checking if {address} ({network}) is allowed...")
      
      contract = w3vars.w3.eth.contract(
        address=w3vars.controller_contract_address, 
        abi=EVM_ABI_DATA.IS_NODE_ACTIVE,
      )

      result = contract.functions.isNodeActive(address).call()
      return result


    def web3_get_oracles(self, network=None, debug=False) -> list:
      """
      Get the list of oracles from the contract

      Parameters
      ----------
      network : str, optional
        the network to use. The default is None.

      Returns
      -------
      list
        the list of oracles addresses.

      """
      w3vars = self._get_web3_vars(network)

      func = w3vars.get_oracles_abi[0]["name"]
      if debug:
        self.P(f"Getting oracles for {w3vars.network} via {w3vars.rpc_url} using `{func}`...")
      
      contract = w3vars.w3.eth.contract(
        address=w3vars.controller_contract_address, 
        abi=w3vars.get_oracles_abi,
      )

      get_oracles_func = getattr(contract.functions, func)
      result = get_oracles_func().call()
      return result    

    
    def web3_get_balance_eth(self, address=None, network=None):
      """
      Get the ETH balance of the address

      Parameters
      ----------
      address : str
          The address to check.

      Returns
      -------
      float
          The balance of the address.
      """
      if address is None:
        address = self.eth_address
      assert self.is_valid_eth_address(address), "Invalid Ethereum address"
      w3vars = self._get_web3_vars(network)
      balance_wei = w3vars.w3.eth.get_balance(address)
      balance_eth = w3vars.w3.from_wei(balance_wei, 'ether')
      return float(balance_eth)


    def web3_send_eth(
      self, 
      to_address, 
      amount_eth, 
      extra_buffer_eth=0.005, 
      network=None,
      wait_for_tx=True,
      timeout=120,
      return_receipt=False,
      raise_if_error=False,
    ):
      """
      Send ETH from the account associated with this object to another address,
      ensuring there is enough balance to cover the transfer amount, gas costs,
      and an additional buffer.

      Parameters
      ----------
      to_address : str
          The recipient Ethereum address.
          
      amount_eth : float
          The amount of ETH to send.
          
      extra_buffer_eth : float, optional
          An additional amount (in ETH) as a safety margin. Default is 0.005 ETH.
          
      network : str, optional
          The network to use. Default is None.
      
      wait_for_tx : bool, optional
          Whether to wait for the transaction to be mined. Default is True.
          
      timeout : int, optional 
          The maximum time to wait for the transaction to be mined, in seconds. Default is 120 seconds.
          
      return_receipt : bool, optional
          If True, returns the transaction receipt instead of the transaction hash. Default is False.
          
      raise_if_error : bool, optional
          If True, raises an exception if the transaction fails. Default is False.

      Returns
      -------
      str
          The transaction hash of the broadcasted transaction.
      """
      w3vars = self._get_web3_vars(network=network)
      network = w3vars.network
      
      # Get the sender's address from the object's stored attribute (assumed available)
      from_address = self.eth_address

      # Fetch the current balance (in Wei)
      balance_wei = w3vars.w3.eth.get_balance(from_address)
      
      # Define gas parameters for a standard ETH transfer.
      gas_limit = 21000  # typical gas limit for a simple ETH transfer
      gas_price = w3vars.w3.to_wei('50', 'gwei')  # example gas price; you may choose a dynamic approach
      
      # Calculate the total gas cost.
      gas_cost = gas_limit * gas_price
      
      # Convert transfer amount and buffer to Wei.
      amount_wei = w3vars.w3.to_wei(amount_eth, 'ether')
      extra_buffer = w3vars.w3.to_wei(extra_buffer_eth, 'ether')
      
      # Compute the total cost: amount to send + gas cost + extra buffer.
      total_cost = amount_wei + gas_cost + extra_buffer
      
      # Check if the balance is sufficient.
      if balance_wei < total_cost:
        msg = "Insufficient funds: your balance is less than the required amount plus gas cost and buffer."
        if raise_if_error:
          raise Exception(msg)
        else:
          self.P(msg, color='r')
          return None
      
      # Get the nonce for the transaction.
      nonce = w3vars.w3.eth.get_transaction_count(from_address)
      
      chain_id = w3vars.w3.eth.chain_id
          
      # Build the transaction dictionary.
      tx = {
        'nonce': nonce,
        'to': to_address,
        'value': amount_wei,
        'gas': gas_limit,
        'gasPrice': gas_price,
        'chainId': chain_id,
      }
      
      self.P(f"Executing transaction on {network} via {w3vars.rpc_url}:\n {json.dumps(tx, indent=2)}", verbosity=2)
          
      # Sign the transaction with the account's private key.
      signed_tx = w3vars.w3.eth.account.sign_transaction(tx, self.eth_account.key)
      
      # Broadcast the signed transaction.
      tx_hash = w3vars.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
      
      if wait_for_tx:
        # Wait for the transaction receipt with the specified timeout.
        self.P("Waiting for transaction to be mined...", verbosity=2)
        tx_receipt = w3vars.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        tx_hash_hex = tx_receipt.transactionHash.hex()
        self.P(f"Transaction mined: {tx_hash_hex}", color='g', verbosity=2)
        if return_receipt:          
          return tx_receipt
        else:
          return tx_hash_hex
      else:
        return tx_hash.hex()


    def web3_get_balance_r1(self, address=None, network=None):
      """
      Get the R1 balance of the address

      Parameters
      ----------
      address : str
          The address to check.

      Returns
      -------
      float
          The balance of the address.
      """
      if address is None:
        address = self.eth_address
      assert self.is_valid_eth_address(address), "Invalid Ethereum address"
      w3vars = self._get_web3_vars(network)

      token_contract = w3vars.w3.eth.contract(
        address=w3vars.r1_contract_address, abi=EVM_ABI_DATA.ERC20_ABI
      )

      try:
        decimals = token_contract.functions.decimals().call()
      except Exception:
        decimals = 18  # default to 18 if the decimals call fails

      raw_balance = token_contract.functions.balanceOf(address).call()
      human_balance = raw_balance / (10 ** decimals)
      return float(human_balance)


    def web3_send_r1(
      self,
      to_address: str,
      amount: float,
      extra_buffer_eth: float = 0.005,
      wait_for_tx: bool = False,
      timeout: int = 120,
      network: str = None,
      return_receipt=False,
      raise_if_error=False,
    ):
      """
      Send R1 tokens from the default account (self.eth_address) to the specified address.

      Parameters
      ----------
      to_address : str
          The recipient's Ethereum address.
          
      amount : float
          The amount of R1 tokens to send (in human-readable units).
          
      extra_buffer_eth : float, optional
          Additional ETH (in Ether) as a buffer for gas fees. Default is 0.005 ETH.
          
      wait_for_tx : bool, optional
          If True, waits for the transaction to be mined and returns the receipt.
          If False, returns immediately with the transaction hash.
          
      timeout : int, optional
          Maximum number of seconds to wait for the transaction receipt. Default is 120.
          
      network : str, optional
          The network to use. If None, uses the default self.evm_network.

      return_receipt: bool, optional
          If True, returns the transaction receipt instead of the transaction hash.
          
      raise_if_error : bool, optional
          If True, raises an exception if the transaction fails. Default is False.  
          
      Returns
      -------
          If wait_for_tx is False, returns the transaction hash as a string.
          If wait_for_tx is True, returns the transaction receipt as a dict.
      """
      # Validate the recipient address.
      assert self.is_valid_eth_address(to_address), "Invalid Ethereum address"
      
      # Retrieve the Web3 instance, RPC URL, and the R1 contract address.
      # Note: This follows the same pattern as web3_get_balance_r1.
      w3vars = self._get_web3_vars(network)
      network = w3vars.network
      
      # Create the token contract instance.
      token_contract = w3vars.w3.eth.contract(
        address=w3vars.r1_contract_address, abi=EVM_ABI_DATA.ERC20_ABI
      )
      
      # Get the token's decimals (default to 18 if not available).
      try:
        decimals = token_contract.functions.decimals().call()
      except Exception:
        decimals = 18

      # Convert the human-readable amount to the token's smallest unit.
      token_amount = int(amount * (10 ** decimals))
      
      # Ensure the sender has enough R1 token balance.
      sender_balance = token_contract.functions.balanceOf(self.eth_address).call()
      if sender_balance < token_amount:
        msg = "Insufficient funds: your $R1 balance is less than the required amount."
        if raise_if_error:
          raise Exception(msg)
        else:
          self.P(msg, color='r')
          return None
      
      # Estimate gas fees for the token transfer.
      gas_price = w3vars.w3.to_wei('50', 'gwei')  # Adjust as needed or use a dynamic gas strategy.
      estimated_gas = token_contract.functions.transfer(
        to_address, token_amount
      ).estimate_gas(
        {'from': self.eth_address}
      )
      gas_cost = estimated_gas * gas_price
      
      # Check that the sender's ETH balance can cover gas costs plus an extra buffer.
      eth_balance = w3vars.w3.eth.get_balance(self.eth_address)
      extra_buffer = w3vars.w3.to_wei(extra_buffer_eth, 'ether')
      if eth_balance < gas_cost + extra_buffer:
        raise Exception("Insufficient ETH balance to cover gas fees and extra buffer.")
      
      # Get the transaction count for the nonce.
      nonce = w3vars.w3.eth.get_transaction_count(self.eth_address)
      
      # Programmatically determine the chainId.
      chain_id = w3vars.w3.eth.chain_id

      # Build the transaction for the ERC20 transfer.
      tx = token_contract.functions.transfer(to_address, token_amount).build_transaction({
        'from': self.eth_address,
        'nonce': nonce,
        'gas': estimated_gas,
        'gasPrice': gas_price,
        'chainId': chain_id,
      })
      
      self.P(f"Executing transaction on {network} via {w3vars.rpc_url}:\n {json.dumps(dict(tx), indent=2)}", verbosity=2)
      
      # Sign the transaction using the internal account (via _get_eth_account).
      eth_account = self._get_eth_account()
      signed_tx = w3vars.w3.eth.account.sign_transaction(tx, eth_account.key)
      
      # Broadcast the transaction.
      tx_hash = w3vars.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
      
      if wait_for_tx:
        # Wait for the transaction receipt if required.
        tx_receipt = w3vars.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        tx_hash_hex = tx_receipt.transactionHash.hex()
        self.P(f"Transaction mined: {tx_hash_hex}", color='g', verbosity=2)
        if return_receipt:          
          return tx_receipt
        else:
          return tx_hash_hex
      else:
        return tx_hash.hex()


    def web3_get_node_info(
      self,
      node_address: str,
      network: str = None,
      raise_if_issue: bool = False,
    ):      
      """
      Retrieve license details for the specified node using getNodeLicenseDetails().

      Parameters
      ----------
      node_address : str
          The node address (must be a valid Ethereum address).
          
      network : str, optional
          The network to use. If None, defaults to self.evm_network.
          
      raise_if_issue : bool, optional
          If True, raises an exception based on custom criteria (e.g., if node is banned).
          Default is False.


      Returns
      -------
      dict
          A dictionary containing all license details returned by getNodeLicenseDetails.
      """
      # Validate the node address.
      assert self.is_valid_eth_address(node_address), "Invalid Ethereum address"

      # Retrieve the necessary Web3 variables (pattern consistent with web3_send_r1).
      w3vars = self._get_web3_vars(network)
      network = w3vars.network

      # Create the contract instance for retrieving node info.
      # Assuming you have a specific contract address in w3vars (e.g. license_contract_address),
      # or you may adapt this code if your contract address is stored differently.
      contract = w3vars.w3.eth.contract(
        address=w3vars.proxy_contract_address,  # or the relevant address from your environment
        abi=EVM_ABI_DATA.GET_NODE_INFO
      )

      self.P(f"`getNodeLicenseDetails` on {network} via {w3vars.rpc_url}", verbosity=2)

      # Call the contract function to get details.
      result_tuple = contract.functions.getNodeLicenseDetails(node_address).call()

      # Unpack the tuple into a dictionary for readability.
      details = {
        "network": network,
        "licenseType": result_tuple[0],
        "licenseId": result_tuple[1],
        "owner": result_tuple[2],
        "nodeAddress": result_tuple[3],
        "totalAssignedAmount": result_tuple[4],
        "totalClaimedAmount": result_tuple[5],
        "lastClaimEpoch": result_tuple[6],
        "assignTimestamp": result_tuple[7],
        "lastClaimOracle": result_tuple[8],
        "isBanned": result_tuple[9],
        "isValid": True, # default to True; set to False if any issues are detected
      }

      
      no_owner = details["owner"] == "0x0000000000000000000000000000000000000000"
      no_real_addr = details["nodeAddress"] == "0x0000000000000000000000000000000000000000"
      is_banned = details["isBanned"]
      
      is_valid = not (
        no_owner or no_real_addr or is_banned
      )
      
      details['isValid'] = is_valid

      self.P(f"Node Info:\n{json.dumps(details, indent=2)}", verbosity=2)

      if not is_valid:
        if raise_if_issue:
          msg = f"Node {node_address} is not valid."
          raise Exception(msg)
        else:
          pass
      #end if
      return details
    
    
    def web3_get_wallet_nodes(self, address: str, network:str = None):
      """
      Retrieve all nodes associated with a given wallet address.

      Parameters
      ----------
      wallet_addr : str
          The Ethereum wallet address to check.
          
      network : str, optional
          The network to use. If None, defaults to self.evm_network.

      Returns
      -------
      list of dict
          A list of dictionaries containing node details.
      """
      assert self.is_valid_eth_address(address), "Invalid Ethereum address"

      # Retrieve the necessary Web3 variables (pattern consistent with web3_send_r1).
      w3vars = self._get_web3_vars(network)
      network = w3vars.network

      # Create the contract instance for retrieving node info.
      # Assuming you have a specific contract address in w3vars (e.g. license_contract_address),
      # or you may adapt this code if your contract address is stored differently.
      contract = w3vars.w3.eth.contract(
        address=w3vars.proxy_contract_address,  # or the relevant address from your environment
        abi=EVM_ABI_DATA.GET_WALLET_NODES,
      )
      
      self.P(f"`getWalletNodes` on {network} via {w3vars.rpc_url}", verbosity=2)
      # Call the contract function to get details.
      result = contract.functions.getWalletNodes(address).call()
      # Unpack the tuple into a dictionary for readability.
      
      return result
    
    def web3_get_addresses_balances(
      self, 
      addresses: list, 
      network: str = None,
    ):
      """
      Retrieve the ETH and R1 balances of multiple addresses in a single call.

      Parameters
      ----------
      addresses : list of str
          The list of Ethereum addresses to check.
          
      network : str, optional
          The network to use. If None, defaults to self.evm_network.

      Returns
      -------
      dict
          A dictionary mapping each address to its balances.
      """
      assert isinstance(addresses, list), "Addresses must be a list"
      assert all(self.is_valid_eth_address(addr) for addr in addresses), "All addresses must be valid Ethereum addresses"

      # Retrieve the necessary Web3 variables (pattern consistent with web3_send_r1).
      w3vars = self._get_web3_vars(network)
      network = w3vars.network

      # Create the contract instance for the proxy contract.
      contract = w3vars.w3.eth.contract(
        address=w3vars.proxy_contract_address,
        abi=EVM_ABI_DATA.GET_ADDRESSES_BALANCES
      )

      self.P(f"`getAddressesBalances` on {network} via {w3vars.rpc_url}", verbosity=2)
      result = contract.functions.getAddressesBalances(addresses).call()
      
      balances = {}
      for item in result:
        addr = item[0]
        eth_balance = item[1] / (10 ** 18)
        r1_balance = item[2] / (10 ** 18)
        balances[addr] = {
          "ethBalance": float(eth_balance),
          "r1Balance": float(r1_balance),
        }

      return balances

    def web3_get_job_details(
      self,
      job_id: int,
      network: str = None
    ):      
      """
      Retrieve license details for the specified node using getNodeLicenseDetails().

      Parameters
      ----------
      job_id : int
          The job ID to retrieve details for.

      network : str, optional
          The network to use. If None, defaults to self.evm_network.


      Returns
      -------
      dict
          A dictionary containing all job details returned by getJobDetails.
      """
      # Validate the job ID.
      assert isinstance(job_id, int), "Invalid job ID"

      # Retrieve the necessary Web3 variables (pattern consistent with web3_send_r1).
      w3vars = self._get_web3_vars(network)
      network = w3vars.network
      contract = w3vars.w3.eth.contract(
        address=w3vars.poai_manager_address,
        abi=EVM_ABI_DATA.POAI_MANAGER_ABI
      )

      self.P(f"`getJobDetails` on {network} via {w3vars.rpc_url}", verbosity=2)

      # Call the contract function to get details.
      result_tuple = contract.functions.getJobDetails(job_id).call()
      details = self._format_job_details(result_tuple, network)
      self.P(f"Job Details:\n{json.dumps(details, indent=2)}", verbosity=2)
      return details

    def web3_get_all_active_jobs(
      self,
      network: str = None
    ):
      """
      Retrieve all active jobs tracked by the PoAI manager.

      Parameters
      ----------
      network : str, optional
          The network to use. Defaults to the current engine network.

      Returns
      -------
      list[dict]
          A list with the job details for every active job.
      """
      w3vars = self._get_web3_vars(network)
      network = w3vars.network
      contract = w3vars.w3.eth.contract(
        address=w3vars.poai_manager_address,
        abi=EVM_ABI_DATA.POAI_MANAGER_ABI
      )

      self.P(f"`getAllActiveJobs` on {network} via {w3vars.rpc_url}", verbosity=2)
      raw_jobs = contract.functions.getAllActiveJobs().call()
      jobs = [self._format_job_details(job, network) for job in raw_jobs]
      self.P(f"Active jobs found: {len(jobs)}", verbosity=2)
      return jobs

    def web3_submit_node_update(
      self,
      job_id: int,
      nodes: list,
      wait_for_tx: bool = False,
      timeout: int = 120,
      network: str = None,
      return_receipt=False,
    ):
      """
      Submit nodes update for a given job.

      Parameters
      ----------
      job_id : int
          The job ID to update.
          
      nodes : list
          The list of new nodes running the job.
          
      network : str, optional
          The network to use. If None, uses the default self.evm_network.

      Returns
      -------
          The transaction hash.
      """
      # Validate the input parameters.
      assert isinstance(job_id, int), "Invalid job ID"
      assert isinstance(nodes, list), "Nodes must be a list"
      
      # Retrieve the Web3 instance, RPC URL, and the R1 contract address.
      # Note: This follows the same pattern as web3_get_balance_r1.
      w3vars = self._get_web3_vars(network)
      network = w3vars.network
      
      # Create the token contract instance.
      poai_manager_contract = w3vars.w3.eth.contract(
        address=w3vars.poai_manager_address, abi=EVM_ABI_DATA.POAI_MANAGER_ABI
      )
      
      # Estimate gas fees for the token transfer.
      gas_price = w3vars.w3.eth.gas_price  # This fetches the current suggested gas price from the network.
      estimated_gas = 1_000_000 # Have enough gas to cover all the actions if consensus is reached
      gas_cost = estimated_gas * gas_price
      
      # Check that the sender's ETH balance can cover gas costs plus an extra buffer.
      eth_balance = w3vars.w3.eth.get_balance(self.eth_address)
      if eth_balance < gas_cost:
        raise Exception("Insufficient ETH balance to cover gas fees.")
      
      # Get the transaction count for the nonce.
      nonce = w3vars.w3.eth.get_transaction_count(self.eth_address)
      
      # Programmatically determine the chainId.
      chain_id = w3vars.w3.eth.chain_id

      # Build the transaction for the ERC20 transfer.
      tx = poai_manager_contract.functions.submitNodeUpdate(job_id, nodes).build_transaction({
        'from': self.eth_address,
        'nonce': nonce,
        'gas': estimated_gas,
        'gasPrice': gas_price,
        'chainId': chain_id,
      })
      
      self.P(f"Executing transaction on {network} via {w3vars.rpc_url}:\n {json.dumps(dict(tx), indent=2)}", verbosity=2)
      
      # Sign the transaction using the internal account (via _get_eth_account).
      eth_account = self._get_eth_account()
      signed_tx = w3vars.w3.eth.account.sign_transaction(tx, eth_account.key)
      
      # Broadcast the transaction.
      tx_hash = w3vars.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
      
      if wait_for_tx:
        # Wait for the transaction receipt if required.
        tx_receipt = w3vars.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        tx_hash_hex = tx_receipt.transactionHash.hex()
        self.P(f"Transaction mined: {tx_hash_hex}", color='g', verbosity=2)
        if return_receipt:          
          return tx_receipt
        else:
          return tx_hash_hex
      else:
        return tx_hash.hex()

    def web3_allocate_rewards_across_all_escrows(
      self,
      network: str = None,
      wait_for_tx=True,
      timeout=120,
      return_receipt=False,
    ):
      """
      Allocate rewards across all escrows.

      Parameters
      ----------
      network : str, optional
          The network to use. If None, uses the default self.evm_network.

      Returns
      -------
          The transaction hash.
      """
      # Retrieve the Web3 instance, RPC URL, and the R1 contract address.
      # Note: This follows the same pattern as web3_get_balance_r1.
      w3vars = self._get_web3_vars(network)
      network = w3vars.network
      
      # Create the token contract instance.
      poai_manager_contract = w3vars.w3.eth.contract(
        address=w3vars.poai_manager_address, abi=EVM_ABI_DATA.POAI_MANAGER_ABI
      )
      
      # Estimate gas fees for the token transfer.
      gas_price = w3vars.w3.eth.gas_price  # This fetches the current suggested gas price from the network.
      estimated_gas = poai_manager_contract.functions.allocateRewardsAcrossAllEscrows().estimate_gas(
        {'from': self.eth_address}
      )
      gas_cost = estimated_gas * gas_price
      
      # Check that the sender's ETH balance can cover gas costs plus an extra buffer.
      eth_balance = w3vars.w3.eth.get_balance(self.eth_address)
      if eth_balance < gas_cost:
        raise Exception("Insufficient ETH balance to cover gas fees.")
      
      # Get the transaction count for the nonce.
      nonce = w3vars.w3.eth.get_transaction_count(self.eth_address)
      
      # Programmatically determine the chainId.
      chain_id = w3vars.w3.eth.chain_id

      # Build the transaction for the ERC20 transfer.
      tx = poai_manager_contract.functions.allocateRewardsAcrossAllEscrows().build_transaction({
        'from': self.eth_address,
        'nonce': nonce,
        'gas': estimated_gas,
        'gasPrice': gas_price,
        'chainId': chain_id,
      })
      
      self.P(f"Executing transaction on {network} via {w3vars.rpc_url}:\n {json.dumps(dict(tx), indent=2)}", verbosity=2)
      
      # Sign the transaction using the internal account (via _get_eth_account).
      eth_account = self._get_eth_account()
      signed_tx = w3vars.w3.eth.account.sign_transaction(tx, eth_account.key)
      
      # Broadcast the transaction.
      tx_hash = w3vars.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
      
      if wait_for_tx:
        # Wait for the transaction receipt if required.
        tx_receipt = w3vars.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        tx_hash_hex = tx_receipt.transactionHash.hex()
        self.P(f"Transaction mined: {tx_hash_hex}", color='g', verbosity=2)
        if return_receipt:          
          return tx_receipt
        else:
          return tx_hash_hex
      else:
        return tx_hash.hex()

    def web3_get_unvalidated_job_ids(
      self,
      oracle_address: str,
      network: str = None
    ):
      """
      Retrieve all the jobs that are pending validation and
      have not been validated by the given oracle.

      Parameters
      ----------
      oracle_address : str
          The oracle address to check for.
          
      network : str, optional
          The network to use. If None, defaults to self.evm_network.

      Returns
      -------
      list
          A list of unvalidated job IDs.
      """
      # Retrieve the necessary Web3 variables (pattern consistent with web3_get_job_details).
      w3vars = self._get_web3_vars(network)
      network = w3vars.network
      
      contract = w3vars.w3.eth.contract(
        address=w3vars.poai_manager_address,
        abi=EVM_ABI_DATA.POAI_MANAGER_ABI
      )

      self.P(f"`getUnvalidatedJobIds` on {network} via {w3vars.rpc_url}", verbosity=2)

      # Call the contract function to get unvalidated job IDs.
      result = contract.functions.getUnvalidatedJobIds(oracle_address).call()
      
      self.P(f"Unvalidated Job IDs: {result}", verbosity=2)

      return result

    def web3_get_first_closable_job_id(
      self,
      network: str = None
    ):
      """
      Retrieve the ID of the first job that can be closed using getFirstClosableJobId().

      Parameters
      ----------
      network : str, optional
          The network to use. If None, defaults to self.evm_network.

      Returns
      -------
      int or None
          The ID of the first closable job, or None if no such job exists.
      """
      w3vars = self._get_web3_vars(network)
      network = w3vars.network

      contract = w3vars.w3.eth.contract(
        address=w3vars.poai_manager_address,
        abi=EVM_ABI_DATA.POAI_MANAGER_ABI
      )

      self.P(f"`getFirstClosableJobId` on {network} via {w3vars.rpc_url}", verbosity=2)

      # Call the contract function to get the first closable job ID.
      result = contract.functions.getFirstClosableJobId().call()
      if result == 0:
        result = None
      self.P(f"First closable job ID: {result}", verbosity=2)

      return result

    def web3_get_is_last_epoch_allocated(
      self,
      network: str = None
    ):
      """
      Check if the last epoch has been allocated using getIsLastEpochAllocated().

      Parameters
      ----------
      network : str, optional
          The network to use. If None, defaults to self.evm_network.

      Returns
      -------
      bool
          True if the last epoch has been allocated, False otherwise.
      """
      # Retrieve the necessary Web3 variables (pattern consistent with web3_get_unvalidated_job_ids).
      w3vars = self._get_web3_vars(network)
      network = w3vars.network
      
      contract = w3vars.w3.eth.contract(
        address=w3vars.poai_manager_address,
        abi=EVM_ABI_DATA.POAI_MANAGER_ABI
      )

      self.P(f"`getIsLastEpochAllocated` on {network} via {w3vars.rpc_url}", verbosity=2)

      # Call the contract function to check if last epoch is allocated.
      result = contract.functions.getIsLastEpochAllocated().call()
      
      self.P(f"Last epoch allocated: {result}", verbosity=2)

      return result
    
    def _format_job_details(self, raw_job_details, network: str):
      """
      Normalize the job details tuple returned by the PoAI Manager contract.
      """
      return {
        "network": network,
        "jobId": raw_job_details[0],
        "projectHash": "0x" + raw_job_details[1].hex(),
        "requestTimestamp": raw_job_details[2],
        "startTimestamp": raw_job_details[3],
        "lastNodesChangeTimestamp": raw_job_details[4],
        "jobType": raw_job_details[5],
        "pricePerEpoch": raw_job_details[6],
        "lastExecutionEpoch": raw_job_details[7],
        "numberOfNodesRequested": raw_job_details[8],
        "balance": raw_job_details[9],
        "lastAllocatedEpoch": raw_job_details[10],
        "activeNodes": raw_job_details[11],
        "escrowAddress": raw_job_details[12],
        "escrowOwner": raw_job_details[13],
      }

  def get_deeploy_url(self):
    """
    Returns the deeploy URL from the environment or the network data

    Returns
    -------
    str
      the deeploy URL.

    """
    current_network = self.current_evm_network
    deeploy_api_base_url = EVM_NET_DATA[current_network][EvmNetData.EE_DEEPLOY_API_URL_KEY]
    return deeploy_api_base_url
