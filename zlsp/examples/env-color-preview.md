# Environment Variable Color Options

Values like `PROD`, `DEBUG`, `INFO`, `TEST` are semantic configuration constants.

<div style="background: #1e1e1e; padding: 20px; font-family: 'Courier New', monospace; font-size: 14px; line-height: 1.6;">

## Current (Cream String):
<span style="color: #9370DB;">logger:</span> <span style="color: #ffffd7;">PROD</span> <span style="color: #666;">(too subtle)</span>

---

## Option 1: Bright Yellow (ANSI 226) - Warning/Attention
<span style="color: #9370DB;">logger:</span> <span style="color: #ffff00;">PROD</span> <span style="color: #666;">← High visibility, "important config"</span><br/>
<span style="color: #9370DB;">logger:</span> <span style="color: #ffff00;">DEBUG</span><br/>
<span style="color: #9370DB;">logger:</span> <span style="color: #ffff00;">INFO</span>

## Option 2: Gold (ANSI 220) - Warm, Less Intense
<span style="color: #9370DB;">logger:</span> <span style="color: #ffd700;">PROD</span> <span style="color: #666;">← Softer than bright yellow</span><br/>
<span style="color: #9370DB;">logger:</span> <span style="color: #ffd700;">DEBUG</span><br/>
<span style="color: #9370DB;">logger:</span> <span style="color: #ffd700;">INFO</span>

## Option 3: Orange (ANSI 208) - Config/Settings Feel
<span style="color: #9370DB;">logger:</span> <span style="color: #ff8700;">PROD</span> <span style="color: #666;">← Distinct from other colors</span><br/>
<span style="color: #9370DB;">logger:</span> <span style="color: #ff8700;">DEBUG</span><br/>
<span style="color: #9370DB;">logger:</span> <span style="color: #ff8700;">INFO</span>

## Option 4: Light Yellow (ANSI 228) - Subtle but Distinct
<span style="color: #9370DB;">logger:</span> <span style="color: #ffff87;">PROD</span> <span style="color: #666;">← Gentle highlight</span><br/>
<span style="color: #9370DB;">logger:</span> <span style="color: #ffff87;">DEBUG</span><br/>
<span style="color: #9370DB;">logger:</span> <span style="color: #ffff87;">INFO</span>

## Option 5: Amber (ANSI 214) - Warm Attention
<span style="color: #9370DB;">logger:</span> <span style="color: #ffaf00;">PROD</span> <span style="color: #666;">← Balance of bright & warm</span><br/>
<span style="color: #9370DB;">logger:</span> <span style="color: #ffaf00;">DEBUG</span><br/>
<span style="color: #9370DB;">logger:</span> <span style="color: #ffaf00;">INFO</span>

</div>

---

## Detection Pattern

Should detect ALL-CAPS strings that match common env patterns:
- **Log Levels:** `PROD`, `DEBUG`, `INFO`, `WARN`, `ERROR`, `TRACE`
- **Environments:** `DEV`, `DEVELOPMENT`, `STAGING`, `PRODUCTION`
- **States:** `ENABLED`, `DISABLED`, `ACTIVE`, `INACTIVE`

**My recommendation:** ANSI **220** (Gold) or **214** (Amber)
- Distinct from existing colors
- Conveys "important configuration"
- Not as aggressive as bright yellow
- Works well with the purple keys

Which color appeals to you? Or suggest your own ANSI code!
