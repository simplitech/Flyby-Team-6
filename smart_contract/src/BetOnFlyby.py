from typing import Any, List, cast

from boa3.builtin import CreateNewEvent, public
from boa3.builtin.contract import abort
from boa3.builtin.interop.binary import deserialize, serialize
from boa3.builtin.interop.blockchain import Transaction
from boa3.builtin.interop.contract import GAS, call_contract, destroy_contract, update_contract
from boa3.builtin.interop.runtime import calling_script_hash, check_witness, executing_script_hash, script_container
from boa3.builtin.interop.storage import delete, find, get, put
from boa3.builtin.type import UInt160, UInt256

# -------------------------------------------
# EVENTS
# -------------------------------------------

on_change_image = CreateNewEvent([('sender', UInt160)],
                                 'ChangeImage')

# -------------------------------------------
# STORAGE KEYS
# -------------------------------------------

OWNER_KEY = b'OWNER'
POOL_OWNER_KEY = b'pool_owner_'
POOL_TOTAL_STAKE_KEY = b'pool_total_stake_'
POOL_OPTIONS_KEY = b'pool_options_'
POOL_DESCRIPTION_KEY = b'pool_description_'
POOL_RESULT_KEY = b'pool_result_'
POOL_BET_KEY = b'pool_bet_'

# -------------------------------------------
# CONTRACT LOGIC
# -------------------------------------------

PRICE_IN_GAS = 1 * 10 ** 8  # bet cost is 1 GAS


@public
def get_pool(pool_id: UInt256) -> list:
    creator = get(POOL_OWNER_KEY + pool_id)

    if len(creator) == 0:
        raise Exception("Pool doesn't exist.")

    description = get(POOL_DESCRIPTION_KEY + pool_id).to_str()
    options: List[str] = deserialize(get(POOL_OPTIONS_KEY + pool_id))

    result = None
    serialized_result = get(POOL_RESULT_KEY + pool_id)
    if len(serialized_result) > 0:
        result = deserialize(serialized_result)

    return [pool_id,
            creator,
            description,
            options,
            result
            ]


@public
def create_pool(creator: UInt160, description: str, options: List[str]) -> UInt256:
    if not check_witness(creator):
        raise Exception('No authorization.')

    options: List[str] = remove_duplicates(options)
    if len(options) < 2:
        raise Exception('Not enough options to create a pool')

    for option in options:
        if len(option) == 0:
            raise Exception('Cannot have an empty option')

    tx: Transaction = script_container
    pool_id = tx.hash

    put(POOL_OWNER_KEY + pool_id, creator)
    put(POOL_TOTAL_STAKE_KEY + pool_id, 0)
    put(POOL_OPTIONS_KEY + pool_id, serialize(options))
    put(POOL_DESCRIPTION_KEY + pool_id, description)

    request_image_change()

    return pool_id


def remove_duplicates(list_with_dups: list) -> list:
    new_list = []
    for value in list_with_dups:
        if value not in new_list:
            new_list.append(value)

    return new_list


@public
def finish_pool(pool_id: UInt256, winner_options: List[str]):
    creator = get(POOL_OWNER_KEY + pool_id)

    if len(creator) == 0:
        raise Exception("Pool doesn't exist.")
    if not check_witness(creator):
        raise Exception('No authorization.')
    if len(get(POOL_RESULT_KEY + pool_id)) > 0:
        raise Exception('Pool is finished already')
    if len(winner_options) == 0:
        raise Exception('At least one winner is required')

    # validate all winner options are valid options
    winner_options: List[str] = remove_duplicates(winner_options)
    pool_options: List[str] = deserialize(get(POOL_OPTIONS_KEY + pool_id))
    for option in winner_options:
        if option not in pool_options:
            raise Exception('Invalid option for this pool')

    winners: List[UInt160] = []

    # get winner players
    bets_key_prefix = POOL_BET_KEY + pool_id
    bet = find(bets_key_prefix)
    if bet.next():
        result_pair = bet.value
        storage_key = cast(bytes, result_pair[0])
        account_bet = cast(str, result_pair[1])

        if account_bet in winner_options:
            address = storage_key[len(bets_key_prefix):]
            account = UInt160(address)
            winners.append(account)

    # distribute the prizes
    if len(winners) > 0:
        total_stake = get(POOL_TOTAL_STAKE_KEY + pool_id).to_int()
        prize_per_winner = total_stake // len(winners)
        executing_contract = executing_script_hash

        for winner in winners:
            transfer_gas(executing_contract, winner, prize_per_winner)

    # set result
    put(POOL_RESULT_KEY + pool_id, serialize(winner_options))


