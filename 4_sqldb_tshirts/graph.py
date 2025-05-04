# import matplotlib.pyplot as plt
# from datetime import datetime
# import mysql.connector
# from mysql.connector import Error

# def get_db_connection(username, host, password, database):
#     try:
#         connection = mysql.connector.connect(
#             host=host,
#             database=database,
#             user=username,
#             password=password
#         )
#         if connection.is_connected():
#             print("Connected to MySQL database")
#             return connection
#         else:
#             raise Exception("Failed to connect to database.")
#     except Error as e:
#         raise Exception(f"Failed to connect to database: {e}")

# def get_accuracy_history():
#     cursor = None
#     db_connection = None
#     try:
#         db_connection = get_db_connection(username='root', host='localhost', 
#                                         password='password', database='universitymanagement')
#         cursor = db_connection.cursor(dictionary=True)
#         query = """
#         SELECT created_at, is_right 
#         FROM human_feedback 
#         ORDER BY created_at ASC  # Changed to ASC to get chronological order
#         LIMIT 150;  # Limit to 150 entries
#         """
#         cursor.execute(query)
#         feedback_data = cursor.fetchall()
#         accuracy_history = []
#         correct_count = 0
#         for i, feedback in enumerate(feedback_data):
#             if feedback['is_right'] == 'yes':
#                 correct_count += 1
#             accuracy_history.append((correct_count / (i + 1)) * 100)
#         return accuracy_history
#     except Exception as e:
#         print(f"Error reading query log: {e}")
#         return []
#     finally:
#         if cursor:
#             cursor.close()
#         if db_connection and db_connection.is_connected():
#             db_connection.close()

# def plot_accuracy_graph():
#     accuracy_history = get_accuracy_history()
    
#     if not accuracy_history:
#         print("No accuracy data to plot.")
#         return
    
#     plt.figure(figsize=(12, 7))
#     plt.plot(range(1, len(accuracy_history)+1), accuracy_history, 
#              marker='o', linestyle='-', color='b', markersize=4, linewidth=2)
    
#     plt.title('Model Accuracy Progression (First 150 Feedback Entries)', fontsize=14)
#     plt.xlabel('Number of Feedback Entries', fontsize=12)
#     plt.ylabel('Cumulative Accuracy (%)', fontsize=12)
#     plt.grid(True, linestyle='--', alpha=0.7)
#     plt.ylim(0, 100)
#     plt.xlim(0, 150)
    
#     # Add reference lines for your target points
#     target_points = [(0, 0), (30, 30), (60, 55), (90, 70), (120, 75), (150, 86)]
#     for x, y in target_points:
#         plt.scatter(x, y, color='red', s=80, zorder=5)
#         plt.text(x+2, y-3, f'Target: {y}%', fontsize=10, color='red')
    
#     # Final accuracy annotation
#     final_accuracy = accuracy_history[-1]
#     plt.annotate(f'Final Accuracy: {final_accuracy:.1f}%', 
#                  xy=(150, final_accuracy),
#                  xytext=(10, 10), textcoords='offset points',
#                  bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
#                  arrowprops=dict(arrowstyle='->'))
    
#     # Add horizontal line at final accuracy
#     plt.axhline(y=final_accuracy, color='green', linestyle=':', alpha=0.5)
    
#     plt.tight_layout()
#     plt.show()

# plot_accuracy_graph()
# # -------------------------------------------------------------------------------------

import matplotlib.pyplot as plt
from datetime import datetime
import mysql.connector
from mysql.connector import Error

def get_db_connection(username, host, password, database):
    try:
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=username,
            password=password
        )
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
        else:
            raise Exception("Failed to connect to database.")
    except Error as e:
        raise Exception(f"Failed to connect to database: {e}")

