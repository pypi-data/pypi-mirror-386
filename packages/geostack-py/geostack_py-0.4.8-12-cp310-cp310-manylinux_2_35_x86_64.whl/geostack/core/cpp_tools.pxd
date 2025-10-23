from libcpp cimport bool
from libcpp.utility cimport pair
from libc.stddef import ptrdiff_t
from libcpp.queue cimport queue, priority_queue

cdef extern from "<functional>" namespace "std" nogil:
    cdef cppclass reference_wrapper[T]:
        # reference_wrapper() except +
        reference_wrapper(T& ref) except +
        reference_wrapper(T&&) except +
        reference_wrapper(reference_wrapper[T]&) except +
        reference_wrapper& get() except +
        T& get() except +
        reference_wrapper operator=(reference_wrapper&) except +
        reference_wrapper& operator[]() except +
    reference_wrapper[T] cpp_ref "std::ref" [T](T& t) except +
    reference_wrapper[T] cpp_ref "std::ref" [T](reference_wrapper[T] t) except +


cdef extern from "<algorithm>" namespace "std" nogil:
    # Modifying sequence operations
    OutputIt copy[InputIt, OutputIt](InputIt first, InputIt last, OutputIt d_first) except +
    #OutputIt copy[ExecutionPolicy, InputIt, OutputIt](ExecutionPolicy&& policy, InputIt first, InputIt last, OutputIt d_first) except +
    OutputIt copy_n[InputIt, Size, OutputIt](InputIt first, Size count, OutputIt result) except +
    #OutputIt copy_n[ExecutionPolicy, InputIt, Size, OutputIt](ExecutionPolicy&& policy, InputIt first, Size count, OutputIt result) except +

#cdef extern from "<execution>" namespace "std::execution" nogil:
#    cdef cppclass sequenced_policy:
#        pass
#    cdef cppclass parallel_policy:
#        pass
#
#    const sequenced_policy seq "std::execution::seq"
#    const parallel_policy par "std::execution::par"

cdef extern from "<iostream>" namespace "std" nogil:
    cdef cppclass ostream:
        ostream& write(const char*, int) except +
    cdef cppclass istream:
        istream& read(const char*, int) except +
    cdef ostream cout
    cdef istream cin

cdef extern from "<iostream>" namespace "std::ios_base" nogil:
    cdef cppclass openmode:
        pass
    cdef cppclass seekdir:
        pass
    cdef openmode ios_binary "std::ios::binary"
    cdef openmode ios_in "std::ios::in"
    cdef openmode ios_out "std::ios::out"
    cdef openmode ios_app "std::ios::app"

    cdef seekdir seek_beg "std::ios::beg"
    cdef seekdir seek_end "std::ios::end"
    cdef seekdir seek_cur "std::ios::cur"

    bool sync_with_stdio(bool) except +

cdef extern from "<fstream>" namespace "std" nogil:
    cdef cppclass ofstream(ostream):
        # constructors
        ofstream(const char*) except +
        ofstream(const char*, openmode) except +
        ofstream& write(char*, int n) except +
        ofstream& flush() except +
        open(const char*, openmode) except +
        void close() except +
        bool is_open() except +
        # using except + for operator<< gives invalid c++ code
        ofstream& operator<< (int& val)
        ofstream& operator<< (float& val)
        ofstream& operator<< (void*& val)
        bint operator bool() except +
        bint operator!() except +

    cdef cppclass ifstream(istream):
        ifstream(const char*) except +
        ifstream(const char*, openmode) except +
        open(const char*, openmode) except +
        void close() except +
        bool is_open() except +
        # using except + for operator>> gives invalid c++ code
        ifstream& operator>> (int& val)
        ifstream& operator>> (float& val)
        ifstream& operator>> (void*& val)
        bint operator bool() except +
        bint operator!() except +

    cdef cppclass fstream:
        fstream(const char*) except +
        fstream(const char*, openmode) except +
        open(const char*, openmode) except +
        bool is_open() except +
        fstream& operator=(const fstream&) except +
        ifstream& read(char*, int n) except +
        # using except + for operator>> gives invalid c++ code
        ifstream& operator>> (int& val)
        ifstream& operator>> (float& val)
        ifstream& operator>> (void*& val)
        ofstream& write(char*, int n) except +
        # using except + for operator<< gives invalid c++ code
        ofstream& operator<< (int& val)
        ofstream& operator<< (float& val)
        ofstream& operator<< (void*& val)
        ofstream& flush() except +
        void close() except +
        bool good() except +
        bool eof() except +
        bint operator bool() except +
        bint operator!() except +

cdef extern from *:
  ctypedef int dynamic "-1"
  ctypedef int one "1"

cdef extern from 'eigen/Dense' namespace "Eigen":
    cdef cppclass Map[M]:
        Map(double*, int, int)

    cdef cppclass Matrix[T,nRow,nCol]:
        Matrix()
        Matrix(const Matrix[T,nRow,nCol] &)
        Matrix(const Map[Matrix[T,nRow,nCol]]&)
        T& operator[](int)
        Matrix[T,nRow,nCol] operator+(const Matrix[T,nRow,nCol] &)
        Matrix[T,nRow,nCol] operator-()
        Matrix[T,nRow,nCol] operator-(const Matrix[T,nRow,nCol] &)
        # Matrix x Scalar
        Matrix[T,nRow,nCol] scalar_mul "operator*"(const T&)
        # Matrix / Scalar
        Matrix[T,nRow,nCol] scalar_div "operator/"(const T&)
        bool operator==(const Matrix[T,nRow,nCol]&)
        bool operator!=(const Matrix[T,nRow,nCol]&)
        T& operator()(int)
        T& operator()(int,int)
        Matrix[T,dynamic,dynamic] block(int, int, int, int)
        Matrix[T,nRow,nCol] inverse()

        T& coeff(int, int)
        int cols()
        Matrix[T,nRow,nCol] cross(const Matrix[T,nRow,nCol] &)
        T dot(const Matrix[T,nRow,nCol] &)
        T norm()
        void normalize()
        Matrix[T,nRow,nCol] normalized()
        int rows()
        int size()
        T squaredNorm()
        Matrix[T,nCol,nRow] transpose()
        void setZero()
        @staticmethod
        Matrix[T,nRow,nCol] Zero(int, int)
        @staticmethod
        Matrix[T,nRow,nCol] Random(int, int)
        T* data()

    ctypedef Matrix[double, dynamic, one] VectorXd
    ctypedef Matrix[double, dynamic, dynamic] MatrixXd
    ctypedef Matrix[float, dynamic, one] VectorXf
    ctypedef Matrix[float, dynamic, dynamic] MatrixXf
    ctypedef Matrix[int, dynamic, one] VectorXi
    ctypedef Matrix[int, dynamic, dynamic] MatrixXi

cdef extern from "eigen/SVD" namespace "Eigen":
    cdef cppclass BDCSVD:
        pass

    cdef cppclass JacobiSVD:
        pass
