"""
What happens if we gift a random token to the strat?
"""
import brownie
from brownie import accounts, interface, MockToken
from helpers.constants import AddressZero


def test_report_an_extra_token(strategy, badgerTree, strategist, treasury, vault, keeper):
  """
  Proves that the strat using `_processExtraToken` will handle perf fee as well as send to tree
  """
  ## Badger Treasury
  donator = accounts.at("0xD0A7A8B98957b9CD3cFB9c0425AbE44551158e9e", force=True)

  ## Badger
  extra_token = interface.IERC20("0x3472A5A71965499acd81997a54BBA8D852C6E53d") 

  ## Initial balances
  initial_tree_balance = extra_token.balanceOf(badgerTree)
  initial_treasury_balance = extra_token.balanceOf(treasury)
  initial_strategist_balance = extra_token.balanceOf(strategist)
  prev_earned = vault.additionalTokensEarned(extra_token)

  ## Send the gift and report it
  amount = 1e18
  extra_token.transfer(strategy, amount, {"from": donator})
  strategy.test_harvest_only_emit(extra_token, amount, {"from": keeper})

  ## There was a net positive balance increase
  assert extra_token.balanceOf(badgerTree) > initial_tree_balance
  assert extra_token.balanceOf(treasury) > initial_treasury_balance
  assert extra_token.balanceOf(strategist) > initial_strategist_balance

  ## More rigorously
  perf_fee_gov = vault.performanceFeeGovernance()
  perf_fee_strat = vault.performanceFeeStrategist()
  max = vault.MAX_BPS()

  fee_gov = amount * perf_fee_gov / max
  fee_strat = amount * perf_fee_strat / max

  to_tree = amount - fee_gov - fee_strat

  assert extra_token.balanceOf(badgerTree) == initial_tree_balance + to_tree
  assert extra_token.balanceOf(treasury) == initial_treasury_balance + fee_gov
  assert extra_token.balanceOf(strategist) == initial_strategist_balance + fee_strat

  ## Verify that onChain APY tracking works
  assert vault.additionalTokensEarned(extra_token) == prev_earned + amount

def test_emit_additional_token_from_vault(strategist, governance, vault, deployer, badgerTree):
    """
    Emit an extra token that was unplanned to tree (and take per fees)
    """
    mint_amount = 10e18
    extra_token = MockToken.deploy({"from": deployer})
    extra_token.initialize(
        [vault], [mint_amount],
        {"from": deployer}
    )

    gov_fee = vault.performanceFeeGovernance()
    strat_fee = vault.performanceFeeStrategist()
    max = vault.MAX_BPS()

    prev_gov_bal = extra_token.balanceOf(governance)
    prev_strat_bal = extra_token.balanceOf(strategist)
    prev_badger_tree_bal = extra_token.balanceOf(badgerTree)

    prev_earned = vault.additionalTokensEarned(extra_token)

    vault.emitNonProtectedToken(extra_token, {"from": strategist})

    gov_tokens = mint_amount * gov_fee / max
    strat_tokens = mint_amount * strat_fee / max
    tree_tokens = mint_amount - gov_tokens - strat_tokens

    assert extra_token.balanceOf(governance) - prev_gov_bal  == gov_tokens
    assert extra_token.balanceOf(strategist) - prev_strat_bal == strat_tokens
    assert extra_token.balanceOf(badgerTree) - prev_badger_tree_bal == tree_tokens

    ## Verify that onChain APY tracking works
    assert vault.additionalTokensEarned(extra_token) == prev_earned + mint_amount

    with brownie.reverts("Address 0"):
        vault.emitNonProtectedToken(AddressZero, {"from": strategist})



## Withdraw operation / Sweeps
def test_withdraw_another_token_from_strat(strategy, strategist, governance, vault, deployer):
    mint_amount = 10e18
    extra_token = MockToken.deploy({"from": deployer})
    extra_token.initialize(
        [strategy], [mint_amount]
    )

    prev_gov_bal = extra_token.balanceOf(governance)

    vault.sweepExtraToken(extra_token, {"from": strategist})

    after_gov_bal = extra_token.balanceOf(governance)

    assert after_gov_bal - prev_gov_bal == mint_amount

    with brownie.reverts("Address 0"):
        vault.sweepExtraToken(AddressZero, {"from": strategist})


def test_withdraw_another_token_from_vault(strategist, governance, vault, deployer):
    mint_amount = 10e18
    extra_token = MockToken.deploy({"from": deployer})
    extra_token.initialize(
        [vault], [mint_amount]
    )

    prev_gov_bal = extra_token.balanceOf(governance)

    vault.sweepExtraToken(extra_token, {"from": strategist})

    after_gov_bal = extra_token.balanceOf(governance)

    assert after_gov_bal - prev_gov_bal == mint_amount

## Security Checks
def test_security_try_rugging_want(deployer, governance, vault, strategy, want):
  ## Try to rug want via withdrawOther
  mint_amount = 1e18
  want.mint(strategy, mint_amount)

  ## Can't sweep want
  with brownie.reverts():
    vault.sweepExtraToken(want, {"from": governance})


def test_security_try_rugging_protected_token(deployer, governance, vault, strategy, want):
  """
  Badger is protected token for testing
  Do a donation to strat, then try rugging
  """

  ## Badger Treasury
  donator = accounts.at("0x4441776e6a5d61fa024a5117bfc26b953ad1f425", force=True)

  ## Badger
  badger = interface.IERC20("0x3472A5A71965499acd81997a54BBA8D852C6E53d") 

  assert strategy.getProtectedTokens()[1] == badger

  ## Send the gift and report it
  amount = 1e18
  badger.transfer(strategy, amount, {"from": donator})

  ## Can't sweep a protected token
  with brownie.reverts():
    vault.sweepExtraToken(badger, {"from": governance})