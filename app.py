from flask import Flask, jsonify, request
from mysql.connector import connect, Error

app = Flask(__name__)

# Database configuration
db_config = {
    'host': 'localhost',
    'port': 8000,  # Replace with the appropriate port
    'user': 'root',
    'password': 'Shiva@1234',
    'database': 'foodie_haven',
}

def get_db_connection():
    try:
        connection = connect(**db_config)
        return connection
    except Error as e:
        print(f"Error connecting to the database: {e}")
        return None
    


def is_snack_available(snack_id):
    connection = get_db_connection()
    
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT availability FROM snacks WHERE id = %s", (snack_id,))
        result = cursor.fetchone()
        connection.close()
        return result and result[0]  
    
    return False

def check_sale_id_exists(sale_id):
    try:
        # Database configuration
        db_config = {
        'host': 'localhost',
        'port': 8000,  # Replace with the appropriate port
        'user': 'root',
        'password': 'Shiva@1234',
        'database': 'foodie_haven',
        }
        
        # Establish a database connection
        connection = connect(**db_config)
        
        if connection:
            cursor = connection.cursor()
            
            # Check if the sale ID exists in the snack_sales table
            cursor.execute("SELECT COUNT(*) FROM snack_sales WHERE sale_id = %s", (sale_id,))
            sale_exists = cursor.fetchone()[0]
            
            connection.close()
            return sale_exists > 0  # True if sale ID exists, False if not
        
        return False  # Failed to connect to the database
    except Error as e:
        print(f"Error checking sale ID existence: {e}")
        return False


@app.route('/')
def index():
    connection = get_db_connection()
    
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM snacks")
        data = cursor.fetchall()
        connection.close()
        return data
    
    return "Failed to connect to the database."

@app.route('/add_snack', methods=['POST'])
def add_snack():
    data = request.get_json()
    
    if 'name' not in data or 'price' not in data or 'availability' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    connection = get_db_connection()
    
    if connection:
        cursor = connection.cursor()
        insert_query = "INSERT INTO snacks (name, price, availability) VALUES (%s, %s, %s)"
        insert_data = (data['name'], data['price'], data['availability'])
        
        try:
            cursor.execute(insert_query, insert_data)
            connection.commit()
            connection.close()
            return jsonify({"message": "Snack added successfully"}), 201
        except Error as e:
            connection.rollback()
            connection.close()
            return jsonify({"error": f"Failed to add snack: {e}"}), 500
    
    return jsonify({"error": "Failed to connect to the database"}), 500

@app.route('/delete_snack/<int:snack_id>', methods=['DELETE'])
def delete_snack(snack_id):
    connection = get_db_connection()
    
    if connection:
        cursor = connection.cursor()
        delete_query = "DELETE FROM snacks WHERE id = %s"
        
        try:
            cursor.execute(delete_query, (snack_id,))
            connection.commit()
            connection.close()
            return jsonify({"message": "Snack deleted successfully"}), 200
        except Error as e:
            connection.rollback()
            connection.close()
            return jsonify({"error": f"Failed to delete snack: {e}"}), 500
    
    return jsonify({"error": "Failed to connect to the database"}), 500

@app.route('/update_availability/<int:dish_id>', methods=['PUT'])
def update_availability(dish_id):
    data = request.get_json()
    
    if 'availability' not in data:
        return jsonify({"error": "Missing 'availability' field in request data"}), 400
    
    new_availability = data['availability']
    
    connection = get_db_connection()
    
    if connection:
        cursor = connection.cursor()
        update_query = "UPDATE snacks SET availability = %s WHERE id = %s"
        
        try:
            cursor.execute(update_query, (new_availability, dish_id))
            connection.commit()
            connection.close()
            return jsonify({"message": "Availability updated successfully"}), 200
        except Error as e:
            connection.rollback()
            connection.close()
            return jsonify({"error": f"Failed to update availability: {e}"}), 500
    
    return jsonify({"error": "Failed to connect to the database"}), 500




