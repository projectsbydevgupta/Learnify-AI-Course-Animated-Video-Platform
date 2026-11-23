DOCUMENTS = [
    {
        "document": "dsa_codility_binary_search.pdf",
        "topic": "Data Structures & Algorithms",
        "section": "Searching Algorithms & Divide-and-Conquer",
        "pages": [
            {
                "page": 1,
                "text": """Chapter 14: Binary Search Algorithm (Codility Limited):
Binary search is a simple and fundamental algorithm whereby linear search algorithms are optimized to run in logarithmic time O(log n).
14.1 Intuition:
Number guessing game between 1 and 16. Linear checking requires up to 16 questions.
By probing the middle element and halving the candidate set on every question, the search space reduces exponentially: 16 -> 8 -> 4 -> 2 -> 1, requiring at most log2(16) = 4 questions.
14.2 Implementation:
Requires a pre-sorted monotonic array A[0] <= A[1] <= ... <= A[n-1].
Maintain pointer bounds: beginning (beg = 0) and end (end = n - 1).
Midpoint calculation: mid = beg + (end - beg) // 2."""
            },
            {
                "page": 2,
                "text": """Python Implementation of Binary Search in O(log n):
def binarySearch(A, x):
    n = len(A)
    beg = 0
    end = n - 1
    result = -1
    while beg <= end:
        mid = beg + (end - beg) // 2
        if A[mid] <= x:
            beg = mid + 1
            result = mid
        else:
            end = mid - 1
    return result

14.3 Binary Search on the Answer / Result Space:
Binary search can be applied to monotonic decision problems: guessing the optimal answer value and verifying feasibility via a greedy check function."""
            },
            {
                "page": 3,
                "text": """14.4 Exercise: Boards Covering Holes Problem:
Problem: Given array A of size n representing holes in a roof (A[i] = 1 if hole) and k boards of uniform length. Find the minimal board length x to cover all holes.
Solution:
Binary search on board size in range [1, n].
Feasibility check function: Greedily place boards from left to right in O(n) time.
Overall Time Complexity: O(n log n). Space Complexity: O(1)."""
            }
        ]
    },
    {
        "document": "dsa_chapter7_quicksort_analysis.pdf",
        "topic": "Data Structures & Algorithms",
        "section": "Sorting Algorithms & Invariant Proofs",
        "pages": [
            {
                "page": 1,
                "text": """Chapter 7: Quicksort Algorithm & Analysis:
Quicksort is an efficient divide-and-conquer sorting algorithm in which division is dynamically carried out via in-place partitioning (unlike static midpoint division in MergeSort).
Three core steps:
1. Divide: Rearrange array A[p..r] into two subarrays A[p..q-1] and A[q+1..r] such that every element in left subarray <= pivot A[q], and every element in right subarray >= pivot.
2. Conquer: Recursively sort the two subarrays by recursive calls to Quicksort.
3. Combine: None (sorting is performed strictly in-place)."""
            },
            {
                "page": 2,
                "text": """The Quicksort Recursive Procedure:
Quicksort(A, p, r):
1: if p < r then
2:     q = Partition(A, p, r)
3:     Quicksort(A, p, q - 1)
4:     Quicksort(A, q + 1, r)
Initial invocation: Quicksort(A, 0, len(A) - 1)."""
            },
            {
                "page": 3,
                "text": """The Subroutine Partition:
Rearranges subarray A[p..r] in-place around a pivot element x = A[r].
Keys are scanned from left to right, placing all elements smaller than or equal to pivot to the left partition."""
            },
            {
                "page": 4,
                "text": """Lomuto Partition Algorithm:
Partition(A, p, r):
1: x = A[r]         // Pivot element
2: i = p - 1        // Boundary of elements <= x
3: for j = p to r - 1:
4:     if A[j] <= x:
5:         i = i + 1
6:         exchange A[i] with A[j]
7: exchange A[i + 1] with A[r]
8: return i + 1     // Final pivot index q"""
            },
            {
                "page": 5,
                "text": """Step-by-Step Trace of Partition:
Example array: [17, 9, 22, 31, 7, 12, 10, 21, 13, 29, 18, 20, 11] with pivot x = 11.
Elements 9, 7, 10 swap into the left partition.
Final swap places pivot 11 at index q with all smaller values to its left and larger to its right."""
            },
            {
                "page": 6,
                "text": """Loop Invariant for Partition Correctness:
At the start of each iteration of the for loop:
1. If p <= k <= i, then A[k] <= x.
2. If i + 1 <= k <= j - 1, then A[k] > x.
3. If k = r, then A[k] == x."""
            },
            {
                "page": 7,
                "text": """Proof of Correctness using Loop Invariant:
- Initialization: Prior to first iteration, i = p - 1 and j = p. Both partitions are empty; conditions hold vacuously.
- Maintenance: If A[j] > x, increment j. If A[j] <= x, increment i, swap A[i] and A[j], maintaining the invariant.
- Termination: At loop conclusion, j = r. Swap A[i + 1] and A[r] places pivot in its exact sorted position."""
            },
            {
                "page": 8,
                "text": """Asymptotic Running Time Analysis:
Partitioning an array of size n takes linear time Theta(n).
Running time of Quicksort depends heavily on whether the partitioning is balanced."""
            },
            {
                "page": 9,
                "text": """Worst-Case Analysis:
Worst-case occurs when partitioning produces one subproblem of size n - 1 and one of size 0 (e.g. already sorted array with last element as pivot).
Recurrence: T(n) = T(n - 1) + T(0) + Theta(n) = T(n - 1) + Theta(n).
Solving by unrolling: T(n) = sum_{k=1}^n Theta(k) = Theta(n^2).
Worst-case Time Complexity: O(n^2)."""
            },
            {
                "page": 10,
                "text": """Best-Case Analysis:
Best-case occurs when partition produces two subproblems of size at most n/2.
Recurrence: T(n) = 2*T(n/2) + Theta(n).
By Master Theorem (Case 2): T(n) = Theta(n log n)."""
            },
            {
                "page": 11,
                "text": """Average-Case & Balanced Partitions:
Even an unbalanced 9-to-1 split yields recurrence T(n) = T(9n/10) + T(n/10) + Theta(n).
The recursion tree depth is O(log n), producing an overall running time of O(n log n)."""
            },
            {
                "page": 12,
                "text": """Randomized Quicksort:
To guarantee expected O(n log n) performance and eliminate worst-case vulnerability on pre-sorted data, use a randomized pivot.
Randomized-Partition(A, p, r):
1: Select random index t uniformly from [p, r]
2: Exchange A[r] with A[t]
3: Return Partition(A, p, r)"""
            },
            {
                "page": 13,
                "text": """Expected Running Time Theorem:
Theorem: The expected running time of Randomized-Quicksort on any input array of size n is Theta(n log n).
Proof: Indicator random variables track the probability that any two elements are compared during execution, bounding total expected comparisons by 2 * n * ln(n)."""
            },
            {
                "page": 14,
                "text": """Space Complexity & Tail Recursion:
Quicksort sorts strictly in-place (O(1) auxiliary data memory).
However, recursive calls allocate frames on the call stack.
Worst-case call stack depth: O(n).
Optimized implementation uses tail-call recursion on the smaller partition, guaranteeing maximum stack depth of O(log n)."""
            },
            {
                "page": 15,
                "text": """Quicksort vs MergeSort vs HeapSort:
- Quicksort: In-place, exceptional cache locality, fast constants, expected O(n log n), worst-case O(n^2) without randomization.
- MergeSort: Guaranteed O(n log n) worst-case, stable, but requires O(n) auxiliary memory.
- HeapSort: In-place, O(n log n) worst-case, but poorer cache performance due to jumping heap indices."""
            }
        ]
    }
]
