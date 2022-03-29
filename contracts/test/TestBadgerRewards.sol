// SPDX-License-Identifier: MIT

pragma solidity 0.8.10;
pragma experimental ABIEncoderV2;

import {RewardsManager} from "@badger-rewards/RewardsManager.sol";

contract TestBadgerRewards is RewardsManager {
  // So Brownie compiles it tbh
  // Changes here invalidate the bytecode, breaking trust of the mix
  // DO NOT CHANGE THIS FILE
}