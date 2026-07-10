import sqlite3
import os
from typing import List, Dict, Optional, Tuple

class Database:
    def __init__(self, db_path: str = "stock_bot.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 유저 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                money INTEGER DEFAULT 1000000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 주식 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                current_price INTEGER NOT NULL,
                previous_price INTEGER DEFAULT 0,
                initial_price INTEGER NOT NULL,
                min_change_rate REAL NOT NULL,
                max_change_rate REAL NOT NULL,
                change_interval INTEGER NOT NULL,
                volume INTEGER DEFAULT 0,
                high_price INTEGER DEFAULT 0,
                low_price INTEGER DEFAULT 0,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 유저 보유 주식 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stock_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                average_price INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (stock_name) REFERENCES stocks(name),
                UNIQUE(user_id, stock_name)
            )
        ''')
        
        # 가격 히스토리 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_name TEXT NOT NULL,
                price INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stock_name) REFERENCES stocks(name)
            )
        ''')
        
        # 거래 내역 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stock_name TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price INTEGER NOT NULL,
                total_amount INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (stock_name) REFERENCES stocks(name)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_or_create_user(self, user_id: int) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT money FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result is None:
            cursor.execute('INSERT INTO users (user_id, money) VALUES (?, 1000000)', (user_id,))
            conn.commit()
            money = 1000000
        else:
            money = result[0]
        
        conn.close()
        return money
    
    def get_user_money(self, user_id: int) -> int:
        return self.get_or_create_user(user_id)
    
    def update_user_money(self, user_id: int, amount: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        current_money = self.get_user_money(user_id)
        new_money = current_money + amount
        
        if new_money < 0:
            conn.close()
            return False
        
        cursor.execute('UPDATE users SET money = ? WHERE user_id = ?', (new_money, user_id))
        conn.commit()
        conn.close()
        return True
    
    def get_user_stocks(self, user_id: int) -> Dict[str, int]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT stock_name, quantity FROM user_stocks WHERE user_id = ?', (user_id,))
        stocks = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        return stocks
    
    def get_user_stock_quantity(self, user_id: int, stock_name: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT quantity FROM user_stocks WHERE user_id = ? AND stock_name = ?', (user_id, stock_name))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else 0
    
    def update_user_stock(self, user_id: int, stock_name: str, quantity_change: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        current_quantity = self.get_user_stock_quantity(user_id, stock_name)
        new_quantity = current_quantity + quantity_change
        
        if new_quantity < 0:
            conn.close()
            return False
        
        if current_quantity == 0:
            cursor.execute('INSERT INTO user_stocks (user_id, stock_name, quantity) VALUES (?, ?, ?)', 
                         (user_id, stock_name, new_quantity))
        elif new_quantity == 0:
            cursor.execute('DELETE FROM user_stocks WHERE user_id = ? AND stock_name = ?', 
                         (user_id, stock_name))
        else:
            cursor.execute('UPDATE user_stocks SET quantity = ? WHERE user_id = ? AND stock_name = ?', 
                         (new_quantity, user_id, stock_name))
        
        conn.commit()
        conn.close()
        return True
    
    def create_stock(self, name: str, price: int, min_change: float, max_change: float, interval: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO stocks (name, current_price, initial_price, min_change_rate, max_change_rate, change_interval)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, price, price, min_change, max_change, interval))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def delete_stock(self, name: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM user_stocks WHERE stock_name = ?', (name,))
        cursor.execute('DELETE FROM stocks WHERE name = ?', (name,))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    
    def get_stock(self, name: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, current_price, initial_price, min_change_rate, max_change_rate, change_interval, last_update
            FROM stocks WHERE name = ?
        ''', (name,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return {
                'name': result[0],
                'current_price': result[1],
                'initial_price': result[2],
                'min_change_rate': result[3],
                'max_change_rate': result[4],
                'change_interval': result[5],
                'last_update': result[6]
            }
        return None
    
    def get_all_stocks(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, current_price, initial_price, min_change_rate, max_change_rate, change_interval, last_update
            FROM stocks
        ''')
        
        stocks = []
        for row in cursor.fetchall():
            stocks.append({
                'name': row[0],
                'current_price': row[1],
                'initial_price': row[2],
                'min_change_rate': row[3],
                'max_change_rate': row[4],
                'change_interval': row[5],
                'last_update': row[6]
            })
        
        conn.close()
        return stocks
    
    def update_stock_price(self, name: str, new_price: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE stocks SET current_price = ?, last_update = CURRENT_TIMESTAMP WHERE name = ?', 
                     (new_price, name))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    
    def update_stock_last_update(self, name: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE stocks SET last_update = CURRENT_TIMESTAMP WHERE name = ?', (name,))
        conn.commit()
        conn.close()
    
    def add_price_history(self, stock_name: str, price: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('INSERT INTO price_history (stock_name, price) VALUES (?, ?)', (stock_name, price))
        conn.commit()
        conn.close()
    
    def get_price_history(self, stock_name: str, limit: int = 100) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT price, timestamp FROM price_history 
            WHERE stock_name = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (stock_name, limit))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'price': row[0],
                'timestamp': row[1]
            })
        
        conn.close()
        return history
    
    def add_transaction(self, user_id: int, stock_name: str, transaction_type: str, quantity: int, price: int, total_amount: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transactions (user_id, stock_name, transaction_type, quantity, price, total_amount)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, stock_name, transaction_type, quantity, price, total_amount))
        conn.commit()
        conn.close()
    
    def get_user_transactions(self, user_id: int, limit: int = 50) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT stock_name, transaction_type, quantity, price, total_amount, timestamp
            FROM transactions 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        transactions = []
        for row in cursor.fetchall():
            transactions.append({
                'stock_name': row[0],
                'transaction_type': row[1],
                'quantity': row[2],
                'price': row[3],
                'total_amount': row[4],
                'timestamp': row[5]
            })
        
        conn.close()
        return transactions
    
    def update_stock_with_history(self, name: str, new_price: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 현재 정보 가져오기
        cursor.execute('SELECT current_price, high_price, low_price FROM stocks WHERE name = ?', (name,))
        result = cursor.fetchone()
        
        if result:
            current_price, high_price, low_price = result
            
            # 이전 가격 저장
            previous_price = current_price
            
            # 최고가/최저가 업데이트
            new_high = max(high_price, new_price) if high_price > 0 else new_price
            new_low = min(low_price, new_price) if low_price > 0 else new_price
            
            # 주식 정보 업데이트
            cursor.execute('''
                UPDATE stocks 
                SET current_price = ?, previous_price = ?, high_price = ?, low_price = ?, last_update = CURRENT_TIMESTAMP
                WHERE name = ?
            ''', (new_price, previous_price, new_high, new_low, name))
            
            # 가격 히스토리 추가
            cursor.execute('INSERT INTO price_history (stock_name, price) VALUES (?, ?)', (name, new_price))
            
            # 거래량 증가
            cursor.execute('UPDATE stocks SET volume = volume + 1 WHERE name = ?', (name,))
        
        conn.commit()
        conn.close()
    
    def get_stock_extended(self, name: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, current_price, previous_price, initial_price, min_change_rate, max_change_rate, 
                   change_interval, volume, high_price, low_price, last_update
            FROM stocks WHERE name = ?
        ''', (name,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return {
                'name': result[0],
                'current_price': result[1],
                'previous_price': result[2],
                'initial_price': result[3],
                'min_change_rate': result[4],
                'max_change_rate': result[5],
                'change_interval': result[6],
                'volume': result[7],
                'high_price': result[8],
                'low_price': result[9],
                'last_update': result[10]
            }
        return None
