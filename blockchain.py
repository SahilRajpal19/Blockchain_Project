'''
Genesis Block{
    index:0,
    timestamp:current time,
    data:" i am the  genesis block"
    proof:3,
    previous_hash:"0"
}->hash()->2343aa 
'''
import datetime as dt
import hashlib
import json
import psycopg2
conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres",
                        password="12345!@", port=5432)
cur = conn.cursor()


class Blockchain:
    def __init__(self):
        cur.execute("""CREATE TABLE IF NOT EXISTS blocks (
        id INT PRIMARY KEY,
        data VARCHAR(255),
        timestamp VARCHAR(255) NOT NULL,
        previous_hash VARCHAR(255) NOT NULL,
        proof INT NOT NULL
        );
        """)
        cur.execute("""CREATE TABLE IF NOT EXISTS users (
        username VARCHAR(255),
        email_id VARCHAR(255),
        hashed_password VARCHAR(255) NOT NULL,
        address VARCHAR(255) NOT NULL,
        balance FLOAT NOT NULL DEFAULT 10
        );
        """)
        cur.execute("""CREATE TABLE IF NOT EXISTS transaction(
                    sender VARCHAR(255),
                    reciever VARCHAR(255),
                    amount INT
        );
        """)
        cur.execute(
            "INSERT INTO blocks (id,data,timestamp, previous_hash,proof) VALUES (%s, %s, %s, %s,%s)",
            (1, "Genesis Block", str(
                dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')), "0", 1)
        )

        conn.commit()

    def mine_block(self, data: str) -> dict:
        previous_block = self.get_previous_block()
        previous_proof = previous_block[4]
        cur.execute("""SELECT COUNT (*) FROM blocks""")
        length = cur.fetchone()
        index = length[0]+1
        proof = self.proof_of_work(previous_proof)
        previous_hash = self.hash(block=previous_block)
        block = self.create_block(
            data=data, proof=proof, previous_hash=previous_hash, index=index)
        return block

    def create_block(self, data: str, proof: int, previous_hash: str, index: int) -> dict:
        block = {
            'index': index,
            'timestamp': str(dt.datetime.now()),
            'data': data,
            'proof': proof,
            'previous_hash': previous_hash,
        }
        return block

    def proof_of_work(self, previous_proof: int):
        # miners proof submitted
        new_proof = 1
        check_proof = False

        while check_proof is False:
            # problem and algorithm based off the previous proof and new proof
            hash_operation = hashlib.sha256(
                str(new_proof ** 2 - previous_proof ** 2).encode()).hexdigest()
        # check miners solution to problem, by using miners proof in cryptographic encryption
        # if miners proof results in 4 leading zero's in the hash operation, then:
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                # if miners solution is wrong, give mine another chance until correct
                new_proof += 1

        return new_proof

    # generate a hash of an entire block
    def hash(self, block: dict) -> str:
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def get_previous_block(self) -> dict:
        # return self.chain[-1]
        cur.execute("""SELECT * FROM blocks ORDER BY id DESC LIMIT 1 """)
        return cur.fetchone()

    # check if the blockchain is valid
    def is_chain_valid(self) -> bool:
        cur.execute("""SELECT * FROM blocks WHERE id=1 """)
        #  get the first block in the chain and it serves as the previous block
        previous_block = cur.fetchone()
        # an index of the blocks in the chain for iteration
        block_index = 2
        cur.execute("""SELECT COUNT(*) FROM blocks""")
        length = cur.fetchone()
        while block_index < length[0]+1:
            # get the current block
            cur.execute(f"""SELECT * FROM blocks WHERE id = {block_index} """)
            block = cur.fetchone()
            # block=self.chain[block_index]
            # check if the current block link to previous block has is the same as the hash of the previous block
            if block[3] != self.hash(previous_block):
                return False
            # get the previous proof from the previous block
            previous_proof = previous_block[4]
            # get the current proof from the current block
            current_proof = block[4]
            # run the proof data through the algorithm
            hash_operation = hashlib.sha256(
                str(current_proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            # check if hash operation is invalid
            if hash_operation[:4] != '0000':
                return False
            # set the previous block to the current block after running validation on current block
            previous_block = block
            block_index += 1
        return True

    def blocks_between_time(self, start_date: str, end_date: str):
        start_date = dt.date.fromisoformat(start_date)
        end_date = dt.date.fromisoformat(end_date)

        blocks_in_range = []
        cur.execute("""SELECT * FROM blocks""")
        blocks = cur.fetchall()
        for block in blocks:
            block_date = block[2]
            block_date = block_date[:10]
            block_date = dt.date.fromisoformat(block_date)
            if (start_date <= block_date <= end_date):
                blocks_in_range.append(block)

        return blocks_in_range
