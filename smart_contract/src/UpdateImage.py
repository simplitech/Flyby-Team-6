from typing import Any

from boa3.builtin import CreateNewEvent, public
from boa3.builtin.interop.contract import destroy_contract, update_contract
from boa3.builtin.interop.runtime import calling_script_hash, check_witness
from boa3.builtin.interop.storage import get, put
from boa3.builtin.type import UInt160

# -------------------------------------------
# EVENTS
# -------------------------------------------

on_change_image = CreateNewEvent([('sender', UInt160)],
                                 'ChangeImage')

# -------------------------------------------
# STORAGE KEYS
# -------------------------------------------

OWNER_KEY = b'OWNER'


# -------------------------------------------
# CONTRACT LOGIC
# -------------------------------------------

@public
def call_me() -> UInt160:
    invoker = calling_script_hash
    on_change_image(invoker)
    return invoker


# -------------------------------------------
# CONTRACT MANAGEMENT
# -------------------------------------------


@public
def _deploy(data: Any, update: bool):
    if update:
        # do nothing on update
        return

    if get(OWNER_KEY).to_int() > 0:
        # it was deployed already
        return

    put(OWNER_KEY, calling_script_hash)


@public
def update(script: bytes, manifest: bytes):
    owner = UInt160(get(OWNER_KEY))
    if not check_witness(owner):
        raise Exception('No authorization.')

    update_contract(script, manifest)


@public
def destroy():
    owner = UInt160(get(OWNER_KEY))
    if not check_witness(owner):
        raise Exception('No authorization.')

    destroy_contract()
