#   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
#        Oumar Mamoun Ibrahim U22200741
#        Abdullah Jafar Abdelhamid U23101327
#        Faris Munadhil Ahmed Alagha U23104246
#        Mohamed Ahmed Saad Khafagy U20101649

import hashlib
import os
import secrets

from sqlalchemy import create_engine, text

HERE = os.path.dirname(os.path.abspath(__file__))

# postgres on the host, sqlite when running on a laptop
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(HERE, "server.db"))

# hosting sites give postgres:// but sqlalchemy wants the driver name
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgres://"):]
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgresql://"):]

engine = create_engine(DATABASE_URL)


def setup():
    f = open(os.path.join(HERE, "schema.sql"))
    sql = f.read()
    f.close()
    conn = engine.connect()
    parts = sql.split(";")
    for p in parts:
        lines = []
        for line in p.split("\n"):
            if line.startswith("--") == False:
                lines.append(line)
        one = "\n".join(lines).strip()
        if one != "":
            conn.execute(text(one))
    conn.commit()
    conn.close()


def run(sql, values=None):
    if values == None:
        values = {}
    conn = engine.connect()
    conn.execute(text(sql), values)
    conn.commit()
    conn.close()


def rows(sql, values=None):
    if values == None:
        values = {}
    conn = engine.connect()
    found = conn.execute(text(sql), values).fetchall()
    conn.close()
    return found


def hash_key(key):
    return hashlib.sha256(key.encode()).hexdigest()


def add_device(device_id):
    key = secrets.token_hex(24)
    # update and not delete, postgres wont delete a device that has sessions
    run("INSERT INTO device (device_id) VALUES (:d) ON CONFLICT (device_id) DO NOTHING", {"d": device_id})
    run("UPDATE device SET api_key_hash=:k WHERE device_id=:d", {"d": device_id, "k": hash_key(key)})
    return key


def hash_password(password, salt=None):
    if salt == None:
        salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return salt + "$" + h.hex()


def check_password(password, saved):
    if saved == None:
        return False
    parts = saved.split("$")
    return secrets.compare_digest(hash_password(password, parts[0]), saved)


# the 4 digit pin never leaves the car, the dashboard has its own password
def set_password(driver_id, name, password):
    run("INSERT INTO driver (driver_id) VALUES (:d) ON CONFLICT (driver_id) DO NOTHING", {"d": driver_id})
    run("UPDATE driver SET display_name=:n, pin_hash=:p WHERE driver_id=:d",
        {"n": name, "p": hash_password(password), "d": driver_id})
