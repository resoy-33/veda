"""Hedera writer: topics, messages, files, NFT collection and minting."""
from __future__ import annotations

from hiero_sdk_python import (
    AccountId,
    Client,
    FileContentsQuery,
    FileCreateTransaction,
    FileId,
    PrivateKey,
    SupplyType,
    TokenCreateTransaction,
    TokenId,
    TokenMintTransaction,
    TokenType,
    TopicCreateTransaction,
    TopicId,
    TopicMessageSubmitTransaction,
)

from ..config import settings
from ..core.canonical import canonical_json


class HederaService:
    def __init__(self) -> None:
        operator_id, operator_key = settings.require_operator()
        self.account_id = AccountId.from_string(operator_id)
        self.key = PrivateKey.from_string(operator_key)
        self.client = Client.for_testnet()
        self.client.set_operator(self.account_id, self.key)

    @property
    def operator_id(self) -> str:
        return str(self.account_id)

    def create_topic(self, memo: str = "veda-filing") -> str:
        receipt = (
            TopicCreateTransaction()
            .set_memo(memo)
            .set_submit_key(self.key.public_key())
            .execute(self.client)
        )
        return str(receipt.topic_id)

    def submit_message(self, topic_id: str, message: dict) -> dict:
        receipt = (
            TopicMessageSubmitTransaction()
            .set_topic_id(TopicId.from_string(topic_id))
            .set_message(canonical_json(message))
            .execute(self.client)
        )
        return {
            "sequence": receipt.topic_sequence_number,
            "transaction_id": str(receipt.transaction_id),
        }

    def create_file(self, contents: bytes) -> str:
        receipt = (
            FileCreateTransaction()
            .set_contents(contents)
            .set_keys([self.key.public_key()])
            .execute(self.client)
        )
        return str(receipt.file_id)

    def read_file(self, file_id: str) -> bytes:
        contents = (
            FileContentsQuery()
            .set_file_id(FileId.from_string(file_id))
            .execute(self.client)
        )
        if isinstance(contents, (bytes, bytearray)):
            return bytes(contents)
        return str(contents).encode("utf-8")

    def create_nft_collection(
        self, name: str = "Dépôt vérifié", symbol: str = "VEDA"
    ) -> str:
        receipt = (
            TokenCreateTransaction()
            .set_token_name(name)
            .set_token_symbol(symbol)
            .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
            .set_supply_type(SupplyType.FINITE)
            .set_max_supply(10_000)
            .set_initial_supply(0)
            .set_decimals(0)
            .set_treasury_account_id(self.account_id)
            .set_supply_key(self.key.public_key())
            .execute(self.client)
        )
        return str(receipt.token_id)

    def mint_nft(self, token_id: str, metadata: bytes) -> int:
        receipt = (
            TokenMintTransaction()
            .set_token_id(TokenId.from_string(token_id))
            .set_metadata([metadata])
            .execute(self.client)
        )
        return int(receipt.serial_numbers[0])
