// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

interface IPool {
    function flashLoanSimple(address receiver, address asset, uint256 amount, bytes calldata params, uint16 referralCode) external;
}
interface IERC20 {
    function approve(address spender, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
}
interface IRouter {
    function swapExactTokensForTokens(uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline) external returns (uint[] memory amounts);
}

contract FlashArbPRO {
    address immutable owner;
    IPool constant AAVE_POOL = IPool(0x794a61358D6845594F94dc1DB02A252b5b4814aD);
    address constant QUICK_ROUTER = 0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff;
    address constant SUSHI_ROUTER = 0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506;

    constructor() { owner = msg.sender; }

    function requestFlashLoan(address _token, uint256 _amount, address _targetToken) external {
        require(msg.sender == owner, "No owner");
        bytes memory data = abi.encode(_targetToken);
        AAVE_POOL.flashLoanSimple(address(this), _token, _amount, data, 0);
    }

    function executeOperation(address asset, uint256 amount, uint256 premium, address initiator, bytes calldata params) external returns (bool) {
        address targetToken = abi.decode(params, (address));
        uint256 amountOwed = amount + premium;

        // 1. Aprobar y Cambiar en QuickSwap (Asset -> Target)
        IERC20(asset).approve(QUICK_ROUTER, amount);
        address[] memory path1 = new address[](2);
        path1[0] = asset;
        path1[1] = targetToken;
        IRouter(QUICK_ROUTER).swapExactTokensForTokens(amount, 0, path1, address(this), block.timestamp + 60);

        // 2. Cambiar en SushiSwap (Target -> Asset)
        uint256 targetBal = IERC20(targetToken).balanceOf(address(this));
        IERC20(targetToken).approve(SUSHI_ROUTER, targetBal);
        address[] memory path2 = new address[](2);
        path2[0] = targetToken;
        path2[1] = asset;
        IRouter(SUSHI_ROUTER).swapExactTokensForTokens(targetBal, 0, path2, address(this), block.timestamp + 60);

        // 3. Devolver préstamo y verificar ganancia
        uint256 finalBal = IERC20(asset).balanceOf(address(this));
        require(finalBal > amountOwed, "Arb fallido: No hay ganancia");
        IERC20(asset).approve(address(AAVE_POOL), amountOwed);
        IERC20(asset).transfer(owner, finalBal - amountOwed);
        
        return true;
    }
}
