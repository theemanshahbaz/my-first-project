from datetime import datetime
from backendddd.book import Book

class Library:
    """
    Library system with members, books, fines, reservation queue, and multiple copies support.
    """

    def __init__(self):
        self.books = []  # List of Book objects
        self.members = {}  # member_id: {name, type, department, cnic, phone, books[], total_fines}

    # Add book
    def add_book(self, book: Book):
        self.books.append(book)
        return f"Book '{book.title}' added successfully."

    # Add member
    def add_member(self, member_id, name, is_university=True, department="", university_id="", cnic="", phone=""):
        if member_id in self.members:
            return "Member ID already exists."

        if is_university:
            if not university_id or not name:
                return "University ID and Name are required for university members."
            member_info = {
                "name": name,
                "type": "university",
                "department": department,
                "university_id": university_id,
                "books": [],
                "total_fines": 0
            }
        else:
            if not cnic or not phone or not name:
                return "CNIC, Phone, and Name are required for non-university members."
            member_info = {
                "name": name,
                "type": "non-university",
                "cnic": cnic,
                "phone": phone,
                "books": [],
                "total_fines": 0
            }

        self.members[member_id] = member_info
        return f"Member '{name}' added successfully with ID {member_id}."

    # Find book by ISBN or ID
    def find_book(self, query):
        return next((b for b in self.books if b.matches_query(query)), None)

    # Issue book
    def issue_book(self, query, member_id):
        if member_id not in self.members:
            return "Member ID does not exist."

        book = self.find_book(query)
        if not book:
            return "Book not found."

        success, msg = book.issue_book(member_id)
        if success:
            if book not in self.members[member_id]["books"]:
                self.members[member_id]["books"].append(book)
        return msg

    # Return book
    def return_book(self, query, member_id):
        book = self.find_book(query)
        if not book:
            return "Book not found."

        returned, fine, msg = book.return_book(member_id)
        if returned:
            if book in self.members[member_id]["books"]:
                self.members[member_id]["books"].remove(book)
            if fine > 0:
                self.members[member_id]["total_fines"] += fine
                return f"{msg} Total fines: {self.members[member_id]['total_fines']}"
        return msg

    # Books issued to a member
    def member_books(self, member_id):
        if member_id not in self.members:
            return []
        return self.members[member_id]["books"]

    # Search books
    def search_books(self, query="", category=""):
        result = self.books
        if query:
            result = [b for b in result if b.matches_query(query)]
        if category:
            result = [b for b in result if category.lower() in b.category.lower()]
        return result

    # Library summary for dashboard / report
    def summary(self):
    total_titles = len(self.books)   # different books
    total_copies = sum(b.copies for b in self.books)  # all physical copies

    issued_books = sum(len(b.issued_records) for b in self.books)
    available_books = sum(b.available_copies for b in self.books)

    overdue_books = sum(
        1 for b in self.books
        for r in b.issued_records
        if r["due_date"] < datetime.now()
    )

    total_members = len(self.members)

    return {
        "total_titles": total_titles,
        "total_copies": total_copies,
        "issued_books": issued_books,
        "available_books": available_books,
        "overdue_books": overdue_books,
        "total_members": total_members
    }


    # Reservation list for a book
    def get_reservation_list(self, query):
        book = self.find_book(query)
        if not book:
            return []
        return book.reserve_member_list()

