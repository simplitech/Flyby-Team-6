import os.path
import unittest
from typing import List

from boa3.boa3 import Boa3
from boa3.neo.smart_contract.VoidType import VoidType
from boa3.neo3.vm import VMState
from boa3_test.tests.test_classes.testengine import TestEngine


class TestExample(unittest.TestCase):
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

    def _create_bet(self, creator_account: bytes, description: str, options: List[str]):
        self.engine.add_signer_account(creator_account)
        return self.engine.run(self.nef_path, 'create_bet', creator_account, description, options)

    def test_create_bet_success(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        result = self._create_bet(creator_account, description, options)
        self.assertEqual(VMState.HALT, self.engine.vm_state)
        self.assertIsInstance(result, bytes)
        self.assertEqual(32, len(result))

    def test_create_bet_fail_check_witness(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = []

        # need signing
        self.engine.run(self.nef_path, 'create_bet', creator_account, description, options)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('No authorization.'))

    def test_create_bet_fail_not_enough_options(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = []

        self.engine.add_signer_account(creator_account)
        # need at least two different options
        self.engine.run(self.nef_path, 'create_bet', creator_account, description, options)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('Not enough options to create a bet'))

        options = ['choice1', 'choice1']  # need at least two different options
        self.engine.add_signer_account(creator_account)
        self.engine.run(self.nef_path, 'create_bet', creator_account, description, options)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('Not enough options to create a bet'))

    def test_create_bet_fail_empty_option(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', '', 'choice2']

        self.engine.add_signer_account(creator_account)

        self.engine.run(self.nef_path, 'create_bet', creator_account, description, options)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('Cannot have an empty option'))

    def _bet(self, bet_id: bytes, player: bytes, option: str):
        price_in_gas = 1 * 10 ** 8  # 1 GAS
        self.engine.add_gas(player, price_in_gas)
        self.engine.add_signer_account(player)
        self.engine.run(self.nef_path, 'bet', player, bet_id, option)

    def test_bet_success(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        player = bytes(range(20))
        bet_option = 'choice1'
        price_in_gas = 1 * 10 ** 8  # 1 GAS

        self.engine.add_signer_account(player)
        self.engine.add_gas(player, price_in_gas)
        result = self.engine.run(self.nef_path, 'bet', player, bet_id, bet_option)
        self.assertEqual(VMState.HALT, self.engine.vm_state)
        self.assertEqual(VoidType, result)

    def test_bet_fail_doesnt_exist(self):
        self.engine.reset_engine()

        bet_id = bytes(32)
        player = bytes(20)
        bet_option = 'choice1'

        self.engine.run(self.nef_path, 'bet', player, bet_id, bet_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith("Bet doesn't exist."))

    def test_bet_fail_check_witness(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        player = bytes(range(20))
        bet_option = 'choice1'

        self.engine.run(self.nef_path, 'bet', player, bet_id, bet_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('No authorization.'))

    def test_bet_fail_finished_already(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        bet_option = 'choice1'
        self._finish_bet(creator_account, bet_id, [bet_option])
        player = bytes(range(20))

        self._bet(bet_id, player, bet_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('Bet is finished already'))

    def test_bet_fail_voted_already(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        player = bytes(range(20))
        bet_option = 'choice1'

        self._bet(bet_id, player, bet_option)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        self._bet(bet_id, player, 'choice2')
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('Only one bet is allowed per account'))

    def test_bet_fail_invalid_option(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        player = bytes(range(20))
        bet_option = 'choice4'

        self._bet(bet_id, player, bet_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('Invalid option for this bet'))

    def test_bet_fail_not_enough_gas(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        player = bytes(range(20))
        bet_option = 'choice1'

        self.engine.add_signer_account(player)
        self.engine.run(self.nef_path, 'bet', player, bet_id, bet_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('GAS transfer was not successful'))

    def _finish_bet(self, creator_account: bytes, bet_id: bytes, winners: List[str]):
        self.engine.add_signer_account(creator_account)
        self.engine.run(self.nef_path, 'finish_bet', bet_id, winners)

    def test_finish_bet_success_one_winner(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        player = bytes(range(20))
        bet_option = 'choice2'
        self._bet(bet_id, player, bet_option)

        winner_option = [bet_option]
        self.engine.add_signer_account(creator_account)
        self.engine.run(self.nef_path, 'finish_bet', bet_id, winner_option)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

    def test_finish_bet_success_two_winners(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        player = bytes(range(20))
        bet_option = 'choice2'
        self._bet(bet_id, player, bet_option)

        winner_option = ['choice1', bet_option]
        self.engine.add_signer_account(creator_account)
        self.engine.run(self.nef_path, 'finish_bet', bet_id, winner_option)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

    def test_finish_bet_fail_doesnt_exist(self):
        self.engine.reset_engine()

        bet_id = bytes(32)
        winner_option = []

        self.engine.run(self.nef_path, 'finish_bet', bet_id, winner_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith("Bet doesn't exist."))

    def test_finish_bet_fail_check_witness(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        winner_option = ['choice1']

        self.engine.run(self.nef_path, 'finish_bet', bet_id, winner_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('No authorization.'))

    def test_finish_bet_fail_finished_already(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        winner_option = ['choice1']
        self._finish_bet(creator_account, bet_id, winner_option)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        self._finish_bet(creator_account, bet_id, winner_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('Bet is finished already'))

    def test_finish_bet_fail_not_enough_winner_options(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        winner_option = []

        self.engine.add_signer_account(creator_account)
        self.engine.run(self.nef_path, 'finish_bet', bet_id, winner_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('At least one winner is required'))

    def test_finish_bet_fail_invalid_winner_option(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        winner_option = ['choice4']

        self.engine.add_signer_account(creator_account)
        self.engine.run(self.nef_path, 'finish_bet', bet_id, winner_option)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('Invalid option for this bet'))

    def _cancel_bet(self, creator_account: bytes, bet_id: bytes):
        self.engine.add_signer_account(creator_account)
        self.engine.run(self.nef_path, 'cancel_bet', bet_id)

    def test_cancel_bet_success(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)

        self.engine.add_signer_account(creator_account)
        self.engine.run(self.nef_path, 'cancel_bet', bet_id)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

    def test_cancel_bet_fail_doesnt_exist(self):
        self.engine.reset_engine()

        bet_id = bytes(32)

        self.engine.run(self.nef_path, 'cancel_bet', bet_id)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith("Bet doesn't exist."))

    def test_cancel_bet_fail_check_witness(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)

        self.engine.run(self.nef_path, 'cancel_bet', bet_id)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('No authorization.'))

    def test_cancel_bet_fail_finished_already(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        winner_option = ['choice1']
        self._finish_bet(creator_account, bet_id, winner_option)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        self.engine.add_signer_account(creator_account)
        self.engine.run(self.nef_path, 'cancel_bet', bet_id)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('Bet is finished already'))

    def test_cancel_player_bet_success(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        player = bytes(range(20))
        bet_option = 'choice1'
        self._bet(bet_id, player, bet_option)

        self.engine.add_signer_account(player)
        self.engine.run(self.nef_path, 'cancel_player_bet', player, bet_id)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

    def test_cancel_player_bet_fail_doesnt_exist(self):
        self.engine.reset_engine()

        bet_id = bytes(32)
        player = bytes(20)

        self.engine.run(self.nef_path, 'cancel_player_bet', player, bet_id)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith("Bet doesn't exist."))

    def test_cancel_player_bet_fail_check_witness(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        player = bytes(range(20))

        self.engine.run(self.nef_path, 'cancel_player_bet', player, bet_id)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('No authorization.'))

    def test_cancel_player_bet_fail_player_didnt_bet(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        player = bytes(range(20))

        self.engine.run(self.nef_path, 'cancel_player_bet', player, bet_id)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith('No authorization.'))

    def test_cancel_player_bet_fail_finished_already(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        player = bytes(range(20))

        self.engine.add_signer_account(player)
        self.engine.run(self.nef_path, 'cancel_player_bet', player, bet_id)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith("Player didn't bet on this pool"))

    def test_get_bet_success_on_going(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        result = self.engine.run(self.nef_path, 'get_bet', bet_id)
        self.assertEqual(VMState.HALT, self.engine.vm_state)
        self.assertIsInstance(result, list)
        self.assertEqual(5, len(result))

        if isinstance(result[1], str):      # test engine converts to string whenever is possible
            result[1] = result[1].encode('utf-8')

        self.assertEqual(bet_id, result[0])             # bet_id
        self.assertEqual(creator_account, result[1])    # creator
        self.assertEqual(description, result[2])        # description
        self.assertEqual(options, result[3])            # options
        self.assertIsNone(result[4])                    # result - is None because it's on going

    def test_get_bet_success_finished(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        winners = ['choice1']
        self._finish_bet(creator_account, bet_id, winners)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        result = self.engine.run(self.nef_path, 'get_bet', bet_id)
        self.assertEqual(VMState.HALT, self.engine.vm_state)
        self.assertIsInstance(result, list)
        self.assertEqual(5, len(result))

        if isinstance(result[1], str):      # test engine converts to string whenever is possible
            result[1] = result[1].encode('utf-8')

        self.assertEqual(bet_id, result[0])             # bet_id
        self.assertEqual(creator_account, result[1])    # creator
        self.assertEqual(description, result[2])        # description
        self.assertEqual(options, result[3])            # options
        self.assertEqual(winners, result[4])            # result

    def test_get_bet_success_cancelled(self):
        self.engine.reset_engine()

        creator_account = bytes(20)
        description = 'Bet for testing'
        options = ['choice1', 'choice2', 'choice3']

        bet_id = self._create_bet(creator_account, description, options)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        self._cancel_bet(creator_account, bet_id)
        self.assertEqual(VMState.HALT, self.engine.vm_state)

        result = self.engine.run(self.nef_path, 'get_bet', bet_id)
        self.assertEqual(VMState.HALT, self.engine.vm_state)
        self.assertIsInstance(result, list)
        self.assertEqual(5, len(result))

        if isinstance(result[1], str):      # test engine converts to string whenever is possible
            result[1] = result[1].encode('utf-8')

        self.assertEqual(bet_id, result[0])                 # bet_id
        self.assertEqual(creator_account, result[1])        # creator
        self.assertEqual(description, result[2])            # description
        self.assertEqual(options, result[3])                # options
        self.assertEqual('Cancelled by owner', result[4])   # result

    def test_get_bet_fail_doesnt_exist(self):
        self.engine.reset_engine()
        bet_id = bytes(32)

        self.engine.run(self.nef_path, 'get_bet', bet_id)
        self.assertEqual(VMState.FAULT, self.engine.vm_state)
        self.assertTrue(self.engine.error.endswith("Bet doesn't exist."))

