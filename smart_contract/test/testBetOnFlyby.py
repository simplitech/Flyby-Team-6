import os.path
import unittest
from typing import List

from boa3.boa3 import Boa3
from boa3.neo.smart_contract.VoidType import VoidType
from boa3.neo3.vm import VMState
from boa3_test.tests.test_classes.testengine import TestEngine


class TestSmartContract(unittest.TestCase):
    engine: TestEngine

    @classmethod
    def setUpClass(cls):
        folders = os.path.abspath(__file__).split(os.sep)
        cls.dirname = '/'.join(folders[:-2])

        test_engine_installation_folder = cls.dirname   # Change this to your test engine installation folder
        cls.engine = TestEngine(test_engine_installation_folder)

        path = f'{cls.dirname}/src/BetOnFlyby.py'
        cls.nef_path = path.replace('.py', '.nef')

        if not os.path.isfile(cls.nef_path):
            Boa3.compile_and_save(path, output_path=cls.nef_path)

    def test_request_image_change(self):
        self.engine.reset_engine()
        on_change_image_event_name = 'ChangeImage'

        result = self.engine.run(self.nef_path, 'request_image_change')
        self.assertEqual(VMState.HALT, self.engine.vm_state)
        self.assertEqual(VoidType, result)

        event_notifications = self.engine.get_events(event_name=on_change_image_event_name)
        self.assertEqual(1, len(event_notifications))

    def _create_pool(self, creator_account: bytes, description: str, options: List[str]):
        self.engine.add_signer_account(creator_account)
        return self.engine.run(self.nef_path, 'create_pool', creator_account, description, options)

    def test_create_pool_success(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        result = self._create_pool(creator_account, description, options)
        self.assertEqual(VMState.HALT, self.engine.vm_state)
        self.assertIsInstance(result, bytes)
        self.assertEqual(32, len(result))

    def test_create_pool_fail_check_witness(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = []

        # need signing
        self.engine.run(self.nef_path, 'create_pool', creator_account, description, options)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('No authorization.'))

    def test_create_pool_fail_not_enough_options(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = []

        self.engine.add_signer_account(creator_account)
        # need at least two different options
        self.engine.run(self.nef_path, 'create_pool', creator_account, description, options)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('Not enough options to create a pool'))

        options = ['choice1', 'choice1']  # need at least two different options
        self.engine.add_signer_account(creator_account)
        self.engine.run(self.nef_path, 'create_pool', creator_account, description, options)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('Not enough options to create a pool'))

    def test_create_pool_fail_empty_option(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', '', 'choice2']

        self.engine.add_signer_account(creator_account)

        self.engine.run(self.nef_path, 'create_pool', creator_account, description, options)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('Cannot have an empty option'))

    def _bet(self, pool_id: bytes, player: bytes, option: str):
        price_in_gas = 1 * 10 ** 8  # 1 GAS
        self.engine.add_gas(player, price_in_gas)
        self.engine.add_signer_account(player)
        self.engine.run(self.nef_path, 'bet', player, pool_id, option)

    def test_bet_success(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        player = bytes(range(20))
        bet_option = 'choice1'
        price_in_gas = 1 * 10 ** 8  # 1 GAS

        self.engine.add_signer_account(player)
        self.engine.add_gas(player, price_in_gas)
        result = self.engine.run(self.nef_path, 'bet', player, pool_id, bet_option)
        self.assertEqual(VMState.HALT, self.engine.vm_state)
        self.assertEqual(VoidType, result)

    def test_bet_fail_doesnt_exist(self):
        self.engine.reset_engine()

        pool_id = bytes(32)
        player = bytes(20)
        bet_option = 'choice1'

        self.engine.run(self.nef_path, 'bet', player, pool_id, bet_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith("Pool doesn't exist."))

    def test_bet_fail_check_witness(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        player = bytes(range(20))
        bet_option = 'choice1'

        self.engine.run(self.nef_path, 'bet', player, pool_id, bet_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('No authorization.'))

    def test_bet_fail_finished_already(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        bet_option = 'choice1'
        self._finish_pool(creator_account, pool_id, [bet_option])
        player = bytes(range(20))

        self._bet(pool_id, player, bet_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('Pool is finished already'))

    def test_bet_fail_voted_already(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        player = bytes(range(20))
        bet_option = 'choice1'

        self._bet(pool_id, player, bet_option)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        self._bet(pool_id, player, 'choice2')
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('Only one bet is allowed per account'))

    def test_bet_fail_invalid_option(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        player = bytes(range(20))
        bet_option = 'choice4'

        self._bet(pool_id, player, bet_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('Invalid option for this pool'))

    def test_bet_fail_not_enough_gas(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        player = bytes(range(20))
        bet_option = 'choice1'

        self.engine.add_signer_account(player)
        self.engine.run(self.nef_path, 'bet', player, pool_id, bet_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('GAS transfer was not successful'))

    def _finish_pool(self, creator_account: bytes, pool_id: bytes, winners: List[str]):
        self.engine.add_signer_account(creator_account)
        self.engine.run(self.nef_path, 'finish_pool', pool_id, winners)

    def test_finish_pool_success_one_winner(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        player = bytes(range(20))
        bet_option = 'choice2'
        self._bet(pool_id, player, bet_option)

        winner_option = [bet_option]
        self.engine.add_signer_account(creator_account)
        self.engine.run(self.nef_path, 'finish_pool', pool_id, winner_option)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

    def test_finish_pool_success_two_winners(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        player = bytes(range(20))
        bet_option = 'choice2'
        self._bet(pool_id, player, bet_option)

        winner_option = ['choice1', bet_option]
        self.engine.add_signer_account(creator_account)
        self.engine.run(self.nef_path, 'finish_pool', pool_id, winner_option)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

    def test_finish_pool_fail_doesnt_exist(self):
        self.engine.reset_engine()

        pool_id = bytes(32)
        winner_option = []

        self.engine.run(self.nef_path, 'finish_pool', pool_id, winner_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith("Pool doesn't exist."))

    def test_finish_pool_fail_check_witness(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        winner_option = ['choice1']

        self.engine.run(self.nef_path, 'finish_pool', pool_id, winner_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('No authorization.'))

    def test_finish_pool_fail_finished_already(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        winner_option = ['choice1']
        self._finish_pool(creator_account, pool_id, winner_option)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        self._finish_pool(creator_account, pool_id, winner_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('Pool is finished already'))

    def test_finish_pool_fail_not_enough_winner_options(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        winner_option = []

        self.engine.add_signer_account(creator_account)
        self.engine.run(self.nef_path, 'finish_pool', pool_id, winner_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('At least one winner is required'))

    def test_finish_pool_fail_invalid_winner_option(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        winner_option = ['choice4']

        self.engine.add_signer_account(creator_account)
        self.engine.run(self.nef_path, 'finish_pool', pool_id, winner_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('Invalid option for this pool'))

    def _cancel_pool(self, creator_account: bytes, pool_id: bytes):
        self.engine.add_signer_account(creator_account)
        self.engine.run(self.nef_path, 'cancel_pool', pool_id)

    def test_cancel_pool_success(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)

        self.engine.add_signer_account(creator_account)
        self.engine.run(self.nef_path, 'cancel_pool', pool_id)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

    def test_cancel_pool_fail_doesnt_exist(self):
        self.engine.reset_engine()

        pool_id = bytes(32)

        self.engine.run(self.nef_path, 'cancel_pool', pool_id)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith("Pool doesn't exist."))

    def test_cancel_pool_fail_check_witness(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)

        self.engine.run(self.nef_path, 'cancel_pool', pool_id)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('No authorization.'))

    def test_cancel_pool_fail_finished_already(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        winner_option = ['choice1']
        self._finish_pool(creator_account, pool_id, winner_option)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        self.engine.add_signer_account(creator_account)
        self.engine.run(self.nef_path, 'cancel_pool', pool_id)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('Pool is finished already'))

    def test_cancel_player_bet_success(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        player = bytes(range(20))
        bet_option = 'choice1'
        self._bet(pool_id, player, bet_option)

        self.engine.add_signer_account(player)
        self.engine.run(self.nef_path, 'cancel_player_bet', player, pool_id)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

    def test_cancel_player_bet_fail_doesnt_exist(self):
        self.engine.reset_engine()

        pool_id = bytes(32)
        player = bytes(20)

        self.engine.run(self.nef_path, 'cancel_player_bet', player, pool_id)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith("Pool doesn't exist."))

    def test_cancel_player_bet_fail_check_witness(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        player = bytes(range(20))

        self.engine.run(self.nef_path, 'cancel_player_bet', player, pool_id)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('No authorization.'))

    def test_cancel_player_bet_fail_player_didnt_bet(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        player = bytes(range(20))

        self.engine.run(self.nef_path, 'cancel_player_bet', player, pool_id)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('No authorization.'))

    def test_cancel_player_bet_fail_finished_already(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        player = bytes(range(20))

        self.engine.add_signer_account(player)
        self.engine.run(self.nef_path, 'cancel_player_bet', player, pool_id)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith("Player didn't bet on this pool"))

    def test_get_pool_success_on_going(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        result = self.engine.run(self.nef_path, 'get_pool', pool_id)
        self.assertEqual(VMState.HALT, self.engine.vm_state)
        self.assertIsInstance(result, list)
        self.assertEqual(6, len(result))

        if isinstance(result[1], str):      # test engine converts to string whenever is possible
            result[1] = result[1].encode('utf-8')

        self.assertEqual(pool_id, result[0])            # pool_id
        self.assertEqual(creator_account, result[1])    # creator
        self.assertEqual(description, result[2])        # description
        self.assertEqual(options, result[3])            # options
        self.assertIsNone(result[4])                    # result - is None because it's on going
        self.assertEqual({}, result[5])                 # bets on this pool

    def test_get_pool_success_has_bets(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        player = bytes(range(20))
        bet_option = 'choice1'

        self._bet(pool_id, player, bet_option)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        result = self.engine.run(self.nef_path, 'get_pool', pool_id)
        self.assertEqual(VMState.HALT, self.engine.vm_state)
        self.assertIsInstance(result, list)
        self.assertEqual(6, len(result))

        if isinstance(result[1], str):      # test engine converts to string whenever is possible
            result[1] = result[1].encode('utf-8')

        self.assertEqual(pool_id, result[0])            # pool_id
        self.assertEqual(creator_account, result[1])    # creator
        self.assertEqual(description, result[2])        # description
        self.assertEqual(options, result[3])            # options
        self.assertIsNone(result[4])                    # result - is None because it's on going
        self.assertIsInstance(result[5], dict)          # bets on this pool
        self.assertEqual(1, len(result[5]))

        bet1_player, bet1_choice = list(result[5].items())[0]
        if isinstance(bet1_player, str):      # test engine converts to string whenever is possible
            bet1_player = bet1_player.encode('utf-8')
        self.assertEqual(player, bet1_player)
        self.assertEqual(bet_option, bet1_choice)

    def test_get_pool_success_finished(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        winners = ['choice1']
        self._finish_pool(creator_account, pool_id, winners)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        result = self.engine.run(self.nef_path, 'get_pool', pool_id)
        self.assertEqual(VMState.HALT, self.engine.vm_state)
        self.assertIsInstance(result, list)
        self.assertEqual(6, len(result))

        if isinstance(result[1], str):      # test engine converts to string whenever is possible
            result[1] = result[1].encode('utf-8')

        self.assertEqual(pool_id, result[0])            # pool_id
        self.assertEqual(creator_account, result[1])    # creator
        self.assertEqual(description, result[2])        # description
        self.assertEqual(options, result[3])            # options
        self.assertEqual(winners, result[4])            # result
        self.assertEqual({}, result[5])                 # bets on this pool

    def test_get_pool_success_cancelled(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        self._cancel_pool(creator_account, pool_id)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        result = self.engine.run(self.nef_path, 'get_pool', pool_id)
        self.assertEqual(VMState.HALT, self.engine.vm_state)
        self.assertIsInstance(result, list)
        self.assertEqual(6, len(result))

        if isinstance(result[1], str):      # test engine converts to string whenever is possible
            result[1] = result[1].encode('utf-8')

        self.assertEqual(pool_id, result[0])                # pool_id
        self.assertEqual(creator_account, result[1])        # creator
        self.assertEqual(description, result[2])            # description
        self.assertEqual(options, result[3])                # options
        self.assertEqual('Cancelled by owner', result[4])   # result
        self.assertEqual({}, result[5])                     # bets on this pool

    def test_get_pool_fail_doesnt_exist(self):
        self.engine.reset_engine()
        pool_id = bytes(32)

        self.engine.run(self.nef_path, 'get_pool', pool_id)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith("Pool doesn't exist."))

    def test_list_open_pools_success_no_pools_created(self):
        self.engine.reset_engine()

        result = self.engine.run(self.nef_path, 'list_on_going_pools')
        self.assertEqual(VMState.HALT, self.engine.vm_state)
        self.assertIsInstance(result, list)
        self.assertEqual(0, len(result))

    def test_list_open_pools_success_found_pool(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        result = self.engine.run(self.nef_path, 'list_on_going_pools')
        self.assertEqual(VMState.HALT, self.engine.vm_state)
        self.assertIsInstance(result, list)
        self.assertEqual(1, len(result))
        pool = result[0]
        self.assertIsInstance(pool, list)
        self.assertEqual(6, len(pool))

        if isinstance(pool[1], str):      # test engine converts to string whenever is possible
            pool[1] = pool[1].encode('utf-8')

        self.assertEqual(pool_id, pool[0])            # pool_id
        self.assertEqual(creator_account, pool[1])    # creator
        self.assertEqual(description, pool[2])        # description
        self.assertEqual(options, pool[3])            # options
        self.assertIsNone(pool[4])                    # result - is None because it's on going

    def test_list_open_pools_success_finished_pool(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        self._finish_pool(creator_account, pool_id, ['choice1'])
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        result = self.engine.run(self.nef_path, 'list_on_going_pools')
        self.assertEqual(VMState.HALT, self.engine.vm_state)
        self.assertIsInstance(result, list)
        self.assertEqual(0, len(result))

    def test_list_open_pools_success_canceled_pool(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        pool_id = self._create_pool(creator_account, description, options)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        self._cancel_pool(creator_account, pool_id)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        result = self.engine.run(self.nef_path, 'list_on_going_pools')
        self.assertEqual(VMState.HALT, self.engine.vm_state)
        self.assertIsInstance(result, list)
        self.assertEqual(0, len(result))
