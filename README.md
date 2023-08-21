# CMIMS_

This project is a web application built using Flask that serves as an inventory management and sales tracking system. It allows users to register, log in, and manage products, as well as track sales and generate PDF bills. The application utilizes SQLAlchemy for database management, Werkzeug for password hashing, and Plotly for interactive sales reports. Additionally, Bootstrap is used to enhance the user interface.

## Features

- User Registration and Login: Users can register with different roles (admin or regular user) and log in to access their respective profiles.

- Product Management: Admin users can add, edit, and delete products in the inventory.

- Cashier Interface: Users can perform product sales transactions, including specifying the quantity and buyer's name.

- PDF Bill Generation: The application generates PDF bills for each sale transaction, providing a record for both the cashier and the buyer.

- Sales History: Users can view a history of all sales, including product details and transaction information.

- Statistics and Graphs: The application displays interactive graphs using Plotly to visualize product sales and inventory statistics.

- Bootstrap UI: The project uses Bootstrap for responsive and visually appealing HTML interfaces.

## Tech Stacks and Libraries Used

- Flask
- SQLAlchemy
- Flask-SQLAlchemy
- Werkzeug
- pdfkit
- plotly
- secrets
- os
- datetime
- Bootstrap

## Usage

1. Clone the repository to your local machine.
2. Install the required Python packages using `pip install -r requirements.txt`.
3. Run the application with `python app.py`.


