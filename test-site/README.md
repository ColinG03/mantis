# 🐛 Mantis Test Site - The Worst Website Ever

This is an intentionally terrible website designed to test the Mantis web crawler's bug detection capabilities. Every page contains multiple accessibility violations, UI bugs, and usability issues.

## 🎯 Purpose

- Test Mantis's ability to detect various types of bugs
- Provide a consistent testing environment for development
- Demonstrate Mantis capabilities with real examples

## 🚀 Running the Test Site

```bash
cd test-site
npm run dev
```

Then test with Mantis:
```bash
cd ..
mantis run http://localhost:3000 --dashboard
```

## 🐛 Intentional Bugs by Page

### Homepage (`/`)
- ❌ Missing alt text on images
- ❌ Poor color contrast
- ❌ Broken heading hierarchy
- ❌ Non-semantic HTML
- ❌ Overlapping elements
- ❌ Missing form labels

### About Page (`/about`)
- ❌ Images broken/404
- ❌ Text invisible due to CSS issues
- ❌ Elements outside viewport
- ❌ Empty clickable elements
- ❌ Keyboard navigation broken

### Contact Form (`/contact`)
- ❌ Form inputs without labels
- ❌ No error handling
- ❌ Missing required field indicators
- ❌ Submit button not accessible
- ❌ CAPTCHA without alternative

### E-commerce (`/shop`)
- ❌ Product images without alt text
- ❌ Buttons without accessible names
- ❌ Price information not screen reader friendly
- ❌ Broken cart functionality

### Blog (`/blog`)
- ❌ Articles without proper headings
- ❌ Links without descriptive text
- ❌ Auto-playing media
- ❌ Pagination not accessible

### Dashboard (`/dashboard`)
- ❌ Complex data tables without proper markup
- ❌ Charts without text alternatives
- ❌ Dynamic content not announced
- ❌ Focus management issues

## 🔧 Development Notes

This site is intentionally bad - don't use it as a reference for good web development practices! 

The bugs are carefully crafted to test specific Mantis detection capabilities.