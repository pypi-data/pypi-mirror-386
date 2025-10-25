def is_even(n):
    return n % 2 == 0

def is_prime(n):
    if n < 2: return False
    for i in range(2, int(n**0.5)+1):
        if n % i == 0:
            return False
    return True

def factorial(n):
    if n <= 1: return 1
    return n * factorial(n-1)

def average(lst):
    return sum(lst)/len(lst) if lst else 0
def is_odd(n):
    return n % 2 != 0

def prime_factors(n):
    factors = []
    i = 2
    while i*i <= n:
        if n % i:
            i += 1
        else:
            n //= i
            factors.append(i)
    if n > 1:
        factors.append(n)
    return factors

def gcd(a,b):
    while b:
        a,b = b, a%b
    return a

def lcm(a,b):
    return abs(a*b)//gcd(a,b)

def is_perfect(n):
    return n == sum(i for i in range(1,n) if n%i==0)
