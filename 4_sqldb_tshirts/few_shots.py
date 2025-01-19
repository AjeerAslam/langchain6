few_shots = [
    {
        'Question': "What is the name of the department where Dr. Alan Turing is the HOD?",
        'SQLQuery': "SELECT DepartmentName FROM Departments WHERE HOD = 'Dr. Alan Turing';",
        'SQLResult': "Computer Science",
        'Answer': "Computer Science"
    },
    {
        'Question': "How many students are enrolled in the Computer Science department?",
        'SQLQuery': "SELECT COUNT(*) FROM Students WHERE DepartmentID = (SELECT DepartmentID FROM Departments WHERE DepartmentName = 'Computer Science');",
        'SQLResult': "3",
        'Answer': "3"
    },
    {
        'Question': "List the names of all courses in the Mechanical Engineering department.",
        'SQLQuery': "SELECT CourseName FROM Courses WHERE DepartmentID = (SELECT DepartmentID FROM Departments WHERE DepartmentName = 'Mechanical Engineering');",
        'SQLResult': ["Thermodynamics"],
        'Answer': ["Thermodynamics"]
    },
    {
        'Question': "What is the contact number of the professor teaching 'Data Structures'?",
        'SQLQuery': """
            SELECT p.ContactNumber 
            FROM Professors p 
            JOIN Classes c ON p.ProfessorID = c.ProfessorID 
            WHERE c.CourseID = (SELECT CourseID FROM Courses WHERE CourseName = 'Data Structures');
        """,
        'SQLResult': "9998887776",
        'Answer': "9998887776"
    },
    {
        'Question': "Which student lives at '101 Elm St'?",
        'SQLQuery': "SELECT CONCAT(FirstName, ' ', LastName) AS StudentName FROM Students WHERE Address = '101 Elm St';",
        'SQLResult': "Diana Prince",
        'Answer': "Diana Prince"
    },
    {
        'Question': "What are the titles of books available in the Computer Science department?",
        'SQLQuery': "SELECT Title FROM Library WHERE DepartmentID = (SELECT DepartmentID FROM Departments WHERE DepartmentName = 'Computer Science');",
        'SQLResult': ["Introduction to Algorithms"],
        'Answer': ["Introduction to Algorithms"]
    },
    {
        'Question': "How many books are issued to 'Alice Johnson'?",
        'SQLQuery': """
            SELECT COUNT(*) 
            FROM LibraryTransactions lt 
            JOIN Students s ON lt.StudentID = s.StudentID 
            WHERE s.FirstName = 'Alice' AND s.LastName = 'Johnson' AND lt.Status = 'Issued';
        """,
        'SQLResult': "2",
        'Answer': "2"
    },
    {
        'Question': "What is the name of the hostel where student 'Bob Smith' is allocated?",
        'SQLQuery': """
            SELECT h.HostelName 
            FROM Hostel h 
            JOIN HostelAllocation ha ON h.HostelID = ha.HostelID 
            JOIN Students s ON ha.StudentID = s.StudentID 
            WHERE s.FirstName = 'Bob' AND s.LastName = 'Smith';
        """,
        'SQLResult': "Newton Hall",
        'Answer': "Newton Hall"
    },
    {
        'Question': "How many students are currently allocated in 'Newton Hall' hostel?",
        'SQLQuery': """
            SELECT COUNT(*) 
            FROM HostelAllocation ha 
            JOIN Hostel h ON ha.HostelID = h.HostelID 
            WHERE h.HostelName = 'Newton Hall';
        """,
        'SQLResult': "5",
        'Answer': "5"
    },
    {
        'Question': "List all the professors in the Civil Engineering department.",
        'SQLQuery': "SELECT CONCAT(FirstName, ' ', LastName) AS ProfessorName FROM Professors WHERE DepartmentID = (SELECT DepartmentID FROM Departments WHERE DepartmentName = 'Civil Engineering');",
        'SQLResult': ["Dr. Gustave Eiffel"],
        'Answer': ["Dr. Gustave Eiffel"]
    }
]

