from injectq import InjectQ


data = {"key1": "value1", "key2": "value2", "key3": "value3"}


if __name__ == "__main__":
    injector = InjectQ()

    # Bind a parameterized factory
    injector.bind_factory("data_store", lambda x: data[x])

    # Method 1: Get factory and call with argument
    factory = injector.get_factory("data_store")
    result1 = factory("key1")
    print(f"Method 1 (get_factory): {result1}")

    # Method 2: Use call_factory shorthand
    result2 = injector.call_factory("data_store", "key2")
    print(f"Method 2 (call_factory): {result2}")

    # Method 3: Chain call
    result3 = injector.get_factory("data_store")("key3")
    print(f"Method 3 (chained): {result3}")

    print("\nAll methods work! ✅")
