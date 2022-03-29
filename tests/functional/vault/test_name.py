import brownie
from brownie import Vault

from helpers.constants import AddressZero

performanceFeeGovernance = 1000
performanceFeeStrategist = 1000
withdrawalFee = 50
managementFee = 50

def test_with_default_name(deployer, governance, keeper, guardian, strategist, badgerTree, token):
  vault = Vault.deploy({"from": deployer})
  vault.initialize(
        token,
        governance,
        keeper,
        guardian,
        governance,
        strategist,
        badgerTree,
        "",
        "",
        [
            performanceFeeGovernance,
            performanceFeeStrategist,
            withdrawalFee,
            managementFee,
        ],
  )

  assert vault.name() == "Badger Sett " + token.name()
  assert vault.symbol() == "b" + token.symbol()

def test_with_custom_name(deployer, governance, keeper, guardian, strategist, badgerTree, token):
  vault = Vault.deploy({"from": deployer})
  vault.initialize(
      token,
      governance,
      keeper,
      guardian,
      governance,
      strategist,
      badgerTree,
      "Custom Name",
      "CST",
      [
          performanceFeeGovernance,
          performanceFeeStrategist,
          withdrawalFee,
          managementFee,
      ],
  )

  assert vault.name() == "Custom Name"
  assert vault.symbol() == "CST"


def test_with_custom_name_default_symbol(deployer, governance, keeper, guardian, strategist, badgerTree, token):
  vault = Vault.deploy({"from": deployer})
  vault.initialize(
        token,
        governance,
        keeper,
        guardian,
        governance,
        strategist,
        badgerTree,
        "Custom Name",
        "",
        [
            performanceFeeGovernance,
            performanceFeeStrategist,
            withdrawalFee,
            managementFee,
        ],
  )

  assert vault.name() == "Custom Name"
  assert vault.symbol() == "b" + token.symbol()


def test_version(deployer, governance, keeper, guardian, strategist, badgerTree, token):
  vault = Vault.deploy({"from": deployer})
  vault.initialize(
        token,
        governance,
        keeper,
        guardian,
        governance,
        strategist,
        badgerTree,
        "",
        "",
        [
            performanceFeeGovernance,
            performanceFeeStrategist,
            withdrawalFee,
            managementFee,
        ],
  )

  assert vault.version() == "1.5-BadgerRewards"