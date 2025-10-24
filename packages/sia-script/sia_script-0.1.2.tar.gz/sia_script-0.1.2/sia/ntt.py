# --------------------- SiaNTT: Simplified OOP Module --------------------- #

class ntt:
    """
    Ultra-simple Object-Oriented module (SiaObj)
    Features:
    - Attributes via positional names
    - Methods via templates (no self, no lambda)
    - Computed properties
    - Validators
    - Polymorphism
    - Inheritance
    - Operator overloading
    """

    def __init__(self, *attrs, **methods):
        self._names = list(attrs)
        self._methods = methods.copy() if methods else {}
        self._computed = {}
        self._validators = {}
        self._defaults = {n: None for n in attrs}
        self._parents = []
        self._polymorphic_methods = {}
        self._operators = {}

    # --------------- Inheritance ---------------- #
    def inherit(self, *parents):
        for p in parents:
            if isinstance(p, ntt):
                self._parents.append(p)
                for n in p._names:
                    if n not in self._names:
                        self._names.append(n)
                        self._defaults[n] = p._defaults.get(n, None)
                for k, v in p._methods.items():
                    if k not in self._methods:
                        self._methods[k] = v
                for n, v in p._computed.items():
                    if n not in self._computed:
                        self._computed[n] = v
                for n, v in p._validators.items():
                    if n not in self._validators:
                        self._validators[n] = v
                if p._parents:
                    self.inherit(*p._parents)
        return self

    # --------------- Polymorphic Methods ---------------- #
    def polymorphic(self, method_name, template):
        if method_name not in self._polymorphic_methods:
            self._polymorphic_methods[method_name] = {}
        self._polymorphic_methods[method_name][id(self)] = template
        setattr(self, method_name, self._apply_template(template))
        return self

    # --------------- Operator Overloading ---------------- #
    def operator(self, symbol, template):
        """Define operator behavior: +, -, *, /, ==, !=, <, >"""
        self._operators[symbol] = template
        return self

    # --------------- Instance Creation ---------------- #
    def __call__(self, *args, **kwargs):
        inst = object.__new__(self.__class__)
        inst._names = self._names.copy()
        inst._methods = self._methods.copy()
        inst._computed = self._computed.copy()
        inst._validators = self._validators.copy()
        inst._defaults = self._defaults.copy()
        inst._parents = self._parents.copy()
        inst._polymorphic_methods = {k: v.copy() for k, v in self._polymorphic_methods.items()}
        inst._operators = self._operators.copy()

        # Set attributes
        for i, v in enumerate(args):
            setattr(inst, inst._names[i], v)
        for k, v in kwargs.items():
            setattr(inst, k, v)
        for n in inst._names:
            if not hasattr(inst, n):
                setattr(inst, n, inst._defaults[n])

        # Apply methods, computed, polymorphic
        for k, t in inst._methods.items():
            setattr(inst, k, self._apply_template(t, inst))
        for n, t in inst._computed.items():
            setattr(inst, n, self._apply_template(t, inst))
        for k, v in inst._polymorphic_methods.items():
            if id(inst) in v:
                setattr(inst, k, self._apply_template(v[id(inst)], inst))
        return inst

    # --------------- Computed Properties ---------------- #
    def computed(self, name, template):
        self._computed[name] = template
        setattr(self, name, self._apply_template(template, self))
        return self

    # --------------- Validators ---------------- #
    def validate(self, name, template):
        self._validators[name] = template
        return self

    # --------------- Set Attributes ---------------- #
    def set(self, *values):
        for i, v in enumerate(values):
            name = self._names[i]
            temp = self._validators.get(name)
            if temp:
                expr = temp
                for j, n in enumerate(self._names):
                    val = v if j == i else getattr(self, n)
                    expr = expr.replace(f"({j})", str(val))
                if not eval(expr):
                    raise ValueError(f"Validation failed: {name}={v}")
            setattr(self, name, v)
        for n, t in self._computed.items():
            setattr(self, n, self._apply_template(t, self))
        for k, v in self._polymorphic_methods.items():
            if id(self) in v:
                setattr(self, k, self._apply_template(v[id(self)], self))
        return self

    # --------------- Add Method Dynamically ---------------- #
    def add_method(self, name, template):
        self._methods[name] = template
        setattr(self, name, self._apply_template(template, self))
        return self

    # --------------- Apply Template ---------------- #
    def _apply_template(self, template, inst=None):
        if inst is None: inst = self
        result = template
        for i, n in enumerate(inst._names):
            result = result.replace(f"({i})", str(getattr(inst, n)))
        return result

    # --------------- Operator Handling ---------------- #
    def _operate(self, other, symbol):
        temp = self._operators.get(symbol)
        if temp is None: return None
        vals = [str(getattr(self, n)) for n in self._names]
        if isinstance(other, ntt):
            vals_other = [str(getattr(other, n)) for n in other._names]
            vals.extend(vals_other)
        else:
            vals.append(str(other))
        result = temp
        for i, v in enumerate(vals):
            result = result.replace(f"({i})", v)
        return result

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