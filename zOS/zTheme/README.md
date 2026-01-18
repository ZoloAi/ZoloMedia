# zTheme

A modern, lightweight CSS framework with handwritten typography (Kalam font) and SVG icon system. Built for zCLI applications but works with any web project.

## Features

- ✨ **Modern CSS utilities** - Layout, spacing, colors, typography
- 🎨 **Beautiful Kalam handwritten font** - Built-in custom typography
- 🔤 **SVG icon sprite system** - Zero HTTP requests, infinite scaling
- 📦 **Single-file import** - Just one `<link>` tag
- 🚀 **Lightweight** - No dependencies, minimal footprint
- ⚡ **Fast** - CDN-ready for instant loading

## Quick Start

### Single Line Import (CDN)

```html
<!DOCTYPE html>
<html>
<head>
  <!-- zTheme CSS -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/YOUR_USERNAME/zTheme@main/dist/ztheme.css">
</head>
<body>
  <!-- Include SVG icons -->
  <object data="https://cdn.jsdelivr.net/gh/YOUR_USERNAME/zTheme@main/dist/icons.svg" type="image/svg+xml" style="display: none;"></object>
  
  <h1 class="zText-primary">Hello zTheme!</h1>
  <button class="zBtn zBtn-primary">
    <svg class="zIcon">
      <use xlink:href="#icon-house"></use>
    </svg>
    Home
  </button>
</body>
</html>
```

### Local Install

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/zTheme.git

# Link in your HTML
<link rel="stylesheet" href="path/to/zTheme/dist/ztheme.css">
```

## Components

### Typography

```html
<h1 class="zText-primary">Heading</h1>
<p class="zText-muted">Muted text</p>
```

### Buttons

```html
<button class="zBtn zBtn-primary">Primary</button>
<button class="zBtn zBtn-success">Success</button>
<button class="zBtn zBtn-outline-danger">Danger</button>
```

### Badges

```html
<span class="zBadge zBadge-primary">New</span>
<span class="zBadge zBadge-success">Active</span>
```

### Icons

```html
<!-- Basic icon -->
<svg class="zIcon zIcon-lg">
  <use xlink:href="#icon-house"></use>
</svg>

<!-- Icon in button -->
<button class="zBtn zBtn-primary">
  <svg class="zIcon">
    <use xlink:href="#icon-user-fill"></use>
  </svg>
  Profile
</button>

<!-- Animated icon -->
<svg class="zIcon zIcon-spin zText-primary">
  <use xlink:href="#icon-arrow-repeat"></use>
</svg>
```

### Spacing

```html
<div class="zmt-3 zmb-4 zp-2">
  Margin top 3, margin bottom 4, padding 2
</div>
```

### Containers

```html
<div class="zContainer">
  <!-- Responsive container -->
</div>

<div class="zContainer-fluid">
  <!-- Full-width container -->
</div>
```

## Available Icons

- **Navigation:** `icon-house`, `icon-apps`, `icon-hamburger-fill`
- **Users:** `icon-user-fill`, `icon-people`
- **Business:** `icon-building`, `icon-dept-fill`, `icon-cart-fill`, `icon-piggy-bank`
- **Package:** `icon-box`, `icon-boxes`, `icon-checklist`
- **Actions:** `icon-arrow-repeat`, `icon-magic`, `icon-pen`, `icon-usb`
- **Communication:** `icon-chat-square`
- **Status:** `icon-wifi`, `icon-circle-fill`

## Color Variables

zTheme uses CSS custom properties for easy theming:

```css
:root {
  --color-primary: #2196f3;
  --color-success: #4caf50;
  --color-danger: #f44336;
  --color-warning: #ff9800;
  --color-info: #00bcd4;
  --color-white: #ffffff;
  --color-darkgray: #333333;
}
```

## File Structure

```
zTheme/
├── dist/               # Production-ready files
│   ├── ztheme.css     # Bundled CSS (single import)
│   ├── ztheme.js      # JavaScript utilities
│   ├── icons.svg      # SVG icon sprite
│   └── fonts/         # Custom fonts
├── src/               # Source files
│   ├── css/          # Individual CSS modules
│   └── js/           # JavaScript source
└── README.md
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers

## License

MIT License - See LICENSE file for details

## Credits

- Built for [zCLI](https://github.com/YOUR_USERNAME/zolo-zcli)
- Icons adapted from Bootstrap Icons (MIT)
- Kalam font by Indian Type Foundry (OFL)

## Contributing

Contributions welcome! Please open an issue or PR on GitHub.

---

**Made with ❤️ for declarative UIs**