@app.route('/record_sale', methods=['POST'])
def record_sale():
    data = request.get_json()
    
    if 'snack_id' not in data or 'customer_name' not in data or 'quantity_sold' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    snack_id = data['snack_id']
    customer_name = data['customer_name']
    quantity_sold = data['quantity_sold']
    
    if not is_snack_available(snack_id):
        return jsonify({"error": "Snack is not available"}), 400
    
    connection = get_db_connection()
    
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT name, price FROM snacks WHERE id = %s", (snack_id,))
        result = cursor.fetchone()
        
        if result:
            snack_name, price = result
            sale_amount = price * quantity_sold
            
            insert_query = "INSERT INTO snack_sales (snack_id, customer_name, snack_name, quantity_sold, sale_amount, timestamp, status) VALUES (%s, %s, %s, %s, %s, NOW(), %s)"
            insert_data = (snack_id, customer_name, snack_name, quantity_sold, sale_amount, "received")
            
            try:
                cursor.execute(insert_query, insert_data)
                connection.commit()
                connection.close()
                return jsonify({"message": "Sale recorded successfully"}), 201
            except Error as e:
                connection.rollback()
                connection.close()
                return jsonify({"error": f"Failed to record sale: {e}"}), 500
    
    return jsonify({"error": "Failed to connect to the database"}), 500


@app.route('/sales')
def get_sales():
    connection = get_db_connection()
    
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM snack_sales")
        sales_data = cursor.fetchall()
        connection.close()
        return jsonify(sales_data)
    
    return jsonify({"error": "Failed to connect to the database"}), 500


@app.route('/update_status/<int:sale_id>/<status>', methods=['PUT'])
def update_status(sale_id, status):
    allowed_statuses = ["received", "ready for pickup", "delivered"]
    if status not in allowed_statuses:
        return jsonify({"error": "Invalid status"}), 400
    
    # Check if the sale ID exists
    if not check_sale_id_exists(sale_id):
        return jsonify({"error": "Sale ID not found"}), 404
    
    connection = get_db_connection()
    
    if connection:
        cursor = connection.cursor()
        
        # Update the status
        update_query = "UPDATE snack_sales SET status = %s WHERE sale_id = %s"
        
        try:
            cursor.execute(update_query, (status, sale_id))
            connection.commit()
            connection.close()
            return jsonify({"message": "Order status updated successfully"}), 200
        except Error as e:
            connection.rollback()
            connection.close()
            return jsonify({"error": f"Failed to update order status: {e}"}), 500
    
    return jsonify({"error": "Failed to connect to the database"}), 500





@app.route('/available_snacks')
def get_available_snacks():
    connection = get_db_connection()
    
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM snacks WHERE availability = 1")
        available_snacks = cursor.fetchall()
        connection.close()
        return jsonify(available_snacks)
    
    return jsonify({"error": "Failed to connect to the database"}), 500





@app.route('/filter_sales')
def filter_sales_by_status():
    # Get the desired order status from query parameters
    status = request.args.get('status')

    allowed_statuses = ["received", "ready for pickup", "delivered"]
    if status not in allowed_statuses:
        return jsonify({"error": "Invalid status"}), 400

    connection = get_db_connection()
    
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM snack_sales WHERE status = %s", (status,))
        filtered_sales = cursor.fetchall()
        connection.close()
        return jsonify(filtered_sales)
    
    return jsonify({"error": "Failed to connect to the database"}), 500



@app.route('/total_sales')
def get_total_sales():
    connection = get_db_connection()
    
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT SUM(sale_amount) FROM snack_sales")
        total_sales = cursor.fetchone()[0] or 0  
        connection.close()
        return jsonify({"total_sales": total_sales})
    
    return jsonify({"error": "Failed to connect to the database"}), 500




if __name__ == '__main__':
    app.run()




# GENAI_B29