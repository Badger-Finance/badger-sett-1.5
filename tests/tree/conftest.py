import time

from brownie import (
    DemoStrategy,
    Vault,
    MockToken,
    AdminUpgradeabilityProxy,
    TestVipCappedGuestListBbtcUpgradeable,
    accounts,
    TestBadgerRewards
)
from helpers.constants import MaxUint256
from helpers.constants import AddressZero
from rich.console import Console

console = Console()

from dotmap import DotMap
import pytest

"""
  TODO: Deploy stuff for Tree
  Setup vault with some shares

  Do some basic operations and see if it works

  Then go into accrual etc...
"""

@pytest.fixture
def tree(deployer):
  c = TestBadgerRewards.deploy({"from": deployer})
  c.startNextEpoch()

  return c

@pytest.fixture
def deploy_with_tree(tree):

    """
    Deploys, vault and test strategy, mock token and wires them up.
    """
    deployer = accounts[1]

    strategist = accounts[2]
    keeper = accounts[3]
    guardian = accounts[4]

    governance = accounts[5]
    proxyAdmin = accounts[6]

    badgerTree = tree
    randomUser = accounts[8]

    token = MockToken.deploy({"from": deployer})
    token.initialize(
        [deployer.address, randomUser.address], [100 * 10 ** 18, 100 * 10 ** 18]
    )
    want = token

    performanceFeeGovernance = 1000
    performanceFeeStrategist = 1000
    withdrawalFee = 50
    managementFee = 50

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
    # NOTE: Vault starts unpaused

    strategy = DemoStrategy.deploy({"from": deployer})
    strategy.initialize(vault, [token])
    # NOTE: Strategy starts unpaused

    vault.setStrategy(strategy, {"from": governance})

    want.approve(vault, MaxUint256, {"from": randomUser})
    want.approve(vault, MaxUint256, {"from": deployer})

    return DotMap(
        deployer=deployer,
        vault=vault,
        strategy=strategy,
        want=want,
        governance=governance,
        randomUser=randomUser
    )

@pytest.fixture
def random_user(deploy_with_tree):
  return deploy_with_tree.randomUser

@pytest.fixture
def vault_with_tree(deploy_with_tree):
  return deploy_with_tree.vault

@pytest.fixture
def want_for_vault_with_tree(deploy_with_tree):
  return deploy_with_tree.want

## Forces reset before each test
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass
