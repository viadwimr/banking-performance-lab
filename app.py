from flask import Flask, jsonify, request
import psycopg2
import time
from psycopg2.pool import ThreadedConnectionPool
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

app = Flask(__name__)

db_pool = ThreadedConnectionPool(
    minconn=5,
    maxconn=20,
    host="postgres",
    database="banking",
    user="bank",
    password="bank"
)

def get_db():
    return db_pool.getconn()

def release_db(conn):
    db_pool.putconn(conn)

@app.route("/health")
def health():
    return jsonify({"status": "UP"})

@app.route("/login", methods=["POST"])
def login():
    time.sleep(0.05)
    return jsonify({
        "token": "demo-token-123",
        "userId": 1001
    })

@app.route("/accounts/<int:account_id>")
def account(account_id):
    start = time.perf_counter()
    conn_start = time.perf_counter()
    conn = get_db()
    conn_time = time.perf_counter() - conn_start

    try:
        query_start = time.perf_counter()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, account_number, balance FROM accounts WHERE id = %s",
            (account_id,)
        )

        row = cur.fetchone()
        query_time = time.perf_counter() - query_start

        cur.close()

        total_time = time.perf_counter() - start

        print(
            f"APM_TRACE endpoint=/accounts/{account_id} "
            f"connection={conn_time*1000:.2f}ms "
            f"query={query_time*1000:.2f}ms "
            f"total={total_time*1000:.2f}ms",
            flush=True
        )

        if not row:
            return jsonify({"error": "Account not found"}), 404

        return jsonify({
            "id": row[0],
            "accountNumber": row[1],
            "balance": float(row[2])
        })

    finally:
        db_pool.putconn(conn)

@app.route("/transactions/<int:account_id>")
def transactions(account_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, amount, transaction_type
        FROM transactions
        WHERE account_id = %s
        ORDER BY id DESC
        LIMIT 100
        """,
        (account_id,)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {
            "id": r[0],
            "amount": float(r[1]),
            "type": r[2]
        }
        for r in rows
    ])

@app.route("/transfer", methods=["POST"])
def transfer():
    data = request.json
    time.sleep(0.05)

    return jsonify({
        "status": "SUCCESS",
        "reference": "TRX-" + str(int(time.time()))
    })

@app.route("/transactions/search")
def search_transactions():
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id, account_id, amount, transaction_type
            FROM transactions
            WHERE amount > 900000
            LIMIT 100
            """
        )

        rows = cur.fetchall()

        return jsonify([
            {
                "id": r[0],
                "accountId": r[1],
                "amount": float(r[2]),
                "type": r[3]
            }
            for r in rows
        ])

    finally:
        cur.close()
        release_db(conn)

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {
        'Content-Type': CONTENT_TYPE_LATEST
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
