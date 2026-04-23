from datetime import datetime, timedelta

class Book:
    """
    Represents a single book in the library system.
    Supports multiple copies, issued records, reservation queue, and fine calculation.
    """

    book_counter = 1000  # Unique ID generator

    def __init__(self, title, author, isbn="", category="General", publisher=None, year=None, copies=1, max_issue_days=15, late_fee_per_day=500):
        # Unique book ID
        self.id = Book.book_counter
        Book.book_counter += 1

        # Book details
        self.title = title
        self.author = author
        self.isbn = isbn
        self.category = category
        self.publisher = publisher
        self.year = year
        self.copies = copies

        # Issued and reservation tracking
        self.issued_records = []  # [{"member_id", "issue_date", "due_date", "fine"}]
        self.reservation_queue = []  # member_ids waiting

        # Library policies
        self.max_issue_days = max_issue_days
        self.late_fee_per_day = late_fee_per_day  # ₹500 per day

    @property
    def available_copies(self):
        """Return number of copies available for issuing."""
        return self.copies - len(self.issued_records)

    @property
    def status(self):
        """Current status string."""
        if self.issued_records:
            return f"Issued ({len(self.issued_records)} issued, {self.available_copies} available)"
        elif self.reservation_queue:
            return f"Reserved ({len(self.reservation_queue)} waiting, {self.available_copies} available)"
        else:
            return f"Available ({self.available_copies})"

    def issue_book(self, member_id, from_queue=False):
        """
        Issue a book to a member.
        If no copies are available, add member to reservation queue (unless called from queue).
        """
        if self.available_copies <= 0:
            if not from_queue and member_id not in self.reservation_queue:
                self.reservation_queue.append(member_id)
                return False, f"No copies available. {member_id} added to reservation queue."
            return False, "No copies available."

        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=self.max_issue_days)

        self.issued_records.append({
            "member_id": member_id,
            "issue_date": issue_date,
            "due_date": due_date,
            "fine": 0
        })

        return True, f"Book issued to {member_id}. Issue: {issue_date.strftime('%d-%m-%Y')} | Due: {due_date.strftime('%d-%m-%Y')}"

    def return_book(self, member_id):
        """
        Return a book issued to a member.
        Calculates fine if overdue and auto-issues to next in reservation queue.
        """
        record = next((r for r in self.issued_records if r["member_id"] == member_id), None)
        if not record:
            return False, 0, "Book was not issued to this member."

        # Calculate fine per overdue day
        overdue_days = (datetime.now() - record["due_date"]).days
        overdue_fee = self.late_fee_per_day * overdue_days if overdue_days > 0 else 0

        # Remove record
        self.issued_records.remove(record)

        # Auto-issue to reservation queue
        i = 0
        while self.available_copies > 0 and i < len(self.reservation_queue):
            next_member = self.reservation_queue.pop(0)
            issued, msg = self.issue_book(next_member, from_queue=True)
            i += 1

        return True, overdue_fee, f"Book returned successfully. Overdue fee: {overdue_fee}"

    def reserve_member_list(self):
        """Return current reservation queue."""
        return self.reservation_queue.copy()

    def to_dict(self):
        """
        Return a dictionary representation for GUI/API use.
        """
        first_record = self.issued_records[0] if self.issued_records else None
        issue_date_str = first_record["issue_date"].strftime("%d-%m-%Y") if first_record else ""
        due_date_str = first_record["due_date"].strftime("%d-%m-%Y") if first_record else ""

        return {
            "ID": self.id,
            "Title": self.title,
            "Author": self.author,
            "ISBN": self.isbn,
            "Category": self.category,
            "Publisher": self.publisher or "",
            "Year": self.year or "",
            "Status": self.status,
            "Total Copies": self.copies,
            "Available Copies": self.available_copies,
            "Issue Date": issue_date_str,
            "Due Date": due_date_str
        }

    def __str__(self):
        pub_year = f"{self.publisher}, {self.year}" if self.publisher and self.year else ""
        return f"[{self.id}] {self.title} by {self.author} ({self.category}) {pub_year} - {self.status}"

    # Additional helper for searching
    def matches_query(self, query):
        """
        Check if book matches a search query by title, author, ISBN or ID.
        """
        query_lower = str(query).lower()
        return (query_lower in self.title.lower() or
                query_lower in self.author.lower() or
                query_lower in str(self.id) or
                query_lower in self.isbn.lower())

