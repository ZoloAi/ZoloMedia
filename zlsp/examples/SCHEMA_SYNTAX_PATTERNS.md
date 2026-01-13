# Industry-Grade Schema Syntax Highlighting Patterns

## Purpose
Compare `zSchema.*.zolo` syntax with industry standards to inform semantic theme design.

---

## 🎨 Common Syntax Highlighting Patterns Across Frameworks

### 1. **Class/Model Names** (Entity Definitions)
- **Color:** Usually **bright/bold** (blue, cyan, yellow)
- **Examples:**
  - Python: `class User(Base):` → `User` is bright
  - Prisma: `model User {` → `model` keyword + `User` name
- **zSchema equivalent:** `users:` (entity/table name)
- **Recommendation:** Special color for entity keys at root level under `zMeta`

### 2. **Field/Column Names**
- **Color:** Usually **white/default** or **light color**
- **Examples:**
  - `email = Column(...)`
  - `name: str`
  - `email String`
- **zSchema equivalent:** `email:`, `password:`, `name:`
- **Recommendation:** Keep as nested keys (golden yellow 222)

### 3. **Type Names** (Data Types)
- **Color:** Usually **green, blue-green, or cyan**
- **Examples:**
  - Python: `String`, `Integer`, `DateTime` → type classes
  - Pydantic: `str`, `int`, `EmailStr` → builtin types
  - Prisma: `String`, `Int`, `DateTime` → special types
- **zSchema equivalent:** `type: str`, `type: int`, `type: datetime`
- **Recommendation:** Special color for type **values** (not the `type:` key)

### 4. **Constraints/Validators** (Field Properties)
- **Color:** Usually **parameters/attributes** - light colors
- **Examples:**
  - `nullable=False`, `unique=True`, `default='active'`
  - `min_length=5`, `max_length=255`
  - `@unique`, `@default`
- **zSchema equivalent:** `required: true`, `unique: true`, `default: active`
- **Recommendation:** Possibly highlight constraint **values** (true/false/defaults)

### 5. **Decorators/Annotations**
- **Color:** Usually **yellow, orange, or magenta**
- **Examples:**
  - Python: `@validator`, `@property`
  - Prisma: `@id`, `@unique`, `@default(...)`
- **zSchema equivalent:** `pk: true`, `auto_increment: true`, `zHash: bcrypt`
- **Recommendation:** `zHash`, `zMigration` could use decorator-style color

### 6. **Special Keywords**
- **Color:** Usually **purple, magenta, or bold**
- **Examples:**
  - `primary_key=True`, `autoincrement=True`
  - `Field(...)`, `Column(...)`
- **zSchema equivalent:** `pk`, `auto_increment`, `rules`, `comment`
- **Recommendation:** Special property keys could have distinct color

### 7. **Enums/Constants**
- **Color:** Usually **uppercase CONSTANTS** - bright blue/cyan/orange
- **Examples:**
  - `UserStatus.active`
  - `ACTIVE`, `SUSPENDED`, `PENDING`
  - `StorageBackend.local`
- **zSchema equivalent:** Pattern values like `^(active|suspended|pending)$`
- **Recommendation:** Could highlight enum-like values inside patterns

---

## 📊 Typical Color Mappings in Popular Editors (VSCode/PyCharm)

| Element | Typical Color | zSchema Equivalent |
|---------|---------------|-------------------|
| Class/Model name | **Bright Yellow/Cyan** | `users:`, `Meta:` |
| Field names | White/Default | `email:`, `name:` |
| Type keywords | **Green/Blue-Green** | `str`, `int`, `datetime` |
| String literals | **Light Orange/Salmon** | `"bcrypt"`, `"email"` |
| Numbers | **Light Green** | `255`, `1073741824` |
| Booleans | **Blue/Cyan** | `true`, `false` |
| Decorators | **Yellow/Orange** | `zHash`, `zMigration` |
| Function calls | **Yellow** | N/A in zSchema |
| Comments | **Gray/Dim** | Already handled |

---

## 🎯 Recommendations for zSchema.*.zolo

Based on industry patterns:

### High Priority (Most Impactful)
1. ✅ **`zMeta:` at root** → Light green (114) - **DONE**
2. 🎨 **Entity names** (`users:`) → Bright color (yellow/cyan)
3. 🎨 **Type values** (`str`, `int`, `datetime`) → Green/blue-green
4. 🎨 **z-prefixed special keys** (`zHash`, `zMigration`) → Yellow/orange (decorator-style)

### Medium Priority
5. 🎨 **Constraint keys** (`pk`, `required`, `unique`, `auto_increment`) → Distinct color
6. 🎨 **Boolean values** specific to schemas → Could use existing boolean color

### Low Priority (Nice to Have)
7. 🎨 **Format validators** (`email`, `pattern`, `min_length`) → Could use string color
8. 🎨 **Rule section** (`rules:`) → Could highlight differently from regular nested keys

---

## 💡 Key Insights

1. **Type information is critical** → Should stand out visually
2. **Decorators/annotations** (like `zHash`) deserve special treatment
3. **Entity/table names** are the "classes" of schemas → Should be prominent
4. **Field names** are usually subtle (not highlighted much)
5. **Keep it clean** → Too many colors = visual noise

---

**Next Steps:** Pick 2-3 elements to theme first, test, iterate! 🎨
