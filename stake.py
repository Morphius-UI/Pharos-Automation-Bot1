from web3 import Web3
from eth_account import Account
import asyncio
import random

class nameclass:
    def __init__(self, proxy: None, priv: str):
        self.proxy = proxy
        self.priv = priv
        self.ADDR = Web3.to_checksum_address('0xd17512b7ec12880bd94eca9d774089ff89805f02')
        self.CTR = Web3.to_checksum_address('0xd17512b7ec12880bd94eca9d774089ff89805f02')
        self.RPC_URL = "https://api.zan.top/node/v1/pharos/testnet/54b49326c9f44b6e8730dc5dd4348421"
        self.STR = ['x', 'tiktok', 'xiaohongshu']
        self.ABI = [
            {
                "inputs": [
                    {
                        "components": [
                            {"internalType": "uint32", "name": "tokenType", "type": "uint32"},
                            {"internalType": "address", "name": "tokenAddress", "type": "address"}
                        ],
                        "name": "token",
                        "type": "tuple"
                    },
                    {
                        "components": [
                            {"internalType": "string", "name": "idSource", "type": "string"},
                            {"internalType": "string", "name": "id", "type": "string"},
                            {"internalType": "uint256", "name": "amount", "type": "uint256"},
                            {"internalType": "uint256[]", "name": "nftIds", "type": "uint256[]"}
                        ],
                        "name": "recipient",
                        "type": "tuple"
                    }
                ],
                "name": "tip",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function"
            }
        ]
        self.god_data = ''
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

    async def get_acc(self):
        try:
            acc = Account.from_key(self.priv)
            return acc.address
        except Exception as e:
            raise Exception(f"Invalid private key: {str(e)}")

    async def check_balance(self, w3, address, token_address='0x0000000000000000000000000000000000000000'):
        if token_address == '0x0000000000000000000000000000000000000000':
            return w3.eth.get_balance(address)
        else:
            # Для ERC20 токенов нужно использовать соответствующий ABI
            token_abi = [...]  # Добавьте ABI ERC20 токена
            token_contract = w3.eth.contract(address=token_address, abi=token_abi)
            return token_contract.functions.balanceOf(address).call()

    async def send(self, j: int):
        try:
            w3 = await self.get_web3_with_check(bool(self.proxy))
            sender_address = Web3.to_checksum_address(await self.get_acc())
            
            # Подготовка данных для токена
            token_data = (
                1,  # uint32 tokenType (1 для ETH)
                '0x0000000000000000000000000000000000000000'  # address tokenAddress
            )
            s = random.choice(self.STR)
            # Подготовка данных получателя
            amount = random.randint(1, 200) * 10**8
            if s == 'x':
                with open('X.txt', 'r') as f:
                    X = [line.strip() for line in f if line.strip()]
                god_data = random.choice(X)

            elif s == 'tiktok':
                with open('tiktok.txt', 'r') as f:
                    tik = [line.strip() for line in f if line.strip()]
                god_data = random.choice(tik)
            else:
                god_data = str(random.randint(100, 1000000000))
            recipient_data = (
                s,  # string idSource
                god_data,  # string id
                amount,  # uint256 amount
                []  # uint256[] nftIds (исправлено на список)
            )

            # Проверка баланса перед отправкой
            balance = await self.check_balance(w3, sender_address)
            if balance < amount + (21000 * w3.eth.gas_price):  # Проверка баланса с учетом газа
                raise Exception(f"Insufficient balance. Need: {amount + (21000 * w3.eth.gas_price)} wei, Have: {balance} wei")

            contract = w3.eth.contract(address=self.CTR, abi=self.ABI)
            nonce = w3.eth.get_transaction_count(sender_address)
            gas_price = w3.eth.gas_price

            try:
                res = contract.functions.tip(
                    token_data,
                    recipient_data
                ).call({'from': sender_address, 'value': amount})
            except Exception as e:
                print(f"❌ Проверка не пройдена: {str(e)}")
                print(f"Допустимые источники ID: {self.VALID_SOURCES}")
                return None

            transaction = contract.functions.tip(
                token_data,
                recipient_data
            ).build_transaction({
                'gas': hex(300000),
                'gasPrice': hex(w3.to_wei(2, 'gwei')),
                'value': hex(amount),
                "from": sender_address,
                'nonce': hex(nonce),

            })
            signed_txn = w3.eth.account.sign_transaction(transaction, self.priv)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            print(f"{sender_address}       ✅ Транзакция номер {j} отправлена! Хеш: {tx_hash.hex()}")
            
            # Ожидаем подтверждения
            print("⏳ Ожидаем подтверждения транзакции...")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                print(f"{sender_address}         Успешно!   💸 Использовано газа: {receipt.gasUsed}")
            else:
                print("❌ Транзакция не выполнена")
                if 'revertReason' in receipt:
                    print(f"Причина: {receipt['revertReason']}")
            
            return receipt

        except Exception as e:
            print(f"🔥 Ошибка: {str(e)}")
            return None


async def _main():
    try:
        with open('accounts.txt', 'r') as f:
            PRIV = [line.strip() for line in f if line.strip()]
        
        with open('proxy.txt', 'r') as f:
            PROX = [line.strip() for line in f if line.strip()]
            
        term = int(input('Сколько раз транзакции отправить минимально:'))
        term1 = int(input('Сколько раз транзакции отправить максимально:'))

        for i, priv in enumerate(PRIV):
            print(f'Начинаем аккаунт №{i+1}')
            proxy = PROX[i] if i < len(PROX) else None
            worker = nameclass(proxy, priv)
            for j in range(random.randrange(term, term1)):
                await worker.send(j+1)
                await asyncio.sleep(random.randint(20, 40))
            print("Ожидаем и переходим к следующему аккаунту")
            await asyncio.sleep(random.randint(30, 40))

    except Exception as e:
        print(f"⚠️ Ошибка в main: {e}")


if __name__ == "__main__":

    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        print('\n🛑 Программа остановлена пользователем')
