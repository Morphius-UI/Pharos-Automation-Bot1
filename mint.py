from web3 import Web3
from web3.exceptions import TransactionNotFound
from eth_utils import to_hex
from eth_account import Account
from eth_account.messages import encode_defunct
import asyncio, random

class NFT:
    def __init__(self, private, proxy):
        self.proxy = proxy
        self.RPC_URL = "https://api.zan.top/node/v1/pharos/testnet/54b49326c9f44b6e8730dc5dd4348421"
        self.ABI = [
            {
                "inputs": [
                {
                    "internalType": "address",
                    "name": "_receiver",
                    "type": "address"
                },
                {
                    "internalType": "uint256",
                    "name": "_quantity",
                    "type": "uint256"
                },
                {
                    "internalType": "address",
                    "name": "_currency",
                    "type": "address"
                },
                {
                    "internalType": "uint256",
                    "name": "_pricePerToken",
                    "type": "uint256"
                },
                {
                    "components": [
                    {
                        "internalType": "bytes32[]",
                        "name": "",
                        "type": "bytes32[]"
                    },
                    {
                        "internalType": "uint256",
                        "name": "",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "",
                        "type": "uint256"
                    },
                    {
                        "internalType": "address",
                        "name": "",
                        "type": "address"
                    }
                    ],
                    "internalType": "struct AllowlistProof",
                    "name": "_allowlistProof",
                    "type": "tuple"
                },
                {
                    "internalType": "bytes",
                    "name": "_data",
                    "type": "bytes"
                }
                ],
                "name": "claim",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function"
            }
            ]

        self._quantity = 1
        self._currency = Web3.to_checksum_address('0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee')
        self._pricePerToken = 1000000000000000000  # 1 ETH in wei
        self.allow = ((), 0, 115792089237316195423570985008687907853269984665640564039457584007913129639935, Web3.to_checksum_address('0x0000000000000000000000000000000000000000'))
        self._data = b''  # Empty bytes instead of null
        self.private = private
    

    async def getadr(self, private):
        acc = Account.from_key(private)
        return acc.address
    
    async def get_web3_with_check(self, use_proxy: bool, retries=3, timeout=60):
        request_kwargs = {"timeout": timeout}
        if use_proxy and self.proxy:
            request_kwargs["proxies"] = {"http": self.proxy, "https": self.proxy}

        for attempt in range(retries):
            try:
                web3 = Web3(Web3.HTTPProvider(self.RPC_URL, request_kwargs=request_kwargs))
                if not web3.is_connected():
                    raise Exception("Not connected to RPC")
                return web3
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                raise Exception(f"Failed to Connect to RPC: {str(e)}")


    async def start(self):
        w3 = await self.get_web3_with_check(bool(self.proxy))
        contract_address = Web3.to_checksum_address('0x96381ed3fcfb385cbacfe6908159f0905b19767a')
        
        # Get sender address
        sender_address = await self.getadr(self.private)
        
        # Check balance
        balance = w3.eth.get_balance(sender_address)
        required_balance = self._pricePerToken * self._quantity + 200000 * w3.eth.gas_price  # Cost + gas
        
        if balance < required_balance:
            print(f"⚠️ Недостаточно средств на аккаунте {sender_address}. Баланс: {w3.from_wei(balance, 'ether')} ETH, требуется: {w3.from_wei(required_balance, 'ether')} ETH")
            return False  # Return False to indicate insufficient funds
        
        # Create contract instance
        contract = w3.eth.contract(address=contract_address, abi=self.ABI)
        
        # Prepare transaction
        try:
            tx = contract.functions.claim(
                _receiver=sender_address,
                _quantity=self._quantity,
                _currency=self._currency,
                _pricePerToken=self._pricePerToken,
                _allowlistProof=self.allow,
                _data=self._data
            ).build_transaction({
                'from': sender_address,
                'nonce': hex(w3.eth.get_transaction_count(sender_address)),
                'gas': hex(1000000),  # Adjust gas limit as needed
                'gasPrice': hex(w3.eth.gas_price),
                'value': hex(1000000000000000000)
            })
            
            # Sign transaction
            signed_tx = w3.eth.account.sign_transaction(tx, self.private)
            
            # Send transaction
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            print(f"✅ Transaction sent: {tx_hash.hex()}")
            
            # Wait for transaction receipt
            try:
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                print(f"Transaction mined: {receipt['transactionHash'].hex()}")
                if receipt['status'] == 1:
                    print("✅ Transaction succeeded!")
                    return True
                else:
                    print("❌ Transaction failed!")
                    return False
            except TransactionNotFound:
                print("⌛ Transaction not found within the timeout period")
                return False
        except Exception as e:
            print(f"⚠️ Ошибка при отправке транзакции: {e}")
            return False

async def main():
    try:
        with open('accounts.txt', 'r') as f:
            PRIV = [line.strip() for line in f if line.strip()]
        
        with open('proxy.txt', 'r') as f:
            PROX = [line.strip() for line in f if line.strip()]

        for i, priv in enumerate(PRIV):
            try:
                prox = PROX[i] if i < len(PROX) else None
                print(f"\n🔑 Обработка аккаунта {i+1}/{len(PRIV)}")
                
                nft = NFT(priv, prox)
                result = await nft.start()
                
                if result is False:  # Если не хватило баланса
                    print("⏩ Переход к следующему аккаунту")
                    continue
                    
                await asyncio.sleep(random.randint(40, 50))
            except Exception as e:
                print(f"⚠️ Ошибка с аккаунтом {i+1}: {e}")
                continue
    except Exception as e:
        print(f"⚠️ Ошибка в main: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n🛑 Программа остановлена пользователем')
