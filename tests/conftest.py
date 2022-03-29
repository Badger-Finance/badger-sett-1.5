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

@pytest.fixture
def deployer():
    return accounts[1]

@pytest.fixture
def tree(deployer):
  c = TestBadgerRewards.deploy({"from": deployer})
  c.startNextEpoch()

  return c

@pytest.fixture
def deployed(tree):
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

    return DotMap(
        deployer=deployer,
        vault=vault,
        strategy=strategy,
        want=want,
        governance=governance,
        proxyAdmin=proxyAdmin,
        randomUser=randomUser,
        performanceFeeGovernance=performanceFeeGovernance,
        performanceFeeStrategist=performanceFeeStrategist,
        withdrawalFee=withdrawalFee,
        badgerTree=badgerTree
    )


@pytest.fixture
def deployed_gueslist(deployed):
    """
    Deploys TestVipCappedGuestListBbtcUpgradeable.sol for testing Guest List functionality
    """

    # NOTE: Change accordingly
    vaultAddr = deployed.vault
    merkleRoot = "0x1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a"
    userCap = 2e18
    totalCap = 50e18

    # Get deployer account from local keystore. Deployer must be the
    # vault's governance address in order to set its guestlist parameters.
    dev = deployed.deployer

    # Get actors
    governance = deployed.governance
    proxyAdmin = deployed.proxyAdmin

    assert governance != AddressZero
    assert proxyAdmin != AddressZero

    # Deploy guestlist
    guestlist = deploy_guestlist(dev, proxyAdmin, vaultAddr)

    # Set guestlist parameters
    guestlist.setUserDepositCap(userCap, {"from": dev})
    assert guestlist.userDepositCap() == userCap

    guestlist.setTotalDepositCap(totalCap, {"from": dev})
    assert guestlist.totalDepositCap() == totalCap

    # Transfers ownership of guestlist to Badger Governance
    guestlist.transferOwnership(governance, {"from": dev})
    assert guestlist.owner() == governance

    return DotMap(guestlist=guestlist)


def deploy_guestlist(dev, proxyAdmin, vaultAddr):

    guestlist_logic = TestVipCappedGuestListBbtcUpgradeable.deploy({"from": dev})

    # Initializing arguments
    args = [vaultAddr]

    guestlist_proxy = AdminUpgradeabilityProxy.deploy(
        guestlist_logic,
        proxyAdmin,
        guestlist_logic.initialize.encode_input(*args),
        {"from": dev},
    )
    time.sleep(1)

    ## We delete from deploy and then fetch again so we can interact
    AdminUpgradeabilityProxy.remove(guestlist_proxy)
    guestlist_proxy = TestVipCappedGuestListBbtcUpgradeable.at(guestlist_proxy.address)

    console.print("[green]Guestlist was deployed at: [/green]", guestlist_proxy.address)

    return guestlist_proxy


## Contracts ##
@pytest.fixture
def vault(deployed):
    return deployed.vault


@pytest.fixture
def strategy(deployed):
    return deployed.strategy


@pytest.fixture
def badgerTree(deployed):
    return deployed.badgerTree


@pytest.fixture
def guestlist(deployed_gueslist):
    return deployed_gueslist.guestlist



## Tokens ##
@pytest.fixture
def want(deployed):
    return deployed.want


@pytest.fixture
def tokens(deployed):
    return [deployed.want]


## Accounts ##
@pytest.fixture
def strategist(strategy):
    return accounts.at(strategy.strategist(), force=True)


@pytest.fixture
def keeper(vault):
    return accounts.at(vault.keeper(), force=True)


@pytest.fixture
def guardian(vault):
    return accounts.at(vault.guardian(), force=True)


@pytest.fixture
def governance(deployed):
    return deployed.governance

@pytest.fixture
def treasury(deployed):
    return deployed.governance


@pytest.fixture
def proxyAdmin(deployed):
    return deployed.proxyAdmin


@pytest.fixture
def randomUser(deployed):
    return deployed.randomUser


## Forces reset before each test
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


### Fees ###
@pytest.fixture
def performanceFeeGovernance(deployed):
    return deployed.performanceFeeGovernance


@pytest.fixture
def performanceFeeStrategist(deployed):
    return deployed.performanceFeeStrategist


@pytest.fixture
def withdrawalFee(deployed):
    return deployed.withdrawalFee


@pytest.fixture
def setup_share_math(deployer, vault, want, governance):

    depositAmount = int(want.balanceOf(deployer) * 0.5)
    assert depositAmount > 0
    want.approve(vault.address, MaxUint256, {"from": deployer})
    vault.deposit(depositAmount, {"from": deployer})

    vault.earn({"from": governance})

    return DotMap(depositAmount=depositAmount)


@pytest.fixture
def strategy_two(deployer, vault, want):
    strategy = DemoStrategy.deploy({"from": deployer})
    strategy.initialize(vault, [want])

    return strategy

## Forces reset before each test
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass
