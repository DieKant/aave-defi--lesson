from scripts.helpful_scripts import get_account
from brownie import config, network, interface
from scripts.get_weth import get_weth

def main():
    account = get_account()
    # prendiamo una variabile erc20 dove andiamo a riprendere un token
    # definito nel brownie config 
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    # chiamiamo il get_weth se non ne abbiamo in conto sulla mainnet fork
    if network.show_active() in ["mainnet-fork"]:
        get_weth()
    # depositiamo qualcosa su aave
    # andiamo a prendere il contratto lending pool che è quello che si 
    # occupa di tute le azioni lato client
    lending_pool = get_lending_pool()
    print(lending_pool)

def get_lending_pool():
    # prendiamo l'address del contratto lending pool dal contratto
    # LendingPoolAddressProvider per il mercato che abbiamo selezionato
    # con il suo metodo getLendingPool()
    lending_pool_address_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_address_provider.getLendingPool()
    # abbiamo l'address e l'abi, possiamo quindi prendere il contratto e usarlo
    lending_pool = interface.ILendingPoolAddressesProvider(lending_pool_address)
    return lending_pool


