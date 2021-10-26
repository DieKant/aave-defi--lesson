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
    # ...ma quanto possiamo prendere in presito
    # con quello che abbiamo depositato, in modo
    # che ci ritorni un health factor accettabile?
    # per fare ciò dobbiamo prima prendere i nostri dati
    # e usare quelli per calcolarlo con il metodo
    # getUserAccountData dentro LendingPool
    print("prendo l'eth che ho depositato, ho preso in prestito(debito), posso prendere in prestito...")
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    print("fatto")
    print("prendo in prestito DAI")
    # dato che dobbiamo convertire ETH in DAI ci serve un price feed
    dai_eth_price = get_asset_price(config["networks"][network.show_active()]["dai_eth_price_feed"])
    print("fatto")
    # moltiplichiamo il nostro valore di borrowable_eth per migliorare
    # il nostro health factor, più è basso meglio è
    # borrowable_eth -> borrwoable_dai * 95%
    amount_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.50)
    print(f"andiamo a prendere in prestito {amount_dai_to_borrow} DAI")
    # lo andiamo a fare con la funzione borrow() di aave che ci richiede:
    # l'address del contratto del token che vogliamo in prestito
    # (lo troviamo su etherscan/aave docs per kovan)
    # quanto chiedere in presito
    # rateo di interesse che possiamo settare a 1 per lo STABLE e 2 per il VARIABLE
    # refferalCode che è obsoleto mettiamo 0
    # il nostro address
    # infine from account
    # e aspettiamo
    dai_address = config["networks"][network.show_active()]["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_address,
        Web3.toWei(amount_dai_to_borrow, "ether"),
        1,
        0,
        account.address,
        {"from": account}
    )
    borrow_tx.wait(1)
    print("fatto")
    print("ripago gli asset prestati")
    # quanto vogliamo ripagare, il contratto e il nostro addrerss
    repay_all(amount, lending_pool, account)
    print("fatto")
    print("Tutti i punti del readme sono stati completati")


def repay_all(amount, lending_pool, account):
    # approviamo il trasferimento
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool,
        config["networks"][network.show_active()]["dai_token"],
        account
    )
    # ripaghiamo il prestito 
    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        1,
        account.address,
        {"from": account}
    )
    repay_tx.wait(1)

def get_asset_price(price_feed_address):
    # prendo abi e address
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    # se una funzione di solidiy ritorna più argomenti la puoi trattare
    # come un vettore e prendere la variabile che ti serve a una posizione
    # del "vettore" che torna indietro
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    print(f"il cambio DAI/ETH è di {converted_latest_price}")
    return(float(converted_latest_price))


def get_borrowable_data(lending_pool, account):
    # questa funzione ritorna 6 valori
    (
        total_collateral_eth,
        total_debt_eth,
        avaiable_borrow_eth,
        current_liquidation_threshold,
        ltv,
        health_factor
    ) = lending_pool.getUserAccountData(account.address)
    # questi valori sono in wei, rendiamoli numeri singoli leggibili
    avaiable_borrow_eth = Web3.fromWei(avaiable_borrow_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    print(f"hai {total_collateral_eth} di eth depositato")
    print(f"hai {total_debt_eth} eth preso in prestito")
    # posso prendere in prestito solo meno di quanto ho depositato per
    # via del liquidation threshold (che è diverso da asset a asset)
    print(f"puoi prendere in presito {avaiable_borrow_eth} eth")
    return (float(avaiable_borrow_eth), float(total_debt_eth))


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
