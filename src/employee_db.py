"""Employee Database — CSV-backed employee registry."""

import csv
import os
from dataclasses import dataclass, fields
from pathlib import Path

APP_DATA_DIR = Path(os.environ.get("APPDATA", ".")) / "PayslipApp"


@dataclass
class Employee:
    id: str       # 9-digit Israeli ID
    name: str     # Full name (Hebrew)
    email: str
    phone: str    # Optional, for reference


def get_csv_path() -> Path:
    """Return path to employees.csv, creating directory if needed."""
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return APP_DATA_DIR / "employees.csv"


def load_employees() -> dict[str, Employee]:
    """Load employees from CSV. Returns dict keyed by ID string."""
    csv_path = get_csv_path()
    employees = {}

    if not csv_path.exists():
        # Create empty CSV with headers
        _write_csv_headers(csv_path)
        return employees

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            emp = Employee(
                id=row["id"].strip(),
                name=row["name"].strip(),
                email=row["email"].strip(),
                phone=row.get("phone", "").strip(),
            )
            employees[emp.id] = emp

    return employees


def save_employees(employees: dict[str, Employee]) -> None:
    """Write full employee dict to CSV."""
    csv_path = get_csv_path()
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "email", "phone"])
        writer.writeheader()
        for emp in employees.values():
            writer.writerow({
                "id": emp.id,
                "name": emp.name,
                "email": emp.email,
                "phone": emp.phone,
            })


def add_employee(employees: dict[str, Employee], emp: Employee) -> None:
    """Add an employee and save."""
    employees[emp.id] = emp
    save_employees(employees)


def update_employee(employees: dict[str, Employee], emp: Employee) -> None:
    """Update an existing employee and save."""
    employees[emp.id] = emp
    save_employees(employees)


def delete_employee(employees: dict[str, Employee], emp_id: str) -> None:
    """Delete an employee by ID and save."""
    employees.pop(emp_id, None)
    save_employees(employees)


def _write_csv_headers(csv_path: Path) -> None:
    """Create an empty CSV with just headers."""
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "email", "phone"])
        writer.writeheader()
