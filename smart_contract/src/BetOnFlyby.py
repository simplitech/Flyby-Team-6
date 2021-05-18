from typing import Any, List, cast

from boa3.builtin import CreateNewEvent, public
from boa3.builtin.contract import abort
from boa3.builtin.interop.binary import deserialize, serialize
from boa3.builtin.interop.blockchain import Transaction
from boa3.builtin.interop.contract import GAS, call_contract, destroy_contract, update_contract
from boa3.builtin.interop.runtime import calling_script_hash, check_witness, executing_script_hash, script_container
from boa3.builtin.interop.storage import find, get, put
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
BET_OWNER_KEY = b'bet_owner_'
BET_TOTAL_STAKE_KEY = b'bet_total_stake_'
BET_OPTIONS_KEY = b'bet_options_'
BET_DESCRIPTION_KEY = b'bet_description_'
BET_RESULT_KEY = b'bet_result_'
BET_VOTE_KEY = b'bet_vote_'

# -------------------------------------------
# CONTRACT LOGIC
# -------------------------------------------

PRICE_IN_GAS = 1 * 10 ** 8  # bet cost is 1 GAS


@public
def get_bet(bet_id: UInt256) -> list:
    creator = get(BET_OWNER_KEY + bet_id)

    if len(creator) == 0:
        raise Exception("Bet doesn't exist.")

    description = get(BET_DESCRIPTION_KEY + bet_id).to_str()
    options: List[str] = deserialize(get(BET_OPTIONS_KEY + bet_id))

    result = None
    serialized_result = get(BET_RESULT_KEY + bet_id)
    if len(serialized_result) > 0:
        result = deserialize(serialized_result)

    return [bet_id,
            creator,
            description,
            options,
            result
            ]


@public
def create_bet(creator: UInt160, description: str, options: List[str]) -> UInt256:
    if not check_witness(creator):
        raise Exception('No authorization.')

    options: List[str] = remove_duplicates(options)
    if len(options) < 2:
        raise Exception('Not enough options to create a bet')

    for option in options:
        if len(option) == 0:
            raise Exception('Cannot have an empty option')

    tx: Transaction = script_container
    bet_id = tx.hash

    put(BET_OWNER_KEY + bet_id, creator)
    put(BET_TOTAL_STAKE_KEY + bet_id, 0)
    put(BET_OPTIONS_KEY + bet_id, serialize(options))
    put(BET_DESCRIPTION_KEY + bet_id, description)

    request_image_change()

    return bet_id


def remove_duplicates(list_with_dups: list) -> list:
    new_list = []
    for value in list_with_dups:
        if value not in new_list:
            new_list.append(value)

    return new_list


@public
def finish_bet(bet_id: UInt256, winner_options: List[str]):
    creator = get(BET_OWNER_KEY + bet_id)

    if len(creator) == 0:
        raise Exception("Bet doesn't exist.")
    if not check_witness(creator):
        raise Exception('No authorization.')
    if len(get(BET_RESULT_KEY + bet_id)) > 0:
        raise Exception("Bet is finished already")
    if len(winner_options) == 0:
        raise Exception('At least one winner is required')

    # validate all winner options are valid options
    winner_options: List[str] = remove_duplicates(winner_options)
    bet_options: List[str] = deserialize(get(BET_OPTIONS_KEY + bet_id))
    for option in winner_options:
        if option not in bet_options:
            raise Exception('Invalid option for this bet')

    winners: List[UInt160] = []

    # get winner players
    votes_key_prefix = BET_VOTE_KEY + bet_id
    vote = find(votes_key_prefix)
    if vote.next():
        result_pair = vote.value
        storage_key = cast(bytes, result_pair[0])
        account_vote = cast(str, result_pair[1])

        if account_vote in winner_options:
            # slice is not implemented for bytes on neo3-boa v0.8.1
            address = storage_key[len(votes_key_prefix):]
            account = UInt160(address)
            winners.append(account)

    # distribute the prizes
    if len(winners) > 0:
        total_stake = get(BET_TOTAL_STAKE_KEY + bet_id).to_int()
        prize_per_winner = total_stake // len(winners)
        executing_contract = executing_script_hash

        for winner in winners:
            transfer_gas(executing_contract, winner, prize_per_winner)

    # set result
    put(BET_RESULT_KEY + bet_id, serialize(winner_options))


@public
def cancel_bet(bet_id: UInt256):
    creator_on_storage = get(BET_OWNER_KEY + bet_id)

    if len(creator_on_storage) == 0:
        raise Exception("Bet doesn't exist.")

    creator = UInt160(creator_on_storage)
    if not check_witness(creator):
        raise Exception('No authorization.')
    if len(get(BET_RESULT_KEY + bet_id)) > 0:
        raise Exception("Bet is finished already")

    # 5% fee of total stake for cancelling the bet
    total_stake = get(BET_TOTAL_STAKE_KEY + bet_id).to_int()
    executing_contract = executing_script_hash
    transfer_gas(creator, executing_contract, total_stake * 5 // 100)

    # refund players
    votes_key_prefix = BET_VOTE_KEY + bet_id
    vote = find(votes_key_prefix)
    if vote.next():
        result_pair: List[bytes] = vote.value
        storage_key = result_pair[0]

        account = UInt160(storage_key[len(votes_key_prefix):])
        transfer_gas(executing_contract, account, PRICE_IN_GAS)

    # set result
    put(BET_RESULT_KEY + bet_id, serialize('Cancelled by owner'))


@public
def bet(player: UInt160, bet_id: UInt256, bet_option: str):
    if len(get(BET_OWNER_KEY + bet_id)) == 0:
        raise Exception("Bet doesn't exist.")
    if not check_witness(player):
        raise Exception('No authorization.')
    if len(get(BET_RESULT_KEY + bet_id)) > 0:
        raise Exception("Bet is finished already")

    player_vote_key = BET_VOTE_KEY + bet_id + player
    if len(get(player_vote_key)) > 0:
        raise Exception('Only one bet is allowed per account')

    valid_options: List[str] = deserialize(get(BET_OPTIONS_KEY + bet_id))
    if bet_option not in valid_options:
        raise Exception('Invalid option for this bet')

    total_stake = get(BET_TOTAL_STAKE_KEY + bet_id).to_int()
    total_stake += PRICE_IN_GAS

    transfer_gas(player, executing_script_hash, PRICE_IN_GAS)
    put(player_vote_key, bet_option)
    put(BET_TOTAL_STAKE_KEY + bet_id, total_stake)

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
