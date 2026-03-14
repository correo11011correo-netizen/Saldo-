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
    function getAmountsOut(uint amountIn, address[] calldata path) external view returns (uint[] memory amounts);
}

contract FlashArbULTIMATE {
    address public immutable owner;
    address constant AAVE_POOL = 0x794a61358D6845594F94dc1DB02A252b5b4814aD;
    address constant QUICK_ROUTER = 0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff;
    address constant SUSHI_ROUTER = 0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506;

    constructor() { owner = msg.sender; }

    // Función principal para iniciar el arbitraje desde el bot
    function requestFlashLoan(address _token, uint256 _amount, address _targetToken) external {
        require(msg.sender == owner, "Unauthorized");
        bytes memory data = abi.encode(_targetToken);
        IPool(AAVE_POOL).flashLoanSimple(address(this), _token, _amount, data, 0);
    }

    // Esta es la función que llama AAVE automáticamente
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external returns (bool) {
        require(msg.sender == AAVE_POOL, "Only Aave");
        
        address targetToken = abi.decode(params, (address));
        uint256 amountOwed = amount + premium;

        // 1. Swap en QuickSwap (Asset -> Target)
        IERC20(asset).approve(QUICK_ROUTER, amount);
        address[] memory path1 = new address[](2);
        path1[0] = asset;
        path1[1] = targetToken;
        IRouter(QUICK_ROUTER).swapExactTokensForTokens(amount, 0, path1, address(this), block.timestamp + 60);

        // 2. Swap en SushiSwap (Target -> Asset)
        uint256 targetBalance = IERC20(targetToken).balanceOf(address(this));
        IERC20(targetToken).approve(SUSHI_ROUTER, targetBalance);
        address[] memory path2 = new address[](2);
        path2[0] = targetToken;
        path2[1] = asset;
        IRouter(SUSHI_ROUTER).swapExactTokensForTokens(targetBalance, 0, path2, address(this), block.timestamp + 60);

        // 3. Verificación de Rentabilidad y Devolución
        uint256 finalBalance = IERC20(asset).balanceOf(address(this));
        require(finalBalance >= amountOwed, "Insolvent: Loss detected");

        // Aprobamos a Aave para que cobre el préstamo + fee
        IERC20(asset).approve(AAVE_POOL, amountOwed);

        // Enviamos la ganancia neta directamente a tu wallet
        if (finalBalance > amountOwed) {
            uint256 profit = finalBalance - amountOwed;
            IERC20(asset).transfer(owner, profit);
        }

        return true;
    }

    // Función de Emergencia: Recuperar tokens enviados por error
    function emergencyWithdraw(address token) external {
        require(msg.sender == owner, "Unauthorized");
        uint256 bal = IERC20(token).balanceOf(address(this));
        IERC20(token).transfer(owner, bal);
    }

    // Permitir recibir POL (nativo) si es necesario
    receive() external payable {}
}
