# Book Store Management System


A web application developed with **Python Flask**, **Bootstrap 5**, and **SQLite / MySQL**, designed to automate book store operations, inventory management, point-of-sale (POS) billing, and sales reporting as specified in the software engineering project document.

---

## 1. Project Overview & Stakeholders

### 1.1 Problem Statement
In traditional book stores, books, stock, and sales are recorded manually in registers or spreadsheets. This process is time-consuming and leads to billing errors, incorrect stock counts, loss of records, and difficulty in generating sales reports.  
This system automates:
- Book inventory tracking and low-stock alerts
- Fast book catalog search and availability checks
- Point-of-Sale (POS) counter billing with automatic stock reduction
- Book returns processing and automatic inventory restocking
- Analytical sales and revenue reporting
- Role-based security access control

### 1.2 Stakeholders & Roles
| Role | Default Username | Default Password | Responsibilities |
|---|---|---|---|
| **System Administrator** | `admin` | `admin123` | Manage books, categories, suppliers, staff accounts, view reports |
| **Store Manager** | `manager` | `manager123` | View sales reports, monitor stock levels, manage replenishment |
| **Sales Staff / Cashier** | `staff` | `staff123` | POS counter billing, item search, discounts, process returns |
| **Customer** | `customer` | `customer123` | Search catalog, check stock availability/price, cart, order history |

---

## 2. Bill Calculation Formula (Section 4.3)

$$\text{Net Amount} = (\text{Price} \times \text{Quantity}) - \text{Discount} + \text{Tax}$$

- **Gross Amount**: $\text{Price} \times \text{Quantity}$
- **Discount**: Configurable percentage or automatic 5% special store discount on orders $\ge$ ₹1,000
- **Tax / GST**: 5% standard rate applied after discount deduction
- **Net Amount**: Final payable sum auto-calculated on POS counter and invoice receipts

---

## 3. Project Directory Structure

```text
BookStoreManagement/
├── app.py                 # Core Flask application & routes (POS, Admin, Manager, Customer)
├── config.py              # Configuration settings (Database URI, Secret Keys)
├── forms.py               # Flask-WTF forms for Books, Categories, Suppliers, Staff, Returns
├── requirements.txt       # Python dependencies (Flask, SQLAlchemy, Flask-Login, WTForms)
├── test_system.py         # Automated test suite covering Test Cases TC01 through TC10
├── schema_mysql.sql       # Optional MySQL DDL script with seed data
├── static/
│   └── style.css          # Design system & print styling
└── templates/
    ├── base.html          # Responsive base layout with role-based navigation
    ├── index.html         # Book catalog with search, category filters, and stock badges
    ├── book_detail.html   # Book details, stock check & add-to-cart
    ├── cart.html          # Shopping cart & checkout with live formula breakdown
    ├── pos.html           # Dedicated Sales Staff Point-of-Sale (POS) billing counter
    ├── returns.html       # Book return processing & inventory restocking
    ├── reports.html       # Store Manager sales & revenue analytical reports
    ├── stock.html         # Stock monitoring and low-stock replenishment
    ├── admin.html         # System Administrator dashboard
    ├── categories.html    # Category CRUD management
    ├── suppliers.html     # Supplier / Publisher management
    ├── staff_manage.html  # Staff accounts creation & role assignment
    ├── book_form.html     # Add / Edit book modal and form
    ├── customer_orders.html # Customer order history & receipts
    ├── 
    ├── login.html         # Login with 1-click demo role credentials
    └── register.html      # Registration with role selection
```

---

## 4. How to Run the Application

### Step 1: Open Terminal & Navigate to Project
```powershell
cd C:\Users\naden\.gemini\antigravity\scratch\BookStoreManagement
```

### Step 2: Activate Virtual Environment (or create one)
```powershell
.\venv\Scripts\Activate.ps1
# Or: python -m venv venv; .\venv\Scripts\activate
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run the Flask Web Application
```powershell
python app.py
```
Open your web browser and visit: **`http://127.0.0.1:5000/`**

---

## 5. Verification & Testing (Section 5)

Run the included automated test runner to verify all 10 project test cases:
```powershell
python test_system.py
```

### Test Case Matrix:
| Test ID | Test Case | Expected Result | Status |
|---|---|---|---|
| **TC01** | Enter valid username/password | Login successful | **PASS** |
| **TC02** | Enter invalid password | Error message | **PASS** |
| **TC03** | Add book | Book added | **PASS** |
| **TC04** | Search book by title | Matching books displayed | **PASS** |
| **TC05** | Add book to cart | Cart updated | **PASS** |
| **TC06** | Generate bill | Correct total displayed | **PASS** |
| **TC07** | Complete a sale | Stock reduced | **PASS** |
| **TC08** | Sell more than available stock | Error message | **PASS** |
| **TC09** | Generate sales report | Report displayed | **PASS** |
| **TC10** | Unauthorized user accesses page | Access denied | **PASS** |

---

## 6. Optional: MySQL Setup
If you want to use MySQL instead of the default zero-config SQLite:
1. Import `schema_mysql.sql` into MySQL Server (using MySQL Workbench, phpMyAdmin, or MySQL CLI).
2. Set your environment variable:
   ```powershell
   $env:DATABASE_URL="mysql+pymysql://username:password@localhost/bookstore_db"
   ```
3. Run `python app.py`.
