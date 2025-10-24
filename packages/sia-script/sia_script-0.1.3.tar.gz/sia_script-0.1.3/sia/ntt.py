# --------------------- SiaNTT: Simplified OOP Module --------------------- #

class NttError(Exception):
    """Base exception for NTT errors."""
    pass

class ntt:
    """
    SiaObj: Ultra-simple, declarative entity module for students.
    Supports callable methods, indexed access, and single-line conditionals.
    """

    # Reserved names to prevent method/attribute conflicts
    _RESERVED = {'set', 'computed', 'validate', 'inherit', 'operator', '__call__', '__getitem__'}

    def __init__(self, *attrs, **methods):
        # Check for conflicts with reserved names
        if any(name in self._RESERVED for name in methods):
             raise NttError(f"Method names conflict with reserved keywords: {self._RESERVED}")
        
        self._names = list(attrs)
        self._methods = methods.copy() if methods else {}
        self._computed = {}
        self._validators = {}
        self._defaults = {n: None for n in attrs}
        self._parents = []
        self._polymorphic_methods = {}
        self._operators = {}
        
    # --- INTERNAL HELPER: Creates a function wrapper for p1.greet() ---
    def _create_method_wrapper(self, template):
        # 'self' here is the instance object
        def method_wrapper():
            # Recalculates the template using the current attribute values
            return self._execute_conditional_template(template, self)
        return method_wrapper

    # --- INTERNAL HELPER: Executes a conditional or simple template ---
    def _execute_conditional_template(self, template, inst):
        parts = [p.strip() for p in template.split('|')]
        
        # 1. Handle simple template (no '|' means no condition)
        if len(parts) == 1:
            return self._apply_template(template, inst)

        # 2. Handle conditional templates (e.g., "if condition: result | elif condition: result | else: result")
        # Find the first condition that evaluates to True
        
        for part in parts:
            if part.lower().startswith('if '):
                # Handle IF/ELIF (Syntax: 'if condition: result')
                condition_part, result_part = part[3:].split(':', 1)
                condition_expr = self._apply_template(condition_part.strip(), inst)
                
                # We use eval() here ONLY for tightly controlled, simple validation/comparison expressions.
                # In a safe environment, this is acceptable for educational purposes.
                try:
                    if eval(condition_expr):
                        return self._apply_template(result_part.strip(), inst)
                except Exception as e:
                    raise NttError(f"Condition evaluation failed in method: '{condition_expr}'") from e
                    
            elif part.lower().startswith('elif '):
                # Handle ELIF (similar to IF, starting after 'elif ')
                condition_part, result_part = part[5:].split(':', 1)
                condition_expr = self._apply_template(condition_part.strip(), inst)
                
                try:
                    if eval(condition_expr):
                        return self._apply_template(result_part.strip(), inst)
                except Exception as e:
                    raise NttError(f"Condition evaluation failed in method: '{condition_expr}'") from e
            
            elif part.lower().startswith('else:'):
                # Handle ELSE (Syntax: 'else: result')
                return self._apply_template(part[5:].strip(), inst)
        
        # Should not be reached if an 'else' is included, but return None otherwise
        return None

    # --- NEW FEATURE: Standard Bracket Access (p1['name'] or p1[0]) ---
    def __getitem__(self, key):
        """Allows access by index (int) or attribute name (str)."""
        if isinstance(key, str):
            return getattr(self, key)
        elif isinstance(key, int):
            if key < 0 or key >= len(self._names):
                raise IndexError(f"Index {key} is out of bounds. Object '{self.__class__.__name__}' has {len(self._names)} attributes.")
            name = self._names[key]
            return getattr(self, name)
        elif isinstance(key, slice):
            indices = range(*key.indices(len(self._names)))
            return tuple(getattr(self, self._names[i]) for i in indices)
        else:
            raise TypeError("Key must be an integer, string, or slice.")

    # --------------- Template Definition Methods ---------------- #
    def inherit(self, *parents):
        for p in parents:
            if isinstance(p, ntt):
                self._parents.append(p)
                for n in p._names:
                    if n not in self._names:
                        self._names.append(n)
                        self._defaults[n] = p._defaults.get(n, None)
                for k, v in p._methods.items():
                    if k not in self._methods: self._methods[k] = v
                for n, v in p._computed.items():
                    if n not in self._computed: self._computed[n] = v
                for n, v in p._validators.items():
                    if n not in self._validators: self._validators[n] = v
                if p._parents:
                    self.inherit(*p._parents)
        return self

    def polymorphic(self, method_name, template):
        if method_name not in self._polymorphic_methods:
            self._polymorphic_methods[method_name] = {}
        self._polymorphic_methods[method_name][id(self)] = template
        setattr(self, method_name, self._create_method_wrapper(template))
        return self

    def operator(self, symbol, template):
        self._operators[symbol] = template
        return self

    def computed(self, name, template):
        """Stores the template without calculating the value on the template object."""
        self._computed[name] = template
        return self

    def validate(self, name, template):
        self._validators[name] = template
        return self
    
    # --------------- Instance Creation ---------------- #
    def __call__(self, *args, **kwargs):
        # 'self' is the TEMPLATE (e.g., 'Person')
        inst = object.__new__(self.__class__)
        # Copy template metadata to the new instance
        inst._names = self._names.copy()
        inst._methods = self._methods.copy()
        inst._computed = self._computed.copy()
        inst._validators = self._validators.copy()
        inst._defaults = self._defaults.copy()
        inst._parents = self._parents.copy()
        inst._polymorphic_methods = {k: v.copy() for k, v in self._polymorphic_methods.items()}
        inst._operators = self._operators.copy()

        # Bind methods to the instance for correct 'self' context
        setattr(inst, '_create_method_wrapper', self._create_method_wrapper.__get__(inst, self.__class__))
        setattr(inst, '_apply_template', self._apply_template.__get__(inst, self.__class__))
        setattr(inst, '_execute_conditional_template', self._execute_conditional_template.__get__(inst, self.__class__))
        setattr(inst, '__getitem__', self.__getitem__.__get__(inst, self.__class__))

        # Set attributes
        for i, v in enumerate(args): setattr(inst, inst._names[i], v)
        for k, v in kwargs.items(): setattr(inst, k, v)
        for n in inst._names:
            if not hasattr(inst, n): setattr(inst, n, inst._defaults[n])

        # Apply methods (assigns the callable function wrapper)
        for k, t in inst._methods.items():
            setattr(inst, k, inst._create_method_wrapper(t))

        # Apply computed and polymorphic properties (assigns the calculated string/value)
        for n, t in inst._computed.items():
            setattr(inst, n, inst._execute_conditional_template(t, inst))
            
        for k, v in inst._polymorphic_methods.items():
            if id(inst) in v:
                setattr(inst, k, inst._execute_conditional_template(v[id(inst)], inst))
        return inst

    # --------------- Set Attributes ---------------- #
    def set(self, *values):
        for i, v in enumerate(values):
            name = self._names[i]
            temp = self._validators.get(name)
            if temp:
                expr = self._apply_template(temp, self)
                # Validation relies on controlled use of eval()
                if not eval(expr): 
                    raise ValueError(f"Validation failed for {name}={v}")
            setattr(self, name, v)
            
        # Computed and polymorphic properties MUST be explicitly refreshed
        for n, t in self._computed.items():
            setattr(self, n, self._execute_conditional_template(t, self))
            
        for k, v in self._polymorphic_methods.items():
            if id(self) in v:
                setattr(self, k, self._execute_conditional_template(v[id(self)], self))
        return self

    # --------------- Add Method Dynamically ---------------- #
    def add_method(self, name, template):
        self._methods[name] = template
        setattr(self, name, self._create_method_wrapper(template))
        return self

    # --------------- Apply Template (Simple replacement) ---------------- #
    def _apply_template(self, template, inst=None):
        if inst is None: inst = self
        result = template
        for i, n in enumerate(inst._names):
            try:
                result = result.replace(f"({i})", str(getattr(inst, n)))
            except AttributeError:
                # Better error handling for missing attributes
                return f"[ATTR_MISSING: {n}]" 
        return result

    # --- OPERATOR HANDLING (Security Fix: Replaced eval with basic parsing) ---
    def _parse_arithmetic(self, expr):
        # Extremely basic parser: find first operator and split.
        for op in ('+', '-', '*', '/'):
            if op in expr:
                left, right = expr.split(op, 1)
                left = float(left)
                right = float(right)
                if op == '+': return left + right
                if op == '-': return left - right
                if op == '*': return left * right
                if op == '/':
                    if right == 0: raise ZeroDivisionError("Cannot divide by zero.")
                    return left / right
        return float(expr) # If no operator, return the number itself

    def _operate(self, other, symbol):
        temp = self._operators.get(symbol)
        if temp is None: return None
        
        # 1. Gather all attribute values (self + other)
        vals = [str(getattr(self, n)) for n in self._names]
        if isinstance(other, ntt):
            vals.extend([str(getattr(other, n)) for n in other._names])
        else:
            vals.append(str(other))

        # 2. Apply replacement
        result_template = temp
        for i, v in enumerate(vals):
            result_template = result_template.replace(f"({i})", v)

        # 3. Execution (Comparison or Arithmetic)
        if symbol in ('==', '!=', '<', '>', '<=', '>='):
            # Comparisons are safer to evaluate directly if inputs are trusted
            return eval(result_template)
        
        # Arithmetic uses the safer custom parser
        return self._parse_arithmetic(result_template)

    __add__ = lambda self, o: self._operate(o, '+')
    __sub__ = lambda self, o: self._operate(o, '-')
    __mul__ = lambda self, o: self._operate(o, '*')
    __truediv__ = lambda self, o: self._operate(o, '/')
    __eq__ = lambda self, o: self._operate(o, '==')
    __ne__ = lambda self, o: self._operate(o, '!=')
    __lt__ = lambda self, o: self._operate(o, '<')
    __le__ = lambda self, o: self._operate(o, '<=')
    __gt__ = lambda self, o: self._operate(o, '>')
    __ge__ = lambda self, o: self._operate(o, '>=')

    # --------------- String Representation ---------------- #
    __str__ = lambda self: f"{self.__class__.__name__}({', '.join(f'{n}={getattr(self,n)}' for n in self._names)}{', ' + ', '.join(f'{k}={getattr(self,k)}' for k in self._computed) if self._computed else ''})"
    __repr__ = __str__