@public
def cancel_pool(pool_id: UInt256):
    creator_on_storage = get(POOL_OWNER_KEY + pool_id)

    if len(creator_on_storage) == 0:
        raise Exception("Pool doesn't exist.")

    creator = UInt160(creator_on_storage)
    if not check_witness(creator):
        raise Exception('No authorization.')
    if len(get(POOL_RESULT_KEY + pool_id)) > 0:
        raise Exception('Pool is finished already')

    executing_contract = executing_script_hash

    # refund players
    bets_key_prefix = POOL_BET_KEY + pool_id
    bet = find(bets_key_prefix)
    if bet.next():
        result_pair: List[bytes] = bet.value
        storage_key = result_pair[0]

        account = UInt160(storage_key[len(bets_key_prefix):])
        transfer_gas(executing_contract, account, PRICE_IN_GAS)

    # set result
    put(POOL_RESULT_KEY + pool_id, serialize('Cancelled by owner'))


@public
def cancel_player_bet(player: UInt160, bet_id: UInt256):
    if len(get(POOL_OWNER_KEY + bet_id)) == 0:
        raise Exception("Pool doesn't exist.")
    if not check_witness(player):
        raise Exception('No authorization.')
    if len(get(POOL_RESULT_KEY + bet_id)) > 0:
        raise Exception('Pool is finished already')
    if len(get(POOL_BET_KEY + bet_id + player)) == 0:
        raise Exception("Player didn't bet on this pool")

    # 5% fee of the bet for cancelling
    refund_value = PRICE_IN_GAS - PRICE_IN_GAS * 5 // 100
    transfer_gas(executing_script_hash, player, refund_value)

    delete(POOL_BET_KEY + bet_id + player)


@public
def bet(player: UInt160, bet_id: UInt256, bet_option: str):
    if len(get(POOL_OWNER_KEY + bet_id)) == 0:
        raise Exception("Pool doesn't exist.")
    if not check_witness(player):
        raise Exception('No authorization.')
    if len(get(POOL_RESULT_KEY + bet_id)) > 0:
        raise Exception('Pool is finished already')

    player_vote_key = POOL_BET_KEY + bet_id + player
    if len(get(player_vote_key)) > 0:
        raise Exception('Only one bet is allowed per account')

    valid_options: List[str] = deserialize(get(POOL_OPTIONS_KEY + bet_id))
    if bet_option not in valid_options:
        raise Exception('Invalid option for this pool')

    total_stake = get(POOL_TOTAL_STAKE_KEY + bet_id).to_int()
    total_stake += PRICE_IN_GAS

    transfer_gas(player, executing_script_hash, PRICE_IN_GAS)
    put(player_vote_key, bet_option)
    put(POOL_TOTAL_STAKE_KEY + bet_id, total_stake)

    request_image_change()


@public
def request_image_change():
    invoker = calling_script_hash
    on_change_image(invoker)


def transfer_gas(from_account: UInt160, to_account: UInt160, amount: int):
    success: bool = call_contract(GAS, 'transfer', [from_account, to_account, amount, None])
    if not success:
        raise Exception('GAS transfer was not successful')


@public
def onNEP17Payment(from_address: UInt160, amount: int, data: Any):
    # accept GAS only
    if calling_script_hash != GAS:
        abort()


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

    put(OWNER_KEY, "NMmy263woLS5thu238tj2WSzcYQNrP4ZqV".to_script_hash())


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
