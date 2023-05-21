# Blockchain_Project
Create a simple Blockchain using Python FastAPI and PostgreSQL. The blockchain should have the following features:

- Mine a Block (API)
- Which generates/creates a new block
- Create a block (function)
- Index, Timestamp, Nonce, previous block and Block Hash
- Get Block Block Number (API)
- Get Previous Block Number (API)
- Get block Hash by Block Number (API)
- check if block number exists (function)
- Get list of Blocks between a timestamp range - start time, end time (API)
- Create Wallet for user (API)
- Create a transaction (API)
- Sender, receiver, amount, time
- Push the transaction to be mined in next block
- Balances - Each user can check their balance (API)
- User transactions (API)

Tables:
- Blocks
- Transactions
- Address

Every time you mine a block all transactions that are pending should process and add to table. Addresses table should not contain balances, but they need to be calculated based on transactions.
Ensure indexes are added wherever needed.
