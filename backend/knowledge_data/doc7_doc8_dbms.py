DOCUMENTS = [
    {
        "document": "dbms_unit4_normalization.pdf",
        "topic": "Database Management Systems",
        "section": "Relational Design & Normalization",
        "pages": [
            {
                "page": 1,
                "text": """Unit 4: Normalization in DBMS:
4.1 Need of Normalization (Consequences of Bad Design: Insert, Update, and Delete Anomalies)
4.2 Normalization Stages: 1NF, 2NF, 3NF, BCNF.
Database normalization is a database schema design technique developed by IBM researcher E.F. Codd in the 1970s.
It decomposes large, redundant tables into smaller, well-structured relations linked via foreign keys to minimize data redundancy and undesirable anomalies."""
            },
            {
                "page": 2,
                "text": """Anomalies in Unnormalized Relational Databases:
Three major anomalies occur when a database schema is not normalized:
1. Update Anomaly: Inconsistency caused when duplicate data exists in multiple rows.
   Example: Employee table where Employee 100 has address 'Bangalore' across two department rows. If address is updated in one row but missed in the second, data becomes inconsistent."""
            },
            {
                "page": 3,
                "text": """2. Insertion Anomaly: Inability to insert legitimate data because attributes are unnaturally coupled and dependent on a missing primary key.
   Example: Cannot insert a newly hired employee who has not yet been assigned to a department if Department ID is part of the primary key.
3. Deletion Anomaly: Deleting one record inadvertently deletes unrelated, vital information.
   Example: Deleting the last employee in Department 103 deletes all existence records of Department 103 itself."""
            },
            {
                "page": 4,
                "text": """Trade-offs of Normalization:
Advantages:
1. Minimizes duplicate storage and eliminates update/delete anomalies.
2. Narrower tables with fewer columns per record page increase buffer pool cache hits.
3. Fewer indexes required per table accelerates write and update performance.
Disadvantages:
1. Highly normalized schemas require multi-table JOINs, increasing read query execution overhead.
2. Complex queries for reporting may require denormalization."""
            },
            {
                "page": 5,
                "text": """First Normal Form (1NF):
Rules:
1. Every table cell must contain a single, atomic value (no multi-valued sets or comma-separated lists).
2. Each record in the table must be unique.
Example: If an employee record has Department: 'Marketing, Sales', it violates 1NF because it contains multiple values in a single cell."""
            },
            {
                "page": 6,
                "text": """Achieving 1NF:
Split multi-valued entries so each attribute holds atomic values.
Second Normal Form (2NF):
A relation is in 2NF if:
1. It is in 1NF.
2. It has NO Partial Dependency (no non-prime attribute is functionally dependent on a proper subset of any candidate key).
Definitions:
- Prime Attribute: An attribute that is a member of any candidate key.
- Non-Prime Attribute: An attribute not part of any candidate key."""
            },
            {
                "page": 7,
                "text": """2NF Decomposition Example:
Table: (Emp_Id, Dept_Id, Emp_Name, Dept_Name).
Composite primary key: (Emp_Id, Dept_Id).
Functional dependencies:
- Emp_Id -> Emp_Name (partial dependency on subset Emp_Id).
- Dept_Id -> Dept_Name (partial dependency on subset Dept_Id).
Both Emp_Name and Dept_Name violate 2NF because they depend on part of the composite key.
Resolution: Decompose into three tables:
1. Employee(Emp_Id, Emp_Name)
2. Department(Dept_Id, Dept_Name)
3. Emp_Dept(Emp_Id, Dept_Id)."""
            },
            {
                "page": 8,
                "text": """Third Normal Form (3NF):
A relation is in 3NF if:
1. It is in 2NF.
2. It has NO Transitive Dependencies (no non-prime attribute is transitively dependent on the primary key).
Formal Rule: For every non-trivial functional dependency X -> Y, either X is a superkey OR Y is a prime attribute."""
            },
            {
                "page": 9,
                "text": """3NF Decomposition Example:
Table: Employee(Emp_Id, Emp_Name, ZIP, City).
Primary key: Emp_Id.
Dependencies:
- Emp_Id -> ZIP
- ZIP -> City
Emp_Id determines City through ZIP (Emp_Id -> ZIP -> City).
Since ZIP is not a superkey and City is non-prime, this transitive dependency violates 3NF.
Resolution: Decompose into:
1. Employee(Emp_Id, Emp_Name, ZIP)
2. Location(ZIP, City)."""
            },
            {
                "page": 10,
                "text": """Transitive Dependencies & Schema Integrity:
Transitive functional dependencies allow updates to non-key attributes to cascade into data corruption.
Decomposing into 3NF isolates entities so each attribute depends solely on the key, the whole key, and nothing but the key."""
            },
            {
                "page": 11,
                "text": """Boyce-Codd Normal Form (BCNF):
BCNF is a stricter version of 3NF that handles multiple overlapping composite candidate keys.
Rule: A relation R is in BCNF if for every functional dependency X -> Y, X is a SUPERKEY.
Example: Relation R(A, B, C, D) with candidate keys A and BC.
If dependency D -> B exists where D is not a superkey, the table violates BCNF.
Resolution: Decompose into R1(A, D, C) and R2(D, B)."""
            }
        ]
    },
    {
        "document": "dbms_acid_properties_transactions.pdf",
        "topic": "Database Management Systems",
        "section": "Transactions & ACID Properties",
        "pages": [
            {
                "page": 1,
                "text": """Database ACID Properties: Atomic, Consistent, Isolated, Durable.
Understanding the foundation of reliable and consistent database transactions.
In modern computing, data is the most valuable organizational asset. Database Management Systems (DBMS) guarantee transaction integrity through the ACID principles."""
            },
            {
                "page": 2,
                "text": """What is a Database Transaction & ACID?
A database transaction is an atomic unit of work comprising one or more database operations (reads, writes, updates).
ACID represents the four core guarantees:
- Atomicity
- Consistency
- Isolation
- Durability"""
            },
            {
                "page": 3,
                "text": """Atomicity: All-or-Nothing Guarantee:
A transaction cannot be partially executed.
Either all modifications commit permanently to disk, or if a failure/abort occurs midway, the database rolls back to its exact pre-transaction state.
Prevents partial execution states during server crashes or lost network connections."""
            },
            {
                "page": 4,
                "text": """Consistency: Integrity Invariant Preservation:
A transaction must transform the database from one valid consistent state to another valid state, preserving all integrity constraints (primary keys, foreign keys, uniqueness, and check constraints).
If an operation violates an explicit constraint (e.g. account balance dropping below zero), the entire transaction aborts and rolls back."""
            },
            {
                "page": 5,
                "text": """Isolation: Concurrency Control & Serializability:
Concurrent execution of transactions must yield the same state as if they executed serially.
Isolation Levels:
1. Read Uncommitted (Dirty reads permitted).
2. Read Committed (Prevents dirty reads).
3. Repeatable Read (Prevents non-repeatable reads).
4. Serializable (Strict serializability via Two-Phase Locking 2PL or MVCC).
Trade-offs: Optimistic locking (validates at commit) vs. Pessimistic locking (locks rows up front)."""
            },
            {
                "page": 6,
                "text": """Durability: Crash Recovery & Persistence:
Once a transaction commits, its effects survive permanently, even in the event of hardware power failure, operating system crash, or storage fault.
Implementation: Write-Ahead Logging (WAL).
Modifications are recorded sequentially in the WAL on non-volatile disk before dirty pages are flushed from in-memory buffer pools to physical tables."""
            },
            {
                "page": 7,
                "text": """ACID in Relational vs NoSQL Databases:
Relational engines (PostgreSQL, SQL Server, MySQL InnoDB) enforce full ACID guarantees out of the box.
NoSQL engines (MongoDB, Cassandra) historically prioritized eventual consistency (BASE) for horizontal scaling, but modern engines now offer multi-document ACID transactions.
Best Practices: Keep transactions short, access rows in uniform order to prevent deadlocks, and shard responsibly."""
            }
        ]
    }
]
