# Component Showcase - Visual Reference

This document shows you exactly what each component should look like when built. Use this as a reference while coding.

## 🎨 Color Palette

### Brand Colors
```
brand-50   #f0f9ff  ████  Lightest
brand-100  #e0f2fe  ████
brand-200  #bae6fd  ████
brand-300  #7dd3fc  ████
brand-400  #38bdf8  ████
brand-500  #0ea5e9  ████  Primary
brand-600  #0284c7  ████  Primary Dark
brand-700  #0369a1  ████
brand-800  #075985  ████
brand-900  #0c4a6e  ████
brand-950  #082f49  ████  Darkest
```

### Semantic Colors
```
Success  #22c55e  ████  Green - Approved, Success
Warning  #f59e0b  ████  Yellow - Pending, Warning
Error    #ef4444  ████  Red - Rejected, Error
Info     #3b82f6  ████  Blue - Information
```

## 🔘 Button Component

### Variants
```jsx
<Button variant="primary">Primary Button</Button>
<Button variant="secondary">Secondary Button</Button>
<Button variant="ghost">Ghost Button</Button>
<Button variant="danger">Danger Button</Button>
```

**Visual:**
```
┌─────────────────┐
│ Primary Button  │  ← Blue background, white text
└─────────────────┘

┌─────────────────┐
│ Secondary Button│  ← Gray background, dark text
└─────────────────┘

  Ghost Button       ← No background, hover shows gray

┌─────────────────┐
│ Danger Button   │  ← Red background, white text
└─────────────────┘
```

### Sizes
```
Small   ┌──────────┐  sm="px-3 py-1.5"
        │  Action  │
        └──────────┘

Medium  ┌─────────────┐  md="px-4 py-2" (default)
        │   Action    │
        └─────────────┘

Large   ┌──────────────────┐  lg="px-6 py-3"
        │     Action       │
        └──────────────────┘
```

## 📝 Input Component

```jsx
<Input 
  label="Email Address" 
  placeholder="you@company.com"
  type="email"
/>
```

**Visual:**
```
Email Address
┌─────────────────────────────────┐
│ you@company.com                 │
└─────────────────────────────────┘
```

**With Error:**
```
Password
┌─────────────────────────────────┐
│ ••••••••                        │ ← Red border
└─────────────────────────────────┘
  Password must be at least 8 characters ← Red text
```

## 📦 Card Component

```jsx
<Card>
  <CardHeader>
    <h3>Card Title</h3>
  </CardHeader>
  <CardBody>
    <p>Card content goes here</p>
  </CardBody>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>
```

**Visual:**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Card Title                 ┃ ← Header (with border-bottom)
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                            ┃
┃ Card content goes here     ┃ ← Body
┃                            ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ ┌────────┐                ┃ ← Footer (with border-top)
┃ │ Action │                ┃
┃ └────────┘                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## 🏷️ Badge Component

```jsx
<Badge variant="success">Approved</Badge>
<Badge variant="warning">Pending</Badge>
<Badge variant="error">Rejected</Badge>
<Badge variant="default">Draft</Badge>
```

**Visual:**
```
 Approved   ← Green background, dark green text
 Pending    ← Yellow background, dark yellow text
 Rejected   ← Red background, dark red text
 Draft      ← Gray background, dark gray text
```

## 📊 Dashboard Card (Example)

**Metric Card:**
```
┏━━━━━━━━━━━━━━━━━━━━━┓
┃ Total Revenue        ┃
┃                      ┃
┃ $45,250.00          ┃ ← Large, bold, brand color
┃                      ┃
┃ ↗ 12% from last month┃ ← Small, muted text
┗━━━━━━━━━━━━━━━━━━━━━┛
```

## 📋 Table Component

**Modern Data Table:**
```
┏━━━━━━━━━━┯━━━━━━━━━┯━━━━━━━┯━━━━━━━━┯━━━━━━━━┓
┃ INVOICE  │ VENDOR  │ AMOUNT│ STATUS │ DATE   ┃ ← Header (uppercase, small, muted)
┣━━━━━━━━━━┿━━━━━━━━━┿━━━━━━━┿━━━━━━━━┿━━━━━━━━┫
┃ INV-001  │ Acme Co │$1,250 │Approved│Jan 15  ┃
┃ INV-002  │ Tech LLC│$850   │Pending │Jan 16  ┃ ← Hover: light background
┃ INV-003  │ Supplies│$2,100 │Paid    │Jan 17  ┃
┗━━━━━━━━━━┷━━━━━━━━━┷━━━━━━━┷━━━━━━━━┷━━━━━━━━┛
```

