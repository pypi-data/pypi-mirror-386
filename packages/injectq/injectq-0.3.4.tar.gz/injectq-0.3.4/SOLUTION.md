# Solution: Parameterized Factories in InjectQ

## 🎯 Your Question

> "What if I need only one element and pass one argument to get? We don't have that feature."
>
> ```python
> # This doesn't work:
> injector.bind_factory("data_store", lambda x: data[x])
> result = injector["data_store"]("key2")  # ERROR!
> ```

## ✅ My Solution

Add **two new methods** to support parameterized factories without breaking existing functionality:

### 1. `get_factory()` - Returns the raw factory function
### 2. `call_factory()` - Shorthand to get and call the factory

## 📊 Before vs After

### ❌ Before (Didn't Work)
```python
data = {"key1": "value1", "key2": "value2"}

injector.bind_factory("data_store", lambda x: data[x])

# Tried but failed:
result = injector["data_store"]("key2")
# ERROR: lambda() missing 1 required positional argument: 'x'
```

### ✅ After (Now Works!)
```python
data = {"key1": "value1", "key2": "value2"}

injector.bind_factory("data_store", lambda x: data[x])

# Method 1: Get factory then call
factory = injector.get_factory("data_store")
result = factory("key2")  # "value2" ✅

# Method 2: Use shorthand
result = injector.call_factory("data_store", "key2")  # "value2" ✅

# Method 3: Chain the calls
result = injector.get_factory("data_store")("key2")  # "value2" ✅
```

## 🔄 No Breaking Changes

All existing code continues to work exactly as before:

```python
# DI factories (no parameters) - Works as always
injector.bind_factory("timestamp", lambda: datetime.now())
timestamp = injector.get("timestamp")  # Auto-invoked ✅

# New parameterized factories - Now also works!
injector.bind_factory("data_store", lambda x: data[x])
value = injector.call_factory("data_store", "key1")  # ✅
```

## 🎨 Why This Approach?

### ✅ Advantages

1. **Backward Compatible** - No existing code breaks
2. **Clear Distinction** - Different methods for different use cases
3. **Intuitive** - `get_factory()` literally gets the factory function
4. **Flexible** - Works with any number of parameters
5. **No New Binding Method** - Reuses existing `bind_factory()`

### 🆚 Alternative Approaches (Not Chosen)

#### ❌ Option A: Change `get()` behavior
```python
# Would break existing code
injector.bind_factory("service", lambda x: ...)
result = injector.get("service", "arg")  # Confusing with DI
```
**Why not?** Breaks backward compatibility and confuses DI vs manual args.

#### ❌ Option B: New binding method
```python
injector.bind_parameterized_factory("service", lambda x: ...)
result = injector.get("service", "arg")
```
**Why not?** Requires learning a new binding method, more complex API.

#### ✅ Option C: New retrieval methods (CHOSEN)
```python
# Same binding method
injector.bind_factory("service", lambda x: ...)

# Different retrieval methods based on use case
result = injector.call_factory("service", "arg")  # Parameterized
result = injector.get("service")  # DI
```
**Why?** Clean separation, no breaking changes, intuitive API.

## 📋 API Reference

### `get_factory(service_type)`

**Purpose:** Get the raw factory function without invoking it

**Signature:**
```python
def get_factory(self, service_type: ServiceKey) -> ServiceFactory
```

**Example:**
```python
factory = injector.get_factory("data_store")
value = factory("key1")
```

### `call_factory(service_type, *args, **kwargs)`

**Purpose:** Get and call a factory with custom arguments

**Signature:**
```python
def call_factory(self, service_type: ServiceKey, *args, **kwargs) -> Any
```

**Example:**
```python
value = injector.call_factory("data_store", "key1")
```

## 💡 Usage Patterns

### Pattern 1: Simple Data Access
```python
data = {"user:1": {"name": "Alice"}, "user:2": {"name": "Bob"}}

injector.bind_factory("get_user", lambda user_id: data[user_id])

user = injector.call_factory("get_user", "user:1")
```

### Pattern 2: Multiple Parameters
```python
injector.bind_factory("calculator", lambda op, a, b: {
    "add": a + b,
    "mul": a * b,
}[op])

result = injector.call_factory("calculator", "add", 10, 5)  # 15
```

### Pattern 3: Keyword Arguments
```python
def create_config(env="dev", debug=False):
    return {"env": env, "debug": debug}

injector.bind_factory("config", create_config)

dev_config = injector.call_factory("config", env="dev", debug=True)
prod_config = injector.call_factory("config", env="prod")
```

### Pattern 4: Factory Reuse
```python
factory = injector.get_factory("data_store")

# Reuse the same factory multiple times
value1 = factory("key1")
value2 = factory("key2")
value3 = factory("key3")
```

### Pattern 5: Mixed DI and Parameterized
```python
# DI factory
injector.bind_factory("logger", lambda: create_logger())
logger = injector.get("logger")  # Auto-invoked

# Parameterized factory
injector.bind_factory("get_user", lambda id: fetch_user(id))
user = injector.call_factory("get_user", 123)  # Manual invocation
```

## 🎯 Decision Matrix

**When to use which method:**

| Use Case | Method to Use | Example |
|----------|--------------|---------|
| Service with dependencies | `get()` | `injector.get(UserService)` |
| Factory with no params | `get()` | `injector.get("timestamp")` |
| Factory with params | `call_factory()` | `injector.call_factory("get_user", 123)` |
| Need raw factory | `get_factory()` | `factory = injector.get_factory("service")` |
| Multiple calls with diff args | `get_factory()` + call | `factory("arg1")`, `factory("arg2")` |

## 🚀 Migration Path

If you have existing code that doesn't work:

**Step 1:** Identify parameterized factories
```python
# These are parameterized (have parameters that aren't dependencies)
injector.bind_factory("data_store", lambda key: data[key])
injector.bind_factory("calculator", lambda op, a, b: calc(op, a, b))
```

**Step 2:** Update retrieval method
```python
# Before (doesn't work)
value = injector.get("data_store")  # ERROR

# After (works)
value = injector.call_factory("data_store", "key1")  # ✅
```

**Step 3:** Test
```python
# Verify it works
assert injector.call_factory("data_store", "key1") == "value1"
```

## 📚 See Also

- Full documentation: `docs/injection-patterns/parameterized-factories.md`
- Examples: `examples/parameterized_factory_example.py`
- Tests: `tests/test_parameterized_factories.py`
- Summary: `PARAMETERIZED_FACTORIES_SUMMARY.md`

## 🎉 Conclusion

The parameterized factory feature is now fully implemented and tested. You can:

✅ Bind factories with parameters using existing `bind_factory()`  
✅ Retrieve and call them using `get_factory()` or `call_factory()`  
✅ Mix DI factories and parameterized factories in the same container  
✅ Use all existing features without any breaking changes  

The solution is clean, intuitive, and backward compatible! 🚀
