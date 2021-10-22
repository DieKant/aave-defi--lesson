from scripts.helpful_scripts import get_account
from brownie import interface, config, network

def get_weth():
    """
    mint weth by depositing eth
    """
    # ci serve l'ABI del contratto weth kovan
    # e il suo ADDRESS
    # andiamo a prendere tutto con una interface
    account = get_account()
    # posso fare cosi invece del get_contract perche sono sicuro che non ho niente da mockare
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    # converto in formato wei il valore per standard e fo la transazione di deposito
    tx = weth.deposit({"from": account, "value": 0.1 * 10 ** 18})
    print(f"recived 0.1 WETH")
    return tx

def main():
    get_weth()