## 🔄 Loading States

**Spinner:**
```
    ⭯    ← Rotating circle
```

**Skeleton:**
```
┌─────────────────┐ ← Pulsing gray
│   ▒▒▒▒▒▒▒▒▒▒   │
└─────────────────┘
```

## 📭 Empty State

```
        ┌───┐
        │ 📋 │ ← Icon in circle
        └───┘

    No invoices yet

  Get started by uploading
      your first invoice

   ┌──────────────────┐
   │  Upload Invoice  │ ← Primary button
   └──────────────────┘
```

## 🎯 Status Badges in Context

**Invoice List:**
```
INV-001  Acme Corp    $1,250   Approved   Jan 15
INV-002  Tech LLC     $850     Pending    Jan 16
INV-003  Supplies Inc $2,100   Rejected   Jan 17
INV-004  Office Co    $450     Paid       Jan 18
```

## 📱 Responsive Behavior

### Desktop (1200px+)
```
┌────────┬────────────────────────────────┐
│        │ Header (Search, Profile)       │
│ Side   ├────────────────────────────────┤
│ bar    │                                │
│        │ Main Content Area              │
│ Fixed  │                                │
│        │                                │
└────────┴────────────────────────────────┘
```

### Mobile (< 768px)
```
┌────────────────────────┐
│ ☰ Header              │
├────────────────────────┤
│                        │
│ Full Width Content     │
│                        │
│ (Sidebar becomes menu) │
│                        │
└────────────────────────┘
```

## 🌙 Dark Mode

**Light Mode:**
```
Background: #fafafa (neutral-50)
Text: #171717 (neutral-900)
Border: #e5e5e5 (neutral-200)
Card: #ffffff (white)
```

**Dark Mode:**
```
Background: #0a0a0a (neutral-950)
Text: #fafafa (neutral-50)
Border: #262626 (neutral-200 in dark)
Card: #171717 (neutral-900 in dark)
```

## 🎨 Visual Hierarchy

### Typography Sizes
```
5xl  48px  ████████  Page Titles
4xl  36px  ███████   Section Titles
3xl  30px  ██████    Sub Titles
2xl  24px  █████     Card Titles
xl   20px  ████      Headings
lg   18px  ███       Sub Headings
base 16px  ██        Body Text
sm   14px  █         Small Text
xs   12px  ▌         Tiny Text
```

### Spacing Scale
```
24  96px   ████████  Page padding
16  64px   ██████    Section spacing
12  48px   ████      Large gaps
8   32px   ███       Medium gaps
6   24px   ██        Card padding
4   16px   █         Content spacing
3   12px   ▌         Small gaps
2   8px    ▏         Tiny gaps
```

## ✨ Interactive States

### Button States
```
Normal:  bg-brand-600
Hover:   bg-brand-700 (darker)
Active:  scale(0.98) (pressed)
Focus:   ring-2 ring-brand-500 (blue outline)
Disabled: opacity-50 (faded)
```

### Input States
```
Normal:  border-neutral-300
Focus:   border-brand-500 + ring-2 ring-brand-500
Error:   border-error-500
Disabled: bg-neutral-50 (gray background)
```

## 🎭 Animations

### Transitions
```
Fast:    150ms  Hover effects
Base:    200ms  Default
Slow:    300ms  Page transitions
```

### Common Animations
```
Fade In:  opacity 0 → 1
Slide Up: translateY(8px) → 0
Scale:    scale(0.95) → 1
Spin:     rotate(0deg) → 360deg (loading)
```

## 📐 Layout Grid

```
Container: max-width: 1280px
Columns:   12-column grid
Gutter:    24px (gap-6)
```

## 🎯 Component Patterns

### Card with Hover
```jsx
<Card hover> ← Lifts on hover
  <CardBody>
    Content
  </CardBody>
</Card>
```

### Form Layout
```jsx
<form className="space-y-4"> ← 16px gaps between inputs
  <Input label="Name" />
  <Input label="Email" />
  <Button>Submit</Button>
</form>
```

### Stat Card
```jsx
<Card>
  <CardBody>
    <p className="text-sm text-neutral-600">Total Revenue</p>
    <p className="text-3xl font-bold text-brand-600">$45,250</p>
    <p className="text-sm text-success-600">↗ 12% increase</p>
  </CardBody>
</Card>
```

---

## 🚀 Using This Guide

1. **Reference colors** from the palette
2. **Match spacing** to the scale
3. **Follow typography** sizes
4. **Implement states** as shown
5. **Test responsive** behavior
6. **Add animations** subtly

This visual guide ensures consistency across all components!
