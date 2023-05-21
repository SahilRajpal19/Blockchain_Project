import fastapi as _fastapi
import blockchain as _blockchain
import uvicorn
import psycopg2
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from jose import JWTError, jwt

from passlib.context import CryptContext
from pydantic import BaseModel
import psycopg2
from typing import Optional
import uuid

SECRET_KEY = "User_creation_Sahil_01"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres",
                        password="12345!@", port=5432)
cur = conn.cursor()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email_id: Optional[str] = None


class Register_user(BaseModel):
    username: str
    email_id: str
    password: str


class Transaction(BaseModel):
    recipient: str
    amount: float


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
blockchain = _blockchain.Blockchain()
app = _fastapi.FastAPI()
transactions = []


# endpoint to mine a block
@app.post("/mine_block/")
def mine_block(data: str):
    block = blockchain.mine_block(data=data)
    cur.execute(
        "INSERT INTO blocks (id,data,timestamp, previous_hash,proof) VALUES (%s, %s, %s, %s,%s)",
        (block["index"], block["data"], block["timestamp"],
        block["previous_hash"], block["proof"])
    )
    if transactions:
        cur.executemany("INSERT INTO transaction (sender,reciever,amount) VALUES (%s, %s, %s)",
                        transactions)
        conn.commit()

    transactions.clear()
    conn.commit()

    return block
# endpoint to return the entire blockchain


@app.get("/blockchain")
def get_blockchain():
    if not blockchain.is_chain_valid():
        return _fastapi.HTTPException(status_code=404, detail="Invalid blockchain")
    # chain = blockchain.chain
    cur.execute("""SELECT * FROM blocks""")
    return cur.fetchall()


# endpoint to see if the chain is valid
@app.get("/validate/")
def is_blockchain_valid():
    if not blockchain.is_chain_valid():
        return _fastapi.HTTPException(status_code=400, detail="The blockchain is invalid")

    return blockchain.is_chain_valid()

# endpoint to return the last block


@app.get("/blockchain/last/")
def previous_block():
    if not blockchain.is_chain_valid():
        return _fastapi.HTTPException(status_code=400, detail="The blockchain is invalid")

    return blockchain.get_previous_block()

# endpoint to get block hash


@app.get("/hash_by_block_number/{index}")
def get_hash_by_block_number(index: int):
    # return blockchain.chain[index+1]["previous_hash"]
    cur.execute(f"""SELECT previous_hash FROM blocks WHERE id={index}""")
    return cur.fetchone()

# endpoint to get block by index


@app.get("/block_number/{index}")
def get_block_by_index(index: int):
    # return blockchain.chain[index-1]
    cur.execute(f"""SELECT * FROM blocks WHERE id={index}""")
    return cur.fetchone()


@app.get("/block_between_time/{start_date}/{end_date}")
def block_between_time(start_date: str, end_date: str):
    if not blockchain.is_chain_valid():
        return _fastapi.HTTPException(status_code=404, detail="Invalid blockchain")
    return blockchain.blocks_between_time(start_date=start_date, end_date=end_date)


# User creation code with authorization
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str):
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    existing_user = cur.fetchone()
    if existing_user:
        return existing_user


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user[2]):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")  # type: ignore
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)  # type: ignore
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user


@app.post("/signup")
def signup(register_user: Register_user):
    # Check if the username already exists
    cur.execute("SELECT * FROM users WHERE username = %s",
                (register_user.username,))
    existing_user = cur.fetchone()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Hash the password
    hashed_password = get_password_hash(register_user.password)
    print(hashed_password)
    address = str(uuid.uuid4())  # Generate a unique address for the user

    # Insert the new user into the database
    cur.execute(
        "INSERT INTO users (username,email_id, hashed_password, address) VALUES (%s,%s, %s, %s)",
        (register_user.username, register_user.email_id, hashed_password, address),
    )
    conn.commit()
    return {"message": "User created successfully"}


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm,
                         Depends()]  # -> username and password
):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user[0]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/transaction")
# -> username and email_id
async def perform_transaction(transaction: Transaction, current_user: Annotated[User, Depends(get_current_active_user)]):

    cur.execute("SELECT * FROM users WHERE username = %s", (current_user[0],))
    user = cur.fetchone()

    cur.execute("SELECT * FROM users WHERE username = %s",
                (transaction.recipient,))
    recipient = cur.fetchone()

    if transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    if not recipient:
        raise HTTPException(status_code=404, detail="Invalid recipient")

    # Check if the sender has sufficient balance
    if user[4] < transaction.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    user_balance = int(user[4])
    user_balance -= transaction.amount
    recipient_amount = int(recipient[4])
    recipient_amount += transaction.amount

    # Perform the transaction
    cur.execute("UPDATE users SET balance = %s WHERE username = %s",
                (user_balance, user[0]))
    cur.execute("UPDATE users SET balance = %s  WHERE username =%s",
                (recipient_amount, recipient[0]))

    transaction = (user[0], recipient[0], transaction.amount)
    transactions.append(transaction)
    print(transactions)
    conn.commit()

    return ("Transaction successful")


@app.get("/user_transaction/{user}")
def user_last_transaction(user: str):
    (cur.execute("SELECT * FROM transaction where sender= %s", (user,)))
    return cur.fetchall()


if __name__ == "__main__":
    uvicorn.run(app)