# Function to get accuracy history
def get_accuracy_history():
    try:
        db_connection = get_db_connection(username='root', host='localhost', password='password', database='universitymanagement')
        cursor = db_connection.cursor(dictionary=True)
        query = """
        SELECT is_right 
        FROM universitymanagement.human_feedback 
        ORDER BY id ASC ;
        """
        cursor.execute(query)
        feedback_data = cursor.fetchall()
        # print(feedback_data)
        accuracy_history = [(0,0)]
        
        for j in range(30, len(feedback_data)+1, 30):
            correct_count = 0
            temp_data = feedback_data[j-30:j]
            print(temp_data)
            for i, feedback in enumerate(temp_data):
                if feedback['is_right'] == 'yes':
                    correct_count += 1
            accuracy_history.append((j,(correct_count / 30) * 100))
        return accuracy_history
    except Exception as e:
        print(f"Error reading query log: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if db_connection:
            db_connection.close()


import matplotlib.pyplot as plt

def plot_custom_accuracy_graph():
    # Your specified data points: (training_number, accuracy)
    # data_points = [
    #     (0, 0),
    #     (30, 30),
    #     (60, 55),
    #     (90, 70),
    #     (120, 75),
    #     (150, 86)
    # ]
    data_points= get_accuracy_history()
    print(data_points)
    # Separate x and y values
    training_numbers = [point[0] for point in data_points]
    accuracies = [point[1] for point in data_points]
    
    plt.figure(figsize=(10, 6))
    plt.plot(training_numbers, accuracies, marker='o', linestyle='-', color='b', linewidth=2)
    
    plt.title('Model Accuracy During Training')
    plt.xlabel('Number of Training Iterations')
    plt.ylabel('Accuracy (%)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.ylim(0, 100)  # Set y-axis from 0% to 100%
    
    # Highlight the final accuracy
    final_point = data_points[-1]
    plt.annotate(f'Final Accuracy: {final_point[1]}%', 
                 xy=final_point,
                 xytext=(10, 10), 
                 textcoords='offset points',
                 bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                 arrowprops=dict(arrowstyle='->'))
    
    # Add data labels for each point
    for x, y in data_points:
        plt.text(x, y+3, f'{y}%', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.show()

# Call the function to plot your graph
plot_custom_accuracy_graph()


# ---------------------------
# import matplotlib.pyplot as plt
# import mysql.connector
# from mysql.connector import Error

# def get_db_connection(username, host, password, database):
#     try:
#         connection = mysql.connector.connect(
#             host=host,
#             database=database,
#             user=username,
#             password=password
#         )
#         if connection.is_connected():
#             print("Connected to MySQL database")
#             return connection
#         else:
#             raise Exception("Failed to connect to database.")
#     except Error as e:
#         raise Exception(f"Failed to connect to database: {e}")

# def get_accuracy_history():
#     cursor = None
#     db_connection = None
#     try:
#         db_connection = get_db_connection(username='root', host='localhost', 
#                                         password='password', database='universitymanagement')
#         cursor = db_connection.cursor(dictionary=True)
#         query = """
#         SELECT is_right 
#         FROM editedbynanbu 
#         ORDER BY id DESC
#         LIMIT 150;
#         """
#         cursor.execute(query)
#         feedback_data = cursor.fetchall()
#         accuracy_history = []
#         correct_count = 0
#         for i, feedback in enumerate(feedback_data):
#             if feedback['is_right'] == 'yes':
#                 correct_count += 1
#             accuracy_history.append((correct_count / (i + 1)) * 100)
#         return accuracy_history
#     except Exception as e:
#         print(f"Error reading query log: {e}")
#         return []
#     finally:
#         if cursor:
#             cursor.close()
#         if db_connection and db_connection.is_connected():
#             db_connection.close()

# def plot_accuracy_comparison():
#     # Your target data points
#     target_points = [(0, 0), (30, 30), (60, 55), (90, 70), (120, 75), (150, 86)]
#     target_x = [point[0] for point in target_points]
#     target_y = [point[1] for point in target_points]
    
#     # Get actual accuracy history
#     actual_history = get_accuracy_history()
#     actual_x = list(range(len(actual_history)))
    
#     plt.figure(figsize=(12, 7))
    
#     # Plot target progression (your desired style)
#     plt.plot(target_x, target_y, marker='o', linestyle='--', color='red', 
#              linewidth=2, markersize=8, label='Target Accuracy')
    
#     # Plot actual accuracy
#     plt.plot(actual_x, actual_history, marker='', linestyle='-', color='blue',
#              linewidth=2, label='Actual Accuracy')
    
#     plt.title('Model Accuracy: Target vs Actual Performance', fontsize=14)
#     plt.xlabel('Number of Feedback Entries', fontsize=12)
#     plt.ylabel('Cumulative Accuracy (%)', fontsize=12)
#     plt.grid(True, linestyle='--', alpha=0.5)
#     plt.ylim(0, 100)
#     plt.xlim(0, 150)
#     plt.legend(loc='lower right')
    
#     # Annotate target points
#     for x, y in target_points:
#         plt.text(x, y+3, f'Target: {y}%', ha='center', va='bottom', color='red')
    
#     # Annotate final actual accuracy
#     if actual_history:
#         final_acc = actual_history[-1]
#         plt.annotate(f'Actual: {final_acc:.1f}%', 
#                      xy=(150, final_acc),
#                      xytext=(10, 10), textcoords='offset points',
#                      bbox=dict(boxstyle='round,pad=0.5', fc='lightblue', alpha=0.7),
#                      arrowprops=dict(arrowstyle='->'))
    
#     plt.tight_layout()
#     plt.show()

# plot_accuracy_comparison()