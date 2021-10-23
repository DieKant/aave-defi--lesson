from scripts.helpful_scripts import get_account
from brownie import config, network, interface
from scripts.get_weth import get_weth
from web3 import Web3

# definiamo un amount
amount = Web3.toWei(0.1, "ether")


def main():
    account = get_account()
    # prendiamo una variabile erc20 dove andiamo a riprendere un token
    # definito nel brownie config
    print("seleziono token erc20...")
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    # chiamiamo il get_weth se non ne abbiamo in conto sulla mainnet fork
    if network.show_active() in ["mainnet-fork"]:
        print("fondi insufficenti, aggiungo del token erc20...")
        get_weth()
    print("fatto")
    # depositiamo qualcosa su aave
    # andiamo a prendere il contratto lending pool che è quello che si
    # occupa di tute le azioni lato client
    print("prendo il contratto LendingPool...")
    lending_pool = get_lending_pool()
    print("fatto")
    # approviamo il deposito del nostro token erc20
    approve_erc20(amount, lending_pool.address, erc20_address, account)
    # depositiamo su aave
    # l'asset, la quantità di asset, chi deposita, come ultima variabile passa 0
    # perche è un paramentro deprecato
    print("deposito il token erc20 su aave...")
    tx = lending_pool.deposit(
        erc20_address, amount, account.address, 0, {"from": account}
    )
    tx.wait(1)
    print("fatto")


# ci serve uno "spender" ossia chi dobbiamo approvare che spenda
# i nostri token e quanto(amount) possono spendere del nostro token(erc20_address)
# infine il nostro account per fare tutta l'operazione
def approve_erc20(amount, spender, erc20_address, account):
    print("approvo l'erc20...")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("approvato")


def get_lending_pool():
    # prendiamo l'address del contratto lending pool dal contratto
    # LendingPoolAddressProvider per il mercato che abbiamo selezionato
    # con il suo metodo getLendingPool()
    lending_pool_address_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_address_provider.getLendingPool()
    # abbiamo l'address e l'abi, possiamo quindi prendere il contratto e usarlo
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool
