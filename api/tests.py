from django.test import TestCase

# Create your tests here.
def custom_decorator(function):
    def wrapper(*args, **kwargs):
        print("До вызова функции")
        result = function(*args, **kwargs)
        print("После вызова функции")
        return result
    return wrapper

@custom_decorator
def example_function():
    print("Внутри функции")

example_function()