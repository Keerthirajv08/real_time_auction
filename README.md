# Real-Time Auction Platform

A high-concurrency auction platform built with Django, utilizing WebSockets for real-time updates and robust database locking to ensure data integrity during simultaneous bids.

## 🚀 Features

* **Real-Time Bidding:** Live price updates pushed instantly to all connected clients using Django Channels and WebSockets.
* **Concurrency Handling:** Uses **Pessimistic Locking** (`select_for_update`) to handle race conditions when multiple users bid simultaneously.
* **Hybrid Architecture:**
    * **REST API:** Standardized endpoints for transactional actions (placing bids).
    * **WebSockets:** Efficient broadcasting for read-only updates (price changes, notifications).
* **User Authentication:** Secure signup, login, and logout functionality.
* **Audit Logging:** Tracks all bidding activities for security and debugging.
* **Dockerized:** Full stack (Web, Database, Redis) containerized for easy deployment.

## 📜 Auction Rules

The platform enforces the following strict business logic (defined in `BidService`):
1.  **Status Check:** Bids are only accepted on auctions marked as `active`.
2.  **Time Validation:** Bids are rejected if the auction `end_time` has passed.
3.  **Price Floor:** A new bid must be greater than `current_price` + `min_increment`.
4.  **Anti-Sniping (Self-Bidding):** A user cannot place a bid if they are *already* the highest bidder.
5.  **Atomic Transactions:** If any validation fails, the entire transaction rolls back, ensuring no partial data states.

## 🛠️ Tech Stack

* **Backend:** Python 3, Django 6.0
* **API:** Django REST Framework (DRF)
* **Real-Time:** Django Channels, Daphne, Redis
* **Database:** PostgreSQL (Production), SQLite (Dev fallback)
* **Infrastructure:** Docker, Docker Compose
* **Frontend:** HTML5, JavaScript (Fetch API + WebSockets), Tailwind CSS

## 📋 Prerequisites & Installation

### Option A: Running with Docker (Recommended)
You need **Docker** and **Docker Compose** installed.

1.  **Clone the repository:**
    ```bash
    git clone <repo_url>
    cd real_time_auction
    ```

2.  **Create a `.env` file:**
    ```bash
    cp .env.example .env
    # Ensure DB_HOST=db and REDIS_HOST=redis
    ```

3.  **Build and Run:**
    ```bash
    docker-compose up --build
    ```
    The app will be available at `http://localhost:8000`.

### Option B: Running Locally (Manual)
You need **Python 3.10+** and a running **Redis** instance.

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Start Redis:**
    ```bash
    docker run -p 6379:6379 -d redis
    ```

3.  **Run Migrations & Server:**
    ```bash
    python manage.py migrate
    python manage.py runserver
    ```

## 🔌 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/auctions/` | List all auctions |
| `GET` | `/api/v1/auctions/{id}/` | Get details of a specific auction |
| `POST` | `/api/v1/auctions/{id}/bid/` | Place a bid (Auth required) |

## 🧪 Architecture Overview

```mermaid
sequenceDiagram
    participant User
    participant API as Django REST API
    participant DB as PostgreSQL
    participant Redis
    participant WS as WebSocket Consumer

    User->>API: POST /bid/ (Amount: $500)
    API->>DB: Lock Row & Validate
    DB-->>API: Success
    API->>Redis: Publish "New Price: $500"
    Redis->>WS: Broadcast Event
    WS->>User: Update UI ($500)


