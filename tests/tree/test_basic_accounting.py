from random import random
from brownie import *
import brownie
import pytest

def test_basic_flow(tree, want_for_vault_with_tree, vault_with_tree, random_user, deployer):
  """
    Deposit, verify it updates
    Transfer, verify it updates
    Withdraw, verify it updates
  """
  assert vault_with_tree.totalSupply() == 0
  current_epoch = tree.currentEpoch()
  deposit_amount = 123123

  assert tree.shares(current_epoch, vault_with_tree, random_user) == 0 ## We never deposited this epoch
  assert tree.getBalanceAtEpoch(current_epoch, vault_with_tree, random_user)[0] == 0 ## We never deposited this epoch

  ## Do a deposit
  vault_with_tree.deposit(deposit_amount, {"from": random_user}) ## NOTE: This works because first deposit
  ## If the vault earns the accounting will be broken

  assert tree.shares(current_epoch, vault_with_tree, random_user) == deposit_amount
  assert tree.getBalanceAtEpoch(current_epoch, vault_with_tree, random_user)[0] == deposit_amount
  assert tree.getTotalSupplyAtEpoch(current_epoch, vault_with_tree)[0] == deposit_amount
  assert tree.getTotalSupplyAtEpoch(current_epoch, vault_with_tree)[0] == vault_with_tree.totalSupply()

  ## Show that share issuance is correct for deposits even if ppfs is different from one

  ## Do a donation
  want_for_vault_with_tree.transfer(vault_with_tree, 42e18, {"from": random_user})

  ## Get diff shares
  initial_shares = vault_with_tree.balanceOf(random_user)
  vault_with_tree.deposit(deposit_amount, {"from": random_user})
  shares_issued = vault_with_tree.balanceOf(random_user) - initial_shares

  new_expected_total_supply = deposit_amount + shares_issued


  ## First deposit with 1 ppfs + shares_issued (second deposit)
  assert tree.getBalanceAtEpoch(current_epoch, vault_with_tree, random_user)[0] == new_expected_total_supply
  assert tree.getTotalSupplyAtEpoch(current_epoch, vault_with_tree)[0] == new_expected_total_supply
  
  ## Do a transfer
  vault_with_tree.transfer(deployer, vault_with_tree.balanceOf(random_user), {"from": random_user})

  ## Total supply is same
  assert tree.getTotalSupplyAtEpoch(current_epoch, vault_with_tree)[0] == new_expected_total_supply

  ## Balance of random is 0
  assert tree.getBalanceAtEpoch(current_epoch, vault_with_tree, random_user)[0] == 0

  ## Balance of deployer is all
  assert tree.getBalanceAtEpoch(current_epoch, vault_with_tree, deployer)[0] == new_expected_total_supply


  ## Then do a withdrawal
  vault_with_tree.withdrawAll({"from": deployer})

  ## Balance is 0
  assert tree.getBalanceAtEpoch(current_epoch, vault_with_tree, deployer)[0] == 0


  ## Because we have fees, the only shares left are for treasury
  ## NOTE: Should pass even if you set to 0
  treasury = vault_with_tree.treasury()
  balance_of_fees = vault_with_tree.balanceOf(treasury)

  ## Tree is tracking balance of treasury
  tree.getBalanceAtEpoch(current_epoch, vault_with_tree, treasury)[0] == balance_of_fees
  tree.getTotalSupplyAtEpoch(current_epoch, vault_with_tree)[0] == balance_of_fees

  assert vault_with_tree.totalSupply() == balance_of_fees